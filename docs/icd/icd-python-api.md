# Foundation Math interface control document: Python library API

| Field | Value |
|---|---|
| Document ID | FMATH-ICD-PYAPI |
| Version | 1.0 |
| Status | Baselined |
| Owner | Akilleez-QA maintainer |
| Date | 2026-11-08 |
| Baseline commit | 53a58dde072b1d3f92836a1365f88f364b880a33 |
| Applies to | foundation-math main at baseline commit |
| Classification | Self-assessed Class E analog; not safety-critical (see [SMP §1](../plan/software-management-plan.md#1-software-classification-self-assessed)) |

> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&page_name=all), [NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the [NASA Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) documentation guidance. This is not a NASA compliance determination or certification. The software classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent verification and validation, or hazard analysis is asserted. The document describes the implementation inspected at the baseline commit.

## 1. Interfacing entities and ownership

| Side | Entity | Owns |
|---|---|---|
| Caller | Python code running in the same interpreter, with the repository root on `sys.path` | Choosing the expected model or system, retaining it independently of witnesses, resource limits, interpretation |
| Foundation Math | Packages `fm_research`, `fm_mapper`, `fm_control`, `fm_certificates`, `fm_identifiability`, `fm_enclosures`, `fm_minimax`, `fm_correlated`, `fm_intervals`, `fm_paths`, `fm_optimization` | Validation, exact computation, result records |

The caller is trusted. These APIs are not sandboxes: Python reflection can bypass frozen dataclasses, and monkey-patching is outside the trust boundary.

## 2. Interface type and transport

In-process synchronous function calls. No serialization, network, file I/O (except `load_bundle`, `read_artifacts`, `load_spec` given a path) or threads. Results are plain values or frozen dataclasses.

## 3. Calls and data elements

Field types, units and limits for every name below are in the [data dictionary](../data/data-dictionary.md). Detailed contracts and proofs are in the linked documents.

| Package | Call | Returns | Contract |
|---|---|---|---|
| `fm_research.problem` | `load_spec(path_or_dict)` | validated dict | [ICD process §3](icd-stdio.md#research-contract) |
| | `run_check(claim)` | `Evidence` | same |
| | `gate(spec, evidence_by_claim)` | dict claim id → status | same |
| `fm_research.rank` | `rank_exact(rows, field='Q', modulus=None)` | `RankCertificate` | DD §2.1 |
| | `verify_rank_certificate(rows, cert, field=None, modulus=None)` | bool | DD §2.1 |
| `fm_research.twoi` | `irrep(label)`, `sym_W(n)`, `Rep.tensor` (`@`), `invariant_count(rep)`, `inner`, `distinguish` | `Rep`, int, list | DD §2.2 |
| `fm_research.p1` | `cohomology(blocks, twists)`, `hom(source, target)` | dict, `Rep` | DD §2.2 |
| `fm_mapper` | `load_bundle`, `validate_bundle`, `binding_for`, `read_artifacts(bundle, root)`, `map_evidence(bundle, artifact_bytes)`, `render_paper(bundle, artifact_bytes)`, `canonical_json`, `digest` | dict, str | [mapper contract](../EVIDENCE-PAPER.md) |
| `fm_control.scalar` | `safe_actions(x, gain, drift, target, admissible)` | interval tuple or `None` | [scalar control](../SCALAR-CONTROL.md) |
| | `obstruction(models, observed, noise_bound, target, admissible)` | bool | same |
| `fm_certificates` | `AffineSystem(context, dimension, inequalities)`, `system_digest(system)` | dataclass, str | [affine certificates](../AFFINE-CERTIFICATES.md) |
| | `make_implication(system, target, multipliers)`, `verify_implication(system, cert)` | `Implication`, bool | same |
| | `make_infeasibility(system, multipliers)`, `verify_infeasibility(system, cert)` | `Infeasibility`, bool | same |
| | `compose_implications(system, inner, outer)` | `Implication` | same |
| `fm_identifiability` | `Model(C, z, L, h, q, d=0)`, `verify_pair(model, PairWitness(...))`, `verify_constancy(model, ConstancyWitness(...))` | `PairResult`, `ConstancyResult` | [query identifiability](../QUERY-IDENTIFIABILITY.md) |
| `fm_enclosures` | `enclose_linear_residual(matrix, candidate, rhs)`, `verify_linear_residual(result, matrix, candidate, rhs)` | `LinearResidualEnclosure`, bool | [numerical enclosures](../NUMERICAL-ENCLOSURES.md) |
| `fm_minimax` | `certify(problem, witness=None)` | dict with status `feasible`, `infeasible`, `unresolved` or `invalid_input`; separate `row_feasibility` and optional `exact_threshold` | [quadratic minimax certificates](../QUADRATIC-MINIMAX.md) |
| `fm_correlated` | `verify(json_text_or_bytes)`; exports `Invalid` and its `Limit` subclass | Conditional receipt dict with upper/lower bounds, represented gap, point admission, separate exact-target and outer-image exclusion flags, offset nonnegativity and non-global probes; CLI `python3 -S -B -m fm_correlated INPUT.json` (`-` for stdin), exit 0 on success or 2 with `rejected_or_unresolved` JSON on recognized failure | [correlated quadratic certificates](../CORRELATED-QUADRATIC.md) |
| `fm_intervals` | `interval(bounds)`, `intersection(intervals)`, `analyze_history(horizon, observations)`, `verify_history(horizon, observations, receipt)` | tuple of `Fraction` endpoints, tuple or `None`, dict, bool | [interval histories](../INTERVAL-HISTORY.md) |
| `fm_paths` | `certify_path_bounds(records, horizon, up, down, integral_band=None, max_pairs=200000)`, `verify_path_bounds(records, horizon, up, down, receipt, integral_band=None)` | receipt dict, bool | [path bounds](../PATH-BOUNDS.md) |
| `fm_optimization` | `LinearProgram(context, dimension, inequalities, equalities, objective, offset=0)`, `program_digest(program)`, `augment_box(program, lower, upper)`, `repair_dual(program, inequality_candidates, equality_candidates, equality_correction=None, box=None)`, `verify_dual_bound(expected, certificate)`, `verify_attainment(expected, certificate, point)` | `LinearProgram`, str, `DualBound`, bool | [linear optimization certificates](../DUAL-REPAIR.md) |

## 4. Errors and result semantics

| Condition | Response | Caller action | Test |
|---|---|---|---|
| Malformed ProblemSpec | `ValueError` or `TypeError` | Fix input | `tests/test_problem.py::ProblemTests.test_validation` |
| Malformed mapper bundle | `SchemaError` (a `ValueError`) | Fix input | `tests/test_mapper.py::MapperTests.test_cycles_dangling_duplicates_and_unknown_fields_rejected` |
| Affine input outside shape or limits | `Unsupported` | Reduce or correct input; not a mathematical result | `tests/test_affine_certificates.py::AffineCertificateTests.test_malformed_and_exact_type_boundaries` |
| Affine witness fails in `make_*` or composition | `InvalidCertificate` | Supply a correct witness; failure proves nothing about feasibility | `test_strict_infeasibility_and_touching`, `test_composition_preserves_nonzero_slack` |
| Affine `verify_*` on a bad record | `False` | — | `test_binding_changes_and_canonical_rationals` |
| Query model or witness malformed, over limits or bound to another model | `ValueError` | Fix input | `tests/test_identifiability.py::IdentifiabilityTests.test_bad_types_dimensions_and_limits` |
| Query witness structurally valid but fails | status `invalid_witness`, no value | — | `test_closed_prior_boundary_and_invalid_points` |
| Enclosure limit exceeded | `EnclosureLimitError` | Reduce input; not evidence of singularity | `tests/test_numerical_enclosures.py::NumericalEnclosureTests.test_shapes_and_limits` |
| Enclosure input malformed | `ValueError` | Fix input | `test_bad_rationals` |
| Enclosure margin β ≤ 0 | `forward_status` `unresolved`, no bound | Not evidence of singularity | `test_unresolved_does_not_mean_singular` |
| Scalar interval malformed | `ValueError` | Fix input | `tests/test_scalar_control.py::Certificate.test_invalid_intervals_rejected_including_zero_gain` |
| Scalar obstruction not established | `False` | Not proof that a common safe action exists | `test_touching_is_not_disjoint` |

## 5. Identity, versioning and compatibility

Each certificate family binds its statement with its own versioned digest: `fm-affine-system/1` (`system_digest`) and `fm-identifiability/1` (`Model.digest`). Enclosure results bind nothing; verification recomputes from inputs the caller supplies. A change to a digest payload is breaking and needs a new version tag. These APIs are separate from the research receipt format and do not enter `kernel_source_sha256`. The public names are the `__all__` lists of `fm_certificates`, `fm_enclosures` and `fm_mapper`, and the module-level names of the other modules; `tools/check_trace.py` fails when a public name is missing from the data dictionary.

## 6. Security and input bounds

Exact types only (`int`, `Fraction`; booleans and subclasses rejected), immutable tuples where stated, and fixed bit, row and dimension caps (data dictionary §6). No network, file, solver or subprocess use in the six certificate packages; the correlated CLI reads a named file or stdin.

## 7. Requirements addressed

| Requirement | Section |
|---|---|
| REQ-MATH-001 to REQ-MATH-004 | §3 research rows |
| REQ-MATH-009, REQ-MATH-010 | §3 mapper row, §4 |
| REQ-MATH-013 | §3, §4 scalar rows |
| REQ-MATH-014 to REQ-MATH-018 | §3, §4 affine rows, §5 |
| REQ-MATH-019 to REQ-MATH-021 | §3, §4 query rows, §5 |
| REQ-MATH-022 to REQ-MATH-025 | §3, §4 enclosure rows |
| REQ-MATH-030 to REQ-MATH-037 | §3 interval history row |
| REQ-MATH-040 to REQ-MATH-046 | §3 path row |
| REQ-MATH-050 to REQ-MATH-057 | §3 optimization row |
| REQ-MATH-070 to REQ-MATH-079 | §3 minimax row; JSON CLI in the linked contract |

## 8. Change acceptance

A change to a public signature, return record, exception type or digest payload updates this document, the data dictionary, the contract document and the requirement in the same pull request, with tests for the changed paths.

## Change history

| Version | Date | Commit | Change | Reviewed in |
|---|---|---|---|---|
| 1.0 | 2026-11-08 | `53a58dd` | Initial Python API interface document | PR #30 |
