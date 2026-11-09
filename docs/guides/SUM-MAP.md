# Foundation Math user manual map

| Field | Value |
|---|---|
| Document ID | FMATH-SUM-MAP |
| Version | 1.0 |
| Status | Baselined |
| Owner | Akilleez-QA maintainer |
| Date | 2026-11-08 |
| Baseline commit | 53a58dde072b1d3f92836a1365f88f364b880a33 |
| Applies to | foundation-math main at baseline commit |
| Classification | Self-assessed Class E analog; not safety-critical (see [SMP §1](../plan/software-management-plan.md#1-software-classification-self-assessed)) |

> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&page_name=all), [NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the [NASA Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) documentation guidance. This is not a NASA compliance determination or certification. The software classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent verification and validation, or hazard analysis is asserted. The document describes the implementation inspected at the baseline commit.

The user manual (SWEHB 5.12, tailored) is the README plus the guides. This map shows where each element lives. The reference material is in the ICDs, the data dictionary and the contract documents rather than a separate `guides/reference/` folder.

| SUM element | Where | Verified how |
|---|---|---|
| Application summary and intended users | [README](../../README.md) intro and Status | Read against code at baseline |
| Inventory (what is shipped) | [README](../../README.md#what-is-inside) What is inside; [version descriptions](../releases/README.md) | VDD generated from the source ZIP |
| Environment and prerequisites | [README](../../README.md#install-and-run) Install and run; [test plan §3](../verification/test-plan.md#3-test-environment) | TP-2 run at baseline |
| Modes and states of operation | [Design §5](../architecture/architecture.md#5-execution-concept); claim statuses in [data dictionary §2.1](../data/data-dictionary.md#21-problemspec-fm-research-problem1-and-research-outputs) | Inspection |
| Security and privacy | [SECURITY.md](../../SECURITY.md); [SMP §7](../plan/software-management-plan.md#7-security-privacy-and-secure-coding) | Inspection |
| Assistance and problem reporting | [SUPPORT.md](../../SUPPORT.md); issue forms in `.github/ISSUE_TEMPLATE/` | Inspection |
| First-time use | [Tutorial: your first finite check](tutorials/first-check.md) | Run end to end at baseline `53a58dd` |
| Starting and stopping | Each CLI run is one process that exits; nothing to stop ([process ICD §2](../icd/icd-stdio.md#2-interface-type-and-transport)) | Inspection |
| Capabilities and commands reference | [Process ICD](../icd/icd-stdio.md), [Python API ICD](../icd/icd-python-api.md), [data dictionary §1](../data/data-dictionary.md#1-tools-and-commands) | Trace check fails on any missing public name |
| Conventions (IDs, units, file layout) | [Data dictionary conventions](../data/data-dictionary.md#conventions); [README: What is inside](../../README.md#what-is-inside) | Inspection |
| Processing procedures | [Source packaging](how-to/source-package.md); contract documents ([affine](../AFFINE-CERTIFICATES.md), [query](../QUERY-IDENTIFIABILITY.md), [enclosures](../NUMERICAL-ENCLOSURES.md), [scalar](../SCALAR-CONTROL.md), [mapper](../EVIDENCE-PAPER.md), [source binding](../SOURCE-BINDING.md)) | Packaging procedure run at baseline (TP-3) |
| Data backup and recovery from errors | [Troubleshooting §Recovering](how-to/troubleshooting.md#recovering) | Inspection |
| Messages, errors and exit codes | [Troubleshooting](how-to/troubleshooting.md) | Rows marked "yes" reproduced at baseline |
| Assumptions and limitations | [README](../../README.md#limitations) Limitations; [limitations](explanation/limitations.md) | Inspection |
| Safety-related constraints | [Limitations](explanation/limitations.md#use-in-safety-engineering-or-regulated-decisions) | Inspection |
| Version-specific changes | `CHANGELOG.md`; [version descriptions](../releases/README.md) | Generated VDD |

## Change history

| Version | Date | Commit | Change | Reviewed in |
|---|---|---|---|---|
| 1.0 | 2026-11-08 | `53a58dd` | Initial map | PR #30 |
