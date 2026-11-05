# Exact continuous path bounds

`fm_paths` concerns real-valued absolutely continuous functions on a finite
rational interval `[0,T]`. It checks mathematical premises supplied by the
caller; it does not establish that those premises describe any external object.
All examples and tests are synthetic.

## Contract

Each record `(s,e,a,b)` states `a <= x(t) <= b` for **every** `t` in the closed
interval `[s,e]`. The directed rate premise is `-q <= x'(t) <= p` almost
everywhere, for supplied nonnegative rational `p,q`. Endpoints are included;
point constraints have `s=e`. Constraints may overlap or leave gaps. The rate
premise extends their implications across gaps; a gap is not an additional
observation. At least one record is required.

`certify_path_bounds(records, horizon, up, down, integral_band=None,
max_pairs=200000)` returns one of:

- `feasible`: exact piecewise-affine lower/upper envelopes, a finite proof of
  their extrema, and the sharp interval of values of `integral x(t) dt`.
- `infeasible`: a rational time and two indexed, conflicting propagated bounds.
- `resource_unresolved`: construction limits were reached. This proves neither
  feasibility nor infeasibility.

An optional closed rational integral band adds `integral_status='attained'`
with an explicit path, or `'excluded'`. Exclusion of the band does not make the
underlying path constraints infeasible. Infeasible receipts already exclude
all paths and do not add a separate integral conclusion.

`verify_path_bounds(records, horizon, up, down, receipt, integral_band=None)`
returns `True` only when the finite proof checks. Invalid inputs or proofs
raise `ValueError`. Supply the band when verifying a band receipt; the verifier
rejects extra or missing fields, rather than silently ignoring integral claims.
A resource outcome is not a certificate and is rejected by the verifier.
The API uses in-process Python values, not an untrusted serialization protocol.
It does not authenticate sources or bind a receipt to a file hash.

## Mathematical derivation

For a record `i`, define

`l_i(t) = a_i - p max(s_i-t,0) - q max(t-e_i,0)`

`u_i(t) = b_i + q max(s_i-t,0) + p max(t-e_i,0)`.

Integrating the directed derivative bounds shows every admissible path obeys
`l_i(t) <= x(t) <= u_i(t)`. Let `L=max_i l_i` and `U=min_i u_i`.
Each branch has slopes among `-q,0,p`; the finite maximum or minimum preserves
the directed Lipschitz inequalities. Thus `L` and `U` are absolutely continuous
and obey the rate premise. If `L<=U` throughout, both obey every record: on a
record's window, `L>=a_i` and `U<=b_i`, and their ordering supplies the other
inequalities. They are attainable pointwise extrema. A strict crossing proves
that no admissible path exists.

The producer includes all record endpoints and all pairwise branch crossings
inside each resulting cell. Every branch is affine on each cell, so endpoint
ordering decides continuous ordering exactly. It does not rely on sampling.
The verifier does **not** repeat the crossing search. It checks:

1. All record endpoints occur in the increasing subdivision, including `0,T`.
2. Every node has the exact maximum lower and minimum upper branch value.
3. A single indexed branch is tight at both endpoints of each cell for each
   envelope. By affine linearity it stays tight across the entire cell.
4. Both supplied envelopes obey the directed rate inequalities on every cell.
5. Exact trapezoidal integrals equal the claimed integral extrema.

For any admissible `x`, integrating `L<=x<=U` bounds its integral. Both extrema
are attained. Every value between them is attained by the global convex
combination `(1-theta)L+theta U`, with `0<=theta<=1`. The band witness uses this
identity, including coincident integral extrema and a zero-length horizon.
This mixture identity is specific to the **linear** integral functional; it
is not a formula for a nonlinear functional.

## Synthetic example

```python
from fm_paths import certify_path_bounds, verify_path_bounds

records = [(0, 4, -1, 3), (0, 0, 0, 0), (4, 4, 0, 0)]
receipt = certify_path_bounds(records, 4, 1, 1, (0, 0))
assert receipt['integrals'] == (-3, 4)
assert verify_path_bounds(records, 4, 1, 1, receipt, (0, 0))
```

The straight segment joining the two endpoint constraints has integral zero,
but it does not identify the sharp extrema `[-3,4]`. Interior bends matter.

## Validation and resource boundary

Accepted scalars are exact built-in `int`, `fractions.Fraction`, or strings
parsed as rational numbers. Booleans, floats and nonfinite tokens are rejected.
Input numerators and denominators are limited to 512 bits; input strings to
256 characters. Horizon/rates must be nonnegative, record windows must lie
inside the horizon, and value intervals must not be reversed. There are at
most 32 records. These input violations raise `ValueError`.

The construction is limited to 200,000 candidate branch-pair comparisons and
4,096 subdivision points. A caller may lower `max_pairs` to a nonnegative
integer. Generated certificate rationals are limited to 32,768 bits, with a
separate verifier cap so correct arithmetic growth is not confused with
oversized original inputs. Resource limits return `resource_unresolved`.
Receipt lists/tuples and exact rational components are checked before use.
The caps limit finite work; they are not a wall-clock or memory guarantee.

## Verification and scope

Fifteen author test methods cover asymmetric directions, missing time coverage,
closed-endpoint contradictions, singleton/constant/zero-horizon cases, integral
bands, malformed inputs, caps, tampering, omitted crossings, and large generated
rational roundtrips. Eighty seeded synthetic cases compare sharp extrema with
an independently implemented exact dynamic program on a half-integer lattice;
those cases use unit rates and integer record endpoints/bounds so their exact
envelope breakpoints and values lie on that lattice.

Run from the repository root:

```sh
python3 -S -B -m unittest tests.test_path_bounds
python3 -S -B -O -m unittest tests.test_path_bounds
```

Author tests are not independent mathematical acceptance or a formal proof
assistant. This API does not infer rate premises, handle arbitrary nonlinear
constraints, optimize nonlinear integrals, or impose higher derivatives.
It is separate from the research JSON dispatcher and its source-bound receipts.
