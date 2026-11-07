# Exact interval linear-system residuals

This source-tree module computes rational enclosures for finite square linear
systems. It uses Python 3.10+ and the standard library. It is not a floating-point
solver, general invertibility test, or formal proof assistant. Natural logarithms and transcendental functions are not
part of this contract.

## Interface and admitted inputs

Import `enclose_linear_residual` and `verify_linear_residual` from
`fm_enclosures`. Call `enclose_linear_residual(matrix, candidate, rhs)` with:

- A square matrix of dimension 1 through 16. Every entry is a closed interval
  represented by a two-element list or tuple `(lower, upper)`.
- An exact rational candidate vector of the same dimension.
- A vector of closed right-hand-side intervals of the same dimension.

Containers must be ordinary lists or tuples, not subclasses or iterators.
Rationals must be ordinary integers, `fractions.Fraction` instances, or strings
matching `[+-]?[0-9]+(?:/[0-9]+)?` in ASCII. Denominators are strictly positive.
Leading zeros and an optional numerator sign are allowed; whitespace, exponent
notation, decimal notation, Unicode digits, floats, booleans, and subclasses are
rejected. A string's length is checked before matching or integer conversion.
Input integers and numerator/denominator components are limited to 256 bits;
strings are limited to 160 characters. String components are checked before
cancellation, whereas an existing Fraction is checked in its reduced form.
Malformed or noncanonical Fraction internals are rejected.

All interval endpoints are finite rationals with lower no greater than upper.
Each matrix coefficient and each right-hand-side coordinate independently ranges
across its supplied interval. There are no hidden correlations or joint
constraints. The candidate vector does not range across intervals.

The return value is a frozen `LinearResidualEnclosure` with:

- `residuals`: a tuple of exact Fraction endpoint pairs for `A x - b`;
- `residual_norm_upper`: the largest absolute residual endpoint;
- `dominance_margin`: the exact uniform margin defined below;
- `forward_error_upper`: a Fraction if the margin is positive, otherwise `None`;
- `forward_status`: `bounded` or `unresolved` respectively.

For example:

```python
from fm_enclosures import enclose_linear_residual

result = enclose_linear_residual(
    [[(3, 4), (-1, 1)], [(0, 1), (4, 5)]],
    [2, -1],
    [(5, 6), (-4, -3)],
)
```

Here the residual intervals are `[-1, 4]` and `[-2, 2]`. The residual infinity
norm is at most 4, the dominance margin is 2, and the solution error in infinity
norm is at most 2 for every admitted matrix and right-hand side.

## Residual enclosure proof and sharpness

Write each coefficient interval as `[l_ij, u_ij]` and each right-hand-side
interval as `[p_i, q_i]`. For the fixed rational coordinate `x_j`, the product
interval has endpoints `min(l_ij*x_j, u_ij*x_j)` and
`max(l_ij*x_j, u_ij*x_j)`. The residual endpoints are therefore:

```text
L_i = sum_j min(l_ij*x_j, u_ij*x_j) - q_i
U_i = sum_j max(l_ij*x_j, u_ij*x_j) - p_i
```

Every term has its own independent interval choice. Selecting the appropriate
endpoint for each coefficient and the opposite endpoint for the right-hand side
attains each bound. Thus each component interval is sharp for the admitted box.
This is not a claim of sharpness when unrepresented correlations are present.
All operations are exact rational operations, with no rounding error or
statistical interpretation.

## Forward error proof

For a closed interval `I`, define `max_abs(I)` as the larger absolute endpoint.
Define `min_abs(I)` as zero if the interval contains zero, and otherwise the
smaller absolute endpoint. Compute

```text
beta = min_i (min_abs(A_ii) - sum_(j != i) max_abs(A_ij)).
R = max_i max(abs(L_i), abs(U_i)).
```

For any admitted concrete matrix and any vector `y`, choose an index `k` where
`|y_k| = ||y||_infinity`. The triangle inequality gives

```text
|(A y)_k| >= |A_kk| |y_k| - sum_(j != k) |A_kj| |y_j|
             >= beta ||y||_infinity.
```

When beta is positive, this forces a trivial nullspace. A finite square matrix
with trivial nullspace is invertible. For its unique solution `z` of `A z = b`,
apply the inequality to `y = x - z`, obtaining

```text
||x - z||_infinity <= ||A x - b||_infinity / beta <= R / beta.
```

The argument permits negative diagonal entries and intervals not centered on a
point. Diagonal intervals containing zero have minimum absolute value zero.
The bound is sufficient and uniform, but need not be the best possible bound.

If beta is zero or negative, the residual enclosures remain valid and sharp,
but the forward status is `unresolved`. This does not assert singularity,
infeasibility, or existence or nonexistence of a solution. For example the point
matrix `[[1, 2], [3, 4]]` is invertible but does not pass this sufficient test.
A zero residual in an unresolved system is not promoted to a unique-solution
forward certificate.

## Verification and trust boundary

`verify_linear_residual(result, matrix, candidate, rhs)` checks ordinary result
and field types, rational limits, and equality against a fresh recomputation
from the supplied problem. It returns False for malformed or altered results or
invalid problem inputs. Exact type checks reject numerically equal boolean or
integer substitutions for Fraction fields. Frozen dataclasses prevent normal
attribute assignment, but Python introspection can bypass freezing; recompute
verification detects changes to mathematical fields. A result alone does not
bind to a stored input identity or authenticate its author. Call verification
with the intended inputs. Different inputs that produce the same output are
intentionally accepted. Runtime monkey-patching of this module or the Python
interpreter is outside the trust boundary.

## Resource behavior and tests

Each call visits at most 256 matrix intervals and 16 vector coordinates and
right-hand-side intervals. All retained arithmetic results are capped at 16,384
bits per numerator and denominator. An individual binary operation can
transiently use up to twice that many operand bits before the result check;
inputs to that operation have already been bounded. Intermediate comparisons
and greatest-common-divisor checks also operate on bounded integers. These are
algorithmic size limits, not a promise of wall time, peak process memory, or
availability in an arbitrary Python runtime. Callers handling untrusted input
should additionally use process CPU, memory, and wall-time limits.

Malformed input raises ValueError. Dimension, text, input-bit, and intermediate
bit-limit failures raise `EnclosureLimitError`, a ValueError subclass. A resource
rejection produces no enclosure and is not evidence of singularity, infeasibility,
or a mathematical counterexample. The verifier returns False on these failures.
It does not hide process-level MemoryError or external interruption.

Synthetic tests cover a hand-calculated enclosure, exhaustive independent
coefficient/right-hand-side corners for multiple candidate signs and zeros,
exact inverse solutions at all corners of a uniformly dominant matrix, negative
diagonals, zero-crossing diagonals, unresolved nonsingular examples, exact string
inputs, malformed grammars and shapes, dimension/bit/text caps, immutable and
intentionally tampered results, noncanonical Fractions, and the arithmetic-limit
failure path under a lowered test cap. No test uses external data or a numerical
solver. Run both assertion modes from the repository root:

```sh
python3 -S -B -m unittest tests.test_numerical_enclosures
python3 -S -B -O -m unittest tests.test_numerical_enclosures
```

Author tests and this proof explanation are separate from independent review.
Focused tests do not by themselves establish release-package validity.
