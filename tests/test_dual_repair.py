from dataclasses import replace
from fractions import Fraction as F
from itertools import product
import random
import unittest
from fm_optimization import (DualBound, InvalidCertificate, LinearProgram, Unsupported,
                             augment_box, program_digest, repair_dual,
                             verify_attainment, verify_dual_bound)


class DualRepairTests(unittest.TestCase):
    def setUp(self):
        self.base = LinearProgram('synthetic-equality', 2, ((1, 0, 3), (-1, 0, 2)),
                                  ((1, -1, 4),), (1, -1))
        self.expected = LinearProgram('synthetic-equality', 2,
                                      ((1, 0, 3), (-1, 0, 2), (1, 0, 3),
                                       (0, 1, -1), (-1, 0, 2), (0, -1, 6)),
                                      ((1, -1, 4),), (1, -1))

    def test_box_repair_and_signed_equality_correction(self):
        proof = repair_dual(self.base, (0, 0), (F(2, 3),), box=((-2, -6), (3, -1)))
        self.assertEqual(proof.upper_bound, F(17, 3))
        self.assertTrue(verify_dual_bound(self.expected, proof))
        exact = repair_dual(self.base, (0, 0), (F(2, 3),), (F(1, 3),))
        self.assertEqual(exact.upper_bound, 4)
        self.assertTrue(verify_attainment(self.base, exact, (0, -4)))
        negative = replace(self.base, equalities=((1, -1, -4),))
        signed = repair_dual(negative, (0, 0), (F(5, 4),), (F(-1, 4),))
        self.assertEqual(signed.upper_bound, -4)
        self.assertTrue(verify_attainment(negative, signed, (0, 4)))

    def test_clamp_recomputes_residual_and_signed_support(self):
        base = LinearProgram('synthetic-clamp', 1, ((-1, -3), (1, 7)), (), (F(-2, 5),))
        expected = LinearProgram('synthetic-clamp', 1,
                                 ((-1, -3), (1, 7), (1, 7), (-1, -3)), (), (F(-2, 5),))
        proof = repair_dual(base, (F(-2, 5), 0), (), box=((3,), (7,)))
        self.assertEqual(proof.inequality_multipliers, (0, 0, 0, F(2, 5)))
        self.assertEqual(proof.upper_bound, F(-6, 5))
        self.assertTrue(verify_attainment(expected, proof, (3,)))

    def test_box_intersection_not_original_domain(self):
        base = LinearProgram('synthetic-box', 1, ((-1, -3),), (), (-1,))
        proof = repair_dual(base, (0,), (), box=((5,), (7,)))
        wide = LinearProgram('synthetic-box', 1, ((-1, -3), (1, 7), (-1, -3)), (), (-1,))
        narrow = LinearProgram('synthetic-box', 1, ((-1, -3), (1, 7), (-1, -5)), (), (-1,))
        self.assertTrue(verify_dual_bound(narrow, proof))
        self.assertFalse(verify_dual_bound(wide, proof))
        self.assertFalse(verify_dual_bound(base, proof))
        self.assertGreater(-3, proof.upper_bound)

    def test_failed_repair_not_objective_unboundedness(self):
        ray = LinearProgram('synthetic-ray', 1, ((-1, -3),), (), (-1,))
        with self.assertRaises(InvalidCertificate):
            repair_dual(ray, (2,), ())
        proof = repair_dual(ray, (1,), ())
        self.assertEqual(proof.upper_bound, -3)
        self.assertTrue(verify_attainment(ray, proof, (3,)))

    def test_common_offset_and_constant_objective(self):
        base = LinearProgram('synthetic-constant', 2, (), (), (0, 0), F(-11, 7))
        proof = repair_dual(base, (), ())
        self.assertEqual(proof.upper_bound, F(-11, 7))
        self.assertTrue(verify_attainment(base, proof, (100, -100)))
        self.assertFalse(verify_dual_bound(replace(base, offset=0), proof))

    def test_empty_and_lower_dimensional_families(self):
        empty = LinearProgram('synthetic-empty', 1, ((1, 0), (-1, -1)), (), (0,))
        proof = repair_dual(empty, (1, 1), ())
        self.assertEqual(proof.upper_bound, -1)
        self.assertTrue(verify_dual_bound(empty, proof))
        for point in ((0,), (1,), (F(1, 2),)):
            self.assertFalse(verify_attainment(empty, proof, point))
        point_set = LinearProgram('synthetic-singleton', 1, (), (), (2,), -1)
        point_proof = repair_dual(point_set, (), (), box=((3,), (3,)))
        expected = LinearProgram('synthetic-singleton', 1, ((1, 3), (-1, -3)), (), (2,), -1)
        self.assertTrue(verify_attainment(expected, point_proof, (3,)))
        self.assertEqual(point_proof.upper_bound, 5)

    def test_binding_all_program_fields_and_row_order(self):
        proof = repair_dual(self.base, (0, 0), (1,))
        changes = ({'context': 'different'}, {'inequalities': tuple(reversed(self.base.inequalities))},
                   {'inequalities': ((1, 0, 4), (-1, 0, 2))}, {'equalities': ((1, -1, 5),)},
                   {'objective': (-1, 1)}, {'offset': 1})
        for fields in changes:
            self.assertFalse(verify_dual_bound(replace(self.base, **fields), proof))
        self.assertEqual(program_digest(replace(self.base, objective=(F(1), F(-1)))),
                         program_digest(self.base))

    def test_tampered_and_malformed_certificates(self):
        proof = repair_dual(self.base, (0, 0), (1,))
        changes = ({'upper_bound': 5}, {'upper_bound': True}, {'upper_bound': float('inf')},
                   {'program_digest': 0}, {'inequality_multipliers': (-1, 0)},
                   {'inequality_multipliers': (0,)}, {'inequality_multipliers': [0, 0]},
                   {'equality_multipliers': (F(1, 2),)}, {'equality_multipliers': (1.0,)},
                   {'equality_multipliers': (1 << 4096,)}, {'upper_bound': 1 << 8192})
        for fields in changes:
            mutation = replace(proof, **fields)
            self.assertFalse(verify_dual_bound(self.base, mutation))
            self.assertFalse(verify_attainment(self.base, mutation, (0, -4)))
        self.assertFalse(verify_dual_bound(self.base, None))

    def test_bad_points_and_bound_does_not_imply_attainment(self):
        proof = repair_dual(self.base, (0, 0), (1,))
        for point in ((4, 0), (0, 0), (0,), [0, -4], (True, -4), (0.0, -4), (1 << 4096, 0)):
            self.assertFalse(verify_attainment(self.base, proof, point))
        loose = repair_dual(self.base, (1, 1), (1,))
        self.assertTrue(verify_dual_bound(self.base, loose))
        self.assertFalse(verify_attainment(self.base, loose, (0, -4)))

    def test_input_types_shapes_and_limits(self):
        for dimension in (0, 17, True, 1.0):
            with self.assertRaises(Unsupported):
                LinearProgram('bad', dimension, (), (), ())
        for context in ('', ' ', 'x' * 129, 0):
            with self.assertRaises(Unsupported):
                LinearProgram(context, 1, (), (), (1,))
        for bad in (True, 1.0, '1', F(1, 1 << 256), 1 << 256):
            with self.assertRaises(Unsupported):
                LinearProgram('bad', 1, (), (), (bad,))
        for fields in ({'inequalities': []}, {'equalities': [(1, 0)]}, {'objective': [1, -1]},
                       {'inequalities': ((1, 0),)}, {'inequalities': ((0, 0, 0),) * 129},
                       {'equalities': ((0, 0, 0),) * 65}):
            with self.assertRaises(Unsupported):
                replace(self.base, **fields)
        with self.assertRaises(Unsupported):
            verify_dual_bound(None, None)

    def test_invalid_repair_candidates_boxes_and_augmentation_limit(self):
        for y, z, correction in (([0, 0], (1,), None), ((0,), (1,), None),
                                  ((0, 0), (1.0,), None), ((0, 0), (1,), ()),
                                  ((0, 0), (1,), (1 << 4096,))):
            with self.assertRaises(Unsupported):
                repair_dual(self.base, y, z, correction)
        for box in ([], (), ((0, 0),), ((0,), (1,)), ((2, 2), (1, 1)), ((0, 0), (1, True))):
            with self.assertRaises(Unsupported):
                repair_dual(self.base, (0, 0), (0,), box=box)
        crowded = LinearProgram('limit', 1, ((0, 0),) * 127, (), (0,))
        with self.assertRaises(Unsupported):
            repair_dual(crowded, (0,) * 127, (), box=((0,), (1,)))

    def test_maximum_dimensions_and_row_counts(self):
        n = 16
        base = LinearProgram('maximum', n, ((0,) * (n + 1),) * 128,
                             ((0,) * (n + 1),) * 64, (0,) * n)
        proof = repair_dual(base, (0,) * 128, (0,) * 64)
        self.assertTrue(verify_attainment(base, proof, (0,) * n))
        box_base = LinearProgram('maximum-box', n, (), (), tuple(range(-8, 8)))
        expected = augment_box(box_base, (-2,) * n, (3,) * n)
        boxed = repair_dual(box_base, (), (), box=((-2,) * n, (3,) * n))
        vertex = tuple(3 if c >= 0 else -2 for c in box_base.objective)
        self.assertTrue(verify_attainment(expected, boxed, vertex))

    def test_exact_vertex_oracle_for_fresh_rational_boxes(self):
        rng = random.Random(317)
        for case in range(90):
            n = 1 + case % 4
            lower = tuple(F(rng.randrange(-9, 3), rng.randrange(1, 6)) for _ in range(n))
            upper = tuple(lo + F(rng.randrange(0, 8), rng.randrange(1, 6)) for lo in lower)
            objective = tuple(F(rng.randrange(-7, 8), rng.randrange(1, 6)) for _ in range(n))
            offset = F(rng.randrange(-9, 10), rng.randrange(1, 6))
            base = LinearProgram('fresh-box-' + str(case), n, (), (), objective, offset)
            proof = repair_dual(base, (), (), box=(lower, upper))
            rows = tuple(tuple(int(i == j) for j in range(n)) + (upper[i],) for i in range(n))
            rows += tuple(tuple(-int(i == j) for j in range(n)) + (-lower[i],) for i in range(n))
            expected = LinearProgram(base.context, n, rows, (), objective, offset)
            values = [offset + sum((c * x for c, x in zip(objective, v)), F(0))
                      for v in product(*zip(lower, upper))]
            self.assertEqual(proof.upper_bound, max(values))
            self.assertTrue(verify_dual_bound(expected, proof))
            vertex = tuple(hi if c >= 0 else lo for c, lo, hi in zip(objective, lower, upper))
            self.assertTrue(verify_attainment(expected, proof, vertex))

    def test_repaired_multipliers_bound_every_feasible_vertex(self):
        rows = ((1, 1, 5), (-1, 2, 4), (-2, -1, 3))
        all_rows = rows + ((1, 0, 4), (0, 1, 3), (-1, 0, 2), (0, -1, 1))
        vertices = set()
        for i, (a, b, r) in enumerate(all_rows):
            for c, d, s in all_rows[i + 1:]:
                det = a * d - b * c
                if not det:
                    continue
                point = (F(r * d - b * s, det), F(a * s - r * c, det))
                if all(sum(v * x for v, x in zip(row[:-1], point)) <= row[-1] for row in all_rows):
                    vertices.add(point)
        self.assertGreater(len(vertices), 2)
        for index, objective in enumerate(product(range(-2, 3), repeat=2)):
            base = LinearProgram('fresh-polytope', 2, rows, (), objective, -2)
            expected = LinearProgram('fresh-polytope', 2, all_rows, (), objective, -2)
            y0 = (F(index - 12, 7), F(8 - index, 5), F(index % 3, 2))
            proof = repair_dual(base, y0, (), box=((-2, -1), (4, 3)))
            self.assertTrue(verify_dual_bound(expected, proof))
            for point in vertices:
                self.assertLessEqual(-2 + sum(c * x for c, x in zip(objective, point)), proof.upper_bound)


if __name__ == '__main__':
    unittest.main()
