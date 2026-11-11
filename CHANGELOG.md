# Changelog

All notable changes to this project will be documented in this file.
The format is based on Keep a Changelog.

## [Unreleased]

### Added

- `fm_optimization`: exact linear optimization dual repair, upper-bound and
  attainment certificates (PR #26).
- `fm_certificates`: exact affine implication, infeasibility and composition
  certificates (#21).
- `fm_identifiability`: exact affine-query pair and constancy witnesses (#24).
- `fm_enclosures`: exact interval residual and conditional forward-error
  enclosures (#29).
- Family-standard documentation set (#30): software management plan, compliance
  matrix, data dictionary, Python API ICD, test plan, assurance record, user
  manual map, tutorial, troubleshooting guide and limitations page; the
  requirements, design, process ICD, verification matrix and configuration plan
  were rewritten to the standard with REQ-MATH-014 to REQ-MATH-028.
- `tools/check_trace.py` with `tests/test_trace.py`: both test suites now fail on
  untraced requirements, unclassified tests, data-dictionary omissions and dead
  links (#30).
- `tools/refresh_manifest.py` to rehash `SOURCE-MANIFEST.json`, and
  `tools/gen_release_docs.py` to generate the test report and version
  description (#30).
- Requirements, architecture design, local-process interface control,
  verification traceability and configuration-management documents under `docs/`.
- Links to retained evidence, source-binding, scalar-control and release guidance.

### Changed

- First-party copyright holder normalized (#20).
- CI actions updated: `actions/checkout` 7, `actions/setup-python` 7,
  `gitleaks/gitleaks-action` 3 (#7, #8, #9).

### Fixed

- Documentation: configuration plan named a superseded candidate; process ICD
  overstated the example's kernel coverage; PROVENANCE byte-preservation summary
  predated #5 (dated correction note added) (#30).
