# Correlated quadratic model admission and probes

`fm_correlated` is a standalone Python 3.10+ standard-library checker using
bounded exact rational arithmetic. Its success status is
`verified_conditional_algebra`, not scientific acceptance. This version admits
models, checks a supplied point against the rows, and verifies realized-pair
probes. Upper-bound, lower-bound and offset-nonnegativity witnesses are not part
of this version. It does not search for witnesses or compute an optimizer.

## Mathematical object

Let M be a symmetric positive-definite n-by-n rational matrix and
P = {x : Bx <= d}. The supplied point w must belong to P, establishing nonemptiness.
For each scenario s and real u with u^T u <= 1, define the joint image

    c_s(u) = p_s + L_s u
    a_s(u) = a0_s + 2 b_s^T u + u^T Q_s u
    f_s(x,u) = a_s(u) + (x-c_s(u))^T M (x-c_s(u)).

Q_s is symmetric but need not be positive semidefinite. The same u generates
the offset and center. Scenario latent dimensions may differ. Zero-dimensional
decision and latent spaces use their unique empty vectors; positive definiteness
of the empty matrix is vacuous. An empty row list imposes no constraints.
At w, the checker computes the exact per-scenario expansion

    z = w-p, q = a0 + z^T M z, g = b-L^T M z, H = Q+L^T M L
    f_s(w,u) = q + 2g^T u + u^T H u.

Each probe supplies a scenario and a common in-ball latent preimage reconstructing
both a and c exactly. Its cost is f_s(w,u); `defeats_supplied_point` means strictly
cost > budget for that represented pair. Equality does not defeat the point.
Probes are tagged with scope and their `global_exclusion` field is always false.
`exact_joint_image` and `outer_joint_image` are caller declarations of image
exactness or target coverage. Under outer scope a probe may lie outside the target.
No application validity or scientific acceptance follows from these declarations.

## Input contract

Call `fm_correlated.verify(json_text_or_bytes)`. Every listed field is required;
unknown fields reject. Root keys are exactly:

- `schema`: `fm-correlated-quadratic/1`.
- `model`: `metric` (n-by-n M), `B` (r-by-n), `d` (r-vector), `scope`
  (`exact_joint_image` or `outer_joint_image`), `scenarios` (nonempty list).
- `budget`: rational; `point`: row-feasible n-vector w.
- `probes`: list of realized pairs, possibly empty.

A scenario has exactly `p` (n-vector), `L` (n-by-k), `a0` (rational), `b`
(k-vector) and `Q` (symmetric k-by-k). A realized pair has exactly `scenario`
(zero-based integer index), `u` (k-vector), `a` (rational) and `c` (n-vector).
Scalars are JSON integers or strings matching
`-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?`. Floats, exponents, booleans, duplicate keys,
leading-zero strings, plus prefixes and nonpositive denominators reject.
Fractions are reduced exactly; inputs are never rounded.

The receipt contains exactly `schema` (`fm-correlated-quadratic/1/receipt`),
`status`, `scope`, `budget`, `row_feasible_point`, `probes`, `operations` and
`premises`. Rationals are strings. Each probe reports `cost`,
`defeats_supplied_point`, `scope` and `global_exclusion`. Premises distinguish
the caller's interpretation from model admission, row feasibility and probe checks.

## Resource and error boundary

Limits: 65,536 UTF-8 input bytes, nesting depth 16, 4,096 parsed value nodes,
4 decision coordinates, 4 latent coordinates per scenario, 6 scenarios, 8 rows
and 12 probes. Input numerator/denominator magnitudes are at most 96 bits;
integer JSON tokens are at most 30 characters and rational strings at most 64
characters. Arithmetic operands and results are limited to 4,096 bits per
numerator/denominator with at most 200,000 counted rational operations.
Byte and nesting checks precede JSON decoding; node counting follows it.
These are deterministic rejection limits, not a sandbox or elapsed-time guarantee.
Use process CPU, memory and wall-time limits for untrusted input.

Failures may raise Invalid (including its Limit subclass), JSON decoding errors
or Unicode errors. Rejection means an input check failed or exceeded a limit.
External process termination need not produce a receipt. Python optimization
does not remove checks: no validation uses assertions.

## Verification scope

Fresh synthetic tests cover correlated probes, both scope tags, strict budget
comparison, matrix admission, row feasibility, empty dimensions, differing latent
dimensions, nonidentity metrics, malformed inputs, decoding and arithmetic limits.
Author tests are distinct from independent review and mathematical acceptance.
