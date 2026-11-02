# Requirements

These requirements describe the implemented source-tree candidate, not NASA
certification or a general solver. T means test; every ID is traced in the
[verification matrix](../verification/verification-matrix.md).

| ID | Requirement (shall) | Rationale | Verification |
|---|---|---|---|
| REQ-MATH-001 | Quadratic arithmetic shall use exact rational coefficients and reject approximate coefficients and invalid radicands. | Preserve exact arithmetic. | T: [tests/test_kernels.py](../../tests/test_kernels.py) |
| REQ-MATH-002 | Rank certificates shall bind matrix bytes and verify a nonsingular minor and rank upper bound over supported fields. | Check finite rank witnesses. | T: [tests/test_kernels.py](../../tests/test_kernels.py) |
| REQ-MATH-003 | Character operations shall use the pinned catalog, preserve distinct physical labels, and restrict symmetric powers to W or Wp in degrees 0 through 256. | Respect the supplied table's scope. | T: [tests/test_kernels.py](../../tests/test_kernels.py) |
| REQ-MATH-004 | Split-bundle operations shall return formal cohomology and Hom characters under the supplied splitting and vendor bounds. | Avoid interpreting characters as chosen maps. | T: [tests/test_kernels.py](../../tests/test_kernels.py) |
| REQ-MATH-005 | ProblemSpec loading shall reject unsupported schemas, fields, kernels, float inputs, duplicate claim IDs and invalid dependency graphs. | Admit only the fixed finite-check contract. | T: [tests/test_problem.py](../../tests/test_problem.py) |
| REQ-MATH-006 | The research gate shall check receipt identities and transitive dependencies before assigning computed claims certified, refuted, blocked or unchecked. | Retain conditional evidence semantics. | T: [tests/test_problem.py](../../tests/test_problem.py) |
| REQ-MATH-007 | Research source identity shall bind the selected source/catalog files, reject catalog changes and leave stale receipts unchecked. | Bind receipts to selected bytes. | T: [tests/test_source_binding.py](../../tests/test_source_binding.py) |
| REQ-MATH-008 | The research CLI shall emit selected claim records and distinguish certified computed selections, unsuccessful selections and input errors by exit status. | Permit local process integration. | T: [tests/test_problem.py](../../tests/test_problem.py) |
| REQ-MATH-009 | The mapper shall validate its closed schema, references, graphs and exact judgment/artifact bindings without promoting evidence counts to theorem support. | Keep supplied judgments explicit. | T: [tests/test_mapper.py](../../tests/test_mapper.py) |
| REQ-MATH-010 | Mapper reports shall preserve qualifications and all proposed claims, mark drafts unaccepted, and render supplied prose as unverified text. | Prevent report text from asserting acceptance. | T: [tests/test_mapper.py](../../tests/test_mapper.py) |
| REQ-MATH-011 | Mapper file handling shall reject artifact root escapes and refuse existing, duplicate or input-replacing output paths. | Bound local file access. | T: [tests/test_mapper.py](../../tests/test_mapper.py) |
| REQ-MATH-012 | Source packaging shall check the exact allowlisted file set and hashes, reject symlinks, and produce deterministic ZIPs outside the source root without overwriting output. | Bind source distribution bytes. | T: [tests/test_package.py](../../tests/test_package.py) |
| REQ-MATH-013 | Scalar certificates shall normalize intervals, compute exact one-step safe actions, and certify ambiguity only for two individually feasible, currently safe, observation-compatible models with disjoint action sets. | Limit the certificate to its mathematical claim. | T: [tests/test_scalar_control.py](../../tests/test_scalar_control.py) |

The [architecture](../architecture/architecture.md) identifies implementations. Existing
[source-binding](../SOURCE-BINDING.md), [mapper](../EVIDENCE-PAPER.md) and
[scalar-control](../SCALAR-CONTROL.md) documents retain detailed contracts and limits.
