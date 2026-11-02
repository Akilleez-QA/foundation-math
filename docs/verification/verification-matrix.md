# Verification matrix

Run from the repository root:

```sh
python3 -S -B -m unittest discover -s tests -t .
python3 -S -B -O -m unittest discover -s tests -t .
```

T = automated test. These are existing synthetic contract tests, not independent
mathematical acceptance. File links and representative method names trace every
[requirement](../requirements/requirements.md) to current evidence sources.
Results belong to a particular run; historical counts in
[VERIFICATION.md](../VERIFICATION.md) describe its recorded candidate only.

| Requirement | Method | Existing test file | Representative checks | Result | Candidate |
|---|---|---|---|---|---|
| REQ-MATH-001 | T | [test_kernels.py](../../tests/test_kernels.py) | `test_exact_field_arithmetic_and_rejection` | Pass in both commands | Source parent `33960b2`; exact candidate tree recorded in this commit body |
| REQ-MATH-002 | T | [test_kernels.py](../../tests/test_kernels.py) | `test_new_small_rank_witnesses_and_tampering` | Pass in both commands | Source parent `33960b2`; exact candidate tree recorded in this commit body |
| REQ-MATH-003 | T | [test_kernels.py](../../tests/test_kernels.py) | `test_low_degree_characters_and_catalog_pin`, `test_selected_character_producer_verifier_pair` | Pass in both commands | Source parent `33960b2`; exact candidate tree recorded in this commit body |
| REQ-MATH-004 | T | [test_kernels.py](../../tests/test_kernels.py) | `test_small_formal_cohomology_and_hom`, `test_selected_split_producer_verifier_pair` | Pass in both commands | Source parent `33960b2`; exact candidate tree recorded in this commit body |
| REQ-MATH-005 | T | [test_problem.py](../../tests/test_problem.py) | `test_validation`, `test_other_kernels_and_errors` | Pass in both commands | Source parent `33960b2`; exact candidate tree recorded in this commit body |
| REQ-MATH-006 | T | [test_problem.py](../../tests/test_problem.py) | `test_example_and_hashes`, `test_dependencies` | Pass in both commands | Source parent `33960b2`; exact candidate tree recorded in this commit body |
| REQ-MATH-007 | T | [test_source_binding.py](../../tests/test_source_binding.py) | Complete closure, each dependency stales receipts, catalog rejection, missing files, deterministic relocation | Pass in both commands | Source parent `33960b2`; exact candidate tree recorded in this commit body |
| REQ-MATH-008 | T | [test_problem.py](../../tests/test_problem.py) | `test_standalone_cli` | Pass in both commands | Source parent `33960b2`; exact candidate tree recorded in this commit body |
| REQ-MATH-009 | T | [test_mapper.py](../../tests/test_mapper.py) | Exact binding, missing/mismatched bytes, schema and DAG rejection, no count-based promotion | Pass in both commands | Source parent `33960b2`; exact candidate tree recorded in this commit body |
| REQ-MATH-010 | T | [test_mapper.py](../../tests/test_mapper.py) | Conditional premises, open obligations, retained failures, title/prose/markup regressions | Pass in both commands | Source parent `33960b2`; exact candidate tree recorded in this commit body |
| REQ-MATH-011 | T | [test_mapper.py](../../tests/test_mapper.py) | `test_path_escape_and_symlink_escape_rejected`, `test_cli_new_outputs_and_refusal_to_overwrite`, `test_cli_cannot_replace_input` | Pass in both commands | Source parent `33960b2`; exact candidate tree recorded in this commit body |
| REQ-MATH-012 | T | [test_package.py](../../tests/test_package.py) | Identical archives, changed/unlisted bytes, symlink and output containment rejection | Pass in both commands | Source parent `33960b2`; exact candidate tree recorded in this commit body |
| REQ-MATH-013 | T | [test_scalar_control.py](../../tests/test_scalar_control.py) | Disjoint witness, touching endpoints, infeasibility, observation/current-state checks, signed/zero gains, exact grid and numeric boundaries | Pass in both commands | Source parent `33960b2`; exact candidate tree recorded in this commit body |

Packaging tests construct disposable synthetic manifests; passing them does not
attest that the working tree matches the checked-in distribution manifest.
No adapter protocol tests exist because no adapter is included. Bounds and
unsupported claims remain as documented in [SCALAR-CONTROL.md](../SCALAR-CONTROL.md),
[SOURCE-BINDING.md](../SOURCE-BINDING.md) and [EVIDENCE-PAPER.md](../EVIDENCE-PAPER.md).

## Candidate run and historical mapping

The commands above run every listed test file. For this documentation candidate,
both complete successfully; the containing commit records the candidate parent,
Git tree, exit statuses, timeout and unrun scope. This is author verification,
not independent review or mathematical acceptance. Re-run both commands after
combining branches; results do not transfer automatically to a new tree.

[VERIFICATION.md](../VERIFICATION.md) is a retained historical candidate report.
Its kernel coverage maps to REQ-MATH-001 through REQ-MATH-004; its ProblemSpec
coverage maps to REQ-MATH-005, REQ-MATH-006 and REQ-MATH-008. Source binding maps
to REQ-MATH-007, mapper checks to REQ-MATH-009 through REQ-MATH-011, packaging
to REQ-MATH-012, and scalar control to REQ-MATH-013. Its reported counts and
execution environment are historical observations, not measurements of this run.

No Cstack ICD is established here: this checkout supplies neither the counterpart
adapter implementation nor its pinned revision. The [local process interface](../icd/icd-stdio.md)
documents the verifiable CLI boundary, not a negotiated cross-repository protocol.
