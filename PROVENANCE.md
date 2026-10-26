# Source provenance summary

The candidate is built from existing Foundation Math, not a replacement kernel.
Its exact selected file identities appear in `SOURCE-MANIFEST.json`.

- Six `fm_research` modules are byte-preserved: initialization, field arithmetic,
  ranks, character API, split-bundle API, and the pinned catalog loader.
- `fm_research/problem.py` retains its 17 mathematical/check/accounting
  definitions unchanged in AST. The standalone module omits non-mathematical
  projection helpers and their unused import. The CLI is check-only.
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
scope. This licensed revision changes only licensing, documentation and metadata;
runtime, tests, examples and packaging tools are byte-identical to the reviewed
standalone baseline. The source manifest pins the new distribution.

Hashes and structural comparison do not prove mathematical correctness, privacy,
rights, or scientific acceptance. No historical execution receipt was rewritten
to impersonate this candidate's evidence.
