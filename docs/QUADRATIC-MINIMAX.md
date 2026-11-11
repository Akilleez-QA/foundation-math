# Exact quadratic minimax problem admission

`fm_minimax` admits a finite rational quadratic minimax problem, checks equality
consistency and reduces shared inequalities. It uses Python's standard library
and performs no optimization search. Witness verification is not part of this
version of the document or implementation. Results concern only the declared
finite system; they are not scientific acceptance or real-world safety approval.

## Declared problem

Choose a common point x in R^n. The shared rational matrix M must be symmetric
positive definite. For each scenario i, supply a constant c_i, center k_i,
equality target r_i and row offset b_i. The declared problem is

    minimize J(x) = max_i [c_i + (x-k_i)^T M(x-k_i)]
    subject to N(x-k_i) = r_i and b_i + Lx <= beta for every i.

The level E asks whether such an x exists with J(x) <= E. Constants and E may be
negative. N and L may have dependent or zero rows. Dimension zero uses the unique
empty vector and vacuously positive-definite empty metric.

All h_i = r_i + Nk_i must agree on h. Disagreement proves the equalities
incompatible. Exact elimination also detects h outside the range of N and checks
a computed left-null multiplier z with z^T N = 0 and z^T h != 0.
The common inequalities reduce exactly to Lx <= d, where

    d_j = beta_j - max_i b_ij.

This reduction uses the same L for every scenario. It does not establish row
feasibility. No uncertainty beyond the finite scenario list is inferred.

## Python interface and results

Call `from fm_minimax import certify`, then `certify(problem)`.
Problem dictionaries require exactly:

- `metric`: n by n M; `equalities`: q by n N; `rows`: m by n L.
- `bounds`: length-m beta; `level`: E.
- `scenarios`: nonempty list of dictionaries with exactly `id`, `constant`,
  `center`, `target`, `row_offset`; vector lengths are n, q and m respectively.

IDs are unique nonempty strings of at most 128 characters. Containers are built-in
lists/dictionaries. Scalars are built-in integers, `Fraction` values or exact
integer/rational strings such as `"-3/7"`. Floats, booleans, unsupported keys,
invalid shapes and non-SPD metrics are rejected. Returned rationals are `Fraction`
values. Every result contains `status`, `reason`, `arithmetic_operations`,
`schema` (`fm-quadratic-minimax/1`), `scope` (`declared finite rational quadratic
system`) and `optimization_search` (`not_performed`).

- `infeasible`: equality incompatibility or an equality-range obstruction.
- `unresolved`: equality checks complete without obstruction, or a resource cap.
- `invalid_input`: malformed problem or unsupported mathematical class.

After admission, results also contain `level`, parsed `scenarios`,
`common_equality_targets` and `row_feasibility` (`not_established` or
`proved_empty`). Equality failures include `obstruction`, containing either
`kind: incompatible_common_equalities` and `targets`, or `kind: equality_range`,
`left_null_multiplier` and `target_pairing`. Otherwise `tightened_common_rows`
contains d and the reason is `no witness verification in this version`.
Malformed or resource-capped inputs may return only the universal result fields.

## Exact arithmetic and limits

At most 8 coordinates, 8 equality rows, 8 scenarios and 16 inequality rows.
Input rational numerator/denominator sizes are at most 512 bits, intermediate
sizes at most 4096 bits, rational text at most 320 characters and counted
arithmetic operations at most 150,000. Unsupported size is unresolved, not
mathematical impossibility. Arithmetic uses exact fractions; metric positivity
and elimination use explicit checks that remain active under -O.

This is a trusted local Python API. It installs no operating-system CPU,
wall-time or memory limits and imposes no serialized byte cap.

## Synthetic verification

`tests/test_minimax.py` covers incompatible equalities, equality-range
obstructions, empty dimension, invalid metrics/scalars/shapes/keys, resource
limits, exact row-offset reduction and unresolved well-formed problems.
Tests check software behavior, not the truth of supplied premises or arbitrary
mathematical statements.
