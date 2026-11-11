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

## Affine-certificate local candidate (2026-11-05)

Prepared against public Foundation Math commit
`090ddeb3c9a7e5937bd5d0de08cc924e099cb800`. The new self-contained
`fm_certificates` implementation is elementary nonnegative linear-combination
arithmetic. Its tests use newly constructed dimensionless synthetic examples.
No external physical data, source tables, model implementation or application
configuration is included. Prior runtime modules, tests, examples and tools
remain unchanged. The research JSON dispatcher and its source-binding scope
are unchanged; affine certificates bind declared statements through a separate
versioned digest. Local preparation and tests do not authorize publication.

## Exact affine-query witnesses (2026-11-05)

The fm_identifiability addition consists of newly authored elementary rational
algebra, fresh synthetic tests and a mathematical contract under GPL-3.0-only.
Existing runtime modules and fixtures are unchanged. The API is separate from
the research receipt dispatcher and its source-binding scope.

## Exact numerical residual and error enclosures (2026-11-05)

Built on public commit `090ddeb3c9a7e5937bd5d0de08cc924e099cb800`.
The addition contains generic rational mathematics and synthetic tests.
Existing runtime modules and their source-binding scheme remain unchanged.
The accompanying contract states the finite checks and their limitations.

## Quadratic minimax problem admission (2026-11-11)

Built on public main commit `84fadd3`. This first stage contains generic rational mathematics, problem admission and synthetic tests. Existing runtime modules and their source-binding scheme remain unchanged. The accompanying contract states the finite checks and their limitations.

## Quadratic minimax witness verification (2026-11-11)

Built on the problem-admission stage of the same package. This second stage adds exact point, dual and Farkas witness verification and the command line. It contains generic rational mathematics and synthetic tests. Existing runtime modules and their source-binding scheme remain unchanged. The accompanying contract states the finite checks and their limitations.

## Correlated quadratic model admission (2026-11-11)

Built on public main commit `84fadd3`. This first stage contains generic exact rational mathematics, model admission, supplied-pair probes and synthetic tests. Existing runtime modules and their source-binding scheme remain unchanged. The accompanying contract states the finite checks and their limitations.

## Correlated quadratic witness verification (2026-11-11)

Built on the model-admission stage of the same package. This second stage adds exact upper-bound, offset-nonnegativity and global lower-bound witness verification, the command line and a synthetic example. It contains generic rational mathematics and synthetic tests. Existing runtime modules and their source-binding scheme remain unchanged. The accompanying contract states the finite checks and their limitations.

## Exact rational interval histories (2026-11-11)

Built on public main commit `84fadd3`. The addition contains generic rational mathematics and synthetic tests. Existing runtime modules and their source-binding scheme remain unchanged. The accompanying contract states the finite checks and their limitations.

## Exact continuous path bounds (2026-11-11)

Built on public main commit `84fadd3`. The addition contains generic rational mathematics and synthetic tests. Existing runtime modules and their source-binding scheme remain unchanged. The accompanying contract states the finite checks and their limitations.

## Correction note (2026-11-08)

The summary at the top of this file predates PR #5 (2026-10-30), which removed
code comments from several retained files. `SOURCE-MANIFEST.json` is the
authority for byte preservation. At commit `53a58dd` it marks these selected
files `byte_preserved: true`: five `fm_research` modules (`__init__`, `field`,
`p1`, `twoi`, `vendor`), `fm_mapper/__init__.py`, and four vendor files
(both `__init__.py` files, `character_ring/catalog.json`,
`character_ring/producer.py`). `fm_research/rank.py`, `fm_research/problem.py`,
`fm_mapper/core.py`, `fm_mapper/__main__.py` and the other five vendor files
are `byte_preserved: false`; their rows keep the original `source_sha256`.
The earlier sections are kept as written.
