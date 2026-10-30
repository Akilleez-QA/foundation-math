# Source provenance summary

The candidate is built from existing Foundation Math, not a replacement kernel.
Its exact selected file identities appear in `SOURCE-MANIFEST.json`.

- Six `fm_research` modules are byte-preserved: initialization, field arithmetic,
  ranks, character API, split-bundle API, and the pinned catalog loader.
- The initial standalone `fm_research/problem.py` retained 17 existing
  definitions. This source-binding revision changes only `_source_hash` and adds
  its explicit dependency list; the other 16 definitions are AST-identical to
  the public baseline. Kernel algorithms and conditional gate logic are unchanged.
  The CLI remains check-only.
- Nine selected v0.14 runtime files are byte-preserved under
  `vendor/foundation-math-v014/`. This subset is not the full v0.14 release.
- All three `fm_mapper` runtime modules are byte-preserved from corrected v2.
  The title correction had an independent 11-case corrective regression pass;
  it was not a new blind evaluation. That prior result does not certify this
  extracted candidate; the candidate has its own bounded checks.
- Mapper generic tests are derived by relocating imports and replacing a
  historical CLI input with a synthetic one. A historical stress test is not
  included. Research tests use new small synthetic fixtures, not old research
  workloads. Kernel checks are newly authored small tests.

The owner selected GPL-3.0-only for the covered first-party files on 2026-10-26;
NOTICE.md reconciles the earlier unselected license state and identifies the exact
scope. The initial licensed revision changed only licensing, documentation and
metadata. This subsequent revision binds the 17 selected mathematical source
files and adds six synthetic regression tests. Other runtime modules, prior tests,
examples and packaging tools remain byte-identical to public baseline
`e492473632e413504ffe450a604fd4eb33e2a559`. The source manifest pins this revision.

Hashes and structural comparison do not prove mathematical correctness, privacy,
rights, or scientific acceptance. No historical execution receipt was rewritten
to impersonate this candidate's evidence.

## Scalar one-step control addition (2026-10-27)

Built on public commit 2d26df9acc3a8a38e21e0c5ddfb8f558535e7399.
New fm_control code is elementary interval algebra with synthetic witnesses.
Prior runtime modules are unchanged. No external physical data or private
application code is included. The normalization regression reflects an actual
prototype defect; validation claims are limited to the stated model and tests.
