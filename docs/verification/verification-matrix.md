# Verification matrix

Run from the repository root:

```sh
python3 -B -m unittest discover -s tests -t .
python3 -B -O -m unittest discover -s tests -t .
```

T = automated test. These are existing synthetic contract tests, not independent
mathematical acceptance. File links and representative method names trace every
[requirement](../requirements/requirements.md) to current evidence sources.
Results belong to a particular run; historical counts in
[VERIFICATION.md](../VERIFICATION.md) describe its recorded candidate only.

| Requirement | Method | Existing test file | Representative checks |
|---|---|---|---|
| REQ-MATH-001 | T | [test_kernels.py](../../tests/test_kernels.py) | `test_exact_field_arithmetic_and_rejection` |
| REQ-MATH-002 | T | [test_kernels.py](../../tests/test_kernels.py) | `test_new_small_rank_witnesses_and_tampering` |
| REQ-MATH-003 | T | [test_kernels.py](../../tests/test_kernels.py) | `test_low_degree_characters_and_catalog_pin`, `test_selected_character_producer_verifier_pair` |
| REQ-MATH-004 | T | [test_kernels.py](../../tests/test_kernels.py) | `test_small_formal_cohomology_and_hom`, `test_selected_split_producer_verifier_pair` |
| REQ-MATH-005 | T | [test_problem.py](../../tests/test_problem.py) | `test_validation`, `test_other_kernels_and_errors` |
| REQ-MATH-006 | T | [test_problem.py](../../tests/test_problem.py) | `test_example_and_hashes`, `test_dependencies` |
| REQ-MATH-007 | T | [test_source_binding.py](../../tests/test_source_binding.py) | Complete closure, each dependency stales receipts, catalog rejection, missing files, deterministic relocation |
| REQ-MATH-008 | T | [test_problem.py](../../tests/test_problem.py) | `test_standalone_cli` |
| REQ-MATH-009 | T | [test_mapper.py](../../tests/test_mapper.py) | Exact binding, missing/mismatched bytes, schema and DAG rejection, no count-based promotion |
| REQ-MATH-010 | T | [test_mapper.py](../../tests/test_mapper.py) | Conditional premises, open obligations, retained failures, title/prose/markup regressions |
| REQ-MATH-011 | T | [test_mapper.py](../../tests/test_mapper.py) | `test_path_escape_and_symlink_escape_rejected`, `test_cli_new_outputs_and_refusal_to_overwrite`, `test_cli_cannot_replace_input` |
| REQ-MATH-012 | T | [test_package.py](../../tests/test_package.py) | Identical archives, changed/unlisted bytes, symlink and output containment rejection |
| REQ-MATH-013 | T | [test_scalar_control.py](../../tests/test_scalar_control.py) | Disjoint witness, touching endpoints, infeasibility, observation/current-state checks, signed/zero gains, exact grid and numeric boundaries |

Packaging tests construct disposable synthetic manifests; passing them does not
attest that the working tree matches the checked-in distribution manifest.
No adapter protocol tests exist because no adapter is included. Bounds and
unsupported claims remain as documented in [SCALAR-CONTROL.md](../SCALAR-CONTROL.md),
[SOURCE-BINDING.md](../SOURCE-BINDING.md) and [EVIDENCE-PAPER.md](../EVIDENCE-PAPER.md).
