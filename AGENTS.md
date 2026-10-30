# Working in Foundation Math

Read [README.md](README.md), [CONTRIBUTING.md](CONTRIBUTING.md), and the relevant
contract before editing. Use [SUPPORT.md](SUPPORT.md) for help and
[SECURITY.md](SECURITY.md) for sensitive reports.

## Scope and contracts

This is a Python 3.10+ source-tree project using the standard library. `PACKAGE.json`
is release metadata, not an npm manifest; preserve its name. No package installation
is needed for the documented workflow.

- `fm_research/` checks structured claims with exact kernels and dependency statuses.
- `fm_mapper/` maps supplied evidence judgments and renders qualified draft reports.
- `fm_control/` provides exact, model-conditional scalar one-step certificates.
- `vendor/foundation-math-v014/` contains only the selected historical source subset.
- `tests/` uses synthetic fixtures and Python's `unittest` runner.

Preserve the distinction between finite computation, admitted assumptions,
supplied judgments, and scientific acceptance. Read
[source binding](docs/SOURCE-BINDING.md), [mapper contracts](docs/EVIDENCE-PAPER.md),
and [scalar-control scope](docs/SCALAR-CONTROL.md) for changes in those areas.
Do not describe certificates as real-world safety approval or general proofs.
Keep work bounded; historical research replays require their own scope and
resource authority as specified in CONTRIBUTING.md.

## Verification

Run from the repository root after edits:

```sh
python3 -S -B -m unittest discover -s tests -t .
python3 -S -B -O -m unittest discover -s tests -t .
```

CI uses Python 3.12 and runs normal and optimized tests, a Gitleaks job, and a
conditional manifest-generation step. See [the workflow](.github/workflows/ci.yml).
Record the candidate commit, commands, resource limits, exit statuses, failures,
and unrun scope. Missing, stale, or interrupted checks do not pass. Author tests
are distinct from independent review and mathematical acceptance.

## Source and release boundaries

[SOURCE-MANIFEST.json](SOURCE-MANIFEST.json) pins an explicit file set and hashes.
[The packager](tools/package_source.py) rejects extra files and changed bytes;
a Git checkout includes files outside that allowlist. These community files are
not added to the source-package manifest. Do not claim checkout packaging or a
release archive is validated by unit tests alone. Follow
[the release checklist](docs/RELEASE-CHECKLIST.md) for exact-artifact verification.

Preserve GPL-3.0-only terms, provenance, and third-party notices; see
[NOTICE.md](NOTICE.md) and [PROVENANCE.md](PROVENANCE.md). Keep secrets and private
research data out of commits. Put rationale in documentation; add no code comments
or docstrings. Do not weaken checks or change expected results to obtain a pass.
