# Candidate verification scope

2026-10-26, Python 3.12.14, Linux. The selected source-tree candidate passed
**48 tests normally and 48 with Python optimization enabled**. CLI subprocesses
inherit optimization mode and disable site-package loading. Import-origin checks
confirm the research layer, mapper, and selected vendor modules load from this
source tree.

| Coverage | Test methods |
|---|---:|
| New small synthetic exact kernels and selected producer/verifier pairs | 7 |
| Derived standalone ProblemSpec/dependency/integrity/CLI checks | 5 |
| Generic synthetic mapper contract and title-correction regressions | 33 |
| New synthetic explicit-manifest packaging checks | 3 |

These are authored software contract checks, not independent mathematical
acceptance or blind evaluation. A previously disclosed mapper title defect is a
regression case, not fresh unseen evidence. A preliminary 45-test run also passed;
the three packaging tests were subsequently added, followed by both 48-test runs.
No failed test or resource interruption occurred in those runs.

## Execution boundaries

Each test process was capped at **20 CPU seconds** and **1 GiB address space**, or
its lower inherited limit. An outer timeout allowed **45 seconds wall time** and
**2 seconds to termination**. Children inherited the process limits. Limits were
not increased. Durations in test-runner logs describe test intervals only; no
performance benchmark, productivity improvement, or total-cost claim is made.

Normal command: `python3 -S -B -m unittest discover -v -s tests -t .`

Optimized command: `python3 -S -B -O -m unittest discover -v -s tests -t .`

The source package includes no historical workload replay, high-degree research
experiment, external solver execution, install, provider call or paid operation.
Fresh-extraction checks and full archive byte comparison are separate exact-artifact
release evidence; their outcome must be read from the corresponding release
receipt rather than inferred from this document.

## Boundaries still open

The owner selected GPL-3.0-only for the covered first-party files. The standalone
baseline passed selected-file release-boundary review; this licensed revision is
a license/documentation/metadata-only delta and requires its own bounded final
review. Fresh licensed-candidate normal/optimized runs, archive rebuilds and
extraction checks are recorded in its exact-artifact release receipt. Neither
local tests nor license selection attest public publication. Source-tree tests do
not establish a wheel/pip installation, every supported Python/OS combination,
the full historical v0.14 suite, formal proof, real geometry, physical validation,
truth of caller judgments, general solver capability or public release.
