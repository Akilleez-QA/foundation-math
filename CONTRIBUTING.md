# Contributing

Foundation Math first-party files are licensed under GPL-3.0-only; see LICENSE
and NOTICE.md. Contributions intended for inclusion must be provided under those
terms by someone authorized to grant the relevant rights. Preserve third-party
notices and identify any material with different terms before proposing it.

## Development setup

You need Python 3.10 or later and Git. There are no dependencies and nothing to
install. Clone the repository and work from its root. Keep fixtures synthetic and
bounded. Distinguish finite computation, formal checking, supplied semantic
judgment, and intended-model or empirical validation.

## Local checks (the same commands CI runs)

```sh
python3 -S -B -m unittest discover -s tests -t .
python3 -S -B -O -m unittest discover -s tests -t .
```

CI runs these without `-S` on Python 3.12, plus a Gitleaks secret scan and a
source-package check (`.github/workflows/ci.yml`). Both suites include the
documentation trace check; run it alone with `python3 -S -B -m tools.check_trace`.
If you add or change a shipped file, `git add` it (the tool reads `git ls-files`),
then refresh and commit the manifest:

```sh
python3 -S -B -m tools.refresh_manifest
```

Record the exact candidate bytes, command, limits, exit status, failed checks,
and unrun scope. Missing, stale, or interrupted results do not pass. Never replay
a historical workload merely to inflate a count; new research execution needs its
own scope and resource authority.

## Changing behaviour

Update in the same pull request: the requirement in
`docs/requirements/requirements.md`, its row in
`docs/verification/verification-matrix.md`, the data dictionary, and the ICD if
an interface changed. The trace check fails when a test or public name is not
documented. Add no code comments or docstrings; put rationale in documents and
commit messages.

## Pull requests and review

Open a pull request against `main` using the template. The template is the peer
review record: name the reviewers (human or agent; agent review is not
independent), the findings and the outcome. Documentation pull requests paste
the family documentation checklist (the "Documentation checklist" section of the
template). The owner merges.

One reviewer should inspect the exact candidate source and release boundaries.
That review is different from author tests and different again from mathematical
acceptance. No private account, deployment credential or paid service should be
required for the source-tree check workflow.
