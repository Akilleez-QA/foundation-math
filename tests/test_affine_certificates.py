from dataclasses import replace
from fractions import Fraction as Q
from itertools import product
import random
import unittest

from fm_certificates import (
    AffineSystem, Implication, Infeasibility, InvalidCertificate, Unsupported,
    compose_implications, make_implication, make_infeasibility,
    system_digest, verify_implication, verify_infeasibility,
)


class AffineCertificateTests(unittest.TestCase):
    def setUp(self):
        self.system = AffineSystem('synthetic-unit-box', 2,
                                   ((1, 0, -2), (-1, 0, 0),
                                    (0, 1, -3), (0, -1, 0)))

    def test_implication_and_constant_slack(self):
        proof = make_implication(self.system, (1, 2, -9), (1, 0, 2, 0))
        self.assertTrue(verify_implication(self.system, proof))
        self.assertTrue(verify_implication(self.system, replace(proof, target=(1, 2, -8))))
        self.assertFalse(verify_implication(self.system, replace(proof, target=(1, 2, -7))))
        self.assertFalse(verify_implication(self.system, replace(proof, target=(2, 2, -9))))
        with self.assertRaises(InvalidCertificate):
            make_implication(self.system, (1, 2, -7), (1, 0, 2, 0))

    def test_strict_infeasibility_and_touching(self):
        empty = AffineSystem('empty-synthetic', 1, ((1, -1), (-1, 2)))
        proof = make_infeasibility(empty, (1, 1))
        self.assertTrue(verify_infeasibility(empty, proof))
        touching = AffineSystem('touching-synthetic', 1, ((1, -1), (-1, 1)))
        self.assertFalse(verify_infeasibility(touching, Infeasibility(system_digest(touching), (1, 1))))
        self.assertFalse(verify_infeasibility(empty, replace(proof, multipliers=(1, 0))))
        self.assertFalse(verify_infeasibility(empty, replace(proof, multipliers=(-1, -1))))
        with self.assertRaises(InvalidCertificate):
            make_infeasibility(touching, (1, 1))

    def test_empty_system_and_zero_target(self):
        universal = AffineSystem('all-space', 3, ())
        proof = make_implication(universal, (0, 0, 0, -2), ())
        self.assertTrue(verify_implication(universal, proof))
        self.assertFalse(verify_implication(universal, replace(proof, target=(0, 0, 0, 1))))
        self.assertFalse(verify_infeasibility(universal, Infeasibility(system_digest(universal), ())))
        self.assertTrue(verify_implication(universal, compose_implications(universal, (), proof)))

    def test_composition_preserves_nonzero_slack(self):
        first = make_implication(self.system, (1, 0, -3), (1, 0, 0, 0))
        second = make_implication(self.system, (0, 1, -5), (0, 0, 1, 0))
        intermediate = AffineSystem(self.system.context, 2, (first.target, second.target))
        outer = make_implication(intermediate, (2, 3, -22), (2, 3))
        direct = compose_implications(self.system, (first, second), outer)
        self.assertEqual(direct.multipliers, (Q(2), Q(0), Q(3), Q(0)))
        self.assertTrue(verify_implication(self.system, direct))
        with self.assertRaises(InvalidCertificate):
            compose_implications(self.system, (second, first), outer)
        with self.assertRaises(InvalidCertificate):
            compose_implications(self.system, (replace(first, multipliers=(0, 0, 0, 0)), second), outer)

    def test_binding_changes_and_canonical_rationals(self):
        proof = make_implication(self.system, (1, 0, -2), (1, 0, 0, 0))
        changed = replace(self.system, context='different-context')
        self.assertFalse(verify_implication(changed, proof))
        self.assertFalse(verify_implication(replace(self.system, inequalities=self.system.inequalities[::-1]), proof))
        rational = replace(self.system, inequalities=tuple(tuple(Q(x) for x in row)
                                                        for row in self.system.inequalities))
        self.assertEqual(system_digest(self.system), system_digest(rational))
        self.assertFalse(verify_implication(self.system, replace(proof, system_digest='0' * 64)))

    def test_malformed_and_exact_type_boundaries(self):
        for dimension in (True, 0, 17, 2.0):
            with self.assertRaises(Unsupported):
                AffineSystem('scope', dimension, ())
        for context in ('', ' ', 'x' * 129, None):
            with self.assertRaises(Unsupported):
                AffineSystem(context, 1, ())
        for rows in ([], ((1,),), ((True, 0),), ((1.0, 0),), ((1, float('nan')),), ((1 << 256, 0),)):
            with self.assertRaises(Unsupported):
                AffineSystem('scope', 1, rows)
        proof = make_implication(self.system, (1, 0, -2), (1, 0, 0, 0))
        for weights in ((True, 0, 0, 0), (1.0, 0, 0, 0), [-1, 0, 0, 0], (),
                        (-1, 0, 0, 0), (1 << 4096, 0, 0, 0)):
            self.assertFalse(verify_implication(self.system, replace(proof, multipliers=weights)))
        for target in ((True, 0, 0), (1, 0), [1, 0, -2], (1, 0, Q(1, 1 << 256))):
            self.assertFalse(verify_implication(self.system, replace(proof, target=target)))
        for other in (None, {}, Infeasibility(system_digest(self.system), (1, 0, 0, 0))):
            self.assertFalse(verify_implication(self.system, other))

    def test_inclusive_resource_limits(self):
        boundary = (1 << 256) - 1
        rows = ((0,) * 16 + (-boundary,),) * 128
        system = AffineSystem('x' * 128, 16, rows)
        proof = make_implication(system, (0,) * 16 + (-boundary,), (1,) + (0,) * 127)
        self.assertTrue(verify_implication(system, proof))
        with self.assertRaises(Unsupported):
            AffineSystem('scope', 16, rows + (rows[0],))
        with self.assertRaises(Unsupported):
            compose_implications(system, (proof,) * 129, proof)

    def test_fresh_constructed_witness_families(self):
        rng = random.Random(761129)
        cases = evaluations = 0
        for dimension in range(1, 5):
            rows = []
            for j in range(dimension):
                e = tuple(int(i == j) for i in range(dimension))
                rows.extend((e + (-2,), tuple(-x for x in e) + (-1,)))
            system = AffineSystem('fresh-normalized-' + str(dimension), dimension, tuple(rows))
            for _ in range(12):
                weights = tuple(Q(rng.randrange(5), rng.randrange(1, 5)) for row in rows)
                total = tuple(sum((w * row[j] for w, row in zip(weights, rows)), Q(0))
                              for j in range(dimension + 1))
                target = total[:-1] + (total[-1] - Q(rng.randrange(4), 3),)
                proof = make_implication(system, target, weights)
                self.assertTrue(verify_implication(system, proof))
                corrupt = replace(proof, target=(target[0] + 1,) + target[1:])
                self.assertFalse(verify_implication(system, corrupt))
                for point in product((Q(-1), Q(1, 2), Q(2)), repeat=dimension):
                    value = sum((a * z for a, z in zip(target[:-1], point)), target[-1])
                    self.assertLessEqual(value, 0)
                    evaluations += 1
                cases += 1
        self.assertEqual((cases, evaluations), (48, 1440))


if __name__ == '__main__':
    unittest.main()
