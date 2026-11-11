# Exact quadratic minimax certificates

`fm_minimax` checks supplied rational witnesses for a finite convex minimax
problem. It performs no optimization search and uses only Python's standard
library. This is a standalone local API and JSON CLI, not an extension of the
research dispatcher. Source-package hashes cover its bytes; its result is not an
authenticated or source-bound research receipt.

## Declared problem

Choose a common point x in R^n. The shared rational matrix M must be symmetric
positive definite. For each scenario i, supply a constant c_i, center k_i,
equality target r_i and row offset b_i. The problem is

    minimize J(x) = max_i [c_i + (x-k_i)^T M(x-k_i)]
    subject to N(x-k_i) = r_i and b_i + Lx <= beta for every i.

The queried level E asks whether such an x exists with J(x) <= E. Constants and
E may be negative. Matrices N and L may have dependent or zero rows. Dimension
zero uses the unique empty vector and vacuously positive-definite empty metric.

All h_i = r_i + Nk_i must agree on h. The checker rejects incompatible h_i or
checks a left-null witness z with z^T N = 0 and z^T h != 0 if h is outside the
range of N. The common inequalities reduce exactly to Lx <= d, where

    d_j = beta_j - max_i b_ij.

This reduction uses the same L for every scenario. No uncertainty beyond the
finite declared scenario list is inferred.

## Supplied witnesses and proof

A `point` witness is checked directly against every original equality,
inequality and quadratic value. A failed point is not a global exclusion.

A `dual` witness supplies lambda >= 0 with sum(lambda) = 1, mu >= 0 and unrestricted
nu. Write kbar = sum_i lambda_i k_i, g = L^T mu + N^T nu, and

    v = kbar - (M^-1 g)/2,
    D = sum_i lambda_i (c_i + k_i^T M k_i)
        - mu^T d - nu^T h - v^T M v.

The checker solves M times a vector equals g by exact elimination, rather than
accepting a supplied inverse. Completing the square gives

    sum_i lambda_i f_i(x) + mu^T(Lx-d) + nu^T(Nx-h)
        = (x-v)^T M(x-v) + D.

On the feasible set this is at most J(x), hence D is a global lower bound.
Only D > E excludes the queried level. D = E alone neither proves feasibility
nor excludes it. A dual bound does not establish that the row/equality set is
nonempty.

An `exact_threshold` is emitted only with a row/equality-feasible point and a
valid dual, after checking all of:

    2M(x-kbar) + L^T mu + N^T nu = 0,
    lambda_i (f_i(x)-J(x)) = 0 for each i,
    mu_j (L_j x-d_j) = 0 for each j,
    J(x) = D.

These sufficient certificate conditions do not require a constraint
qualification or a strictly feasible point. No claim that the checker will find
such witnesses is made.

A `farkas` witness supplies mu >= 0 and unrestricted nu with

    L^T mu + N^T nu = 0 and mu^T d + nu^T h < 0.

Their weighted sum proves the row/equality set empty. Equality at zero is
insufficient. These are classical quadratic duality and Farkas certificates,
not new theorem claims or formal proof-assistant verification.

## Python and JSON interfaces

Call `from fm_minimax import certify`, then `certify(problem, witness=None)`.
Problem dictionaries require exactly:

- `metric`: n by n M.
- `equalities`: q by n N.
- `rows`: m by n L.
- `bounds`: length-m beta.
- `level`: E.
- `scenarios`: nonempty list of dictionaries, each with exactly `id`, `constant`,
  `center`, `target`, `row_offset`. Vector lengths are n, q and m respectively.

IDs are unique nonempty strings of at most 128 characters. Containers are built-in
lists/dictionaries. Scalars are exact built-in integers, `Fraction` values or
integer/rational strings such as `"-3/7"`. Floats, booleans, unsupported keys,
invalid matrix shapes and non-SPD metrics are rejected.

The optional witness dictionary may contain:

- `point`: length-n vector.
- `dual`: exactly `scenario_weights`, `row_multipliers`, `equality_multipliers`,
  with lengths equal to the number of scenarios, m and q.
- `farkas`: exactly `row_multipliers`, `equality_multipliers`.

Run `python3 -S -B -m fm_minimax < request.json`. The JSON object has `problem`
and optionally `witness`. Duplicate keys are rejected. Output rational values
are strings, and output schema is `fm-quadratic-minimax/1`. Process exit alone
is not a proof: inspect the complete result and its `status`.

- `feasible`: a supplied point proves J(x) <= E under all declared constraints.
- `infeasible`: exact equality contradiction, strict Farkas certificate, or
  strict dual lower bound excludes that condition.
- `unresolved`: no decisive valid witness, including missing/invalid witnesses
  and resource caps. A failed candidate never proves infeasibility.
- `invalid_input`: malformed problem or unsupported mathematical class.

`row_feasibility` separately distinguishes `proved_nonempty`, `proved_empty`,
and `not_established`. `exact_threshold` concerns the minimax optimum and may
exceed E. Invalid optional components do not erase other independently valid
components; exhausting the shared arithmetic cap returns unresolved.

## Bounds and execution

At most 8 coordinates, 8 equality rows, 8 scenarios and 16 inequality rows.
Input rational numerator/denominator sizes are at most 512 bits, intermediate
sizes at most 4096 bits, rational text at most 320 characters and counted
arithmetic operations at most 150,000. The CLI reads at most 131,072 bytes.
Unsupported size is a resource failure, not mathematical impossibility.

This is a trusted local Python API, not a hardened arbitrary-code sandbox.
For external JSON, use a bounded subprocess with CPU, wall-time and memory
limits; this module does not install operating-system limits. Interrupted or
incomplete output is unresolved. The direct API does not impose a serialized
byte cap. All runtime decisions use explicit checks and remain active under -O.

## Synthetic verification

`tests/test_minimax.py` covers a nondiagonal two-active-scenario optimum of 24,
strict level comparisons, equality multiplier signs, negative constants and
levels, nonoptimal/failed points, Farkas strictness, redundant constraints,
zero dimension, coordinate congruence and malformed/resource-capped inputs.
It includes 96 newly constructed scalar boundary optima. Tests check software
behavior, not arbitrary mathematical statements or the truth of supplied premises.
