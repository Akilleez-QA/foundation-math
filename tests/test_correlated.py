import json
import subprocess
import sys
import unittest
from fractions import Fraction
from unittest.mock import patch
from fm_correlated import Invalid, Limit, verify
from fm_correlated.quadratic import Arithmetic, LIMITS, decode


def fixture():
    return {'schema': 'fm-correlated-quadratic/1',
        'model': {'metric': [[1]], 'B': [], 'd': [], 'scope': 'exact_joint_image',
            'scenarios': [{'p': [0], 'L': [[1]], 'a0': 1, 'b': [0], 'Q': [[0]]}]},
        'budget': 2, 'point': [0], 'upper': [{'lambda': 1, 'y': [0], 'bound': 2}],
        'lower': {'pairs': [
            {'scenario': 0, 'u': [-1], 'a': 1, 'c': [-1], 'weight': '1/2'},
            {'scenario': 0, 'u': [1], 'a': 1, 'c': [1], 'weight': '1/2'}],
            'mu': [], 'v': [0], 'bound': 2}, 'probes': [],
        'offset_nonnegative': [{'lambda': 0, 'y': [0], 'bound': -1}]}


def check(obj):
    return verify(json.dumps(obj))


class CorrelatedTests(unittest.TestCase):
    def test_matching_bounds(self):
        r = check(fixture())
        self.assertEqual((r['upper'], r['lower'], r['represented_bound_gap']), ('2', '2', '0'))
        self.assertTrue(r['point_admitted_by_upper'])
        self.assertTrue(r['offsets_proved_nonnegative'])
        self.assertFalse(r['target_globally_excluded'])

    def test_outer_not_target_exclusion(self):
        obj = fixture()
        obj['budget'] = '3/2'
        self.assertTrue(check(obj)['target_globally_excluded'])
        obj['model']['scope'] = 'outer_joint_image'
        r = check(obj)
        self.assertFalse(r['target_globally_excluded'])
        self.assertTrue(r['outer_image_globally_excluded'])

    def test_correlated_pair_and_non_global_probe(self):
        obj = fixture()
        obj['model']['scenarios'][0].update(a0=2, b=[1], Q=[[-1]])
        obj.update(upper=[{'lambda': 1, 'y': [1], 'bound': 4}], lower=None,
                   offset_nonnegative=None, probes=[{'scenario': 0, 'u': [1], 'a': 3, 'c': [1]}])
        r = check(obj)
        self.assertEqual(r['probes'][0]['cost'], '4')
        self.assertTrue(r['probes'][0]['defeats_supplied_point'])
        self.assertFalse(r['probes'][0]['global_exclusion'])
        obj['model']['scope'] = 'outer_joint_image'
        self.assertFalse(check(obj)['target_globally_excluded'])
        obj['probes'][0]['a'] = -1
        with self.assertRaises(Invalid):
            check(obj)

    def test_singular_range_failure(self):
        obj = fixture()
        obj['model']['scenarios'][0]['b'] = [1]
        with self.assertRaisesRegex(Invalid, 'range'):
            check(obj)

    def test_psd_zero_pivots_and_strictness(self):
        ar = Arithmetic()
        def mat(rows):
            return [[Fraction(x) for x in row] for row in rows]
        self.assertFalse(ar.psd(mat([[0, 1], [1, 0]])))
        self.assertFalse(ar.psd(mat([[-1, 0], [0, -1]])))
        self.assertTrue(ar.psd(mat([[1, 1], [1, 1]])))
        self.assertFalse(ar.psd(mat([[1, 1], [1, 1]]), strict=True))
        self.assertTrue(ar.psd(mat([[0, 0], [0, 1]])))

    def test_row_dual(self):
        obj = fixture()
        obj['model'].update(B=[[-1]], d=[-2])
        obj.update(point=[2], upper=[{'lambda': 3, 'y': [-1], 'bound': 10}])
        obj['lower'] = {'pairs': [{'scenario': 0, 'u': [-1], 'a': 1, 'c': [-1], 'weight': 1}],
                        'mu': [6], 'v': [2], 'bound': 10}
        self.assertEqual(check(obj)['represented_bound_gap'], '0')
        obj['point'] = [0]
        with self.assertRaisesRegex(Invalid, 'row-feasible'):
            check(obj)

    def test_empty_dimensions(self):
        obj = fixture()
        obj['model'].update(metric=[], scenarios=[{'p': [], 'L': [], 'a0': 3, 'b': [], 'Q': []}])
        obj.update(point=[], upper=[{'lambda': 0, 'y': [], 'bound': 3}], lower=None, offset_nonnegative=None)
        self.assertEqual(check(obj)['upper'], '3')
        obj['model'].update(metric=[[2]], scenarios=[{'p': [1], 'L': [[]], 'a0': 3, 'b': [], 'Q': []}])
        obj.update(point=[0], upper=[{'lambda': 0, 'y': [], 'bound': 5}])
        self.assertEqual(check(obj)['upper'], '5')

    def test_nonidentity_metric_multiple_scenarios(self):
        obj = fixture()
        obj['model'].update(metric=[[2, 1], [1, 2]], scenarios=[
            {'p': [0, 0], 'L': [[1], [0]], 'a0': 1, 'b': [0], 'Q': [[0]]},
            {'p': [1, 1], 'L': [[], []], 'a0': 1, 'b': [], 'Q': []}])
        obj.update(point=[0, 0], lower=None, offset_nonnegative=None,
            upper=[{'lambda': 2, 'y': [0], 'bound': 3}, {'lambda': 0, 'y': [], 'bound': 7}])
        self.assertEqual(check(obj)['upper'], '7')

    def test_invalid_witness_mutations(self):
        mutations = [
            lambda x: x['upper'][0].update(bound=1),
            lambda x: x['upper'][0].update(**{'lambda': -1}),
            lambda x: x['upper'][0].update(y=[]),
            lambda x: x['lower'].update(bound=3),
            lambda x: x['lower'].update(v=[1]),
            lambda x: x['lower']['pairs'][0].update(weight=1),
            lambda x: x['lower']['pairs'][0].update(u=[2]),
            lambda x: x['lower']['pairs'][0].update(scenario=True),
            lambda x: x['offset_nonnegative'][0].update(bound=1),
            lambda x: x['model'].update(metric=[[0]]),
            lambda x: x['model'].update(scope='unverified'),
            lambda x: x.update(unexpected=True),
            lambda x: x['model']['scenarios'][0].update(L=[]),
            lambda x: x.update(upper=[])]
        for index, mutate in enumerate(mutations):
            obj = fixture()
            mutate(obj)
            with self.subTest(index=index), self.assertRaises(Invalid):
                check(obj)

    def test_numeric_and_json_rejection(self):
        for value in (True, 0.5, '0.5', '1/0', '01', '+1', '1/-2', 2**96):
            obj = fixture()
            obj['budget'] = value
            with self.subTest(value=value), self.assertRaises(Invalid):
                check(obj)
        for data in ('{"a":1,"a":2}', '[NaN]', '[1e0]', '['*17 + ']'*17,
                     ' '*(LIMITS['bytes']+1), '[' + ','.join(['0']*4096) + ']'):
            with self.subTest(data=data[:30]), self.assertRaises(Invalid):
                decode(data)
        with self.assertRaises(UnicodeError):
            verify(b'\xff')

    def test_arithmetic_limits(self):
        with patch.dict(LIMITS, operations=0):
            with self.assertRaises(Limit):
                check(fixture())
        with patch.dict(LIMITS, intermediate_bits=1):
            with self.assertRaises(Limit):
                Arithmetic().mul(Fraction(2), Fraction(1))

    def test_rational_grid(self):
        for b in (-2, -1, 0, 1, 2):
            obj = fixture()
            lam = max(1, abs(b))
            bound = 3 + lam + Fraction(b*b, lam)
            obj['model']['scenarios'][0].update(a0=3, b=[b], Q=[[-1]])
            obj.update(upper=[{'lambda': lam, 'y': [str(Fraction(b, lam))], 'bound': str(bound)}],
                       lower=None, offset_nonnegative=None)
            upper = Fraction(check(obj)['upper'])
            for i in range(-20, 21):
                u = Fraction(i, 20)
                a, c = 3 + 2*b*u - u*u, u
                self.assertLessEqual(a+c*c, upper)

    def test_cli(self):
        for value, expected in ((json.dumps(fixture()), 0), ('{}', 2)):
            p = subprocess.run([sys.executable, '-S', '-B', '-m', 'fm_correlated', '-'],
                               input=value, text=True, capture_output=True, timeout=10)
            self.assertEqual(p.returncode, expected, p.stderr)
            self.assertIn('status', json.loads(p.stdout))
