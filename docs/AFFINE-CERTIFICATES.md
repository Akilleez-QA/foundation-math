# Exact affine certificates

Local candidate for review. This module verifies supplied rational certificates;
it is not a solver and does not discover multipliers or establish external facts.

## Contract

`fm_certificates` accepts a finite system of affine inequalities
`a_i dot x + c_i <= 0`. Each row is an immutable tuple with coordinate coefficients
followed by its constant. Coordinates range over real numbers. A system may be
unbounded, lower dimensional or empty, and may contain zero constraints.

An `AffineSystem` carries a nonempty caller-supplied context identifier, dimension
1 through 16, and at most 128 inequalities. Exact Python `int` and `Fraction`
values are admitted; booleans, floats, strings and mutable sequences are not.
Numerators and denominators have at most 256 bits in system rows and targets,
4096 bits in multipliers, and 8192 bits in checked accumulation intermediates.
Caps are inclusive. A cap is an implementation limit, not mathematical evidence.

## Implication

For a requested target `b dot x + d <= 0`, provide nonnegative multipliers
lambda. The checker verifies the exact coordinate equality
`sum_i lambda_i a_i = b` and constant inequality `sum_i lambda_i c_i >= d`.
Then throughout the declared feasible set,

    b dot x + d <= sum_i lambda_i (a_i dot x + c_i) <= 0.

The constant comparison direction matters. Extra nonnegative constant slack is
allowed. Implications from an empty system of constraints can establish only
nonpositive constants using the empty multiplier vector. An implication may be
vacuously valid on an infeasible declared set; it does not establish nonemptiness.

## Infeasibility

An `Infeasibility` certificate requires nonnegative multipliers, all summed
coordinate coefficients equal to zero, and a strictly positive summed constant.
Any feasible point would therefore imply a positive constant is at most zero.
A zero constant is not a contradiction. A failed or missing certificate is not
evidence that a system is feasible or that a desired implication is false.

## Composition

`compose_implications` checks every inner implication from the original system,
then checks the outer implication from the exact ordered tuple of inner targets.
If inner multipliers form the nonnegative matrix Lambda and outer multipliers
are mu, the result uses `mu Lambda`. Nonnegative multiplication preserves every
inner constant slack. The direct result is verified again against the original
system before return. No optimization or vertex enumeration is involved.

The intermediate system must use the same context identifier and dimension.
Every intermediate proof is checked, even if its outer coefficient is zero.
The API does not compose infeasibility receipts, infer a minimal constraint set,
or carry any conclusion across a changed statement.

## Binding and return values

`system_digest` binds a versioned encoding of the context, dimension, ordered
rows and exact rational values. Integer and equivalent Fraction representations
give the same digest. Reordering rows changes it. This is statement integrity,
not a signature, evidence authentication, loaded-code authentication or the
research runner's separate source-binding receipt. These new APIs are separate
from the existing `fm_research` JSON dispatcher; no JSON parser or CLI is added.

`make_implication` and `make_infeasibility` check supplied witnesses and return
frozen certificate records. They do not generate the mathematics of the witness.
Invalid supplied witnesses raise `InvalidCertificate`. Verification returns
False for malformed, wrong-kind, stale, oversized or invalid certificate records.
Unsupported system declarations raise `Unsupported`. Composition may also raise
Unsupported for shape or arithmetic caps. No unsuccessful result establishes
feasibility, infeasibility, a counterexample or a physical conclusion.

This is a trusted local Python API, not a sandbox for hostile Python objects.
No network, file, solver, third-party package or equipment access is performed.
External interpretation, completeness, units, truth and applicability remain
caller obligations. Certificates are mathematical implications under supplied
premises, not safety approval, scientific acceptance or a novelty claim.

## Synthetic example

Take `0 <= x <= 2` and `0 <= y <= 3`. In coordinate-then-constant format the
rows are `(1,0,-2)`, `(-1,0,0)`, `(0,1,-3)` and `(0,-1,0)`.
The target `(1,2,-9)` is proved by multipliers `(1,0,2,0)` because
`x+2y-9 <= x+2y-8 <= 0`. All numbers are invented dimensionless mathematics.

Focused checks:

    python3 -S -B -m unittest tests.test_affine_certificates
    python3 -S -B -O -m unittest tests.test_affine_certificates

The fresh synthetic suite covers signed coefficients, nonzero constant slack,
strict versus touching infeasibility, unbounded and empty-constraint systems,
composition, statement binding, exact types, malformed inputs and inclusive
resource bounds. Constructed witness families include 48 witnesses across four
systems and 1,440 point evaluations. Finite evaluations are regression evidence; the
inequality arguments above provide the universal conditional reasoning.
