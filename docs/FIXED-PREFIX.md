# Exact fixed-prefix continuation

`fm_prefix` is a bounded rational calculation for the supplied mathematical model

    x'(s) = H x(s) + B v(s), x(0) = initial,
    integral_0^end D(s) v(s) ds = moment,
    integral_0^end v(s)^T R v(s) ds <= budget.

The vector-valued input on `[0, cut]` is fixed, not optimized. The remaining input
ranges over real square-integrable functions on `[cut, end]`. No positivity,
pointwise input limits, derivative bounds, uncertain coefficients, or extra
path constraints are implied. The coefficients and fixed prefix are supplied
assumptions, not validated observations. These calculations are conditional on the supplied data, not a general
theorem-proving procedure.

## Input contract

Import `Continuation` from `fm_prefix`. Its keyword-only arguments are `H`, `B`,
`initial`, `R`, `D`, `moment`, `budget`, `end`, `cut`, `prefix`. With state dimension
n, input dimension m, moment dimension q, the shapes are H[n,n], B[n,m],
initial[n], R[m,m], moment[q], and D a list of q-by-m coefficient matrices.
All dimensions are 1 through 4. H must be exactly nilpotent (H^n=0); R must be
exactly symmetric positive definite. D has degree at most 3, in ascending powers
of absolute time s. Zero moments may be represented by a zero row with zero
right-hand side.

A prefix piece is `(lo, hi, coefficients)`, where coefficients is a list of
m-vectors in ascending powers of absolute time. Degree is at most 3 and there
are at most 8 pieces. Pieces must tile `[0, cut]` in order with positive lengths
and no gap or overlap. An empty prefix is required when cut is zero. Endpoint
values at joins do not affect the integrals. Require `end > 0`,
`0 <= cut <= end`, and `budget >= 0`.

Public scalar inputs must be exact Python `int` or `Fraction`, not bool, float,
string, or subclasses. Numerator magnitude and denominator are limited to 128
bits each. Containers must be lists or tuples. Derived exact rationals are not
truncated to the input bit bound. Unsupported input raises ValueError; no
floating-point fallback is used. These structural bounds are not a universal
runtime guarantee. Caller-imposed CPU, wall-clock and memory bounds remain
necessary, especially for hostile inputs.

## Calculation and justification

Let p be the fixed prefix and c its quadratic cost. Integrating the polynomial
state kernel gives the exact state at cut. Define

    r = moment - integral_0^cut D(s) p(s) ds,
    G = integral_cut^end D(s) R^-1 D(s)^T ds.

The tail moment is attainable exactly when r lies in range(G). Solve G alpha=r
by exact elimination, choosing free variables zero. This is an arbitrary
solution, not a Moore-Penrose inverse. The minimum-norm tail representative is
v0(s)=R^-1 D(s)^T alpha, with cost r^T alpha. Its function and cost are independent
of the chosen solution because null(G) is annihilated by the corresponding Gram
map. Orthogonality in the R-weighted L2 inner product makes every feasible tail
v0+w, where the moment of w is zero and its remaining budget is
rho=budget-c-r^T alpha.

`status` is `no_continuation_moment_range`, `no_continuation_budget`, or `feasible`.
The latter two expose minimum tail and total costs and reserve rho; an
inconsistent moment has these fields set to None. `minimum_tail_value(s)`
returns the polynomial representative, also when it exceeds the budget. This
is not an admitted continuation in that case. L2 functions have no intrinsic
point values; the method selects this particular polynomial representative.

For cut <= t <= end, let L_t(s)=exp(H(t-s))B on `[cut,t]`, extended by zero up
to end. Nilpotence makes the exponential polynomial. Set

    W = integral_cut^t L_t R^-1 L_t^T,
    V = integral_cut^t L_t R^-1 D^T,
    G Q = V^T,
    S = W - V Q,
    b = exp(H(t-cut)) x(cut) + V alpha.

The Gram range identity guarantees that Q exists; S is positive semidefinite
and solution-independent. Projection onto the zero-moment subspace gives the
conditional image exactly as b plus the ellipsoid with shape rho*S. In finite
dimension the minimum norm for displacement d in range(S) is d^T y, where
S y=d. Thus `future(t).target(x)` tests range membership and cost <= rho,
including singular S and zero rho. Its minimum_total_cost includes the fixed
prefix cost. Inconsistent range returns None costs; over-budget targets still
report their mathematical minimum cost.

`future(t).row(a, bound)` tests whether every state in this set satisfies
`a^T x <= bound`. It computes center `a^T b`, radius squared `rho*a^T S*a`,
and signed slack `bound-a^T b`; containment requires nonnegative slack and
slack squared at least radius squared. No irrational square root is needed.
Each query concerns one time and one target or row. Separately reachable
targets at different times need not share a single tail. These methods do not
certify an entire trajectory or optimize the prefix.

Only results returned by an unmodified Continuation instance and its `future`
method have this interpretation. Direct construction of result dataclasses,
mutation of an instance, or modification of runtime code is outside the
certificate contract; the API does not authenticate its inputs or caller.

## Synthetic example and regression scope

```python
from fractions import Fraction as Q
from fm_prefix import Continuation
c = Continuation(H=[[0]], B=[[1]], initial=[0], R=[[1]], D=[[[1]]],
                 moment=[0], budget=3, end=2, cut=1,
                 prefix=[(0, 1, [[1]])])
s = c.future(Q(3, 2))
assert s.center == (Q(1, 2),)
assert s.shape == ((Q(1, 4),),)
assert s.target([1]).reachable
```

The scalar prefix spends 1, its required tail mean is -1, and the least tail
cost is 1. Reserve is 1. Tests cover this exact boundary, singular and duplicate
moments, range failure, exhausted tails, a nilpotent two-state chain, polynomial
moments and cubic prefixes, a non-diagonal norm, rejection boundaries, and the
fact that a rejected fixed prefix is not replaced by an easier one. Opposite
two-piece prefixes with equal state and spent cost retain distinct moment
residuals and therefore different terminal centers. Tests are
finite regression evidence, distinct from independent review and mathematical
acceptance. Existing research receipt source binding is unchanged and does not
cover this module; the source-package manifest pins its bytes separately.
