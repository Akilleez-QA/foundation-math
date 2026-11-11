from copy import deepcopy
from fractions import Fraction as Q
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from fm_minimax import certify
from fm_minimax import core


def scenario(name, constant, center, target=None, row_offset=None):
    return {'id': name, 'constant': constant, 'center': center,
            'target': [] if target is None else target,
            'row_offset': [] if row_offset is None else row_offset}


def problem(metric, scenarios, level, rows=None, bounds=None, equalities=None):
    return {'metric': metric, 'scenarios': scenarios, 'level': level,
            'rows': [] if rows is None else rows,
            'bounds': [] if bounds is None else bounds,
            'equalities': [] if equalities is None else equalities}


def dual(weights, rows=None, equalities=None):
    return {'scenario_weights': weights,
            'row_multipliers': [] if rows is None else rows,
            'equality_multipliers': [] if equalities is None else equalities}


def construction():
    p = problem([[2, 1], [1, 3]],
                [scenario('a', -4, [-1, 0], row_offset=[2]),
                 scenario('b', 12, [3, 0], row_offset=[1])], 24,
                rows=[[0, -1]], bounds=[0])
    w = {'point': [1, 2], 'dual': dual([Q(1, 4), Q(3, 4)], [10])}
    return p, w


class MinimaxTests(unittest.TestCase):
    def test_two_active_nondiagonal_metric(self):
        p, w = construction()
        r = certify(p, w)
        self.assertEqual(r['status'], 'feasible')
        self.assertEqual(r['exact_threshold'], 24)
        self.assertTrue(r['kkt']['verified'])
        self.assertEqual(r['witness_checks']['point']['scenario_total_costs'], [24, 24])
        self.assertEqual(r['tightened_common_rows'], [-2])
        self.assertEqual(r['row_feasibility'], 'proved_nonempty')

    def test_strict_dual_level_and_equality(self):
        p, w = construction()
        self.assertEqual(certify(p, {'dual': w['dual']})['status'], 'unresolved')
        p['level'] = Q(2399, 100)
        r = certify(p, {'dual': w['dual']})
        self.assertEqual(r['status'], 'infeasible')
        self.assertEqual(r['row_feasibility'], 'not_established')
        r = certify(p, w)
        self.assertEqual(r['exact_threshold'], 24)
        self.assertEqual(r['row_feasibility'], 'proved_nonempty')

    def test_equality_multiplier_sign(self):
        p = problem([[4]], [scenario('q', -2, [1], target=[4])], 14,
                    equalities=[[2]])
        w = {'point': [3], 'dual': dual([1], equalities=[-8])}
        self.assertEqual(certify(p, w)['exact_threshold'], 14)
        w['dual']['equality_multipliers'] = [8]
        r = certify(p, w)
        self.assertEqual(r['status'], 'feasible')
        self.assertFalse(r['kkt']['verified'])
        self.assertNotIn('exact_threshold', r)

    def test_negative_constant_and_negative_level(self):
        p = problem([[3]], [scenario('q', -7, [2])], -7)
        self.assertEqual(certify(p, {'point': [2], 'dual': dual([1])})['exact_threshold'], -7)
        p['level'] = -8
        self.assertEqual(certify(p, {'dual': dual([1])})['status'], 'infeasible')

    def test_failed_point_is_not_exclusion(self):
        p, w = construction()
        for candidate in ([1, 0], [100, 100], [False, 2], [1]):
            self.assertEqual(certify(p, {'point': candidate})['status'], 'unresolved')
        r = certify(p, {'point': w['point'], 'dual': dual([-1, 2], [0])})
        self.assertEqual(r['status'], 'feasible')
        self.assertFalse(r['witness_checks']['dual']['valid'])

    def test_nonoptimal_point_is_not_threshold(self):
        p = problem([[2]], [scenario('q', 0, [0])], 10)
        r = certify(p, {'point': [1], 'dual': dual([1])})
        self.assertEqual(r['status'], 'feasible')
        self.assertFalse(r['kkt']['verified'])
        self.assertNotIn('exact_threshold', r)

    def test_farkas_and_zero_boundary(self):
        p = problem([[1]], [scenario('q', 0, [0], row_offset=[0, 0])], 100,
                    rows=[[1], [-1]], bounds=[1, -2])
        w = {'farkas': {'row_multipliers': [1, 1], 'equality_multipliers': []}}
        r = certify(p, w)
        self.assertEqual((r['status'], r['row_feasibility']), ('infeasible', 'proved_empty'))
        p['bounds'] = [1, -1]
        self.assertEqual(certify(p, w)['status'], 'unresolved')
        w['farkas']['row_multipliers'] = [-1, -1]
        self.assertEqual(certify(p, w)['status'], 'unresolved')

    def test_incompatible_equalities_and_range(self):
        p = problem([[1]], [scenario('a', 0, [0], [1]), scenario('b', 0, [1], [1])], 10,
                    equalities=[[1]])
        r = certify(p)
        self.assertEqual((r['status'], r['row_feasibility']), ('infeasible', 'proved_empty'))
        p = problem([[1]], [scenario('a', 0, [0], [2, 5])], 100,
                    equalities=[[1], [2]])
        r = certify(p)
        self.assertEqual(r['status'], 'infeasible')
        z = r['obstruction']['left_null_multiplier']
        self.assertEqual(z[0] + 2 * z[1], 0)
        self.assertNotEqual(2 * z[0] + 5 * z[1], 0)

    def test_redundant_equalities_and_singleton_rows(self):
        p = problem([[2]], [scenario('a', 3, [0], [1, 2], [0, 0])], 5,
                    equalities=[[1], [2]], rows=[[1], [-1]], bounds=[1, -1])
        r = certify(p, {'point': [1], 'dual': dual([1], [0, 0], [-4, 0])})
        self.assertEqual(r['exact_threshold'], 5)

    def test_empty_dimension(self):
        p = problem([], [scenario('a', -3, [], [0], [2]), scenario('b', -2, [], [0], [1])], -2,
                    equalities=[[]], rows=[[]], bounds=[2])
        r = certify(p, {'point': [], 'dual': dual([0, 1], [0], [0])})
        self.assertEqual(r['exact_threshold'], -2)
        p['bounds'] = [1]
        r = certify(p, {'farkas': {'row_multipliers': [1], 'equality_multipliers': [0]}})
        self.assertEqual(r['row_feasibility'], 'proved_empty')

    def test_96_constructed_scalar_thresholds(self):
        for m in (Q(2, 7), Q(5, 3), Q(11, 2)):
            for k in (-3, -1, 0, 2):
                for c in (-9, 4):
                    for distance in (Q(1, 5), Q(2, 3), 1, 3):
                        x = k + distance
                        value = c + m * distance ** 2
                        p = problem([[m]], [scenario('q', c, [k], row_offset=[0])], value,
                                    rows=[[-1]], bounds=[-x])
                        w = {'point': [x], 'dual': dual([1], [2 * m * distance])}
                        self.assertEqual(certify(p, w)['exact_threshold'], value)
                        p['level'] = value - Q(1, 37)
                        self.assertEqual(certify(p, w)['status'], 'infeasible')

    def test_coordinate_congruence(self):
        p, w = construction()
        p['metric'] = [[8, 6], [6, 27]]
        p['rows'] = [[0, -3]]
        p['scenarios'][0]['center'] = [Q(-1, 2), 0]
        p['scenarios'][1]['center'] = [Q(3, 2), 0]
        w['point'] = [Q(1, 2), Q(2, 3)]
        self.assertEqual(certify(p, w)['exact_threshold'], 24)

    def test_invalid_metric_scalars_shapes_and_keys(self):
        p = problem([[1]], [scenario('a', 0, [0])], 0)
        for value in (True, 0.25, '0.25', '1/0', 'nan', None):
            self.assertEqual(certify(dict(p, level=value))['status'], 'invalid_input')
        for metric in ([[0]], [[-1]], [[1, 2], [2, 1]], [[1, 1], [0, 1]], [[1], [1]]):
            self.assertEqual(certify(dict(p, metric=metric))['status'], 'invalid_input')
        for changes in ({'scenarios': []}, {'scenarios': p['scenarios'] * 2}, {'unexpected': 1}, {'rows': [[1, 2]]}):
            self.assertEqual(certify(dict(p, **changes))['status'], 'invalid_input')
        for bad in (None, [], {'surprise': 1}, {'point': [False]}):
            self.assertEqual(certify(p, bad)['status'], 'unresolved')

    def test_limits_fail_unresolved(self):
        p = problem([[1]], [scenario('a', 0, [0])], 0)
        for value in (1 << 513, '1' * 321):
            self.assertEqual(certify(dict(p, level=value))['status'], 'unresolved')
        many = [scenario(str(i), 0, [0]) for i in range(9)]
        self.assertEqual(certify(dict(p, scenarios=many))['status'], 'unresolved')
        with patch.object(core, 'MAX_OPS', 2):
            self.assertEqual(certify(p)['status'], 'unresolved')
        with self.assertRaises(core.Limit):
            core.Exact().bound(Q(1 << (core.MAX_ARITH_BITS + 1)))

    def test_cli_and_duplicate_keys(self):
        p, w = construction()
        request = json.dumps(core.jsonable({'problem': p, 'witness': w}))
        for payload, status in ((request, 'feasible'), ('{"problem":{},"problem":{}}', 'invalid_input'),
                                ('[', 'invalid_input'), (' ' * (core.MAX_JSON_BYTES + 1), 'unresolved')):
            r = subprocess.run([sys.executable, '-B', '-m', 'fm_minimax'], input=payload,
                               text=True, capture_output=True, check=True)
            self.assertEqual(json.loads(r.stdout)['status'], status)
            self.assertEqual(json.loads(r.stdout)['schema'], 'fm-quadratic-minimax/1')


if __name__ == '__main__':
    unittest.main()
