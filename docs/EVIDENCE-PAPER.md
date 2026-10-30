# Frozen API and schema v1

## Python entry points

```python
from fm_mapper import (
    SchemaError, canonical_json, digest, load_bundle, validate_bundle,
    binding_for, read_artifacts, map_evidence, render_paper,
)
b = load_bundle('examples/evidence-mapper/legacy-conditional.json')
data = read_artifacts(b, 'examples/evidence-mapper')   # dict artifact ID -> bytes; no execution
report = map_evidence(b, data)         # deterministic JSON-compatible dict
markdown = render_paper(b, data)      # independently maps original bundle anew
```

`render_paper` does not accept map output or caller-edited dispositions; it takes
the original bundle and artifact bytes. `map_evidence` and `render_paper` perform
no file or network I/O. `load_bundle` accepts a path or detaches a dict.
`validate_bundle` raises `SchemaError` for closed-shape/reference/DAG failures.
`binding_for(b, target_type, target_id, evidence_ids)` creates identity pins only;
it does not create judgments or establish truth. `digest(x)` is SHA-256 of UTF-8
canonical JSON (sorted object keys, compact separators, list order retained,
nonfinite numbers prohibited). Byte artifact hashes are ordinary SHA-256.

## Closed JSON fields

Every field listed is required; use empty arrays/maps or `null` where stated.
Unknown fields, duplicate IDs/JSON keys/references, dangling references, cycles,
missing claims in the manuscript, nonfinite/negative/bool costs are rejected.
Collections max 1,000 items; text max 32,768 characters; input and aggregate
artifact bytes max 8 MiB. IDs match `[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}`.

- Root: `schema` = `fm-evidence-paper/1`, `problem`, `artifacts`, `evidence`,
  `obligations`, `claims`, `judgments`, `attempts`, `costs`, `paper`.
- Problem: `id`, `revision`, `title`, `objective` (nonempty text).
- Artifact: `id`, `path` (relative contained file; no traversal/backslashes),
  `sha256`, `description`. Missing bytes/mismatches are visible and invalidate
  affected judgments. Symlinks escaping the explicit root are refused.
- Evidence: `id`, `kind`, `artifact_ids` (nonempty), `description`, `provenance`,
  `family`, `legacy_status` (null or certified/cited/argued/refuted/blocked/unchecked).
- Claim: `id`, `statement`, `scope`, `depends_on` (claim IDs), `evidence_ids`,
  `assumptions`, `exclusions`, `obligations` (obligation IDs).
- Obligation: same fields as claim **except** no `obligations`; `depends_on`
  refers to other obligations. Its exact statement is part of its identity.
- Judgment: `id`, `target_type` (claim/obligation), `target_id`, `binding`,
  `decision` (supports/refutes/inconclusive), `scope`, `supported_statement`,
  `evidence_ids`, `conditions`, `checks`, `assessor`, `method`, `family`, `rationale`.
  A refuting/inconclusive judgment's `supported_statement` names the assessed
  target statement; it is not an assertion that the statement is true.
- Binding: `problem_sha256`, `target_sha256` (entire original target record),
  `evidence_sha256` (ID -> canonical whole-evidence hash), `artifacts_sha256`
  (ID -> declared byte hash), exactly covering the judgment's evidence.
- Attempt: `id`, `claim_ids`, `outcome` (successful/failed/inconclusive/cancelled/
  duplicate/not_run), `artifact_ids`, `note`. All attempts retained, no inferred
  exhaustive denominator.
- Cost: `id`, `value` (finite nonnegative number or null = unknown), `unit`,
  `coverage`, `source_artifact_ids`. Known costs are reported, never extrapolated.
- Paper: `title`, `claim_ids` (exact permutation of all proposed claims),
  `limitations` (text array). Caller text is escaped in Markdown rendering.

## Non-interchangeable scopes and substantive evidence kinds

| Evidence kind | Allowed supported scopes |
|---|---|
| artifact | artifact_record |
| citation | cited |
| exact_computation | finite_computation |
| argument | reviewed_argument, conditional_theorem, intended_theorem |
| formal_proof | formal_statement, conditional_theorem, intended_theorem |
| numerical_verification | numerical_verification |
| empirical_validation | empirical_validation |
| metadata, test_report, review_report | none (context only) |

One judgment needs at least one matching substantive kind. This is a supplied
classification, not automatic interpretation of artifact prose. Lying/mistaken
judgments remain possible. The mapper is not a general counterexample analyzer.
For a finite refutation use a finite-computation target; broader logical
refutations require an explicitly supplied argument at the assessed scope.

`checks` maps named checks to passed/failed/unknown. Allowed keys are
`statement_correspondence`, `assumptions_audited`, `dependencies_complete`,
`axioms_audited`, `quantity_semantics`, `empirical_scope`, `uncertainty`.
Required supplied passes:
- formal_statement: axioms_audited;
- conditional_theorem/intended_theorem: statement_correspondence,
  assumptions_audited, dependencies_complete; formal-proof evidence additionally
  requires axioms_audited;
- empirical_validation: quantity_semantics, empirical_scope, uncertainty.
A supplied failed check invalidates a supporting judgment. These values are
**external semantic judgments**, not checks the mapper knows how to perform.

## Decisions

` supported ` means the exact requested statement/scope is supported under the
supplied judgments and required obligations, not independent truth verification.
`conditional` retains explicit assumptions/premises. Cited premises are always
conditional and propagate; their truth is not inferred. `intended_theorem`
cannot acquire unconditional status from conditional premises; use an explicitly
conditional theorem target instead. Mathematical hypotheses already inside the
precise target statement are distinct from unverified external assumptions.

`narrowed` preserves a supplied differently scoped/textual finding while marking
the requested claim unmet. `refuted` and `inconclusive` retain valid supplied
negative/uncertain outcomes. `blocked` records unresolved dependencies or required
obligations. `unbound` records unusable/stale judgments. `unsupported` records no
usable judgment. Conflicting exact-scope support/refutation yields `conflicting`,
not a majority vote. Duplicate support conditions are unioned, not erased.
Narrowed/blocked/conflicting nodes cannot discharge dependencies. Ordinary
conditional dependencies are retained with inherited conditions, not silently
promoted. Required obligations discharge only at exact scope with `supported`.

Reports include every original judgment, audit reasons, evidence family, legacy
status, condition, exclusion, obligation, attempt and cost. Claims counted once
by declared ID; different IDs with synonymous prose are **not** automatically
recognized/deduplicated. No scientific-completion boolean is inferred. The paper
state is always `draft_not_scientifically_accepted`.

## Verification boundary

Tests are synthetic software contract checks, not mathematical or empirical acceptance.
No report authenticates the truth of supplied judgments.

## v2 presentation revision (same input schema/API)

The top heading is constant: `# Foundation Math evidence report`. Neither caller
title is an accepted-result heading. Submitted titles/objective appear under
explicitly unverified metadata; other supplied prose is labeled by provenance.
Reported source prose cannot override a structured disposition. Caller limitations
are separated from tool-authored boundaries. CR/CRLF are normalized before quoted
rendering, and formatting controls are displayed literally. This is presentation
containment, not semantic understanding or truth validation of caller prose.

The title repair is a disclosed regression, not fresh blind validation.
See VERIFICATION.md for the separate standalone candidate check scope.
