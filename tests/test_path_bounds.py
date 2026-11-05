import copy
from fractions import Fraction as F
import random
import unittest

from fm_paths import certify_path_bounds, verify_path_bounds


class PathBoundsTests(unittest.TestCase):
    def test_exact_extrema_and_integral_witnesses(self):
        rows = [(0, 4, -1, 3), (0, 0, 0, 0), (4, 4, 0, 0)]
        for target in (-3, F(-2, 7), 0, F(11, 3), 4):
            receipt = certify_path_bounds(rows, 4, 1, 1, (target, target))
            self.assertEqual(receipt['integrals'], (-3, 4))
            self.assertEqual(receipt['target'], target)
            self.assertTrue(verify_path_bounds(rows, 4, 1, 1, receipt, (target, target)))

    def test_integral_exclusion_is_not_path_infeasibility(self):
        rows = [(0, 1, 2, 3)]
        for band in ((0, 1), (4, 5)):
            receipt = certify_path_bounds(rows, 1, 0, 0, band)
            self.assertEqual(receipt['status'], 'feasible')
            self.assertEqual(receipt['integral_status'], 'excluded')
            self.assertTrue(verify_path_bounds(rows, 1, 0, 0, receipt, band))

    def test_closed_endpoint_contradiction(self):
        rows = [(0, 1, 0, 1), (1, 2, 2, 3)]
        receipt = certify_path_bounds(rows, 2, 5, 5)
        self.assertEqual(receipt['status'], 'infeasible')
        self.assertTrue(verify_path_bounds(rows, 2, 5, 5, receipt))

    def test_rate_contradiction_between_disjoint_singletons(self):
        rows = [(0, 0, 0, 0), (2, 2, 3, 3)]
        receipt = certify_path_bounds(rows, 2, 1, 2)
        self.assertEqual(receipt['status'], 'infeasible')
        self.assertTrue(verify_path_bounds(rows, 2, 1, 2, receipt))

    def test_uncovered_times_are_bounded_by_rate_premises(self):
        rows = [(1, 1, 0, 0)]
        receipt = certify_path_bounds(rows, 3, 2, 1)
        self.assertEqual(receipt['lower'][0], -2)
        self.assertEqual(receipt['upper'][0], 1)
        self.assertEqual(receipt['lower'][-1], -2)
        self.assertEqual(receipt['upper'][-1], 4)
        self.assertTrue(verify_path_bounds(rows, 3, 2, 1, receipt))

    def test_zero_horizon_and_rates(self):
        for horizon in (0, 4):
            rows = [(0, horizon, -2, 3)]
            receipt = certify_path_bounds(rows, horizon, 0, 0, (0, 0))
            self.assertEqual(receipt['integrals'], (-2 * horizon, 3 * horizon))
            self.assertTrue(verify_path_bounds(rows, horizon, 0, 0, receipt, (0, 0)))

    def test_constant_singleton_integral(self):
        rows = [(0, 5, F(3, 2), F(3, 2))]
        receipt = certify_path_bounds(rows, 5, 0, 0, (7, 8))
        self.assertEqual(receipt['theta'], 0)
        self.assertEqual(receipt['target'], F(15, 2))
        self.assertTrue(verify_path_bounds(rows, 5, 0, 0, receipt, (7, 8)))

    def test_malformed_problem_inputs(self):
        cases = [([], 1, 1, 1), ([(0, 2, 0, 1)], 1, 1, 1),
                 ([(1, 0, 0, 1)], 1, 1, 1), ([(0, 1, 2, 1)], 1, 1, 1),
                 ([(0, 1, 0, 1)], -1, 1, 1), ([(0, 1, 0, 1)], 1, -1, 1),
                 ([(0, 1, 0, 1)], 1, 1, -1), ([(0, 1, 0)], 1, 1, 1),
                 ([(0, 1, 0, 1)] * 33, 1, 1, 1)]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                certify_path_bounds(*case)
        for bad in (True, 0.5, float('inf'), float('nan'), 'nan', '1/0', '9' * 257, 1 << 513):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                certify_path_bounds([(0, 1, bad, 1)], 1, 1, 1)

    def test_rational_strings(self):
        rows = [('0', '1/2', '-1/3', '2/3')]
        receipt = certify_path_bounds(rows, '1/2', '1', '2')
        self.assertEqual(receipt['integrals'], (F(-1, 6), F(1, 3)))
        self.assertTrue(verify_path_bounds(rows, '1/2', '1', '2', receipt))

    def test_budget_validation_and_pair_limit(self):
        rows = [(0, 1, 0, 1)]
        for band in ((2, 1), (), (0, True), [0, 1, 2]):
            with self.assertRaises(ValueError):
                certify_path_bounds(rows, 1, 1, 1, band)
        for limit in (True, -1, 200001, 1.0):
            with self.assertRaises(ValueError):
                certify_path_bounds(rows, 1, 1, 1, max_pairs=limit)
        receipt = certify_path_bounds(rows, 1, 1, 1, max_pairs=0)
        self.assertEqual(receipt['status'], 'resource_unresolved')
        with self.assertRaises(ValueError):
            verify_path_bounds(rows, 1, 1, 1, receipt)

    def test_receipt_tampering(self):
        rows = [(0, 4, -1, 3), (0, 0, 0, 0), (4, 4, 0, 0)]
        receipt = certify_path_bounds(rows, 4, 1, 1, (0, 0))
        for key in ('lower', 'upper', 'integrals', 'path'):
            bad = copy.deepcopy(receipt)
            bad[key] = list(bad[key])
            bad[key][0] += F(1, 11)
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_path_bounds(rows, 4, 1, 1, bad, (0, 0))
        for key, value in [('theta', 2), ('target', 1), ('active', [None]),
                           ('points', []), ('points', [0] * 4097), ('extra', True)]:
            bad = copy.deepcopy(receipt)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_path_bounds(rows, 4, 1, 1, bad, (0, 0))
        with self.assertRaises(ValueError):
            verify_path_bounds(rows, 4, 1, 1, receipt)

    def test_missing_crossings_cannot_certify_extrema(self):
        rows = [(0, 4, -1, 3), (0, 0, 0, 0), (4, 4, 0, 0)]
        bad = dict(status='feasible', points=[0, 4], lower=[0, 0], upper=[0, 0],
                   active=[(1, 1)], integrals=(0, 0))
        with self.assertRaises(ValueError):
            verify_path_bounds(rows, 4, 1, 1, bad)

    def test_infeasibility_receipt_tampering(self):
        rows = [(0, 0, 0, 0), (1, 1, 2, 2)]
        receipt = certify_path_bounds(rows, 1, 1, 1)
        for key, value in [('time', -1), ('lower', -9), ('upper', 9),
                           ('lower_index', True), ('upper_index', -1), ('extra', 0)]:
            bad = dict(receipt, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_path_bounds(rows, 1, 1, 1, bad)

    def test_large_generated_rationals_roundtrip(self):
        value = F(1, (1 << 301) + 17)
        rows = [(0, 2, -1, 2), (0, 0, value, value), (2, 2, 1, 1)]
        receipt = certify_path_bounds(rows, 2, 1, 1)
        self.assertEqual(receipt['status'], 'feasible')
        self.assertTrue(verify_path_bounds(rows, 2, 1, 1, receipt))

    def test_seeded_exact_dynamic_program_reference(self):
        rng = random.Random(71249)
        for case in range(80):
            horizon = 2
            rows = [(0, horizon, -2, 2)]
            for unused in range(rng.randrange(1, 5)):
                start = rng.randrange(horizon + 1)
                end = rng.randrange(start, horizon + 1)
                low = rng.randrange(-2, 3)
                rows.append((start, end, low, rng.randrange(low, 3)))
            nodes = [F(i, 2) for i in range(2 * horizon + 1)]
            states = [F(i, 2) for i in range(-4, 5)]
            current = {x: (F(0), F(0)) for x in states
                       if all(a <= x <= b for s, e, a, b in rows if s <= 0 <= e)}
            for time in nodes[1:]:
                next_values = {}
                for x in states:
                    if not all(a <= x <= b for s, e, a, b in rows if s <= time <= e):
                        continue
                    candidates = [(lo + (y + x) / 4, hi + (y + x) / 4)
                                  for y, (lo, hi) in current.items() if abs(x - y) <= F(1, 2)]
                    if candidates:
                        next_values[x] = (min(lo for lo, hi in candidates), max(hi for lo, hi in candidates))
                current = next_values
            receipt = certify_path_bounds(rows, horizon, 1, 1)
            with self.subTest(case=case):
                self.assertTrue(verify_path_bounds(rows, horizon, 1, 1, receipt))
                if not current:
                    self.assertEqual(receipt['status'], 'infeasible')
                else:
                    self.assertEqual(receipt['status'], 'feasible')
                    self.assertEqual(receipt['integrals'],
                                     (min(lo for lo, hi in current.values()), max(hi for lo, hi in current.values())))


if __name__ == '__main__':
    unittest.main()
