# Exact affine-query witnesses

`fm_identifiability` is an independent standard-library verifier for supplied
rational witnesses. It neither finds witnesses nor solves feasibility problems.
All examples here are fresh synthetic algebraic instances.

## Model and interface

For an n-dimensional real vector x, define the closed fiber

F = {x : C x = z and L x <= h},

with componentwise inequalities, and the affine query f(x) = d + q x.
Every coefficient and witness coordinate must be an exact built-in `int` or
`fractions.Fraction`. Booleans, subclasses, floats, and strings are rejected.
Vectors and matrices must be built-in tuples, including every matrix row.
Empty tuples represent absent constraints. Zero-dimensional models are allowed.

`Model(C, z, L, h, q, d=0)` normalizes rationals and checks dimensions. The model,
witnesses, and results are frozen, slotted data classes with tuple fields.
Constructing a model copies rational scalars. The SHA-256 `model.digest` covers
a version tag and the entire ordered model: C, z, L, h, q, and d, with canonical
numerator/denominator pairs. Equivalent int/Fraction encodings bind identically;
reordering or scaling constraints generally changes the digest.

The caller supplies its independently selected expected `Model` to each
verification function. Witnesses carry that model's digest. The verifier
revalidates the model and witness at every call and rejects a binding mismatch.
It does not choose the expected model from the witness. A digest binds data, not
the identity of its author, loaded-code authenticity, or intended applicability.
Python reflection can bypass frozen attributes; this is not an adversarial
in-process sandbox or a cryptographic signature. The caller must retain the
expected model independently of untrusted witness input.

Malformed inputs, unsupported types, dimensional mismatches, binding mismatches,
and resource-limit failures raise `ValueError`. A structurally valid witness
that fails a mathematical obligation returns `invalid_witness` and no value.
There is no CLI, serialization parser, optimizer, or external dependency.

## Two supplied feasible points

`verify_pair(expected_model, PairWitness(model.digest, first, second))` checks
both equalities and all closed inequalities at both points. Only if both points
are feasible does it evaluate f exactly and return:

- `query_distinct`, with both values, if the values differ. This proves F is
  nonempty and f is not constant on F.
- `same_query`, with both values, if the values coincide. This proves only
  agreement at the supplied points, not constancy over F. The points may coincide.

An invalid point does not prove an empty fiber. Even two distinct feasible points
with equal query values need not establish full constancy.

```python
from fm_identifiability import Model, PairWitness, verify_pair

model = Model(((1, 1),), (6,), ((-1, 0), (0, -1)), (0, 0), (1, 0), 7)
result = verify_pair(model, PairWitness(model.digest, (1, 5), (4, 2)))
print(result.status, result.values)
```

This gives `query_distinct` and exact values 8 and 11. A common offset changes
both query values equally and cannot change whether they differ.

## Sufficient whole-fiber constancy

`verify_constancy(expected_model, ConstancyWitness(model.digest, anchor,
multipliers))` checks a feasible anchor and an exact row vector lambda satisfying
lambda C = q. It returns `constant_on_fiber` with value d + lambda z only if both
obligations hold. The anchor prevents a vacuous certificate for inconsistent
constraints or an empty fiber.

Proof: for every x in F, q x = (lambda C) x = lambda (C x) = lambda z.
Adding d yields the returned value. The feasible anchor establishes nonemptiness.
This argument applies to real feasible points, not only rational witnesses.
Neither full row rank nor unique multipliers is required.

```python
from fractions import Fraction as F
from fm_identifiability import Model, ConstancyWitness, verify_constancy

model = Model(((1, 2), (2, 4)), (3, 6), (), (), (F(1, 2), 1), F(2, 3))
witness = ConstancyWitness(model.digest, (1, 1), (F(3, 2), F(-1, 2)))
result = verify_constancy(model, witness)
print(result.status, result.value)
```

The rank-deficient equalities certify the constant 13/6. With no equality rows,
this verifier certifies only q = 0, still requiring a feasible anchor.

This is sufficient, not necessary, in the presence of priors. For example,
C and z empty, L = ((1,), (-1,)), h = (2, -2), q = (1,), and d = 3 force x = 2
and hence f = 5. No equality-row-span witness exists for this model. Rejecting
that witness says nothing about whether another proof of constancy exists.
This module does not derive implied equalities from inequalities or certify
infeasibility. It does not interpret coefficients as measurements or empirical
claims. Successful checks are finite, model-conditional mathematical evidence.

## Bounded work and verification

At most 32 coordinates, 64 equality rows, and 64 inequality rows are accepted.
Each normalized input numerator and denominator has at most 256 bits. Every
arithmetic product, accumulation, and final offset addition is checked against
16,384 bits. Limits are fixed constants rather than caller-controlled budgets.
Arithmetic can therefore reject an otherwise valid witness on resource grounds;
that exception is not a mathematical refutation. These checks are not an OS
memory/time sandbox, and callers are responsible for bounding input parsing.

Tests cover offsets, rank deficiency, rational values, zero-dimensional models,
empty and inconsistent equalities, closed prior boundaries, prior-only
constancy, exact model binding, immutable containers, malformed witnesses, and
input/intermediate resource limits. Run both modes from the repository root:

```sh
python3 -S -B -m unittest tests.test_identifiability
python3 -S -B -O -m unittest tests.test_identifiability
```

Author tests do not replace independent source review or mathematical review.
