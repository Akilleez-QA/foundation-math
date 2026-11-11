# Supplied correlated quadratic certificates

`fm_correlated` is a standalone Python 3.10+ standard-library verifier of bounded,
exact rational certificates. It does not search for witnesses, compute an optimizer,
validate an application model or authenticate premises. Its success status is
`verified_conditional_algebra`, not scientific acceptance. Rejection means the
supplied certificate failed or exceeded a limit, not that the proposed inequality
is false. This module is separate from the research receipt source-binding format.
Its source bytes are pinned by SOURCE-MANIFEST.json; receipts themselves do not
contain a source digest.

## Mathematical object

Let M be a symmetric positive-definite n-by-n rational matrix and
P = {x : Bx <= d}. The supplied point w must belong to P, establishing nonemptiness.
For each scenario s and real u with u^T u <= 1, define the joint image

    c_s(u) = p_s + L_s u
    a_s(u) = a0_s + 2 b_s^T u + u^T Q_s u
    f_s(x,u) = a_s(u) + (x-c_s(u))^T M (x-c_s(u))
    F(x) = max_s max_{u^T u <= 1} f_s(x,u).

Q_s is symmetric but need not be positive semidefinite. The same u generates the
offset and center; independently matching their marginal ranges is insufficient.
Scenario latent dimensions may differ. Zero-dimensional decision and latent spaces
are supported using their unique empty vectors; positive definiteness of the
empty matrix is vacuous. An empty row list imposes no constraints. All reasoning is about
the represented finite union of joint images, with real latent balls.

## Upper bound at the supplied point

Expand at w using z = w-p:

    q = a0 + z^T M z, g = b-L^T M z, H = Q+L^T M L.

For each scenario, supply lambda >= 0, y and U_s. The verifier checks
K = lambda I-H is positive semidefinite, Ky=g and
U_s >= q+lambda+g^T y. Indeed,

    q + 2g^T u + u^T H u
      = q + lambda u^T u + g^T y - (u-y)^T K (u-y)
      <= q + lambda + g^T y.

This works for singular K. A failed range identity is rejected; no pseudoinverse
is assumed. Exact Schur elimination checks symmetry, negative pivots and the
remaining row at each zero pivot. A determinant alone is not used. The maximum
of the supplied per-scenario bounds is U, so F(w) <= U. Bounds can be conservative.
Optional offset nonnegativity witnesses apply this same argument to
q=-a0, g=-b, H=-Q, with supplied bound <= 0.

## Global lower bound on the represented problem

Each supplied pair (a_i,c_i) must include a scenario index and a common in-ball
latent preimage reconstructing both entries exactly. Supply nonnegative weights
summing to one, nonnegative row multipliers mu and vector v satisfying

    cbar = sum_i weight_i c_i
    Mv = M cbar - B^T mu / 2.

For feasible x, the maximum defining F(x) is at least the weighted average, and
adding mu^T(Bx-d) cannot increase that average. Completing the square gives

    F(x) >= (x-v)^T M (x-v)
            + sum_i weight_i (a_i+c_i^T M c_i) - mu^T d - v^T M v.

The supplied D must not exceed the constant term. Thus D <= inf_{x in P} F(x).
When both bounds are present, D <= inf F <= F(w) <= U; `represented_bound_gap`
is U-D, not an optimizer computation. Matching bounds give the represented
problem's exact value at the supplied feasible point. No claim of witness
completeness, optimizer search, runtime accuracy for approximated inputs, or
originality of these algebraic inequalities is made.

## Exact versus outer scope

`exact_joint_image` declares that the represented joint image is the target set.
`outer_joint_image` declares only that the target is contained in it. These are
caller premises, not verified evidence. For either scope, U <= budget admits the
supplied point conditional on the premise. D > budget excludes all feasible
points for the represented problem. It excludes the target problem only under
exact scope. For outer scope, the receipt sets only `outer_image_globally_excluded`;
that is not target infeasibility. Equality with the budget never triggers strict
exclusion. A failed admission flag is not proof of infeasibility.

Probes check the loss of one reconstructed pair at w. They never give global
exclusion. Under outer scope, a defeating probe may lie outside the target and
therefore does not even establish failure of w for that target. The probe flag
`defeats_supplied_point` refers only to the represented image, tagged by scope.
No input evidence flag promotes outer-image exclusion to target exclusion.

## Input contract

Call `fm_correlated.verify(json_text_or_bytes)` or run
`python3 -S -B -m fm_correlated INPUT.json`, using `-` for stdin.
`examples/correlated-quadratic.json` is a fresh synthetic equality example.
Every listed field is required; unknown fields reject. Optional witness categories
use JSON null. Scalars are JSON integers or strings matching
`-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?`. Floats, exponents, booleans, duplicate keys,
leading-zero strings, plus prefixes and nonpositive denominators reject.
Fractions are reduced exactly; inputs are never rounded.

Root fields:

- `schema`: `fm-correlated-quadratic/1`.
- `model`: `metric` (n-by-n M), `B` (r-by-n), `d` (r-vector), `scope`
  (`exact_joint_image` or `outer_joint_image`), `scenarios` (nonempty list).
- `budget`: rational; `point`: feasible n-vector w.
- `upper`: null or one upper witness per scenario, in scenario order.
- `lower`: null or a global lower witness.
- `probes`: list of realized pairs, possibly empty.
- `offset_nonnegative`: null or one upper witness per scenario for its negated offset.

A scenario has exactly `p` (n-vector), `L` (n-by-k), `a0` (rational), `b`
(k-vector) and `Q` (symmetric k-by-k). An upper witness has exactly `lambda`,
`y` (k-vector) and `bound`. A realized pair has exactly `scenario` (zero-based
integer index), `u` (k-vector), `a` (rational) and `c` (n-vector). A lower witness
has exactly `pairs` (nonempty realized-pair list with an extra `weight` field on
each), `mu` (r-vector), `v` (n-vector) and `bound`. Repeated pairs are permitted.

The receipt uses schema `fm-correlated-quadratic/1/receipt`; rationals are strings,
absent bounds and gaps are null. It reports scope, budget, point row feasibility,
upper/lower bounds, admission, the two separate global-exclusion flags, optional
offset nonnegativity, non-global probes and arithmetic operation count. Missing
certificates leave the corresponding positive conclusion false or null; they do
not certify its negation.

## Resource and error boundary

Limits: 65,536 UTF-8 input bytes, nesting depth 16, 4,096 parsed value nodes,
4 decision coordinates, 4 latent coordinates per scenario, 6 scenarios, 8 rows,
12 lower pairs and 12 probes. Input numerator/denominator magnitudes are at most
96 bits; integer JSON tokens are at most 30 characters and rational strings at
most 64 characters. Arithmetic results and operands are limited to 4,096 bits per
numerator/denominator with at most 200,000 counted rational operations.
The byte and nesting checks precede JSON decoding; node counting follows it.
These are deterministic rejection limits, not a sandbox or an elapsed-time
service guarantee. Use process CPU, memory and wall-time limits for untrusted input.
Do not modify the module's limits when interpreting this contract.

Library failures may raise Invalid (including its Limit subclass), JSON decoding
errors or Unicode errors. The CLI reads at most the byte limit plus one, emits
`rejected_or_unresolved` JSON and exits 2 on recognized input/file failures;
success exits 0. Process termination from an external resource limit need not
produce a receipt. Python optimization does not remove checks: no validation
uses assertions.

## Verification scope

Fresh synthetic tests cover correlation, exact/outer logic, strict budget
boundaries, singular and indefinite matrices, nonidentity metrics, differing
latent dimensions, row-dual identities, empty dimensions, malformed inputs,
resource-limit rejection and CLI behavior. A 205-point rational grid compares
upper certificates with direct substitution; finite tests are regression evidence,
not a proof over all inputs. Full normal and optimized suites and selected-source
packaging must be checked on the exact candidate bytes before promotion.
