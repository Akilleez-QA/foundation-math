from fractions import Fraction as Q
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


class MinimaxTests(unittest.TestCase):
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

    def test_empty_dimension(self):
        p = problem([], [scenario('a', -3, [], [0], [2]), scenario('b', -2, [], [0], [1])], -2,
                    equalities=[[]], rows=[[]], bounds=[2])
        r = certify(p)
        self.assertEqual(r['status'], 'unresolved')
        self.assertEqual(r['tightened_common_rows'], [0])
        self.assertEqual(r['common_equality_targets'], [[0], [0]])
        p['bounds'] = [1]
        self.assertEqual(certify(p)['row_feasibility'], 'not_established')

    def test_invalid_metric_scalars_shapes_and_keys(self):
        p = problem([[1]], [scenario('a', 0, [0])], 0)
        for value in (True, 0.25, '0.25', '1/0', 'nan', None):
            self.assertEqual(certify(dict(p, level=value))['status'], 'invalid_input')
        for metric in ([[0]], [[-1]], [[1, 2], [2, 1]], [[1, 1], [0, 1]], [[1], [1]]):
            self.assertEqual(certify(dict(p, metric=metric))['status'], 'invalid_input')
        for changes in ({'scenarios': []}, {'scenarios': p['scenarios'] * 2}, {'unexpected': 1}, {'rows': [[1, 2]]}):
            self.assertEqual(certify(dict(p, **changes))['status'], 'invalid_input')

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

    def test_tightened_common_rows(self):
        p = problem([[1]], [scenario('a', 0, [0], row_offset=['1/2', -3]),
                            scenario('b', 0, [1], row_offset=[-2, '2/3'])], 0,
                    rows=[[1], [-1]], bounds=[3, 2])
        self.assertEqual(certify(p)['tightened_common_rows'], [Q(5, 2), Q(4, 3)])

    def test_without_witness_is_unresolved(self):
        r = certify(problem([[1]], [scenario('a', -7, [2])], -8))
        self.assertEqual(r['status'], 'unresolved')
        self.assertEqual(r['reason'], 'no witness verification in this version')
        self.assertEqual(r['row_feasibility'], 'not_established')


if __name__ == '__main__':
    unittest.main()
