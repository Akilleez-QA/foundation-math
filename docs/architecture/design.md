# Architecture design

Foundation Math is a Python 3.10+ source-tree package using the standard library
and a selected local vendor subset. It implements finite mathematical checks,
supplied-evidence mapping and scalar certificates. There is no bridge package or
stdio adapter implementation in this repository.

| Component | Source | Responsibility |
|---|---|---|
| Exact fields | `fm_research/field.py` | Rational coefficients in quadratic fields |
| Rank | `fm_research/rank.py` | Elimination, matrix identity and certificate verification |
| Characters | `fm_research/twoi.py`, `fm_research/vendor.py` | Pinned catalog, virtual characters, tensor and restricted symmetric powers |
| Formal bundles | `fm_research/p1.py` | Supplied split-bundle cohomology and Hom characters |
| Selected vendor | `vendor/foundation-math-v014/` | Character and split-bundle contracts, producers, retained verifiers and catalog |
| Research contract | `fm_research/problem.py` | ProblemSpec validation, kernel dispatch, receipts and dependency gate |
| Research process | `fm_research/__main__.py` | File input, selected checks, JSON lines and exit status |
| Evidence mapper | `fm_mapper/core.py`, `fm_mapper/__main__.py` | Supplied judgment validation, artifact identity and draft rendering |
| Scalar certificates | `fm_control/scalar.py` | Fraction-based one-step intervals and two-model ambiguity |
| Packaging | `tools/package_source.py` | Exact manifest verification and deterministic source ZIP |

## Data flow and boundaries

Research JSON → `load_spec` → fixed `KERNELS` dispatch → `Evidence` → `gate` →
per-claim CLI JSON. Rank dispatch verifies its generated witness. Computed claims
can be certified only with matching receipts and certified/cited ancestors;
this does not prove surrounding prose. Cited and argued claims remain admitted
inputs. The CLI can write a separate evidence JSONL file.

Mapper bundle → schema/reference validation → bounded artifact reads → integrity
and supplied-judgment evaluation → map JSON and optional Markdown draft. It does
not rerun research checks or infer judgments from receipts. Scope, conditions,
open obligations and conflicting findings remain visible. Every paper remains
`draft_not_scientifically_accepted`.

Scalar functions operate separately on caller-supplied values; they are not
exposed through the research kernel registry or mapper. Their certificates are
model-conditional one-step statements, not physical validation.

The research fingerprint binds selected mathematical sources on disk, while
`SOURCE-MANIFEST.json` binds the distribution allowlist. Neither is a signature,
reviewer authentication or loaded-code authenticity check. See
[source binding](../SOURCE-BINDING.md) and the
[adapter ICD](../icd/icd-stdio.md).
