# Foundation Math software management plan

| Field | Value |
|---|---|
| Document ID | FMATH-SMP |
| Version | 1.0 |
| Status | Baselined |
| Owner | Akilleez-QA maintainer |
| Date | 2026-11-08 |
| Baseline commit | 53a58dde072b1d3f92836a1365f88f364b880a33 |
| Applies to | foundation-math main at baseline commit |
| Classification | Self-assessed Class E analog; not safety-critical (see §1) |

> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&page_name=all), [NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the [NASA Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) documentation guidance. This is not a NASA compliance determination or certification. The software classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent verification and validation, or hazard analysis is asserted. The document describes the implementation inspected at the baseline commit.

## 1. Software classification (self-assessed)

- Assessed against: NPR 7150.2D Appendix D and NASA-STD-8739.8B §4.2, as an analog. Foundation Math is not NASA software and no NASA authority has reviewed this assessment.
- Analog class: **Class E** (general-purpose research/technology software). Rationale: runs on general-purpose computers; supports no ground test, flight test or operation; a defect affects the productivity of an individual user or a small group; it is not used for decisions about an operational system.
- Not Class F: not Agency business or IT infrastructure.
- Safety-critical determination (SWE-205 analog): **not safety-critical.** Foundation Math meets none of the five criteria in NASA-STD-8739.8B §4.2, and no hazard analysis assigns it a hazard cause, control or mitigation. It commands nothing; `fm_control` computes on supplied numbers only.
- Outputs are bounded observations for research and acceptance checks. They are not engineering approvals. Anyone who relies on them for engineering, safety or regulatory decisions takes on the Class D-analog obligations for that use and must verify against authoritative sources. This applies in particular to `fm_control` scalar certificates and `fm_enclosures` error bounds if their numbers are given physical meaning.
- Documentation baseline: Class E with voluntary adoption of the Class D documentation set; see the [compliance matrix](compliance-matrix.md).
- Re-evaluation triggers: commanding physical hardware; use in a regulated, safety or production decision path; handling personal or secret data beyond local configuration; external deployment as a shared service.
- Assessed by / date / baseline commit: Akilleez-QA maintainer (prepared by an agent documentation lane) / 2026-11-08 / `53a58dde072b1d3f92836a1365f88f364b880a33`.

## 2. Purpose, scope and organization

Foundation Math is a Cstack-family **foundation** repository: exact mathematical kernels and physics research tools with evidence reports. Unlike the other foundations it ships no stdio JSON-RPC bridge; its interfaces are two command-line programs and Python packages ([design](../architecture/architecture.md)). Cstack vendors Foundation Math byte-pinned; docs are fixed here and re-pinned there.

Authority: the repository owner (Akilleez-QA) is the sole approver and merges pull requests. Agent lanes and external contributors propose changes by pull request. `.github/CODEOWNERS` assigns all paths to the owner.

## 3. Life-cycle model and work tracking

Trunk-based development on `main`. Each change is a branch and a pull request; the pull request is the review record (see §6). Work breakdown is the GitHub issue and pull-request list; there are no milestones at the baseline. Source candidates are named in `PACKAGE.json` (`candidate`); no release tag has been created. Promotion follows the [release checklist](../RELEASE-CHECKLIST.md). Cost, staffing, schedule and CMMI planning: N/A (unfunded single-maintainer open source).

## 4. Engineering and test environment

| Item | Version / source | Where defined |
|---|---|---|
| Language runtime | Python ≥ 3.10 declared; CI runs 3.12; local records state their version | `PACKAGE.json` `python_requires`; `.github/workflows/ci.yml` |
| Dependencies | None (standard library only) | `PACKAGE.json` `dependencies: []` |
| Test runner | `unittest` (standard library) | `.github/workflows/ci.yml` |
| Static analysis | No linter in CI. The release-record generator runs ruff (E9, F rules) when a binary is supplied | `tools/gen_release_docs.py` |
| Secret scanning | Gitleaks (`gitleaks/gitleaks-action@v3`, default rules) | `.github/workflows/ci.yml`, `.gitleaks.toml` |
| CI | GitHub Actions on push and pull request to `main`: jobs `tests`, `gitleaks`, `manifest` on `ubuntu-latest` | `.github/workflows/ci.yml` |
| Dependency updates | Dependabot for GitHub Actions | `.github/dependabot.yml` |

## 5. Verification and validation approach

Verification: pull-request review, automated unit tests (normal and `-O`), the documentation trace check, the source-package check, and secret scanning. Records: [verification matrix](../verification/verification-matrix.md), [test plan](../verification/test-plan.md), [test reports](../verification/reports/README.md), [assurance record](../assurance/assurance-record.md).

Validation (does it do the intended job): the quickstart and tutorial are run end to end and recorded in the test plan; mathematical contracts carry written proofs in the contract documents (for example [numerical enclosures](../NUMERICAL-ENCLOSURES.md)). Independent mathematical review is a separate step that tests do not replace.

Acceptance criteria for a source candidate (SWE-034): both unit suites pass with zero failures and errors; the trace check reports zero problems; the source package builds, rebuilds identically and rebuilds identically from its own extraction; Gitleaks reports no leaks; the STR and VDD are generated at the candidate commit. Publication additionally needs owner authorization per the release checklist.

## 6. Software assurance

There is one maintainer, so there is **no organizational independence**. Agent reviewers and CI gates provide separation of method only; agent review is not independent review.

| Gate | Command | Fails on | Record |
|---|---|---|---|
| Unit tests | `python -B -m unittest discover -s tests -t .` (CI); locally `python3 -S -B -m unittest discover -s tests -t .` | Any failed or erroring test, including the trace check in `tests/test_trace.py` | CI log; STR |
| Optimized unit tests | `python -B -O -m unittest discover -s tests -t .` (CI) | Same, with assertions stripped | CI log; STR |
| Trace and link check | `python3 -S -B -m tools.check_trace` (also inside both suites) | Untraced requirement, missing test, unclassified test, unallocated component, data-dictionary omission, dead relative link | STR metrics |
| Source package | CI `manifest` job: `git archive HEAD` into a temp dir, then `python -B tools/package_source.py OUT.zip` | Manifest row mismatch, unlisted file, symlink | CI log; VDD |
| Secret scan | CI `gitleaks` job | Any finding under the default rules | CI log; STR |
| Static analysis | `ruff check --select E9,F` via `tools/gen_release_docs.py --ruff PATH` | Recorded only; not a gate | STR; SAR |
| Peer review | Pull request with template | Owner does not merge | PR; SAR summary |

## 7. Security, privacy and secure coding

Attack surface: two CLIs that read caller-named JSON files and write caller-named outputs; Python APIs for trusted in-process callers; one subprocess (`git rev-parse HEAD`, fixed arguments, 5-second timeout). No network, no credentials, no plugin loading, no `eval`, no external solver.

Secure-coding practices in the code: closed JSON schemas with duplicate-key rejection and no floats or nonfinite numbers; fixed kernel registry; explicit size and bit limits; artifact paths contained under a root with symlink escape rejected; output files opened exclusively (`x` mode) and never allowed to replace inputs; recomputation rather than trusting stored results. Secrets: Gitleaks in CI; `.gitleaks.toml` extends the default rules. Dependencies: none at runtime; GitHub Actions versions are updated by Dependabot and reviewed by pull request. Privacy: fixtures are synthetic; no personal data is processed. Reporting: [SECURITY.md](../../SECURITY.md).

## 8. Open-source, reused and vendored components

| Component | License | Pin method | Update policy |
|---|---|---|---|
| `vendor/foundation-math-v014/` (character ring, split bundle) | GPL-3.0-only (first-party, see `NOTICE.md`) | Manifest rows with the original `source_sha256` (four `byte_preserved: true`, five changed only by comment removal in PR #5); catalog SHA-256 in `character_ring/contract.py` | Not updated; a change needs fresh receipts and review |
| Python standard library | PSF | Python version recorded in every receipt and STR | Follow supported Python releases |
| GitHub Actions `actions/checkout@v7`, `actions/setup-python@v7`, `gitleaks/gitleaks-action@v3` | Their own licenses | Major-version tags in the workflow | Dependabot PRs |

Reuse by others: GPL-3.0-only; commercial licenses are offered in the README. Acquire versus develop (SWE-033): all code is developed in-house; no COTS product is used.

## 9. Problem reporting and severity

| Severity | Meaning | Response |
|---|---|---|
| S1 | Wrong result presented as valid (for example a false `certified` or `bounded`), data loss, or security exposure | Fix or withdraw the candidate before the next merge |
| S2 | Feature unusable, no workaround | Next candidate |
| S3 | Feature degraded, workaround exists | Scheduled |
| S4 | Cosmetic or documentation | As convenient |

Problems and change requests use the GitHub issue forms in `.github/ISSUE_TEMPLATE/`; severity is a reporter field and an `S1`–`S4` label applied at triage. Closure needs a linked pull request that names the verifying test.

## 10. Configuration management

Baselines are commits; source candidates are named in `PACKAGE.json`; every shipped byte is pinned in `SOURCE-MANIFEST.json`. See the [configuration management plan](../configuration/configuration-management.md).

## 11. Operations, maintenance and retirement

Changes are analysed in the issue or pull request, implemented on a branch, reviewed and merged by the owner, and recorded in `CHANGELOG.md`. Supported versions: only the latest `main` commit ([SECURITY.md](../../SECURITY.md)); no tag exists. Delivery: the public Git repository and, for a promoted candidate, the explicit-allowlist source ZIP. Users find version data in `PACKAGE.json`, the [version descriptions](../releases/README.md) and receipts (`kernel_source_sha256`, `python_version`). Migration notes go in the CHANGELOG. Backup operational software: N/A; a prior commit is the fallback. Retirement: archive the GitHub repository after a final commit that states the status in the README.

## 12. Risk register

Reviewed at each source candidate. Likelihood (L) and consequence (C) on 1–5.

| ID | Risk | L | C | Mitigation | Status | Issue |
|---|---|---|---|---|---|---|
| R-1 | A user reads `certified`, `bounded` or `supported` as proof of a research claim or as engineering approval | 3 | 4 | Status meanings in README, contracts and [limitations](../guides/explanation/limitations.md); mapper drafts always `draft_not_scientifically_accepted` | Open | — |
| R-2 | Receipt provenance misleads: `fm_research_commit` names an enclosing repository's HEAD (defect D1) | 2 | 3 | Documented in the data dictionary and assurance record; `kernel_source_sha256` is the binding identity | Open | — |
| R-3 | Documentation drifts from code as open PRs (#22, #23, #25–#28) add modules | 4 | 2 | `tools/check_trace.py` fails on unlisted public names and untraced tests; PR template asks for SRS and matrix updates | Open | — |
| R-4 | Declared Python 3.10 floor is untested (only 3.12 and 3.14 run) | 3 | 2 | Gap GAP-MATH-011 recorded; add a CI matrix entry when needed | Open | — |
| R-5 | Single maintainer: no independent review | 5 | 2 | Stated plainly; agent review labelled not independent; CI gates | Accepted | — |

## 13. Measurement

Each test report carries a generated metrics block (tests run and passed in both modes, requirement and gap counts, issue and PR counts from `gh`, ruff findings, comment and docstring counts, Gitleaks summary, in-process line coverage from the standard-library `trace` module, line counts). Produced by `python3 -S -B -m tools.gen_release_docs --pr N`. Numbers are never typed by hand.

## 14. Training

Not applicable. SWEHB 5.15 anticipates one training plan per NASA Center, NPR SWE-017 applies only to Classes A–C, and the repo has no staff. Contributor onboarding is CONTRIBUTING plus the tutorials.

## 15. Documentation list

The [documentation index](../README.md) lists every control document and guide with its path.

## Change history

| Version | Date | Commit | Change | Reviewed in |
|---|---|---|---|---|
| 1.0 | 2026-11-08 | `53a58dd` | Initial baseline | PR #30 |
