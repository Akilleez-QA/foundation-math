# Configuration management

## Controlled items

`PACKAGE.json` identifies the source candidate as `scalar-control-v1-20261027`,
requires Python >=3.10, lists no dependencies and declares GPL-3.0-only.
This is candidate metadata, not a new release or a SemVer guarantee.
Runtime code, selected vendor sources/catalog, tests, synthetic examples,
documentation and packaging metadata are maintained in this repository.

`SOURCE-MANIFEST.json` records an explicit distribution file list with byte sizes
and SHA-256 hashes, plus retained provenance fields. The manifest excludes itself
from its rows; `tools/package_source.py` includes it in the archive. The tool
rejects missing or extra files, symlinks and mismatched bytes. It writes a
deterministic stored ZIP to a fresh path outside the source root.

The separate `fm-research-source/2` identity is implemented by `_source_hash`
and `_SOURCE_FILES` in `fm_research/problem.py`. It binds 17 selected mathematical
source/catalog files; mapper, scalar-control, tests and docs do not enter that
fingerprint. Catalog bytes must also match the vendor contract pin. See
[SOURCE-BINDING.md](../SOURCE-BINDING.md) for framing and trust limits.

## Change and verification procedure

Follow [CONTRIBUTING.md](../../CONTRIBUTING.md) and the existing
[release checklist](../RELEASE-CHECKLIST.md): review the exact candidate scope,
preserve notices and historical receipts, run normal and optimized tests, and
record actual commands, failures, resource limits and unrun scope. The
[verification matrix](../verification/verification-matrix.md) connects the
implemented requirements to tests. Tests and hashes alone do not authorize release.

There is no `tools/build_manifest.py` in this repository. The packaging tool
verifies a manifest; it does not regenerate one. This documentation-only addition
leaves the existing candidate manifest unchanged. The new documents and changelog
must be explicitly included with current sizes and hashes when assembling a new
distribution candidate; the old manifest is not evidence for the expanded tree.

Changes to selected mathematical sources require fresh receipts; copying old
receipts cannot make them current. Changes to packaged bytes require an updated
distribution manifest and fresh archive/extraction checks. Retain the distinction
between source identity, software verification, mathematical acceptance and
publication approval. No new release, tag or host adapter pin is established by
these documents. Track unreleased documentation changes in
[CHANGELOG.md](../../CHANGELOG.md).
