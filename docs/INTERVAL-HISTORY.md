# Exact rational interval histories

`fm_intervals` is a standalone Python-standard-library mathematical module.
Every quantity and example below is synthetic and dimensionless. No domain
interpretation or external fact is inferred from the supplied intervals.

## Contract

A horizon is a nonempty finite closed rational interval `[a, b]`, allowing
`a = b`. Each observation is a pair `(time_interval, value_interval)` of such
intervals. Its mathematical meaning is the supplied constraint

> For every t in the time interval, x(t) belongs to the value interval.

Only constraints restricted to the supplied horizon are checked. The unknown
function x has no continuity, differentiability, monotonicity, or other temporal
coupling assumption. Contradiction outside the horizon is not checked.
The word “history” refers only to this finite family of supplied constraints.

At a point t, active observations are those whose closed time intervals contain
t. Their value intervals are intersected exactly:

- `consistent`: at least one observation is active and the intersection is
  nonempty. A singleton intersection is nonempty.
- `contradictory`: at least one observation is active and the intersection is
  empty. This is a contradiction among supplied constraints at that point.
- `missing`: no observation is active. No value interval is asserted. The
  receipt's null intersection is not a claim that the feasible set is empty.

Coverage is separate from consistency:

- `none`: no point in the horizon has an active observation.
- `partial`: some, but not all, points have an active observation.
- `full`: every point has at least one active observation, even if some active
  constraints contradict each other.

Overall consistency is `contradictory` when any cell is contradictory;
otherwise it is `undetermined` when any cell is missing; otherwise it is
`consistent`. Here `undetermined` reports missing coverage, not an undecidable
mathematical problem. Partial coverage without contradiction admits a function
satisfying the supplied constraints; it does not supply constraints everywhere.
Full consistent coverage establishes only pointwise compatibility of the
supplied intervals, not a unique function, a continuous function, authenticity,
external validity, or scientific acceptance.

## Public API

```python
from fm_intervals import analyze_history, intersection, interval, verify_history

interval(["-1/2", "3/2"])
intersection([[0, 1], [1, 2]])

horizon = [0, 2]
observations = [([0, 1], [0, 0]), ([1, 2], [1, 1])]
receipt = analyze_history(horizon, observations)
assert receipt["coverage"] == "full"
assert receipt["consistency"] == "contradictory"
assert verify_history(horizon, observations, receipt)
```

In this example, the sole contradiction is the singleton time t = 1. The open
intervals `(0, 1)` and `(1, 2)` are each consistent. Replacing both value intervals
by `[0, 1]` makes the whole horizon consistent. Conversely, a sole observation on
`[0, 1]` over horizon `[0, 2]` gives partial coverage, not full coverage merely
because the intervals overlap. A singleton observation on `[1, 1]` also gives
partial coverage on `[0, 2]`; zero length does not mean an empty set.

`interval(bounds)` returns two `Fraction` values and rejects reversed endpoints.
`intersection(intervals)` accepts one through 128 intervals and returns their
closed intersection as two `Fraction` values, or `None` for an empty intersection.
It rejects the empty family rather than pretending an unbounded intersection is
a finite interval.

`analyze_history(horizon, observations)` returns the JSON-compatible exact
receipt described below. It raises `ValueError` for invalid inputs.
`verify_history(horizon, observations, receipt)` returns a Boolean. Invalid
mathematical inputs or a receipt that differs from the canonical result produce
`False`. The verifier recomputes the result with the same checking implementation;
it is not an independent implementation, proof assistant, signature, or
source-bound certificate. Bind verification to the intended horizon and
observations, not to inputs copied out of an untrusted receipt.

## Receipt and finite partition

Schema `fm-interval-history/1` contains canonical `horizon`, ordered
`observations`, `coverage`, `consistency`, and ordered `cells` fields. All rational
values are reduced strings produced by `Fraction`, with integers printed without
`/1`. Each observation has `time` and `value` fields. Observation ordering and
duplicates are retained; active indices are zero-based indices into that order.

Clip intersecting time intervals to the horizon. Sort their endpoints together
with the horizon endpoints. Emit a singleton `point` cell at each distinct
endpoint and an `open` cell between consecutive distinct endpoints. Each cell
has `kind`, `bounds`, `witness`, `active`, `status`, and `intersection` fields.
The witness is its endpoint for a point cell and its exact midpoint for an open
cell. The intersection is a canonical pair of rational strings when consistent
and null otherwise; the status disambiguates missing information and
contradiction. Bounds on an `open` cell exclude both endpoints. Singleton cells
include their sole endpoint.

This partition is exhaustive and disjoint. No observation boundary lies in the
interior of an open cell, so its active set is constant. Closed endpoints require
separate singleton cells: both touching intervals are active at their shared
endpoint. Checking the representative therefore checks the entire cell.
For active value intervals `[l_i, u_i]`, their intersection is
`[max(l_i), min(u_i)]` exactly when `max(l_i) <= min(u_i)`. This establishes the
reported pointwise results and coverage without numerical tolerances or sampling
assumptions. It does not establish any condition relating values in different
cells.

Receipts require exact shape and types. Extra or missing fields, reordered cells,
changed witnesses or active indices, noncanonical rationals, and Boolean or
floating-point substitutes for integer indices fail verification. JSON round
trips preserve valid receipts. No source identity, timestamps, signatures,
provenance or trusted observation judgments are attached.

## Input and resource bounds

Only exact built-in `int`, `fractions.Fraction`, and rational-text inputs are
accepted. Boolean values, floating-point values (including infinities and NaN),
other numeric classes and subclasses are rejected. Rational text is an optional
sign followed by ASCII digits, optionally followed by `/` and a strictly positive
integer denominator with no leading zero. Decimal notation, whitespace,
underscores, exponents and negative denominator text are rejected. Numerators may
have leading zeros; canonical output removes them.

Each normalized input rational has numerator and denominator of at most 256 bits.
Rational text has at most 160 characters before parsing. Inputs exceeding either
applicable limit are rejected; a long fraction reduced to small parts still has
the text-length limit. Intermediate midpoint arithmetic may exceed the input bit
limit and is kept exact. All interval and observation containers must be built-in
lists or tuples of the specified shape; iterators are not consumed. At most 128
observations are accepted. Even observations disjoint from the horizon are
validated and retained in the receipt.

There are at most 258 distinct partition endpoints and 515 cells. The direct
checker performs O(n squared) interval-activity work and emits O(n squared) active
indices in the worst case. Bit and count limits bound this computation; they are
not a sandbox or a wall-time guarantee for hostile Python objects or the process
hosting it. The verifier compares only the finite expected receipt shape and
rejects differing types or container sizes before descending.

## Verification scope

`tests/test_interval_history.py` covers malformed shapes and numeric values,
input limits, touching endpoints, singleton horizons and values, clipping,
missing coverage, contradictions, round trips, caller-input binding, and receipt
tampering. An independent finite reference checks all 1,296 ordered pairs from
36 synthetic observations: time and value endpoints in `{0, 1, 2}`. It enumerates
integer feasible values and endpoint/midpoint probes, which are exhaustive for
that test family. This finite regression is not a general independent proof.

From the repository root:

```sh
python3 -S -B -m unittest tests.test_interval_history
python3 -S -B -O -m unittest tests.test_interval_history
```

Both focused commands pass 12 tests for this candidate. These author tests do not
validate a release package or source manifest. The module does not depend on
other newly proposed modules, alter the research dispatcher, or claim to join
existing source-bound receipt schemes. No historical workload is replayed.
