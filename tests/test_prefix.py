import unittest
from fractions import Fraction as Q
from fm_prefix import Continuation


def scalar(**changes):
    values = dict(H=[[0]], B=[[1]], initial=[0], R=[[1]], D=[[[1]]],
                  moment=[0], budget=4, end=2, cut=1, prefix=[(0, 1, [[1]])])
    values.update(changes)
    return Continuation(**values)


class PrefixTests(unittest.TestCase):
    def test_fixed_prefix_cost_and_residual(self):
        c = scalar()
        self.assertEqual((c.state, c.moment_residual), ((1,), (-1,)))
        self.assertEqual((c.spent_cost, c.minimum_tail_cost, c.reserve), (1, 1, 2))
        self.assertEqual(c.minimum_tail_value(Q(3, 2)), (-1,))
        self.assertEqual(c.future(1).shape, ((0,),))
        self.assertEqual(c.future(2).center, (0,))
        self.assertEqual(c.future(2).shape, ((0,),))

    def test_conditional_ellipsoid(self):
        s = scalar().future(Q(3, 2))
        self.assertEqual((s.center, s.shape), ((Q(1, 2),), ((Q(1, 4),),)))
        self.assertTrue(s.target([Q(6, 5)]).reachable)
        self.assertFalse(s.target([Q(5, 4)]).reachable)
        self.assertEqual(s.target([Q(6, 5)]).extra_cost, Q(49, 25))
        self.assertTrue(s.row([1], Q(5, 4)).contained)
        self.assertFalse(s.row([1], Q(6, 5)).contained)
        self.assertFalse(s.row([0], -1).contained)
        self.assertTrue(s.row([0], 0).contained)

    def test_boundary_and_range(self):
        c = scalar(budget=3)
        s = c.future(Q(3, 2))
        self.assertTrue(s.target([1]).reachable)
        self.assertEqual(s.target([1]).minimum_total_cost, 3)
        self.assertTrue(s.row([1], 1).contained)
        self.assertFalse(c.future(2).target([1]).reachable)
        self.assertEqual(c.future(2).target([1]).reason, 'outside_range')
        self.assertTrue(c.future(2).target([0]).reachable)

    def test_budget_failure_does_not_reoptimize_prefix(self):
        c = scalar(budget=Q(3, 2))
        self.assertEqual(c.status, 'no_continuation_budget')
        self.assertEqual(c.minimum_tail_value(1), (-1,))
        with self.assertRaises(ValueError):
            c.future(2)
        self.assertEqual(scalar(cut=0, prefix=[], budget=Q(3, 2)).status, 'feasible')

    def test_duplicate_moments_and_inconsistent_range(self):
        c = scalar(D=[[[1], [2]]], moment=[0, 0])
        self.assertEqual(c.future(Q(3, 2)).shape, ((Q(1, 4),),))
        bad = scalar(D=[[[1], [2]]], moment=[0, 1])
        self.assertEqual(bad.status, 'no_continuation_moment_range')
        self.assertIsNone(bad.minimum_tail_cost)
        with self.assertRaises(ValueError):
            bad.minimum_tail_value(1)

    def test_empty_tail(self):
        c = scalar(cut=2, prefix=[(0, 2, [[1]])], moment=[2], budget=2)
        self.assertEqual(c.status, 'feasible')
        self.assertEqual(c.future(2).center, (2,))
        self.assertEqual(c.minimum_tail_cost, 0)
        self.assertEqual(scalar(cut=2, prefix=[(0, 2, [[1]])]).status,
                         'no_continuation_moment_range')

    def test_nilpotent_chain(self):
        c = scalar(H=[[0, 1], [0, 0]], B=[[0], [1]], initial=[0, 0],
                   cut=0, end=1, prefix=[], budget=12)
        s = c.future(1)
        self.assertEqual(s.shape, ((Q(1, 12), 0), (0, 0)))
        self.assertTrue(s.target([1, 0]).reachable)
        self.assertFalse(s.target([1, 1]).reachable)
        self.assertTrue(s.row([1, 0], 1).contained)

    def test_polynomial_moment(self):
        c = scalar(D=[[[0]], [[1]]], moment=[1], cut=0, end=1, prefix=[], budget=3)
        self.assertEqual(c.minimum_tail_cost, 3)
        self.assertEqual(c.minimum_tail_value(Q(1, 2)), (Q(3, 2),))
        self.assertEqual(c.future(1).center, (Q(3, 2),))
        self.assertEqual(c.reserve, 0)
        self.assertTrue(c.future(1).target([Q(3, 2)]).reachable)
        self.assertFalse(c.future(1).target([0]).reachable)

    def test_nonidentity_norm_and_multiple_inputs(self):
        c = scalar(B=[[1, 1]], R=[[2, 1], [1, 2]], D=[[[1, 1]]],
                   moment=[1], cut=0, end=1, prefix=[], budget=2)
        self.assertEqual(c.minimum_tail_cost, Q(3, 2))
        self.assertEqual(c.minimum_tail_value(0), (Q(1, 2), Q(1, 2)))
        self.assertEqual(c.future(1).center, (1,))

    def test_piecewise_cubic_absolute_time(self):
        c = scalar(cut=1, prefix=[(0, Q(1, 2), [[0], [0], [0], [1]]),
                                  (Q(1, 2), 1, [[0], [0], [0], [1]])],
                   moment=[Q(1, 4)], budget=1)
        self.assertEqual(c.spent_cost, Q(1, 7))
        self.assertEqual(c.state, (Q(1, 4),))
        self.assertEqual(c.moment_residual, (0,))

    def test_highest_supported_dimension_and_degree(self):
        H = [[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [0, 0, 0, 0]]
        c = scalar(H=H, B=[[0], [0], [0], [1]], initial=[0, 0, 0, 0],
                   D=[[[0]], [[0]], [[0]], [[1]]], moment=[Q(1, 4)],
                   cut=0, end=1, prefix=[], budget=1)
        self.assertEqual(c.minimum_tail_cost, Q(7, 16))
        self.assertEqual(c.minimum_tail_value(1), (Q(7, 4),))
        s = c.future(1)
        self.assertEqual(s.center, (Q(1, 480), Q(7, 480), Q(7, 80), Q(7, 16)))
        self.assertTrue(s.target(s.center).reachable)
        self.assertTrue(s.row([0, 0, 0, 0], 0).contained)

    def test_equal_state_and_cost_retain_distinct_moment_memory(self):
        results = []
        for sign in (1, -1):
            c = scalar(D=[[[0]], [[1]]], moment=[0], cut=2, end=4, budget=3,
                       prefix=[(0, 1, [[sign]]), (1, 2, [[-sign]])])
            self.assertEqual(c.state, (0,))
            self.assertEqual(c.spent_cost, 2)
            self.assertEqual(c.moment_residual, (sign,))
            self.assertEqual(c.tail_gram, ((Q(56, 3),),))
            self.assertEqual(c.minimum_tail_cost, Q(3, 56))
            terminal = c.future(4)
            self.assertEqual(terminal.center, (sign*Q(9, 28),))
            self.assertEqual(terminal.shape, ((Q(1, 14),),))
            results.append(terminal)
        self.assertNotEqual(results[0].center, results[1].center)

    def test_unsupported_inputs(self):
        changes = [dict(H=[[1]]), dict(H=[[0, 0]]), dict(B=[]), dict(initial=[True]),
                   dict(budget=1.0), dict(budget='4'), dict(budget=2**128),
                   dict(budget=Q(1, 2**128)), dict(R=[[0]]), dict(R=[[-1]]),
                   dict(cut=3), dict(end=0), dict(budget=-1), dict(prefix=[]),
                   dict(prefix=[(Q(1, 2), 1, [[1]])]),
                   dict(prefix=[(0, 1, [[1]]), (0, 1, [[1]])]),
                   dict(prefix=[(0, 1, [[1]]*5)]), dict(D=[[[1]]]*5),
                   dict(moment=[0]*5), dict(prefix=[(0, 1, [[1]])]*9),
                   dict(B=[[1, 1]], R=[[1, 1], [0, 1]]), dict(prefix=[(0, 1)]),
                   dict(prefix=[(0, 1, [[1, 2]])])]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                scalar(**change)
        c = scalar()
        for t in [-1, 3, 1.0, True]:
            with self.subTest(t=t), self.assertRaises(ValueError):
                c.future(t)
        with self.assertRaises(ValueError):
            c.future(1).target([0, 0])
        with self.assertRaises(ValueError):
            c.future(1).row([1], 0.0)


if __name__ == '__main__':
    unittest.main()
