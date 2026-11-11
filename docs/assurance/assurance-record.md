# Foundation Math software assurance record

| Field | Value |
|---|---|
| Document ID | FMATH-SAR |
| Version | 1.0 |
| Status | Baselined |
| Owner | Akilleez-QA maintainer |
| Date | 2026-11-08 |
| Baseline commit | 53a58dde072b1d3f92836a1365f88f364b880a33 |
| Applies to | foundation-math main at baseline commit |
| Classification | Self-assessed Class E analog; not safety-critical (see [SMP §1](../plan/software-management-plan.md#1-software-classification-self-assessed)) |

> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&page_name=all), [NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the [NASA Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) documentation guidance. This is not a NASA compliance determination or certification. The software classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent verification and validation, or hazard analysis is asserted. The document describes the implementation inspected at the baseline commit.

Rolling record of requirements, design, test, code-quality and configuration analyses (SWEHB 5.21, 5.22, 5.23, 5.25, 5.26) and the peer-review summary (5.03). Newest entry first.

## Entry 2026-11-08 — baseline 53a58dd (PR #30)

- Analyzed by: agent documentation lane N3 for the Akilleez-QA maintainer. Agent analysis is not independent.
- Inputs: all source, tests, CI workflow and documents at `53a58dde072b1d3f92836a1365f88f364b880a33`; `gh` issue and PR lists; the family documentation standard.
- Environment: Linux, Python 3.14.9 (local); CI definition Python 3.12.

### Requirements analysis

Techniques: line-by-line comparison of each requirement with the code; testability review (every requirement must name a test or procedure); orphan check by `tools/check_trace.py`; search for public behaviour with no requirement.

Findings:

- The previous SRS (13 requirements) had no requirement for the three packages merged on 2026-11-06 (`fm_certificates` #21, `fm_identifiability` #24, `fm_enclosures` #29), for local-tree loading, or for the stdlib-only constraint. Added REQ-MATH-014 to REQ-MATH-028.
- Twelve implemented behaviours have no test. They are recorded as GAP-MATH-001 to GAP-MATH-012 in [SRS §9](../requirements/requirements.md#9-untested-behaviour-requirement-gaps), not as requirements.
- Trace check after the update: 28 requirements, 28 traced, 0 TBD, 101 test methods all traced (95 existing plus 6 in `tests/test_trace.py`), 0 problems. Command: `python3 -S -B -m tools.check_trace`.

### Design analysis

Technique: comparison of the old architecture table with `git ls-files` and the import graph.

Findings: the old design omitted `fm_certificates`, `fm_identifiability` and `fm_enclosures`, and described the selected vendor subset as wholly byte-preserved. The manifest shows only four of nine vendor files are `byte_preserved: true`; five lost code comments in PR #5. Both corrected in the [SDD](../architecture/architecture.md). Every component now lists its requirements or is marked infrastructure.

### Testing analysis

Techniques: matrix rows against the test tree (AST scan); reading each test's assertions for the claimed observation; in-process line coverage with the standard-library `trace` module (full value per commit in the STR).

Findings:

- All 95 baseline tests pass in both modes (`python3 -S -B -m unittest discover -s tests -t .` and the same with `-O`; 0.66 s and 0.65 s test time on the machine above).
- Three of the seven ProblemSpec kernels are never dispatched by any test (GAP-MATH-001); the tutorial exercises one by hand.
- Several limits are untested at their upper bound (GAP-MATH-002 to 005, 012).
- Lowest in-process line coverage at baseline: `fm_research/twoi.py` 69.6%, `vendor/.../split_bundle/contract.py` 75.0%, `fm_research/field.py` 77.1% (stdlib `trace`, Python 3.14.9; CLI subprocess lines not counted).

### Source code quality

| Tool | Command | Findings (new / total) |
|---|---|---|
| ruff 0.17.0, rules E9 and F | `ruff check --no-cache --isolated --select E9,F --target-version py310 .` | 0 / 10 at baseline: all F401 unused imports (`fm_control/__init__.py` ×4, `fm_research/twoi.py` `vendor` (imported for its catalog check side effect), `tests/test_affine_certificates.py`, `tests/test_mapper.py`, vendor `producer.py` ×2, vendor `split_bundle/verifier.py`) |
| Comment scan (tokenize) | in `tools/gen_release_docs.py` | 0 `#` comments in 39 tracked Python files |
| Docstring scan (ast) | in `tools/gen_release_docs.py` | 92 docstrings in 28 files at baseline; AGENTS.md forbids adding new ones. New tools in PR #30 add none |
| Gitleaks 8.30.1 | `gitleaks git --no-banner --redact -c .gitleaks.toml .` | no leaks found |

### Configuration audit

- `python3 -S -B -m tools.refresh_manifest --check` at baseline: no differences (every manifest row matches the committed bytes).
- Source ZIP from `git archive 53a58dd`: 68 files, 347,074 bytes, SHA-256 `fed29100e6f31af136937e4b75759bf8917523ab1c24de3ecbfee853e1c50d1e`; rebuild and rebuild-from-extraction byte-identical; suite OK inside the extraction.
- Docs versus code: stale claims found and fixed in PR #30 are listed in the PR body docs-audit table. The main ones: the SCMP named candidate `scalar-control-v1-20261027` while `PACKAGE.json` says `numerical-enclosures-v1-20261105`; the process ICD said the example shows argument shapes for all kernels (it shows two of seven); PROVENANCE's byte-preservation summary predates PR #5 (a dated correction note was added, the original text kept).
- No tag exists, so no tag-versus-docs audit applies.

### Peer review summary

`gh pr list --state merged` at 2026-11-08: 23 merged pull requests; 5 have a GitHub review and 18 have a review or a comment. Open pull requests #22, #23, #25, #26, #27, #28 add further certificate modules; each will need SRS, matrix and dictionary rows (the trace check enforces the dictionary and test parts).

### Findings

| ID | Severity | Finding | Location | Issue | Status |
|---|---|---|---|---|---|
| D1 | S3 | `run_check` fills `fm_research_commit` from `git rev-parse HEAD` in the repository directory. Inside any enclosing Git repository (for example an extracted source ZIP placed in another project) it records that repository's HEAD; in a dirty checkout it records HEAD without noting changes. Reproduced: an extraction inside a fresh repository recorded that repository's commit | `fm_research/problem.py` `run_check` | — | Open (documented; not fixed in a docs PR) |
| D2 | S4 | 92 docstrings remain in 28 files although AGENTS.md says to add none (pre-existing) | see Source code quality | — | Open |
| D3 | S4 | 10 ruff F401 unused imports (one is an intended side-effect import) | see Source code quality | — | Open |
| D4 | S4 | The research CLI replaces an existing `--evidence-out` file while the mapper refuses existing outputs; inconsistent but documented | `fm_research/__main__.py` | — | Open (documented) |
| D5 | S4 | Stale docs (SCMP candidate name, ICD example claim, PROVENANCE byte-preservation summary, missing requirements for three packages) | docs | — | Closed in PR #30 |

### Overall assessment

The code matches its contracts as far as inspected. All requirements trace to passing tests; twelve behaviours remain untested and one provenance-field defect (D1) is open. Assurance is author-side only; no independent review has been performed.

## Change history

| Version | Date | Commit | Change | Reviewed in |
|---|---|---|---|---|
| 1.0 | 2026-11-08 | `53a58dd` | First entry | PR #30 |
