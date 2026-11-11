# Foundation Math requirements mapping matrix

| Field | Value |
|---|---|
| Document ID | FMATH-RMM |
| Version | 1.0 |
| Status | Baselined |
| Owner | Akilleez-QA maintainer |
| Date | 2026-11-08 |
| Baseline commit | 53a58dde072b1d3f92836a1365f88f364b880a33 |
| Applies to | foundation-math main at baseline commit |
| Classification | Self-assessed Class E analog; not safety-critical (see [SMP §1](software-management-plan.md#1-software-classification-self-assessed)) |

> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&page_name=all), [NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the [NASA Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) documentation guidance. This is not a NASA compliance determination or certification. The software classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent verification and validation, or hazard analysis is asserted. The document describes the implementation inspected at the baseline commit.

Self-assessed class: Class E analog, not safety-critical. Baseline: Class E with voluntary adoption of the Class D documentation set.

| SWE | Topic | NPR classes | Decision | How met / rationale |
|---|---|---|---|---|
| 013 | Software plans | A–E | Applies | [SMP](software-management-plan.md) |
| 020 | Classification | A–E | Applies | [SMP §1](software-management-plan.md#1-software-classification-self-assessed) |
| 176 | Classification records | A–E | Applies | [SMP §1](software-management-plan.md#1-software-classification-self-assessed) and its change history |
| 205 | Safety-critical determination | A–E | Applies | [SMP §1](software-management-plan.md#1-software-classification-self-assessed): not safety-critical |
| 022 | SA / safety / IV&V planning | A–E | Tailored | [SMP §6](software-management-plan.md#6-software-assurance); no independent SA organization; no IV&V |
| 033 | Acquire vs develop | A–E | Applies | [SMP §8](software-management-plan.md#8-open-source-reused-and-vendored-components): developed in-house |
| 042 | Source code access | A–E | Applies | Public repository [Akilleez-QA/foundation-math](https://github.com/Akilleez-QA/foundation-math) |
| 121 / 139 / 125 | Tailoring, compliance, this matrix | A–E | Applies | This document |
| 148 | Contribute to reuse | A–E | Applies | GPL-3.0-only ([LICENSE](../../LICENSE)); [README](../../README.md#related-projects) family table |
| 156 | Cybersecurity assessment | A–E | Applies | [SMP §7](software-management-plan.md#7-security-privacy-and-secure-coding), [SECURITY.md](../../SECURITY.md) |
| 024 / 034 / 036 / 037 | Tracking, acceptance criteria, doc plan, milestones | A–D | Tailored | GitHub issues and PRs (no milestones); [SMP §5](software-management-plan.md#5-verification-and-validation-approach) acceptance; [docs index](../README.md) |
| 039 / 040 | Developer status reporting and deliverables to acquirer | A–D | N/A | No acquirer/supplier split; public repository and releases serve the purpose |
| 027 | COTS/OSS components | A–D | Applies | [SMP §8](software-management-plan.md#8-open-source-reused-and-vendored-components): none at runtime |
| 015 / 151 / 174 / 016 / 046 / 018 | Cost and schedule | A–D (018: A–C) | N/A | Unfunded single-maintainer project; milestones only |
| 017 | Training | A–C | N/A | [SMP §14](software-management-plan.md#14-training) |
| 141 / 131 / 178 / 179 | IV&V | A–B | N/A | Not an IV&V-category project |
| 023 / 134 / 219 / 220 | Safety-critical software | A–D if safety-critical | N/A | Not safety-critical (SWE-205) |
| 032 | CMMI rating | A–B | N/A | Not applicable to open-source single maintainer |
| 146 / 206 | Auto-generated code | A–C / A–D | N/A | No generated source code. Generated documents (STR, VDD) and the manifest are controlled per [SCMP §6](../configuration/configuration-management.md#6-generated-outputs) |
| 147 | Reusability requirements | A–D | Tailored | [SRS §5](../requirements/requirements.md#5-non-functional-requirements): stdlib-only importable packages; no separate reuse requirement |
| 154 / 157 / 159 / 207 / 185 / 210 | Cybersecurity risks, protections, secure coding, verification | A–D (210: A–C) | Tailored | [SMP §7](software-management-plan.md#7-security-privacy-and-secure-coding), [assurance record](../assurance/assurance-record.md) static-analysis entry |
| 050 / 051 / 053 / 054 / 055 | Requirements | A–D (051: A–C) | Applies | [SRS](../requirements/requirements.md), [assurance record](../assurance/assurance-record.md) |
| 184 | Safety constraints in requirements | A–C | N/A | No hazards |
| 052 | Bidirectional traceability | A–D | Applies | [Verification matrix](../verification/verification-matrix.md), `tools/check_trace.py` in both test suites |
| 057 / 058 | Architecture and design | A–C | Applies (voluntary) | [SDD](../architecture/architecture.md), [process ICD](../icd/icd-stdio.md), [Python API ICD](../icd/icd-python-api.md) |
| 143 | Architecture review | A–C | Tailored | PR review of SDD changes |
| 060 / 061 | Code, coding standards | A–C / A–D | Tailored | [CONTRIBUTING](../../CONTRIBUTING.md) and AGENTS.md rules (stdlib only, no comments or docstrings in new code); no linter in CI |
| 135 | Static analysis | A–D | Tailored | ruff E9/F recorded by the STR generator, not a CI gate ([SMP §6](software-management-plan.md#6-software-assurance), [assurance record](../assurance/assurance-record.md)) |
| 062 / 186 | Unit test, repeatable | A–D | Applies | [Test plan](../verification/test-plan.md) |
| 063 | Version description | A–D | Applies | [Version descriptions](../releases/README.md), generated by `tools/gen_release_docs.py` |
| 136 / 070 | Tool / model accreditation | A–C | Tailored | Tools listed in [SMP §4](software-management-plan.md#4-engineering-and-test-environment); no accreditation |
| 065 / 066 / 068 / 071 | Test plan, testing, evaluate results, update | A–D | Applies | [Test plan](../verification/test-plan.md), [test reports](../verification/reports/README.md) |
| 187 | CM before test | A–C | Applies | CI runs on committed code |
| 073 | Target platform validation | A–C | Tailored | CI: `ubuntu-latest`, Python 3.12; local runs record their platform in the STR |
| 189 / 190 | Code coverage | A–D / A–C | Tailored | Standard-library `trace` line coverage recorded in each STR; no threshold |
| 191 | Regression testing | A–C | Applies | Full suite in both modes on every push and PR ([ci.yml](../../.github/workflows/ci.yml)) |
| 192 / 193 | Hazard tests, uplinked data | A–D / A–B | N/A | No hazards; no uplink |
| 211 | Test reused components | A–C | Tailored | Vendor producer/verifier pairs and catalog audit run in `tests/test_kernels.py` |
| 075 / 077 / 194 / 195 / 196 | Operations, delivery, maintenance, retirement | A–D | Tailored | [SMP §11](software-management-plan.md#11-operations-maintenance-and-retirement), [VDDs](../releases/README.md) |
| 079–085 | Configuration management | A–D | Applies | [SCMP](../configuration/configuration-management.md) |
| 045 | Joint audits | A–C | N/A | No acquirer |
| 086 | Risk management | A–C | Tailored | [SMP §12](software-management-plan.md#12-risk-register) |
| 087 / 088 / 089 | Peer review | A–C | Tailored | [PR template](../../.github/pull_request_template.md); [assurance record](../assurance/assurance-record.md) summary; no effort metrics |
| 090 / 093 / 094 / 199 / 200 | Measurement | A–C (200: A–B) | Tailored | Generated STR metrics block ([SMP §13](software-management-plan.md#13-measurement)) |
| 201 / 202 | Non-conformances, severity | A–D / A–C | Applies | GitHub issue forms; [SMP §9](software-management-plan.md#9-problem-reporting-and-severity) |
| 203 / 204 | OSS defect assessment, process assessment | A–C / A–B | Tailored | No runtime dependencies; Dependabot for Actions; S1 root-cause note in the issue |

## Change history

| Version | Date | Commit | Change | Reviewed in |
|---|---|---|---|---|
| 1.0 | 2026-11-08 | `53a58dd` | Initial baseline | PR #30 |
