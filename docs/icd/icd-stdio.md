# Foundation Math interface control document: local processes

| Field | Value |
|---|---|
| Document ID | FMATH-ICD-PROCESS |
| Version | 2.0 |
| Status | Baselined |
| Owner | Akilleez-QA maintainer |
| Date | 2026-11-08 |
| Baseline commit | 53a58dde072b1d3f92836a1365f88f364b880a33 |
| Applies to | foundation-math main at baseline commit |
| Classification | Self-assessed Class E analog; not safety-critical (see [SMP §1](../plan/software-management-plan.md#1-software-classification-self-assessed)) |

> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&page_name=all), [NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the [NASA Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) documentation guidance. This is not a NASA compliance determination or certification. The software classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent verification and validation, or hazard analysis is asserted. The document describes the implementation inspected at the baseline commit.

The file name `icd-stdio.md` is kept for inbound links. Despite the name, there is no stdio protocol: this document covers the two command-line programs. The Python library interface is in the [Python API ICD](icd-python-api.md).

## Implemented boundary

This source subset contains no stdio adapter, JSON-RPC server, tool inventory, `initialize`, `tools/list` or `tools/call` implementation. An external adapter's protocol and pin-verification behavior cannot be specified from this code. No Cstack ICD is established here: this checkout supplies neither a counterpart adapter nor its pinned revision.

## 1. Interfacing entities and ownership

| Side | Entity | Owns |
|---|---|---|
| Caller | A user, script or host process | Input files, chosen output paths, the working directory, resource limits, interpretation of results |
| Foundation Math | `fm_research` and `fm_mapper` CLIs | Validation, computation, output records and exit status |

## 2. Interface type and transport

Process invocation with arguments. Inputs are files named on the command line, not requests on standard input. Output is UTF-8 text on standard output; diagnostics go to standard error. Each invocation is independent and synchronous; there is no session, framing or timeout beyond the 5-second `git rev-parse` call inside the research CLI.

| Interface | Invocation from repository root | Input | Standard output |
|---|---|---|---|
| Research | `python3 -B -m fm_research check SPEC [--claim ID] [--evidence-out PATH]` | `fm-research-problem/1` JSON file | One JSON object per selected claim |
| Mapper | `python3 -B -m fm_mapper BUNDLE [--artifact-root DIR] [--json-out PATH] [--paper-out PATH]` | `fm-evidence-paper/1` JSON file and declared artifacts | Indented map JSON, or delivery summary when `--json-out` is set |

## 3. Messages and data elements

Field types, units and limits are in the [data dictionary](../data/data-dictionary.md) (§2.1 research, §2.3 mapper). Summary:

### Research contract

ProblemSpec has exactly `schema`, `problem_id`, `title`, `objective`, `repo`, `roles`, `assumptions`, `exclusions`, `claims`. Each claim has `id`, `statement`, `kind`, `depends_on`, `check`; kinds are `computed`, `cited`, `argued`. Computed checks have `kernel`, `args`, `expect`; other kinds have a null check. Floats and nonfinite JSON numbers are rejected.

Registered kernels: `twoi.decompose_sym_W`, `twoi.decompose_tensor`, `twoi.invariant_count_sym_W`, `twoi.distinct`, `rank`, `p1.h0_dim`, `p1.h1_dim`. The synthetic `examples/research-regression.problem.json` shows the `twoi.decompose_sym_W` and `rank` argument shapes; the [data dictionary §1.2](../data/data-dictionary.md#12-problemspec-kernels-kernels-in-fm_researchproblempy) gives all seven. Rank JSON supports `Q`, `Q(sqrt5)` and `F_p`; rationals use integers or `n/d` strings, and quadratic entries may use pairs of rational coefficients.

Each output record has `claim_id`, `status`, `evidence` (null for noncomputed claims). Evidence fields are `claim_id`, `kernel`, `args_sha256`, `expected`, `observed`, `verdict`, `output_sha256`, `kernel_source_sha256`, `fm_research_commit`, `python_version`. Verdicts are `PASS`, `FAIL`, `ERROR`. `--claim` includes transitive computed prerequisites for execution but prints only selected claims. `--evidence-out` writes computed receipts as JSON lines and can replace an existing file.

### Mapper contract

The mapper emits `fm-evidence-map/1` JSON. Without `--artifact-root`, artifact paths resolve relative to the bundle's parent. Bundle size and aggregate artifact bytes are each limited to 8 MiB; resolved artifact paths must stay within the root. Missing bytes remain missing evidence. Optional output files must be fresh and distinct from inputs and one another; created files are not transactional as a pair. With `--json-out`, standard output carries `{"delivery": "mapped" or "mapped_and_rendered", "scientific_acceptance": false, "summary": {...}}`. The [mapper contract](../EVIDENCE-PAPER.md) defines the schema, judgment checks, dispositions and rendering qualifications in detail.

## 4. Errors and result semantics

| Condition | Response | Caller action | Test |
|---|---|---|---|
| Research: at least one selected computed claim, all certified | Exit 0 | Read records; certification is conditional on admitted dependencies, not theorem acceptance | `tests/test_problem.py::ProblemTests.test_standalone_cli` |
| Research: any other completed selection (a refuted, blocked or unchecked computed claim, or no computed claim selected) | Exit 1 | Inspect `status` per record | `test_standalone_cli` (refuted fixture) |
| Research: invalid spec, unknown claim, unreadable file, argument error | Exit 2; `Type: message` on stderr (argparse usage errors also exit 2) | Fix input | `test_standalone_cli` (unknown claim) |
| Research: kernel raises during a check | Record with verdict `ERROR`, status `unchecked`; exit 1 | Fix arguments | `tests/test_problem.py::ProblemTests.test_other_kernels_and_errors` |
| Mapper: mapping and rendering completed | Exit 0, whatever the scientific disposition | Read dispositions | `tests/test_mapper.py::MapperTests.test_cli_new_outputs_and_refusal_to_overwrite` |
| Mapper: invalid bundle, escaping path, existing or conflicting output | Exit 2; `Mapper error (not a scientific refutation): ...` on stderr | Fix input or choose fresh paths | `test_cli_new_outputs_and_refusal_to_overwrite`, `test_cli_cannot_replace_input` |

## 5. Identity, versioning and compatibility

Schema strings identify each format: `fm-research-problem/1`, `fm-evidence-paper/1`, `fm-evidence-map/1`. A change to a required field or its meaning is breaking and needs a new schema string. Receipts carry `kernel_source_sha256` (the `fm-research-source/2` identity) so a receipt from changed sources is detected as stale (`tests/test_source_binding.py`). The source candidate is named in `PACKAGE.json`.

## 6. Security and input bounds

JSON floats, NaN and infinity are rejected; mapper JSON also rejects duplicate keys. Identifiers are bounded to 128 characters. Mapper bundle and artifacts are each limited to 8 MiB, collections to 1,000 items and texts to 32,768 characters. Artifact paths must be relative, contain no `..` or backslash, and resolve inside the artifact root (symlink escapes rejected). Mapper outputs are created exclusively. The research CLI writes only `--evidence-out`. Neither program uses the network.

## 7. Requirements addressed

| Requirement | Section |
|---|---|
| REQ-MATH-005, REQ-MATH-006, REQ-MATH-008 | §3 Research contract, §4 |
| REQ-MATH-009, REQ-MATH-010, REQ-MATH-011 | §3 Mapper contract, §4, §6 |
| REQ-MATH-007 | §5 |

## 8. Change acceptance

A change to either CLI's arguments, records or exit codes updates this document, the data dictionary and the matching requirement in the same pull request, with a test for each changed error path. The owner reviews and merges.

## Change history

| Version | Date | Commit | Change | Reviewed in |
|---|---|---|---|---|
| 1.0 | 2026-10-30 | `1a610cf` | Initial local-process interface description | PR #4 |
| 2.0 | 2026-11-08 | `53a58dd` | Family standard format; error table with tests; corrected the example-coverage statement; identity and bounds sections | PR #30 |
