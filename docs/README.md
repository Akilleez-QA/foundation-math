# Documentation

Start with the task you have. Foundation Math checks mathematical claims and
certificates exactly; the [README](../README.md) explains what it is and shows an
example.

## Start here

| I want to | Read |
|---|---|
| Learn: run it for the first time | [Tutorial: your first finite check](guides/tutorials/first-check.md) |
| Do: a specific task | [Check research claims and write them up](guides/how-to/research-claims.md) · [Build and verify a source package](guides/how-to/source-package.md) · [Troubleshoot errors and exit codes](guides/how-to/troubleshooting.md) |
| Look up: commands, calls, fields, units, limits | [Command-line reference](icd/icd-stdio.md) · [Python API reference](icd/icd-python-api.md) · [Data dictionary](data/data-dictionary.md) |
| Understand: the design and limits | [Design](architecture/architecture.md) · [Limitations and safety-relevant use](guides/explanation/limitations.md) |
| Where each user-manual topic lives | [User manual map](guides/SUM-MAP.md) |

## Mathematical contracts (reference)

These keep their uppercase names for inbound links.

- [Affine certificates](AFFINE-CERTIFICATES.md)
- [Exact affine-query witnesses](QUERY-IDENTIFIABILITY.md)
- [Exact numerical residual and error enclosures](NUMERICAL-ENCLOSURES.md)
- [Exact linear optimization certificates](DUAL-REPAIR.md)
- [Evidence mapper schema and API](EVIDENCE-PAPER.md)
- [Scalar one-step certificates](SCALAR-CONTROL.md)
- [Research source binding](SOURCE-BINDING.md)
- [Release checklist](RELEASE-CHECKLIST.md)
- [Historical candidate verification, 2026-10-30](VERIFICATION.md) (historical record; not current evidence)

## Engineering records

Control documents carry their own baseline commits. Reading or indexing them does not create a new verification result. Classification: self-assessed Class E analog, not safety-critical; this is not a NASA compliance determination or certification (see the [software management plan](plan/software-management-plan.md#1-software-classification-self-assessed)).


| Document | ID | SWEHB | Path |
|---|---|---|---|
| Software management plan | FMATH-SMP | 5.08, 5.04, 5.17, 5.27 | [plan/software-management-plan.md](plan/software-management-plan.md) |
| Requirements mapping matrix | FMATH-RMM | 7.16 | [plan/compliance-matrix.md](plan/compliance-matrix.md) |
| Requirements | FMATH-SRS | 5.09 | [requirements/requirements.md](requirements/requirements.md) |
| Design | FMATH-SDD | 5.13 | [architecture/architecture.md](architecture/architecture.md) |
| Interfaces | FMATH-ICD-PROCESS, FMATH-ICD-PYAPI | 5.02 | [icd/icd-stdio.md](icd/icd-stdio.md), [icd/icd-python-api.md](icd/icd-python-api.md) |
| Data dictionary | FMATH-DD | 5.07 | [data/data-dictionary.md](data/data-dictionary.md) |
| Test plan and procedures | FMATH-STP | 5.10, 5.14 | [verification/test-plan.md](verification/test-plan.md) |
| Verification matrix | FMATH-VM | SWE-052 | [verification/verification-matrix.md](verification/verification-matrix.md) |
| Test reports | FMATH-STR-* | 5.11, 5.05 | [verification/reports/](verification/reports/README.md) |
| Configuration management | FMATH-SCMP | 5.06 | [configuration/configuration-management.md](configuration/configuration-management.md) |
| Version descriptions | FMATH-VDD-* | 5.16 | [releases/](releases/README.md) |
| Assurance record | FMATH-SAR | 5.21–5.23, 5.25, 5.26 | [assurance/assurance-record.md](assurance/assurance-record.md) |
| User manual map | FMATH-SUM-MAP | 5.12 | [guides/SUM-MAP.md](guides/SUM-MAP.md) |

Not applicable for this family (rationale in the SMP): training plan (5.15), safety plan (5.18), assurance status report (5.19), IV&V plan (5.20), hazard report (5.24; the [limitations page](guides/explanation/limitations.md) is the substitute). Repository rules live in `AGENTS.md` and [CONTRIBUTING](../CONTRIBUTING.md); there is no `docs/rules/` folder.

Check the documents against the code with `python3 -S -B -m tools.check_trace`. See [Contributing](../CONTRIBUTING.md) and [Security](../SECURITY.md).
