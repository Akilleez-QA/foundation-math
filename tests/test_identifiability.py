from dataclasses import FrozenInstanceError
from fractions import Fraction as F
import unittest

from fm_identifiability import (
    Model, PairWitness, ConstancyWitness, verify_pair, verify_constancy,
    MAX_DIMENSION, MAX_ROWS, MAX_INPUT_BITS,
)


class IdentifiabilityTests(unittest.TestCase):
    def setUp(self):
        self.model = Model(((1, 1),), (6,), ((-1, 0), (0, -1)), (0, 0), (1, 0), 7)

    def pair(self, model, first, second):
        return verify_pair(model, PairWitness(model.digest, first, second))

    def constant(self, model, anchor, multipliers):
        return verify_constancy(model, ConstancyWitness(model.digest, anchor, multipliers))

    def test_distinct_and_offset(self):
        result = self.pair(self.model, (1, 5), (4, 2))
        self.assertEqual((result.status, result.values), ('query_distinct', (8, 11)))
        shifted = Model(self.model.C, self.model.z, self.model.L, self.model.h, self.model.q, -9)
        self.assertEqual(self.pair(shifted, (1, 5), (4, 2)).values, (-8, -5))

    def test_same_query_does_not_prove_constancy(self):
        self.assertEqual(self.pair(self.model, (1, 5), (1, 5)).status, 'same_query')
        self.assertEqual(self.constant(self.model, (1, 5), (1,)).status, 'invalid_witness')
        model = Model((), (), (), (), (1, 0))
        self.assertEqual(self.pair(model, (2, 3), (2, 7)).status, 'same_query')
        self.assertEqual(self.pair(model, (2, 3), (3, 7)).status, 'query_distinct')

    def test_rank_deficiency_and_rational_constant(self):
        model = Model(((1, 2), (2, 4)), (3, 6), (), (), (F(1, 2), 1), F(2, 3))
        result = self.constant(model, (1, 1), (F(3, 2), F(-1, 2)))
        self.assertEqual((result.status, result.value), ('constant_on_fiber', F(13, 6)))
        self.assertEqual(self.constant(model, (-1, 2), (F(1, 2), 0)), result)

    def test_closed_prior_boundary_and_invalid_points(self):
        self.assertEqual(self.pair(self.model, (0, 6), (6, 0)).status, 'query_distinct')
        for point in ((-1, 7), (1, 4)):
            self.assertEqual(self.pair(self.model, point, (1, 5)).status, 'invalid_witness')
            self.assertIsNone(self.pair(self.model, (1, 5), point).values)
        constant = Model(((1,),), (1,), ((1,),), (0,), (1,))
        self.assertEqual(self.constant(constant, (1,), (1,)).status, 'invalid_witness')

    def test_prior_only_constancy_not_certified(self):
        model = Model((), (), ((1,), (-1,)), (2, -2), (1,), 3)
        self.assertEqual(self.pair(model, (2,), (2,)).values, (5, 5))
        result = self.constant(model, (2,), ())
        self.assertEqual((result.status, result.value), ('invalid_witness', None))

    def test_empty_equalities_zero_query_and_zero_dimension(self):
        model = Model((), (), (), (), (0, 0), F(4, 3))
        self.assertEqual(self.constant(model, (9, -7), ()).value, F(4, 3))
        zero = Model(((),), (0,), ((),), (0,), (), 8)
        self.assertEqual(self.constant(zero, (), (7,)).value, 8)
        self.assertEqual(self.pair(zero, (), ()).status, 'same_query')

    def test_inconsistent_equalities_require_anchor(self):
        model = Model(((1,), (1,)), (0, 1), (), (), (1,))
        for anchor in ((0,), (1,)):
            self.assertEqual(self.constant(model, anchor, (1, 0)).status, 'invalid_witness')
        self.assertEqual(self.pair(model, (0,), (1,)).status, 'invalid_witness')
        zero = Model(((),), (1,), (), (), ())
        self.assertEqual(self.constant(zero, (), (0,)).status, 'invalid_witness')

    def test_binding_every_field_and_canonical_numbers(self):
        model = self.model
        self.assertEqual(Model(model.C, model.z, model.L, model.h, (F(1), F(0)), F(7)).digest, model.digest)
        alternatives = [
            Model(((1, 2),), model.z, model.L, model.h, model.q, model.d),
            Model(model.C, (7,), model.L, model.h, model.q, model.d),
            Model(model.C, model.z, ((-2, 0), (0, -1)), model.h, model.q, model.d),
            Model(model.C, model.z, model.L, (1, 0), model.q, model.d),
            Model(model.C, model.z, model.L, model.h, (0, 1), model.d),
            Model(model.C, model.z, model.L, model.h, model.q, 8),
        ]
        for other in alternatives:
            with self.assertRaises(ValueError):
                verify_pair(other, PairWitness(model.digest, (1, 5), (4, 2)))
            with self.assertRaises(ValueError):
                verify_constancy(other, ConstancyWitness(model.digest, (1, 5), (1,)))

    def test_frozen_and_mutation_revalidation(self):
        model = self.model
        with self.assertRaises(FrozenInstanceError):
            model.q = (0, 1)
        witness = PairWitness(model.digest, (1, 5), (4, 2))
        with self.assertRaises(FrozenInstanceError):
            witness.first = (0, 6)
        object.__setattr__(model, 'd', F(99))
        with self.assertRaises(ValueError):
            verify_pair(model, witness)
        self.setUp()
        object.__setattr__(witness, 'first', [1, 5])
        with self.assertRaises(ValueError):
            verify_pair(self.model, witness)

    def test_bad_types_dimensions_and_limits(self):
        class IntSubclass(int):
            pass
        class FractionSubclass(F):
            pass
        for value in (True, 1.0, '1', None, IntSubclass(1), FractionSubclass(1), 1 << MAX_INPUT_BITS, F(1, 1 << MAX_INPUT_BITS)):
            with self.assertRaises(ValueError):
                Model((), (), (), (), (value,))
        for q in ([1], (0,) * (MAX_DIMENSION + 1)):
            with self.assertRaises(ValueError):
                Model((), (), (), (), q)
        cases = [(((1,),), (), (), (), (1,)), (((1, 2),), (0,), (), (), (1,)),
                 ((), (), ((1,),), (), (1,)), ([(1,)], (0,), (), (), (1,)),
                 (((1,),) * (MAX_ROWS + 1), (0,) * (MAX_ROWS + 1), (), (), (1,))]
        for args in cases:
            with self.assertRaises(ValueError):
                Model(*args)
        for first in ((), (1,), (1, 2, 3)):
            with self.assertRaises(ValueError):
                self.pair(self.model, first, (1, 5))
        with self.assertRaises(ValueError):
            self.constant(self.model, (1, 5), ())
        for digest in ('', 'z' * 64, 9):
            with self.assertRaises(ValueError):
                PairWitness(digest, (), ())
        with self.assertRaises(ValueError):
            verify_pair(self.model, object())
        with self.assertRaises(ValueError):
            verify_constancy(self.model, PairWitness(self.model.digest, (1, 5), (1, 5)))

    def test_intermediate_resource_limit(self):
        primes = []
        number = 2
        while len(primes) < 128:
            if all(number % prime for prime in primes):
                primes.append(number)
            number += 1
        denominators = []
        for prime in primes:
            value = prime
            while (value * prime).bit_length() <= MAX_INPUT_BITS:
                value *= prime
            denominators.append(value)
        model = Model(tuple((F(1, value),) for value in denominators[:64]),
                      (0,) * 64, (), (), (0,))
        with self.assertRaisesRegex(ValueError, 'Intermediate'):
            self.constant(model, (0,), tuple(F(1, value) for value in denominators[64:]))

    def test_limit_boundaries(self):
        value = (1 << MAX_INPUT_BITS) - 1
        model = Model((), (), (), (), (value,))
        self.assertEqual(self.pair(model, (value,), (0,)).values, (value * value, 0))
        wide = Model(((0,) * MAX_DIMENSION,) * MAX_ROWS, (0,) * MAX_ROWS, (), (), (0,) * MAX_DIMENSION)
        self.assertEqual(self.constant(wide, (0,) * MAX_DIMENSION, (0,) * MAX_ROWS).value, 0)


if __name__ == '__main__':
    unittest.main()
