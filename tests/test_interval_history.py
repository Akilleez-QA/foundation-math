import copy
from fractions import Fraction as Q
from itertools import combinations_with_replacement, product
import json
import unittest

from fm_intervals import (
    MAX_OBSERVATIONS, analyze_history, intersection, interval, verify_history,
)


class IntervalHistoryTests(unittest.TestCase):
    def test_exact_inputs_and_intersection(self):
        self.assertEqual(interval(['-2/4', Q(3, 2)]), (Q(-1, 2), Q(3, 2)))
        self.assertEqual(intersection([[0, 1], [1, 2]]), (Q(1), Q(1)))
        self.assertIsNone(intersection([[0, 1], ['3/2', 2]]))
        self.assertEqual(intersection([[0, 3], [1, 2], [1, 1]]), (Q(1), Q(1)))

    def test_invalid_rationals(self):
        invalid = [True, False, 0.0, 1.5, float('inf'), float('nan'), None,
                   {}, [], 'NaN', 'Infinity', '1.0', '1e2', ' 1', '1 ',
                   '1/0', '1/-2', '1/02', '1_000', '9' * 161,
                   1 << 256, Q(1, 1 << 256)]
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    interval([value, 2])
        self.assertEqual(interval([-(1 << 255), (1 << 255)]), (Q(-(1 << 255)), Q(1 << 255)))

    def test_shapes_and_bounds(self):
        for value in [None, '01', [], [0], [0, 1, 2], {0, 1}, iter([0, 1]), [2, 1]]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    interval(value)
        for value in [None, [], iter([[0, 1]]), [[0, 1]] * (MAX_OBSERVATIONS + 1)]:
            with self.assertRaises(ValueError):
                intersection(value)
        for value in [None, {}, iter([]), [None], [[[0, 1]]], [[[0, 1], [0, 1], [0, 1]]], [[[0, 1], [2, 1]]]]:
            with self.assertRaises(ValueError):
                analyze_history([0, 1], value)
        with self.assertRaises(ValueError):
            analyze_history([0, 1], [[[0, 1], [0, 1]]] * (MAX_OBSERVATIONS + 1))

    def test_missing_and_contradictory_are_distinct(self):
        empty = analyze_history([0, 2], [])
        self.assertEqual((empty['coverage'], empty['consistency']), ('none', 'undetermined'))
        receipt = analyze_history([0, 2], [[[0, 1], [0, 0]], [[0, 1], [1, 1]]])
        self.assertEqual((receipt['coverage'], receipt['consistency']), ('partial', 'contradictory'))
        self.assertEqual({cell['status'] for cell in receipt['cells']}, {'missing', 'contradictory'})
        self.assertTrue(all(cell['intersection'] is None for cell in receipt['cells']))

    def test_touching_time_intervals_endpoint_contradiction(self):
        receipt = analyze_history([0, 2], [[[0, 1], [0, 0]], [[1, 2], [1, 1]]])
        self.assertEqual((receipt['coverage'], receipt['consistency']), ('full', 'contradictory'))
        bad = [cell for cell in receipt['cells'] if cell['status'] == 'contradictory']
        self.assertEqual(len(bad), 1)
        self.assertEqual((bad[0]['kind'], bad[0]['witness'], bad[0]['bounds']), ('point', '1', ['1', '1']))

    def test_touching_value_intervals_singleton_witness(self):
        receipt = analyze_history([0, 2], [[[0, 2], [0, 1]], [[0, 2], [1, 2]]])
        self.assertEqual(receipt['consistency'], 'consistent')
        self.assertTrue(all(cell['intersection'] == ['1', '1'] for cell in receipt['cells']))

    def test_point_horizon_and_point_observation(self):
        receipt = analyze_history([1, 1], [[[0, 1], [3, 3]]])
        self.assertEqual(receipt['coverage'], 'full')
        self.assertEqual(len(receipt['cells']), 1)
        receipt = analyze_history([0, 2], [[[1, 1], [3, 3]]])
        self.assertEqual(receipt['coverage'], 'partial')
        self.assertEqual(receipt['consistency'], 'undetermined')
        self.assertEqual(sum(c['status'] == 'consistent' for c in receipt['cells']), 1)

    def test_clipping_outside_and_gap(self):
        receipt = analyze_history([0, 3], [[[-2, 0], [0, 0]], [[1, 4], [0, 0]], [[5, 6], [2, 2]]])
        self.assertEqual(receipt['coverage'], 'partial')
        missing = [c for c in receipt['cells'] if c['status'] == 'missing']
        self.assertEqual(len(missing), 1)
        self.assertEqual((missing[0]['kind'], missing[0]['bounds'], missing[0]['witness']), ('open', ['0', '1'], '1/2'))
        self.assertEqual(analyze_history([0, 1], [[[2, 3], [0, 0]]])['coverage'], 'none')

    def test_maximum_bound_and_exact_midpoint(self):
        observations = [[[i, i], [0, 0]] for i in range(MAX_OBSERVATIONS)]
        receipt = analyze_history([-1, MAX_OBSERVATIONS], observations)
        self.assertEqual(len(receipt['cells']), 2 * MAX_OBSERVATIONS + 3)
        self.assertTrue(verify_history([-1, MAX_OBSERVATIONS], observations, receipt))
        receipt = analyze_history(['1/3', '2/3'], [])
        self.assertEqual(receipt['cells'][1]['witness'], '1/2')

    def test_receipt_roundtrip_and_input_binding(self):
        observations = [[[0, 1], [0, 2]], [[1, 2], [1, 3]]]
        receipt = analyze_history([0, 2], observations)
        self.assertTrue(verify_history([0, 2], observations, json.loads(json.dumps(receipt))))
        self.assertFalse(verify_history([0, 3], observations, receipt))
        self.assertFalse(verify_history([0, 2], observations[::-1], receipt))
        self.assertFalse(verify_history([True, 2], observations, receipt))
        self.assertFalse(verify_history([0, 2], None, receipt))
        self.assertEqual(observations, [[[0, 1], [0, 2]], [[1, 2], [1, 3]]])

    def test_tampering(self):
        observations = [[[0, 2], [0, 1]], [[1, 2], [1, 2]]]
        receipt = analyze_history([0, 2], observations)
        edits = [
            lambda r: r.update(schema='fm-interval-history/2'),
            lambda r: r.update(coverage='partial'),
            lambda r: r.update(consistency='contradictory'),
            lambda r: r.update(extra=0),
            lambda r: r.pop('horizon'),
            lambda r: r['horizon'].__setitem__(0, '0/1'),
            lambda r: r['observations'][0]['value'].__setitem__(1, '2'),
            lambda r: r['cells'].pop(),
            lambda r: r['cells'].reverse(),
            lambda r: r['cells'][0].update(witness='1/2'),
            lambda r: r['cells'][0].update(kind='open'),
            lambda r: r['cells'][0].update(status='missing'),
            lambda r: r['cells'][0].update(intersection=None),
            lambda r: r['cells'][0].update(active=[False]),
            lambda r: r['cells'][0].update(active=[0.0]),
            lambda r: r['cells'][0].update(active=[1]),
            lambda r: r['cells'][0].update(bounds=['0', '1']),
            lambda r: r['cells'][0].update(active=tuple(r['cells'][0]['active'])),
        ]
        for edit in edits:
            changed = copy.deepcopy(receipt)
            edit(changed)
            self.assertFalse(verify_history([0, 2], observations, changed))
        for invalid in [None, [], True, 1, 'receipt']:
            self.assertFalse(verify_history([0, 2], observations, invalid))

    def test_independent_finite_reference(self):
        time_intervals = list(combinations_with_replacement(range(3), 2))
        value_intervals = list(combinations_with_replacement(range(3), 2))
        observations = list(product(time_intervals, value_intervals))
        probes = [Q(i, 2) for i in range(5)]
        for first, second in product(observations, repeat=2):
            supplied = [first, second]
            receipt = analyze_history([0, 2], supplied)
            statuses = []
            for point in probes:
                active = [value for time, value in supplied if time[0] <= point <= time[1]]
                feasible = [v for v in range(3) if all(lo <= v <= hi for lo, hi in active)]
                status = 'missing' if not active else 'consistent' if feasible else 'contradictory'
                statuses.append(status)
                matching = [c for c in receipt['cells'] if
                            (c['kind'] == 'point' and Q(c['witness']) == point) or
                            (c['kind'] == 'open' and Q(c['bounds'][0]) < point < Q(c['bounds'][1]))]
                self.assertEqual(len(matching), 1)
                self.assertEqual(matching[0]['status'], status)
                if active and feasible:
                    self.assertEqual(matching[0]['intersection'], [str(min(feasible)), str(max(feasible))])
            coverage = 'none' if all(s == 'missing' for s in statuses) else 'partial' if 'missing' in statuses else 'full'
            consistency = 'contradictory' if 'contradictory' in statuses else 'undetermined' if 'missing' in statuses else 'consistent'
            self.assertEqual((receipt['coverage'], receipt['consistency']), (coverage, consistency))


if __name__ == '__main__':
    unittest.main()
