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
and `_SOURCE_FILES` in `fm_research/problem.py`. It binds the selected mathematical
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
leaves the existing candidate manifest unchanged. Files selected for a new distribution candidate need explicit current sizes and
hashes. Community files remain outside the source-package allowlist; a Git
checkout includes additional files and is not itself the packaging input tree.
The old manifest is not evidence for changed bytes or an expanded file set.

Changes to selected mathematical sources require fresh receipts; copying old
receipts cannot make them current. Changes to packaged bytes require an updated
distribution manifest and fresh archive/extraction checks. Retain the distinction
between source identity, software verification, mathematical acceptance and
publication approval. No new release, tag or host adapter pin is established by
these documents. Track unreleased documentation changes in
[CHANGELOG.md](../../CHANGELOG.md).

## Baselines and pins

Inspect the candidate metadata and pins without changing them:

```sh
git rev-parse HEAD
git status --short
python3 -S -B -m json.tool PACKAGE.json
python3 -S -B -m json.tool SOURCE-MANIFEST.json
```

A Git commit identifies a checkout baseline. Each manifest row identifies a
selected distribution path, byte size and SHA-256 digest; retained source hashes
and preservation fields describe provenance. The manifest itself enters the ZIP
and needs an external digest to avoid a recursive self-pin. The catalog has its
own SHA-256 pin in the selected vendor contract. None of these identities proves
mathematical truth or authenticates a reviewer.

Keep the names `PACKAGE.json`, `SOURCE-MANIFEST.json` and every pinned path when
working against this candidate. Changing a README or pinned contract leaves the
old distribution hash stale even when source-tree tests pass. Do not refresh pins
as a side effect of documentation styling.

## Versioning and promotion

The candidate identifier is not a SemVer release. This checkout does not define a
SemVer compatibility policy or automated tag/promotion process. A future version
or tag needs an explicitly selected candidate and owner-authorized publication;
these documents assign neither a version nor a tag.

The [release checklist](../RELEASE-CHECKLIST.md) governs promotion: inspect exact
source and license boundaries, assemble an allowlisted tree, run bounded normal
and optimized checks, rebuild and compare archives, extract and check pins and
selected tests, then obtain independent exact-candidate review. Record actual
failures, interruptions and omitted stages. Archive output must be fresh and
outside the source root. Publication and verification of the public commit remain
separate authorized steps; local test success does not satisfy them.
