import json
import unittest
from fractions import Fraction
from unittest.mock import patch
from fm_correlated import Invalid, Limit, verify
from fm_correlated.quadratic import Arithmetic, LIMITS, decode


def fixture():
    return {'schema': 'fm-correlated-quadratic/1',
        'model': {'metric': [[1]], 'B': [], 'd': [], 'scope': 'exact_joint_image',
            'scenarios': [{'p': [0], 'L': [[1]], 'a0': 2, 'b': [1], 'Q': [[-1]]}]},
        'budget': 2, 'point': [0], 'probes': [{'scenario': 0, 'u': [1], 'a': 3, 'c': [1]}]}


def check(obj):
    return verify(json.dumps(obj))


class CorrelatedTests(unittest.TestCase):
    def test_correlated_pair_and_non_global_probe(self):
        for scope in ('exact_joint_image', 'outer_joint_image'):
            obj = fixture()
            obj['model']['scope'] = scope
            r = check(obj)
            self.assertEqual(set(r), set('schema status scope budget row_feasible_point probes operations premises'.split()))
            self.assertTrue(r['row_feasible_point'])
            self.assertEqual(r['probes'], [dict(cost='4', defeats_supplied_point=True, scope=scope, global_exclusion=False)])
            obj['budget'] = 4
            self.assertFalse(check(obj)['probes'][0]['defeats_supplied_point'])

    def test_psd_zero_pivots_and_strictness(self):
        for rows, psd, pd in (([[0, 1], [1, 0]], False, False), ([[-1, 0], [0, -1]], False, False),
                              ([[1, 1], [1, 1]], True, False), ([[0, 0], [0, 1]], True, False)):
            mat = [[Fraction(x) for x in row] for row in rows]
            self.assertEqual(Arithmetic().psd(mat), psd)
            self.assertEqual(Arithmetic().psd(mat, strict=True), pd)

    def test_row_feasibility(self):
        obj = fixture()
        obj['model'].update(B=[[-1]], d=[-2])
        obj['point'] = [2]
        self.assertTrue(check(obj)['row_feasible_point'])
        obj['point'] = [0]
        with self.assertRaisesRegex(Invalid, 'row-feasible'): check(obj)

    def test_empty_dimensions_and_nonidentity_metric(self):
        obj = fixture()
        obj['model'].update(metric=[], scenarios=[dict(p=[], L=[], a0=3, b=[], Q=[])])
        obj.update(point=[], probes=[dict(scenario=0, u=[], a=3, c=[])])
        self.assertEqual(check(obj)['probes'][0]['cost'], '3')
        obj['model'].update(metric=[[2, 1], [1, 2]], scenarios=[
            dict(p=[0, 0], L=[[1], [0]], a0=1, b=[0], Q=[[0]]),
            dict(p=[1, 1], L=[[], []], a0=1, b=[], Q=[])])
        obj.update(point=[0, 0], probes=[dict(scenario=0, u=[1], a=1, c=[1, 0]), dict(scenario=1, u=[], a=1, c=[1, 1])])
        self.assertEqual([p['cost'] for p in check(obj)['probes']], ['3', '7'])

    def test_invalid_mutations(self):
        for section, field, value in [('model', 'metric', [[0]]), ('model', 'scope', 'unverified'),
                ('model', 'scenarios', []), ('model', 'B', [[]]), ('root', 'unexpected', True),
                ('root', 'point', []), ('root', 'upper', None), ('root', 'probes', [0]*13),
                ('scenario', 'L', []), ('scenario', 'Q', [[0, 1], [0, 0]]),
                ('probe', 'u', [2]), ('probe', 'scenario', True), ('probe', 'a', -1),
                ('probe', 'c', [-1]), ('probe', 'weight', 1)]:
            obj = fixture()
            target = {'root': obj, 'model': obj['model'], 'scenario': obj['model']['scenarios'][0], 'probe': obj['probes'][0]}[section]
            target[field] = value
            with self.subTest(section=section, field=field), self.assertRaises(Invalid): check(obj)

    def test_numeric_and_json_rejection(self):
        for value in (True, 0.5, '0.5', '1/0', '01', '+1', '1/-2', 2**96):
            obj = fixture()
            obj['budget'] = value
            with self.subTest(value=value), self.assertRaises(Invalid): check(obj)
        for data in ('{"a":1,"a":2}', '[NaN]', '[1e0]', '['*17 + ']'*17, '1'*31,
                     ' '*(LIMITS['bytes']+1), '[' + ','.join(['0']*4096) + ']'):
            with self.subTest(data=data[:30]), self.assertRaises(Invalid): decode(data)
        with self.assertRaises(UnicodeError): verify(b'\xff')
        self.assertEqual(verify(json.dumps(fixture()).encode()), check(fixture()))
        self.assertEqual(decode('"[\\\""'), '["')

    def test_arithmetic_limits(self):
        with patch.dict(LIMITS, operations=0), self.assertRaises(Limit): check(fixture())
        with patch.dict(LIMITS, intermediate_bits=1), self.assertRaises(Limit):
            Arithmetic().mul(Fraction(2), Fraction(1))
