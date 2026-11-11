# Foundation Math software requirements specification

| Field | Value |
|---|---|
| Document ID | FMATH-SRS |
| Version | 2.0 |
| Status | Baselined |
| Owner | Akilleez-QA maintainer |
| Date | 2026-11-08 |
| Baseline commit | 53a58dde072b1d3f92836a1365f88f364b880a33 |
| Applies to | foundation-math main at baseline commit, plus the documentation tooling added in PR #30 |
| Classification | Self-assessed Class E analog; not safety-critical (see [SMP §1](../plan/software-management-plan.md#1-software-classification-self-assessed)) |

> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&page_name=all), [NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the [NASA Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) documentation guidance. This is not a NASA compliance determination or certification. The software classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent verification and validation, or hazard analysis is asserted. The document describes the implementation inspected at the baseline commit.

## 1. Introduction

### 1.1 Purpose and audience

This document states what Foundation Math does, as inspected in the code at the baseline commit, and how each statement is verified. It is for contributors changing the code and for reviewers checking a change. Every requirement describes implemented behaviour that a test, inspection or demonstration checks. Behaviour with no test is listed in [§9](#9-untested-behaviour-requirement-gaps) as a gap, not as a requirement.

### 1.2 Scope

In scope: the exact research kernels and ProblemSpec gate (`fm_research`), the evidence mapper (`fm_mapper`), the scalar one-step certificates (`fm_control`), affine certificates (`fm_certificates`), affine-query witnesses (`fm_identifiability`), interval residual enclosures (`fm_enclosures`), exact interval histories (`fm_intervals`), the selected v0.14 vendor subset, the source packager and the documentation trace check.

Out of scope: any stdio JSON-RPC bridge or Cstack adapter (none exists in this repository), installation as a wheel, physical or engineering validation, and scientific acceptance of any claim.

Trust assumptions: one trusted local operator runs the code on files they chose. Input files may be wrong or malformed, so they are validated. In-process Python callers are trusted; the library APIs are not sandboxes against hostile Python objects.

### 1.3 System overview

Foundation Math is a Python 3.10+ standard-library source tree. It exposes two command-line programs and seven Python packages. The [design description](../architecture/architecture.md) shows the components. The [process interface ICD](../icd/icd-stdio.md) and the [Python API ICD](../icd/icd-python-api.md) define the external interfaces. The [data dictionary](../data/data-dictionary.md) defines every input and output field.

## 2. Requirement record format

Each requirement has an ID, one "shall" statement, rationale, derivation (source paths), allocated-to (SDD component), verification method (T test, A analysis, I inspection, D demonstration) and status (Proposed, Baselined, Deleted). IDs follow the existing `REQ-MATH-###` scheme and are never reused. REQ-MATH-001 to REQ-MATH-013 keep their earlier wording. `tools/check_trace.py` parses this format.

## 3. Functional requirements

### 3.1 Exact research kernels

### REQ-MATH-001 — Exact quadratic arithmetic

Quadratic arithmetic shall use exact rational coefficients and reject approximate coefficients and invalid radicands.

- Rationale: Preserve exact arithmetic.
- Derivation: `fm_research/field.py`
- Allocated to: SDD §4 Exact fields
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-002 — Rank certificates

Rank certificates shall bind matrix bytes and verify a nonsingular minor and rank upper bound over supported fields.

- Rationale: Check finite rank witnesses.
- Derivation: `fm_research/rank.py`, `fm_research/problem.py`
- Allocated to: SDD §4 Rank
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-003 — Pinned character arithmetic

Character operations shall use the pinned catalog, preserve distinct physical labels, and restrict symmetric powers to W or Wp in degrees 0 through 256.

- Rationale: Respect the supplied table's scope.
- Derivation: `fm_research/twoi.py`, `fm_research/vendor.py`, `vendor/foundation-math-v014/character_ring/`
- Allocated to: SDD §4 Characters, Selected vendor
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-004 — Formal split-bundle characters

Split-bundle operations shall return formal cohomology and Hom characters under the supplied splitting and vendor bounds.

- Rationale: Avoid interpreting characters as chosen maps.
- Derivation: `fm_research/p1.py`, `vendor/foundation-math-v014/split_bundle/`
- Allocated to: SDD §4 Formal bundles, Selected vendor
- Verification: T — see verification matrix
- Status: Baselined

### 3.2 ProblemSpec contract and research gate

### REQ-MATH-005 — ProblemSpec admission

ProblemSpec loading shall reject unsupported schemas, fields, kernels, float inputs, duplicate claim IDs and invalid dependency graphs.

- Rationale: Admit only the fixed finite-check contract.
- Derivation: `fm_research/problem.py`
- Allocated to: SDD §4 Research contract
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-006 — Conditional evidence gate

The research gate shall check receipt identities and transitive dependencies before assigning computed claims certified, refuted, blocked or unchecked.

- Rationale: Retain conditional evidence semantics.
- Derivation: `fm_research/problem.py`
- Allocated to: SDD §4 Research contract
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-007 — Research source identity

Research source identity shall bind the selected source/catalog files, reject catalog changes and leave stale receipts unchecked.

- Rationale: Bind receipts to selected bytes.
- Derivation: `fm_research/problem.py`, `fm_research/vendor.py`
- Allocated to: SDD §4 Research contract
- Verification: T — see verification matrix
- Status: Baselined

### 3.3 Evidence mapper

### REQ-MATH-009 — Mapper bundle validation

The mapper shall validate its closed schema, references, graphs and exact judgment/artifact bindings without promoting evidence counts to theorem support.

- Rationale: Keep supplied judgments explicit.
- Derivation: `fm_mapper/core.py`
- Allocated to: SDD §4 Evidence mapper
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-010 — Qualified draft reports

Mapper reports shall preserve qualifications and all proposed claims, mark drafts unaccepted, and render supplied prose as unverified text.

- Rationale: Prevent report text from asserting acceptance.
- Derivation: `fm_mapper/core.py`
- Allocated to: SDD §4 Evidence mapper
- Verification: T — see verification matrix
- Status: Baselined

### 3.4 Scalar control certificates

### REQ-MATH-013 — Scalar one-step certificates

Scalar certificates shall normalize intervals, compute exact one-step safe actions, and certify ambiguity only for two individually feasible, currently safe, observation-compatible models with disjoint action sets.

- Rationale: Limit the certificate to its mathematical claim.
- Derivation: `fm_control/scalar.py`
- Allocated to: SDD §4 Scalar certificates
- Verification: T — see verification matrix
- Status: Baselined

### 3.5 Affine certificates

### REQ-MATH-014 — Affine system admission and bounds

`AffineSystem` construction shall accept only a nonempty context of at most 128 characters, dimension 1 through 16, at most 128 tuple rows of exact `int` or `Fraction` values with at most 256 numerator and denominator bits, and raise `Unsupported` otherwise.

- Rationale: Keep the certificate arithmetic exact and bounded.
- Derivation: `fm_certificates/affine.py`
- Allocated to: SDD §4 Affine certificates
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-015 — Affine implication check

Implication verification shall accept a certificate only when its nonnegative multipliers reproduce the target coordinates exactly and give a summed constant at least the target constant.

- Rationale: This is the condition under which the target inequality follows from the system.
- Derivation: `fm_certificates/affine.py`
- Allocated to: SDD §4 Affine certificates
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-016 — Affine infeasibility check

Infeasibility verification shall accept a certificate only when its nonnegative multipliers sum the coordinates to zero and the constants to a strictly positive value.

- Rationale: A zero constant is not a contradiction.
- Derivation: `fm_certificates/affine.py`
- Allocated to: SDD §4 Affine certificates
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-017 — Affine implication composition

`compose_implications` shall verify every inner implication and the outer implication over the ordered inner targets, then return a direct implication that is verified again against the original system.

- Rationale: Composition must not carry an unchecked step.
- Derivation: `fm_certificates/affine.py`
- Allocated to: SDD §4 Affine certificates
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-018 — Affine statement binding

`system_digest` shall bind the context, dimension, row order and exact rational values so that equal rationals give equal digests and a certificate with another digest does not verify.

- Rationale: A certificate must not transfer to a changed statement.
- Derivation: `fm_certificates/affine.py`
- Allocated to: SDD §4 Affine certificates
- Verification: T — see verification matrix
- Status: Baselined

### 3.6 Affine-query witnesses

### REQ-MATH-019 — Query model admission, binding and limits

`Model` and witness construction shall accept only built-in tuples of exact `int` or `Fraction` values within 32 coordinates, 64 equality rows, 64 inequality rows, 256 input bits and 16,384 working bits, bind every model field in `digest`, and raise `ValueError` for any violation or binding mismatch.

- Rationale: Bounded exact work and no transfer of a witness to another model.
- Derivation: `fm_identifiability/__init__.py`
- Allocated to: SDD §4 Affine-query witnesses
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-020 — Two-point query check

`verify_pair` shall return `query_distinct` or `same_query` with both exact values only when both supplied points satisfy every equality and closed inequality, and `invalid_witness` otherwise.

- Rationale: Agreement at two points does not prove constancy; only feasible points count.
- Derivation: `fm_identifiability/__init__.py`
- Allocated to: SDD §4 Affine-query witnesses
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-021 — Whole-fiber constancy check

`verify_constancy` shall return `constant_on_fiber` with value d + λz only when the anchor is feasible and λC = q holds exactly, and `invalid_witness` otherwise.

- Rationale: The feasible anchor prevents a vacuous certificate for an empty fiber.
- Derivation: `fm_identifiability/__init__.py`
- Allocated to: SDD §4 Affine-query witnesses
- Verification: T — see verification matrix
- Status: Baselined

### 3.7 Interval residual enclosures

### REQ-MATH-022 — Enclosure input admission

`enclose_linear_residual` shall accept only square matrices of dimension 1 through 16 with interval entries, exact rationals given as `int`, reduced `Fraction` or ASCII `n` or `n/d` strings of at most 160 characters and 256 bits, and raise `EnclosureLimitError` for limit violations and `ValueError` for other malformed input.

- Rationale: Bounded exact arithmetic with a strict input grammar.
- Derivation: `fm_enclosures/numerical.py`
- Allocated to: SDD §4 Interval enclosures
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-023 — Sharp residual enclosure

The residual enclosure shall give, for each row, the exact minimum and maximum of A x − b over the independent coefficient and right-hand-side intervals.

- Rationale: Each endpoint is attained at a corner, so the enclosure is sharp for the admitted box.
- Derivation: `fm_enclosures/numerical.py`
- Allocated to: SDD §4 Interval enclosures
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-024 — Conditional forward error bound

The enclosure shall report `bounded` with forward error R/β only when the uniform diagonal-dominance margin β is positive, and `unresolved` with no bound otherwise.

- Rationale: The bound needs β > 0; β ≤ 0 is not evidence of singularity.
- Derivation: `fm_enclosures/numerical.py`
- Allocated to: SDD §4 Interval enclosures
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-025 — Enclosure verification

`verify_linear_residual` shall return True only for an unaltered `LinearResidualEnclosure` of exact field types that equals a fresh recomputation from the supplied problem.

- Rationale: Detect tampered or mistyped results.
- Derivation: `fm_enclosures/numerical.py`
- Allocated to: SDD §4 Interval enclosures
- Verification: T — see verification matrix
- Status: Baselined

### 3.8 Exact interval histories

### REQ-MATH-030 — Exact interval operations

`interval` and `intersection` shall return exact `Fraction` endpoints, retaining singleton intersections and returning `None` for empty intersections.

- Rationale: Distinguish a singleton feasible set from an empty intersection.
- Derivation: `fm_intervals/history.py`, `docs/INTERVAL-HISTORY.md`
- Allocated to: SDD §4 Interval histories
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-031 — Interval rational admission

Interval endpoints shall reject Boolean, floating-point and malformed rational inputs, rational text longer than 160 characters, and normalized numerators or denominators exceeding 256 bits with `ValueError`.

- Rationale: Keep admitted quantities exact and bounded.
- Derivation: `fm_intervals/history.py`, `docs/INTERVAL-HISTORY.md`
- Allocated to: SDD §4 Interval histories
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-032 — Interval container admission

Interval operations and history analysis shall reject malformed containers, reversed endpoints, empty intersection families, and families exceeding 128 intervals or observations with `ValueError`.

- Rationale: Restrict inputs to the finite interval and observation shapes.
- Derivation: `fm_intervals/history.py`, `docs/INTERVAL-HISTORY.md`
- Allocated to: SDD §4 Interval histories
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-033 — Pointwise history classification

`analyze_history` shall classify cells by the exact intersection of active closed value intervals, distinguish missing coverage from contradiction, report coverage as `none`, `partial` or `full`, and report overall consistency as `contradictory` if any cell contradicts, otherwise `undetermined` if any cell is missing, otherwise `consistent`.

- Rationale: Pointwise compatibility does not establish temporal coupling or external validity.
- Derivation: `fm_intervals/history.py`, `docs/INTERVAL-HISTORY.md`
- Allocated to: SDD §4 Interval histories
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-034 — Horizon restriction

`analyze_history` shall restrict coverage and cell construction to the supplied horizon, clipping overlapping time intervals and leaving uncovered gaps missing.

- Rationale: Constraints outside the horizon do not establish coverage inside it.
- Derivation: `fm_intervals/history.py`, `docs/INTERVAL-HISTORY.md`
- Allocated to: SDD §4 Interval histories
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-035 — Exact history partition

`analyze_history` shall emit ordered point cells at distinct clipped endpoints and open cells between them with exact midpoint witnesses, including histories with 128 observations.

- Rationale: Separate closed endpoints from open interiors without approximate sampling.
- Derivation: `fm_intervals/history.py`, `docs/INTERVAL-HISTORY.md`
- Allocated to: SDD §4 Interval histories
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-036 — History receipt input binding

`verify_history` shall accept JSON round trips of canonical receipts only against the supplied horizon and ordered observations, returning `False` for changed or invalid inputs.

- Rationale: Recomputation binds the result to caller-supplied inputs without source authentication.
- Derivation: `fm_intervals/history.py`, `docs/INTERVAL-HISTORY.md`
- Allocated to: SDD §4 Interval histories
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-037 — History receipt verification

`verify_history` shall reject receipts with altered fields, missing or extra fields, reordered or missing cells, noncanonical rationals, or substituted field types.

- Rationale: Compare the exact canonical receipt shape and values.
- Derivation: `fm_intervals/history.py`, `docs/INTERVAL-HISTORY.md`
- Allocated to: SDD §4 Interval histories
- Verification: T — see verification matrix
- Status: Baselined

### 3.9 Source tree, packaging and documentation integrity

### REQ-MATH-012 — Deterministic source packaging

Source packaging shall check the exact allowlisted file set and hashes, reject symlinks, and produce deterministic ZIPs outside the source root without overwriting output.

- Rationale: Bind source distribution bytes.
- Derivation: `tools/package_source.py`
- Allocated to: SDD §4 Packaging
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-026 — Local selected-tree loading

The research layer, mapper and selected vendor modules shall load from this source tree, with the vendor catalog read only from the local vendor directory.

- Rationale: Results must come from the pinned bytes, never from another installation or the network.
- Derivation: `fm_research/vendor.py`
- Allocated to: SDD §4 Selected vendor
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-027 — Documentation trace check

`tools/check_trace.py` shall report a problem for a requirement with no verification-matrix row, a matrix reference to a missing test, an unclassified test, a design component with no requirement or infrastructure label, a public API name or data field missing from the data dictionary, and a dead relative Markdown link.

- Rationale: Keep requirements, design, tests and documents consistent with the code.
- Derivation: `tools/check_trace.py`, `tests/test_trace.py`
- Allocated to: SDD §4 Documentation tools
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-029 — Release record success condition

`tools/gen_release_docs.py` shall report a release record as passing, and exit 0, only when both unittest suites exit 0 with every test run, parsed and `ok` (no skipped, failed, errored, expected-failure or unexpected-success outcome), the trace check reports no problem, the coverage run exits 0, the Gitleaks scan was run and exits 0, and the source package rebuilds byte-identically from the tree and from its extracted ZIP, listing each other outcome as a deviation in the STR summary and problems table and exiting 1.

- Rationale: A release record must never say "all automated checks passed" over a skipped test, a detected secret or a missing scan (2026-11-09 backfill review finding).
- Derivation: `tools/gen_release_docs.py`, `tests/test_gen_release_docs.py`
- Allocated to: SDD §4 Release record generator
- Verification: T — see verification matrix
- Status: Baselined

## 4. Interface requirements

### REQ-MATH-008 — Research CLI

The research CLI shall emit selected claim records and distinguish certified computed selections, unsuccessful selections and input errors by exit status.

- Rationale: Permit local process integration. Interface: [ICD process interfaces](../icd/icd-stdio.md#research-contract).
- Derivation: `fm_research/__main__.py`
- Allocated to: SDD §4 Research process
- Verification: T — see verification matrix
- Status: Baselined

### REQ-MATH-011 — Mapper file handling

Mapper file handling shall reject artifact root escapes and refuse existing, duplicate or input-replacing output paths.

- Rationale: Bound local file access. Interface: [ICD process interfaces](../icd/icd-stdio.md#mapper-contract).
- Derivation: `fm_mapper/__main__.py`, `fm_mapper/core.py`
- Allocated to: SDD §4 Evidence mapper
- Verification: T — see verification matrix
- Status: Baselined

The Python library interfaces of REQ-MATH-013 to REQ-MATH-037 are defined in the [Python API ICD](../icd/icd-python-api.md).

## 5. Non-functional requirements

### REQ-MATH-028 — Standard library only

The source tree shall run its documented workflow and both test suites with the Python standard library alone, without site packages.

- Rationale: No installation, credentials or network are needed (`PACKAGE.json` lists no dependencies).
- Derivation: `PACKAGE.json`, `.github/workflows/ci.yml`
- Allocated to: SDD §4 Packaging
- Verification: D — both suites and the quickstart run under `python3 -S` (no site packages); see test plan TP-1 and TP-2
- Status: Baselined

Performance and timing: no requirement. The code bounds work by input size limits, not by time; no timing has been measured or promised. Reusability (SWE-147): the packages are plain importable modules under GPL-3.0-only; no separate requirement is stated.

## 6. Not applicable categories

- Safety requirements: N/A, not safety-critical ([SMP §1](../plan/software-management-plan.md#1-software-classification-self-assessed)).
- Control-system, operating-system, board-support-package, partitioning and hardware-interface requirements: N/A, the software has none of these elements. `fm_control` is arithmetic on supplied numbers and commands nothing.
- Communication-protocol requirements: N/A, there is no network or stdio protocol; interfaces are files, arguments and Python calls.

## 7. Qualification provisions

T requirements are verified by the unit tests named in the [verification matrix](../verification/verification-matrix.md), run by the two commands in the [test plan](../verification/test-plan.md). D requirements are verified by the numbered procedures in the test plan. Results are recorded per commit in the [test reports](../verification/reports/README.md).

## 8. Open items

No TBD items. Open defects found while writing this baseline are recorded in the [assurance record](../assurance/assurance-record.md).

## 9. Untested behaviour (requirement gaps)

These behaviours exist in the code but no test checks them. They are not requirements until a test is added. The trace check fails if a gap ID appears as a traced matrix row.

| ID | Behaviour in code | Location | Observed at baseline |
|---|---|---|---|
| GAP-MATH-001 | ProblemSpec kernels `twoi.decompose_tensor`, `twoi.invariant_count_sym_W` and `twoi.distinct` dispatch correctly; no test or fixture uses them | `fm_research/problem.py` `KERNELS` | Run by hand: `{'factors': ['W', {'sym_W': 2}]}` gave `W+S4`; degree 12 gave 1; `W` vs `Wp` gave True |
| GAP-MATH-002 | Symmetric-power degree above 256 is rejected; only the bool type case is tested | `fm_research/twoi.py` `_degree` | Degree 257 gave `ValueError` |
| GAP-MATH-003 | `Block` rejects twist outside [−64, 64] and multiplicity outside [0, 1,000,000] | `fm_research/p1.py` | Twist 65 gave `ValueError` |
| GAP-MATH-004 | F_p modulus must lie in [2, 10^12]; only a composite modulus is tested | `fm_research/rank.py` `_prepare` | 10^12+39 gave `ValueError` |
| GAP-MATH-005 | Mapper limits: 8 MiB bundle, 8 MiB aggregate artifacts, 1,000 items per collection, 32,768 characters per text | `fm_mapper/core.py` | Not exercised |
| GAP-MATH-006 | Public helpers `molien_check`, `invariant_degrees`, `inner`, `character_values`, `distinguish`, `rank_mod_p`, `rank_over_Q_and_mod_p` | `fm_research/twoi.py`, `fm_research/rank.py` | `molien_check(60)` gave True; `inner(W, W)` gave 1 |
| GAP-MATH-007 | Rank over Q(sqrt d) for d ≠ 5 through the Python API | `fm_research/rank.py` | Not exercised |
| GAP-MATH-008 | `fm_research_commit` evidence field value; see defect D1 in the assurance record | `fm_research/problem.py` `run_check` | Records the HEAD of any enclosing Git repository |
| GAP-MATH-009 | `obstruction` raises `ValueError` for a model count other than two or negative noise | `fm_control/scalar.py` | Not exercised |
| GAP-MATH-010 | Mapper standard-output mode and the `--json-out`-only delivery summary | `fm_mapper/__main__.py` | Standard-output mode run by the README quickstart (exit 0) |
| GAP-MATH-011 | Declared floor `python_requires >=3.10`; no run on 3.10 or 3.11 | `PACKAGE.json` | Suites run on 3.12 (CI) and 3.14 (local) only |
| GAP-MATH-012 | Affine accumulation cap `ARITHMETIC_BITS` (8,192 bits) raises `Unsupported` | `fm_certificates/affine.py` `_combination`, `compose_implications` | Not exercised |

## Change history

| Version | Date | Commit | Change | Reviewed in |
|---|---|---|---|---|
| 1.0 | 2026-10-30 | `1a610cf` | Initial requirements table REQ-MATH-001 to 013 | PR #4 |
| 1.1 | 2026-10-30 | `2afa06b` | Linked requirements to the architecture | PR #13 |
| 2.0 | 2026-11-08 | `53a58dd` | Family standard format; added REQ-MATH-014 to 028 for affine certificates, query witnesses, enclosures, local loading, trace check and stdlib-only; added untested-gap list | PR #30 |
| 2.1 | 2026-11-10 | review backfill | Added REQ-MATH-029, the release record success condition | PR #33 |
