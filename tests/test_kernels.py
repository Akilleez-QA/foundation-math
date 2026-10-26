"""New small synthetic checks; not a historical research workload or benchmark."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import unittest
from unittest.mock import patch
from fm_research import p1, twoi, vendor
from fm_research.field import QuadraticElement, Q5
from fm_research.rank import rank_exact, verify_rank_certificate
from character_ring import producer as cp, verifier as cv
from split_bundle import producer as sp, verifier as sv


class SmallKernelTests(unittest.TestCase):
    def test_exact_field_arithmetic_and_rejection(self):
        x, y = Q5(2, 3), Q5(Fraction(3, 7), -2)
        self.assertEqual(x * x.conjugate(), -41)
        self.assertEqual(x / x, 1)
        self.assertEqual(x * (y + 4), x * y + 4 * x)
        with self.assertRaises(TypeError):
            Q5(0.25)
        with self.assertRaises(ValueError):
            QuadraticElement(1, 1, 9)
        with self.assertRaises(ZeroDivisionError):
            Q5(0).inverse()

    def test_new_small_rank_witnesses_and_tampering(self):
        cases = [([[2, 5], [6, 15]], 'Q', None, 1),
                 ([[3, 1], [1, 5]], 'Q', None, 2),
                 ([[3, 1], [1, 5]], 'F_p', 7, 1),
                 ([[Q5(0, 1), 0], [0, Q5(3)]], 'Q(sqrt5)', None, 2),
                 ([], 'Q', None, 0)]
        for matrix, field, modulus, expected in cases:
            cert = rank_exact(matrix, field, modulus)
            self.assertEqual(cert.rank, expected)
            self.assertTrue(verify_rank_certificate(matrix, cert))
            self.assertFalse(verify_rank_certificate(matrix, replace(cert, matrix_sha256='0' * 64)))
        with self.assertRaises(ValueError):
            rank_exact([[1]], 'F_p', 9)

    def test_low_degree_characters_and_catalog_pin(self):
        self.assertEqual(vendor.catalog_sha256(), cv.PIN)
        self.assertEqual(len(cv.check_catalog()), 9)
        for n, label in enumerate(('1', 'W', 'A', 'S4', 'D', 'T6')):
            self.assertEqual(twoi.sym_W(n), twoi.irrep(label))
            self.assertEqual(twoi.sym_W(n).dim, n + 1)
        self.assertEqual(twoi.irrep('W') @ twoi.irrep('W'), twoi.irrep('1') + twoi.irrep('A'))
        with patch.object(vendor, 'CATALOG_SHA256', 'wrong'):
            with self.assertRaises(RuntimeError):
                vendor.catalog_sha256()
        with self.assertRaises(TypeError):
            twoi.sym_W(True)

    def test_small_formal_cohomology_and_hom(self):
        rows = p1.cohomology([p1.Block('1', 0)], [-3, -1, 0, 2])
        self.assertEqual([(rows[t]['h0_dim'], rows[t]['h1_dim']) for t in rows], [(0, 2), (0, 0), (1, 0), (3, 0)])
        self.assertEqual(p1.hom([p1.Block('1', -1)], [p1.Block('1', 0)]), twoi.irrep('W'))
        self.assertEqual(p1.hom([p1.Block('1', 1)], [p1.Block('1', 0)]), twoi.Rep())

    def test_selected_character_producer_verifier_pair(self):
        request = {'schema': 'fm-character-request-v1', 'expression': {'op': 'symmetric_power', 'degree': 4},
                   'expectation': {'classification': 'genuine', 'equals': {'D': 1}}}
        cert = cp.calculate(request)
        result = cv.verify(request, cert)
        self.assertEqual(result['status'], 'verified_arithmetic')
        self.assertFalse(result['runtime_acceptance'])
        wrong = deepcopy(cert)
        wrong['result']['dimension'] = 6
        with self.assertRaises(cv.VerificationError):
            cv.verify(request, wrong)

    def test_selected_split_producer_verifier_pair(self):
        request = {'schema': 'fm-split-bundle-request-v1', 'operation': 'cohomology',
                   'bundle': [{'irrep': '1', 'twist': -1, 'multiplicity': 2}], 'twists': [-1, 0, 1]}
        cert = sp.calculate(request)
        result = sv.verify(request, cert)
        self.assertFalse(result['geometric_realization'])
        wrong = deepcopy(cert)
        wrong['result']['bundle']['degree'] = 0
        with self.assertRaises(sv.VerificationError):
            sv.verify(request, wrong)

    def test_imports_are_from_this_selected_tree(self):
        from pathlib import Path
        import fm_mapper.core
        import fm_research.problem
        root = Path(__file__).resolve().parents[1]
        for module in (fm_mapper.core, fm_research.problem, cp, cv, sp, sv):
            self.assertTrue(Path(module.__file__).resolve().is_relative_to(root))
        self.assertEqual(vendor.VENDOR.resolve(), root / 'vendor/foundation-math-v014')
