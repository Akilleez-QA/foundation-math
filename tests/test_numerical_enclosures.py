from dataclasses import FrozenInstanceError, replace
from fractions import Fraction as F
from itertools import product
import unittest

from fm_enclosures import (
    EnclosureLimitError,
    enclose_linear_residual,
    verify_linear_residual,
)


def point(value):
    return (value, value)


class NumericalEnclosureTests(unittest.TestCase):
    def test_hand_example(self):
        matrix = [[(3, 4), (-1, 1)], [(0, 1), (4, 5)]]
        candidate = [2, -1]
        rhs = [(5, 6), (-4, -3)]
        result = enclose_linear_residual(matrix, candidate, rhs)
        self.assertEqual(result.residuals, ((F(-1), F(4)), (F(-2), F(2))))
        self.assertEqual(result.residual_norm_upper, 4)
        self.assertEqual(result.dominance_margin, 2)
        self.assertEqual(result.forward_error_upper, 2)
        self.assertEqual(result.forward_status, "bounded")
        self.assertTrue(verify_linear_residual(result, matrix, candidate, rhs))

    def test_exhaustive_corners(self):
        matrix = [[(-3, -2), (-2, 1)], [(1, 4), (5, 7)]]
        rhs = [(-1, 2), (0, 3)]
        boxes = [pair for row in matrix for pair in row] + rhs
        for candidate in product((F(-2), F(0), F(3, 2)), repeat=2):
            result = enclose_linear_residual(matrix, candidate, rhs)
            values = [[], []]
            for corner in product(*boxes):
                values[0].append(corner[0] * candidate[0] + corner[1] * candidate[1] - corner[4])
                values[1].append(corner[2] * candidate[0] + corner[3] * candidate[1] - corner[5])
            self.assertEqual(result.residuals, tuple((min(v), max(v)) for v in values))

    def test_forward_bound_at_every_corner(self):
        matrix = [[(-5, -4), (-1, 1)], [(0, 1), (3, 4)]]
        rhs = [(-1, 1), (2, 3)]
        candidate = [F(1, 3), F(-2, 5)]
        result = enclose_linear_residual(matrix, candidate, rhs)
        self.assertEqual(result.dominance_margin, 2)
        boxes = [pair for row in matrix for pair in row] + rhs
        for a, b, c, d, u, v in product(*boxes):
            determinant = a * d - b * c
            solution = (F(d * u - b * v, determinant), F(a * v - c * u, determinant))
            error = max(abs(candidate[i] - solution[i]) for i in range(2))
            self.assertLessEqual(error, result.forward_error_upper)

    def test_unresolved_does_not_mean_singular(self):
        matrix = [[point(1), point(2)], [point(3), point(4)]]
        result = enclose_linear_residual(matrix, [0, 0], [point(1), point(2)])
        self.assertEqual(result.forward_status, "unresolved")
        self.assertIsNone(result.forward_error_upper)
        self.assertEqual(result.residuals, ((F(-1), F(-1)), (F(-2), F(-2))))
        for diagonal in [(-1, 1), (0, 1), (-1, 0), (0, 0)]:
            result = enclose_linear_residual([[diagonal]], [0], [point(0)])
            self.assertEqual(result.dominance_margin, 0)
            self.assertEqual(result.forward_status, "unresolved")

    def test_zero_and_exact_strings(self):
        result = enclose_linear_residual([[('-3/2', '-1/2')]], ['+0/9'], [point('0')])
        self.assertEqual(result.residual_norm_upper, 0)
        self.assertEqual(result.forward_error_upper, 0)
        self.assertEqual(result.dominance_margin, F(1, 2))

    def test_bad_rationals(self):
        class IntChild(int):
            pass
        class FractionChild(F):
            pass
        class StringChild(str):
            pass
        bad = [True, False, 1.0, float('nan'), None, {}, '1e999999999', '1.0', ' 1',
               '1 ', '1/-2', '1/+2', '1/0', '1/2/3', '²', '１２', '', '--1',
               '0' * 161, 1 << 256, F(1, 1 << 256), str(1 << 256),
               '1/' + str(1 << 256), IntChild(1), FractionChild(1), StringChild('1')]
        for value in bad:
            with self.subTest(value=repr(value)[:50]):
                with self.assertRaises(ValueError):
                    enclose_linear_residual([[point(1)]], [value], [point(0)])

    def test_shapes_and_limits(self):
        class ListChild(list):
            pass
        bad = [([], [], []), ([[point(1)]] * 17, [0] * 17, [point(0)] * 17),
               ([[point(1), point(2)]], [0], [point(0)]),
               ([[(2, 1)]], [0], [point(0)]),
               ([[point(1)]], [], [point(0)]),
               ([[point(1)]], [0], []),
               ([[point(1)]], iter([0]), [point(0)]),
               (ListChild([[point(1)]]), [0], [point(0)])]
        for args in bad:
            with self.assertRaises(ValueError):
                enclose_linear_residual(*args)
        n = 16
        matrix = [[point(int(i == j)) for j in range(n)] for i in range(n)]
        result = enclose_linear_residual(matrix, [0] * n, [point(0)] * n)
        self.assertEqual(result.forward_error_upper, 0)

    def test_immutable_and_tampered(self):
        args = ([[point(2)]], [1], [point(0)])
        result = enclose_linear_residual(*args)
        with self.assertRaises(FrozenInstanceError):
            result.forward_status = 'unresolved'
        variants = [replace(result, residuals=((F(0), F(0)),)),
                    replace(result, residual_norm_upper=F(0)),
                    replace(result, dominance_margin=F(3)),
                    replace(result, forward_error_upper=F(0)),
                    replace(result, forward_error_upper=True),
                    replace(result, residual_norm_upper=2),
                    replace(result, residuals=[(F(2), F(2))]),
                    replace(result, forward_status='unresolved'), None]
        for changed in variants:
            self.assertFalse(verify_linear_residual(changed, *args))
        object.__setattr__(result, 'forward_error_upper', F(0))
        self.assertFalse(verify_linear_residual(result, *args))
        self.assertFalse(verify_linear_residual(enclose_linear_residual(*args), [], [], []))

    def test_corrupted_fraction_rejected(self):
        for numerator, denominator in [(2, 2), (1, -1), (1, 0), (True, 1)]:
            value = F(1)
            object.__setattr__(value, '_numerator', numerator)
            object.__setattr__(value, '_denominator', denominator)
            with self.assertRaises(ValueError):
                enclose_linear_residual([[point(1)]], [value], [point(0)])

    def test_intermediate_limit(self):
        from unittest.mock import patch
        with patch('fm_enclosures.numerical.MAX_INTERMEDIATE_BITS', 4):
            with self.assertRaises(EnclosureLimitError):
                enclose_linear_residual([[point(15)]], [15], [point(0)])
