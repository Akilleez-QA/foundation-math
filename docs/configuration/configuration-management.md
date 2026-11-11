# Foundation Math software configuration management plan

| Field | Value |
|---|---|
| Document ID | FMATH-SCMP |
| Version | 2.0 |
| Status | Baselined |
| Owner | Akilleez-QA maintainer |
| Date | 2026-11-08 |
| Baseline commit | 53a58dde072b1d3f92836a1365f88f364b880a33 |
| Applies to | foundation-math main at baseline commit, plus the documentation tooling added in PR #30 |
| Classification | Self-assessed Class E analog; not safety-critical (see [SMP §1](../plan/software-management-plan.md#1-software-classification-self-assessed)) |

> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&page_name=all), [NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the [NASA Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) documentation guidance. This is not a NASA compliance determination or certification. The software classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent verification and validation, or hazard analysis is asserted. The document describes the implementation inspected at the baseline commit.

## 1. Organization and responsibilities

The repository owner (Akilleez-QA) approves and merges every change and alone may authorize publication of a source candidate. Contributors and agent lanes prepare branches and pull requests. CI runs the checks in [SMP §6](../plan/software-management-plan.md#6-software-assurance).

## 2. Configuration identification

| Item | Identity | Control point |
|---|---|---|
| Source tree | Git commit (40-hex). Branch names are mutable and are not baselines | Pull request merge into `main` |
| Source candidate | `PACKAGE.json` `candidate` (at baseline `numerical-enclosures-v1-20261105`). Not a SemVer release; no tag exists | Owner edit by pull request |
| Distribution file set | `SOURCE-MANIFEST.json`: every shipped path with byte size and SHA-256; retained provenance fields (`byte_preserved`, `source_sha256`, `source_git_blob_sha1`) | `tools/refresh_manifest.py`; checked by `tools/package_source.py` and CI `manifest` job |
| Mathematical source identity | `fm-research-source/2` hash over the 17 files in `_SOURCE_FILES` (`fm_research/problem.py`) | Recomputed in every receipt (`kernel_source_sha256`) |
| Character catalog | SHA-256 `84ceb37bc32d10c4908e5b5f1f2f5994082074f2c2a9f36c846347750c79fa74` in `vendor/foundation-math-v014/character_ring/contract.py` and in the manifest | Rechecked on every catalog read |
| Selected vendor subset | Nine files under `vendor/foundation-math-v014/`. Four are `byte_preserved: true`; five had code comments removed in PR #5 and carry `byte_preserved: false` with their original `source_sha256` | Manifest rows; `refresh_manifest` refuses to change a `byte_preserved: true` row |
| CI workflow | `.github/workflows/ci.yml` | Pull request; Dependabot for action versions |
| Documentation | `docs/` control documents, each with a baseline commit and change history | Pull request; trace check |
| Generated records | `docs/verification/reports/STR-*.md`, `docs/releases/VDD-*.md` | `tools/gen_release_docs.py` (§6) |

Excluded from the distribution by `tools/package_source.py` and therefore not in the manifest: `.github/`, `AGENTS.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`. The manifest does not list itself; its digest is recorded externally (in the VDD).

### 2.1 Byte identities

The manifest is the generated digest table for every shipped file. Inspect it and the candidate metadata without changing them:

```sh
git rev-parse HEAD
git status --short
python3 -S -B -m json.tool PACKAGE.json
python3 -S -B -m json.tool SOURCE-MANIFEST.json
python3 -S -B -m tools.refresh_manifest --check
```

The last command prints nothing and exits 0 when every manifest row matches the committed bytes. At the baseline commit it printed nothing (exit 0). Each VDD records the manifest SHA-256 and the source ZIP SHA-256 for its commit.

## 3. Change control

`main` has no branch protection at the baseline (`gh api repos/Akilleez-QA/foundation-math/branches/main/protection` returns "Branch not protected"). Change control is procedural: every change goes through a pull request that the owner merges after CI. Rules:

- A change to shipped bytes also refreshes `SOURCE-MANIFEST.json` in the same pull request (`python3 -S -B -m tools.refresh_manifest`), or CI `manifest` fails.
- A change to any file in `_SOURCE_FILES` or the catalog changes the mathematical source identity. Earlier receipts become stale and must be regenerated, never copied.
- A change to behaviour updates the SRS, verification matrix and data dictionary in the same pull request; `tests/test_trace.py` fails otherwise for public names and tests.
- Files marked `byte_preserved: true` are not edited; a deliberate change must set the flag to `false` by hand with a recorded reason, as PR #5 did.
- Historical records (`docs/VERIFICATION.md`, provenance sections, earlier change-history rows) stay as written.

## 4. Status accounting

- `git log` and merged pull requests: what changed and who approved it.
- `CHANGELOG.md` `[Unreleased]`: user-visible changes since the last candidate.
- `PACKAGE.json`: current candidate name.
- [Version descriptions](../releases/README.md) and [test reports](../verification/reports/README.md): what a recorded commit contains and how it tested.

## 5. Configuration audits

At each recorded candidate: the docs baseline commit is named; `refresh_manifest --check` is clean; the source ZIP is rebuilt from `git archive` and from its own extraction with identical bytes; the VDD's digests match. The result is an entry in the [assurance record](../assurance/assurance-record.md).

## 6. Generated outputs

| Output | Generator | Inputs | Committed | Rule |
|---|---|---|---|---|
| `SOURCE-MANIFEST.json` rows | `tools/refresh_manifest.py` | `git ls-files` minus the excluded set; file bytes | Yes | Rerun after edits; never hand-edit digests |
| `docs/verification/reports/STR-<candidate>.md` | `tools/gen_release_docs.py` | Both unit suites, trace check, `trace` coverage, ruff, Gitleaks, `gh` issue/PR lists, `git` | Yes | Generated at a clean commit; committed in the next commit; never hand-edited |
| `docs/releases/VDD-<candidate>.md` | `tools/gen_release_docs.py` | `PACKAGE.json`, `git`, CHANGELOG, source ZIP build, manifest | Yes | Same |
| Source ZIP | `tools/package_source.py` | Manifest file set | No (built on demand) | Output path must be fresh and outside the tree |

No source code is generated.

## 7. Release management and delivery

There is no automated tag or publication process. A promotion follows the [release checklist](../RELEASE-CHECKLIST.md): select the candidate, run TP-1 to TP-5 of the [test plan](../verification/test-plan.md), generate the STR and VDD, obtain review, and publish only after the owner authorizes it. The deliverable is the public Git commit and, when requested, the explicit-allowlist source ZIP built with the [source packaging guide](../guides/how-to/source-package.md). It is not a wheel or a tested pip installation. These documents assign no version or tag.

## 8. Plan maintenance

Update this plan in the same pull request as any change to CI, the packager, the manifest format or the release process.

## Change history

| Version | Date | Commit | Change | Reviewed in |
|---|---|---|---|---|
| 1.0 | 2026-10-30 | `1a610cf` | Initial configuration document | PR #4 |
| 1.1 | 2026-10-30 | `f49c84f` | Clarified baselines, pins and release authority | PR #15 |
| 2.0 | 2026-11-08 | `53a58dd` | Family standard format; corrected the candidate name (was `scalar-control-v1-20261027`); added manifest refresh tool, generated records, change-control rules and branch-protection status | PR #30 |
