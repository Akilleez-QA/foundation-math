# Copyright, license and source scope

Copyright (c) 2026 Akilleez-QA.

## GPL-3.0-only

The owner selects GNU General Public License version 3 only (SPDX:
`GPL-3.0-only`) for the first-party Foundation Math files in this source
distribution. This is not an "or later" grant. The complete license is in LICENSE.
The software is supplied without warranty; see LICENSE sections 15 and 16.

Covered first-party paths are `fm_research/`, `fm_mapper/`, the nine selected
runtime files under `vendor/foundation-math-v014/`, `tests/`, `examples/`, `tools/`,
`docs/`, and the first-party root documentation and metadata, as enumerated in
`SOURCE-MANIFEST.json`. The root manifest itself is included in that scope.
LICENSE is the Free Software Foundation's license document, copied verbatim;
its own copyright and copying notice remain intact.

The selected-file review identified no third-party software components or
additional third-party software notices in this release file set. This scope
does not purport to relicense rights belonging to others. Any subsequently
identified third-party rights or notices must be preserved and reconciled.

## Historical reconciliation and changes

Earlier v0.14 documentation stated that a project license had not been selected.
This 2026-10-26 release explicitly selects GPL-3.0-only for the covered
first-party sources included here; it does not silently inherit a license or
rewrite earlier frozen artifacts. The selected subset is not the complete
historical v0.14 distribution.

The standalone extraction dated 2026-10-26 preserves selected mathematical
modules and corrects the distribution boundary to a check-only research CLI,
with synthetic tests and examples. The initial licensed revision changed only
licensing, documentation and metadata. This subsequent source-binding revision,
also dated 2026-10-26, changes only the research source fingerprint and its declared
dependencies, adds synthetic regression tests, and updates related documentation
and metadata. Mathematical kernels, prior tests, examples and packaging tools
remain unchanged from the public baseline.

LICENSE was copied byte-for-byte from the public Foundation Engine LICENSE at
commit `a005aefe5ee54fa1c07a81bae2c93466ebcc49a1`, blob
`f6cdd22a6c1fbc887e08a215cb4beb3c47048041`:
[license source](https://github.com/Akilleez-QA/foundation-engine/blob/a005aefe5ee54fa1c07a81bae2c93466ebcc49a1/LICENSE).
This copies the license text, not any Engine implementation.
