# Exact linear optimization certificates

`fm_optimization` verifies rational upper bounds for the maximization problem

    maximize d + c*x subject to A*x <= b and E*x = f.

A row tuple `(a_1, ..., a_n, b)` encodes one inequality or equality. All rows,
coordinates, the objective, its offset, and an ordered context label are bound
by the certificate's SHA-256 digest. The label is an identifier, not evidence.
The caller supplies the independently intended `LinearProgram` to every verifier.

## Weak duality and attainment

For nonnegative y and unrestricted z satisfying `A^T*y + E^T*z = c`, every
feasible x satisfies

    d + c*x <= d + b*y + f*z = U.

`verify_dual_bound(expected, certificate)` checks this identity, nonnegativity,
and the exact bound U. A feasible supplied point with objective U additionally
proves that U is the attained maximum; `verify_attainment` checks both premises.
No optimizer or feasibility search is performed. An upper-bound implication may
be vacuous when the supplied constraints are inconsistent. Only a verified
attaining point proves nonemptiness and optimality.

Signed constants remain signed. Negative upper bounds are valid. No tolerance,
absolute-value substitution, or floating-point rounding is used.

## Repairing a candidate

`repair_dual(program, inequality_candidates, equality_candidates,
equality_correction=None, box=None)`:

1. Clamps negative inequality candidates to zero.
2. Adds a supplied signed correction to equality candidates.
3. Recomputes the exact residual `s = c - A^T*y - E^T*z` after both changes.
4. If s is zero, constructs a certificate without a box.
5. Otherwise requires an explicit finite box `[l,u]`. Its support value is
   `sum_j max(s_j*l_j, s_j*u_j)`, including the signed center contribution.

For a supplied box, the output always binds the augmented inequalities, ordered
as the original A rows, all `x_j <= u_j` rows, then all `-x_j <= -l_j` rows.
The new multipliers are y, the positive part of s, then the negative part of s.
Their exact identity reproduces c. The bound includes `f*z`, so an equality
correction changes the constant as well as the residual.

**The certificate concerns the explicit intersection with the box.** The repair
routine and `augment_box` do not prove that the original feasible set lies in
the box. Using the result as a bound on the original problem requires a separate
justification of that containment. Do not treat a model returned by a helper as
independent evidence that it is the intended problem.

A residual that cannot be repaired without a box does not prove that the
objective is unbounded. It rejects this route using these candidates only.
Supplying a zero correction is allowed; corrections are not searched for.

## Synthetic example

```python
from fractions import Fraction as F
from fm_optimization import LinearProgram, repair_dual, verify_attainment

problem = LinearProgram(
    'synthetic-equality', 2,
    ((1, 0, 3), (-1, 0, 2)),
    ((1, -1, 4),),
    (1, -1),
)
certificate = repair_dual(problem, (0, 0), (F(2, 3),), (F(1, 3),))
assert certificate.upper_bound == 4
assert verify_attainment(problem, certificate, (0, -4))
```

This is a constant query on an affine slice. A separate box-only test enumerates
all vertices of 90 fresh rational boxes, while a two-dimensional test derives
all feasible pairwise row intersections to check repaired upper bounds. These
are finite synthetic tests, not claims of exhaustive mathematical validation.

## Input and resource contract

Python 3.10+ and standard library only. Inputs use exact built-in `int` or
`fractions.Fraction`; booleans, floats, strings, numeric subclasses and mutable
containers are rejected. Dimensions are 1–16, with at most 128 inequalities
and 64 equalities. Box augmentation counts toward the 128-row limit. Context
labels are nonblank strings of at most 128 characters.

Numerator/denominator limits: 256 bits for problem coefficients and box endpoints;
4,096 bits for candidates, corrections, multipliers and supplied points; 8,192
bits for accumulated arithmetic and reported bound values. Loops are bounded.
Constructors and repair raise `Unsupported` for arithmetic beyond these limits;
it is not a mathematical refutation. Invalid expected problems also raise
`Unsupported`. For a well-formed expected problem, malformed or false
certificates/points, including witness arithmetic exceeding the limit, return
`False`.
`repair_dual` raises `InvalidCertificate` for a nonzero box-free residual.

`program_digest` normalizes equal rational values, but preserves row order and
every problem field. It binds mathematical input, not source code or provenance.
Frozen records and exact types are not a sandbox against Python object tampering,
monkey-patching or preallocation of arbitrarily large inputs by a caller. No CLI
or JSON transport, network service, solver integration or general LP solver is
included. This module is separate from source-bound research receipts.

## Verification

```sh
python3 -S -B -m unittest tests.test_dual_repair
python3 -S -B -O -m unittest tests.test_dual_repair
python3 -S -B -m unittest discover -s tests -t .
python3 -S -B -O -m unittest discover -s tests -t .
```

Focused tests cover signed corrections and support, negative candidate clamping,
wrong-box and model mutation rejection, degenerate boxes, empty feasible sets,
attainment failures, row/dimension bounds, malformed witnesses and exact vertex
oracles. Keep finite test success separate from independent review, formal
proof-assistant verification, source-package verification and remote CI.
