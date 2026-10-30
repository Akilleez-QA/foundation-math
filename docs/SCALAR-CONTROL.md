# Exact one-step scalar certificate prototype

This is synthetic mathematical infrastructure, not a physical model, experimental
validation, controller, or new general theorem. No material properties, equipment data,
provider calls or consumed fixtures are used.

For x_next=x+g*u+d, safe target [L,H], and allowed actions [a,b], the exact
safe action set is the intersection of [a,b] with the interval whose endpoints
are (L-x-d)/g and (H-x-d)/g (sort them when g<0). For g=0 it is all allowed
actions if x+d is safe, otherwise empty. This follows by rearranging the two
linear inequalities, reversing inequalities for a negative divisor.

If two individually feasible, currently safe models admit the same measured y
under y=x+e, |e|<=epsilon, and these exact action sets are disjoint, no single
action selected from that observation can ensure next-step safety for both.
This is a one-step statement, not continuous-time invariance or compatibility
with a full observation history. The measured witness and model inclusion must
be established separately for any real application.

The positive example has x=y=1/2, g=1, d=-1 versus d=+1, zero measurement noise,
target [0,1], actions [-2,2]. Safe sets are [1/2,3/2] and [-3/2,-1/2].
Neither individual infeasibility nor touching endpoints counts as this certificate.

Run from the source root: python -m unittest tests.test_scalar_control -v
Eleven tests passed. The arithmetic-grid test checks 3*5*5*49=3675 action
memberships against direct substitution. That finite check is regression evidence,
not a proof over all real parameters. All arithmetic uses Python Fraction.

## Numeric boundary and physical interpretation

Every target and admissible endpoint is normalized before any arithmetic,
including zero-gain cases. Malformed, reversed and nonfinite intervals are rejected.
Fraction(float) represents the exact binary value supplied, not decimal intent.
Use integers, Fraction values or rational/decimal strings when decimal intent
matters; for example "0.1" rather than the float 0.1. A microscopic separation
in exact supplied numbers is not an experimental distinguishability claim.
Measurement uncertainty, units and model validity must be declared by the caller.
The state, target, drift and observation must share units; gain times action must
have state units. No dimensional analysis, property model or pressure-reference
conversion is performed by this module. In particular, gauge and absolute
pressures must not be mixed silently. This module does not assert equipment safety.

This revision corrects a discovered mixed-float/Fraction boundary defect in an
initial prototype. A touching safe-action boundary could be reported disjoint if
raw interval endpoints bypassed normalization. The regression preserves that
counterexample and a zero-gain boundary case. This is a tested correction, not
an independent blind evaluation or a new control theorem.

A False result means this particular obstruction certificate did not pass. It
does not prove a common safe action exists, since incompatible observations or
individual infeasibility also return False. Invalid scalar inputs may raise
conversion exceptions; only interval validation standardizes ValueError.
Intersection propagates an empty-set None without validating other operands.
