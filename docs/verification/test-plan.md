# Foundation Math software test plan and procedures

| Field | Value |
|---|---|
| Document ID | FMATH-STP |
| Version | 1.0 |
| Status | Baselined |
| Owner | Akilleez-QA maintainer |
| Date | 2026-11-08 |
| Baseline commit | 53a58dde072b1d3f92836a1365f88f364b880a33 |
| Applies to | foundation-math main at baseline commit, plus the documentation tooling added in PR #30 |
| Classification | Self-assessed Class E analog; not safety-critical (see [SMP §1](../plan/software-management-plan.md#1-software-classification-self-assessed)) |

> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&page_name=all), [NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the [NASA Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) documentation guidance. This is not a NASA compliance determination or certification. The software classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent verification and validation, or hazard analysis is asserted. The document describes the implementation inspected at the baseline commit.

## 1. Scope and approach

All automated tests are synthetic `unittest` contract tests in `tests/`. They run twice: normally and with `-O` (assertions stripped), because the code must not depend on `assert`. The executable tests are the test procedures for every T requirement. Procedures TP-1 to TP-5 below cover the demonstrations and release checks that are not unit tests. Formal witnessing: N/A; the owner's merge is the sign-off.

## 2. Test levels

| Level | What it covers | Location | Command |
|---|---|---|---|
| Unit | Kernels, certificates, enclosures, mapper functions, packager, trace check | `tests/test_*.py` | `python3 -S -B -m unittest discover -s tests -t .` |
| Integration | ProblemSpec → kernels → gate; mapper bundle → artifacts → map → paper; vendor producer and verifier pairs | `tests/test_problem.py`, `tests/test_mapper.py`, `tests/test_kernels.py` | same |
| System / end-to-end | Both CLIs as subprocesses with exit codes and output files | `test_standalone_cli`, `test_cli_*` in the files above; TP-2 | same |
| Regression | Full suite, normal and optimized, on every push and pull request | CI `tests` job | `python -B -m unittest discover -s tests -t .` and `python -B -O -m unittest discover -s tests -t .` |
| Documentation consistency | Requirement ↔ test ↔ design ↔ dictionary trace and links | `tests/test_trace.py` | inside both suites; standalone `python3 -S -B -m tools.check_trace` |
| Release | Source package build and reproducibility; secret scan | CI `manifest` and `gitleaks` jobs; TP-3, TP-4 | see procedures |

No performance or load tests exist; no timing requirement is stated.

## 3. Test environment

| Item | Values | Source |
|---|---|---|
| OS | `ubuntu-latest` (GitHub-hosted) in CI; any OS locally, recorded in the STR | `.github/workflows/ci.yml` |
| Runtime | Python 3.12 in CI (`actions/setup-python@v7`); declared floor 3.10 is not tested (GAP-MATH-011) | `.github/workflows/ci.yml`, `PACKAGE.json` |
| Flags | Local commands add `-S` (no site packages) to prove the stdlib-only requirement; CI runs without `-S` | AGENTS.md, CI |
| External services | None. Tests use temporary directories and subprocesses of the same interpreter | — |

## 4. Pass criteria and acceptance

- Both suites: zero failures, zero errors, zero skips expected.
- Trace check: zero problems.
- Source package: CI `manifest` job passes; TP-3 rebuilds are byte-identical.
- Secret scan: no leaks.
- No known failure is accepted at the baseline.

## 5. Coverage

Tool: the standard-library `trace` module, so no dependency is added. Command (run by the STR generator):

```sh
python3 -S -B -m trace --count --summary -C "$(mktemp -d)" --ignore-dir="$(python3 -c 'import sys; print(sys.prefix)')" --module unittest discover -s tests -t .
```

It counts lines executed inside the test process only; code run in CLI subprocesses is not counted. The measured value per commit is in the STR. No coverage threshold is set. MC/DC: N/A (not safety-critical, SWE-219).

## 6. Test data and fixtures

All test data is synthetic: `examples/research-regression.problem.json`, `examples/evidence-mapper/`, `tests/fixtures/false-claim.problem.json`, and values constructed inside the tests. `tests/mapper_helpers.py` builds mapper bundles. No external or private data is used.

## 7. Procedures

Automated tests: the code is the procedure. Run each file alone with `python3 -S -B -m unittest tests.test_<name>`; the full suites with the commands in §2.

### TP-1 — Both unit suites without site packages

- Purpose / requirements: all T requirements; REQ-MATH-028 (standard library only).
- Preconditions: clean checkout; Python ≥ 3.10.
- Steps: from the repository root run
  ```sh
  python3 -S -B -m unittest discover -s tests -t .
  python3 -S -B -O -m unittest discover -s tests -t .
  ```
- Expected result and pass/fail criteria: each ends with `OK`; exit status 0.
- Last run: 2026-11-08, PR #30 head; results in the [test report](reports/README.md).

### TP-2 — Quickstart commands

- Purpose / requirements: REQ-MATH-008, REQ-MATH-028; validation that the README quickstart works.
- Preconditions: as TP-1.
- Steps:
  ```sh
  python3 -S -B -m fm_research check examples/research-regression.problem.json
  python3 -S -B -m fm_research check examples/research-regression.problem.json --claim rank-q5
  python3 -S -B -m fm_mapper examples/evidence-mapper/legacy-conditional.json
  ```
- Expected result: first command prints four records (`sym2`, `sym3`, `rank-q5` certified; `research-argument` argued), exit 0; second prints only `rank-q5` certified, exit 0; third prints map JSON with `summary.dispositions` `{"conditional": 2}`, exit 0.
- Last run: 2026-11-08 at baseline `53a58dd`, Python 3.14.9, Linux: all three exit 0 with the expected records.

### TP-3 — Source package build and reproducibility

- Purpose / requirements: REQ-MATH-012 on the real manifest; release integrity.
- Preconditions: every change committed; `SOURCE-MANIFEST.json` refreshed with `python3 -S -B -m tools.refresh_manifest`.
- Steps: the commands in the [source packaging guide](../guides/how-to/source-package.md) (export, build twice, compare, extract, rebuild from the extraction, compare, run the suites in the extraction).
- Expected result: all builds print the same `sha256`; both `cmp` commands are silent; the suites pass in the extraction.
- Last run: 2026-11-08 at baseline `53a58dd`: 68 files, 347,074 bytes, SHA-256 `fed29100e6f31af136937e4b75759bf8917523ab1c24de3ecbfee853e1c50d1e`, both rebuilds identical, suite OK in the extraction. The VDD records the value at its own commit.

### TP-4 — Secret scan

- Purpose: no credentials in history.
- Steps: CI `gitleaks` job; locally `gitleaks git --no-banner --redact -c .gitleaks.toml --log-opts=HEAD .`
- Expected result: `no leaks found`.
- Last run: recorded in the STR.

### TP-5 — Release records

- Purpose: generate the STR and VDD from a recorded run.
- Preconditions: clean working tree at the commit to record.
- Steps: `python3 -S -B -m tools.gen_release_docs --pr <PR number> --ruff <ruff binary> --gitleaks <gitleaks binary>`; commit the two files; then `python3 -S -B -m tools.refresh_manifest` and commit the manifest.
- Expected result: exit 0; the STR states zero failures and zero trace problems.
- Last run: 2026-11-08, PR #30.

## 8. Test risks and limitations

- Tests are written by the authors of the code; they are not independent or blind evaluation.
- One CI platform and Python version; the 3.10 floor is untested.
- Finite synthetic examples are regression evidence, not proofs over all inputs; the proofs are in the contract documents.
- Twelve behaviours have no test; see [SRS §9](../requirements/requirements.md#9-untested-behaviour-requirement-gaps).

## 9. Traceability

See the [verification matrix](verification-matrix.md).

## Change history

| Version | Date | Commit | Change | Reviewed in |
|---|---|---|---|---|
| 1.0 | 2026-11-08 | `53a58dd` | Initial baseline | PR #30 |
