# Foundation Math

Exact mathematical kernels and evidence reports

[<img alt="License: GPL-3.0-only" src="https://img.shields.io/badge/license-GPL--3.0--only-2400FF?style=flat-square&amp;labelColor=000000">](LICENSE)

## Status

This source-tree candidate checks finite mathematical claims, maps supplied
evidence judgments into qualified draft reports, and computes model-conditional
scalar one-step certificates. It uses Python 3.10+ and the standard library.
A local candidate does not by itself establish public publication.

## Quickstart

```sh
python3 -S -B -m fm_research check examples/research-regression.problem.json
python3 -S -B -m fm_research check examples/research-regression.problem.json --claim rank-q5
python3 -S -B -m fm_mapper examples/evidence-mapper/legacy-conditional.json
```

The example is synthetic. Its repository commit identifies a README-only public
scaffold, not the implementation. `SOURCE-MANIFEST.json` pins this candidate's
actual bytes; generated check receipts contain their own kernel-source hash.
Use a fresh output path for mapper `--json-out` and `--paper-out`.

## What is inside

- Exact quadratic-field arithmetic and finite matrix rank certificates.
- Virtual character arithmetic on a byte-pinned SL2(F5) character catalog.
- Formal supplied split-bundle cohomology and Hom-space characters.
- Structured finite checks, dependency accounting, and bound local receipts.
- An optional evidence mapper that records caller-supplied judgments and renders
  a visibly qualified draft report.

Only the selected character and split-bundle runtime components of v0.14 are
included. This is **not** the full historical v0.14 distribution or its tool suite.
No paid service, credentials, network access, package installation or external
solver is needed for the included source-tree workflow. Python 3.10+ is required;
the candidate verification records the Python version actually used.

## Read the evidence correctly

`fm_research` retains its existing `certified`, `cited`, `argued`, `refuted`,
`blocked`, and `unchecked` statuses. **Certified means a finite check passed
under its admitted dependency assumptions**, not that surrounding prose is proved.
`cited` is admitted, not independently proved. Historical receipts do not become
current receipts merely by copying them.

Version-2 source binding covers the selected mathematical source/catalog
files, including vendor implementations and retained verifiers. Changed source
bytes make earlier receipts stale; catalog mismatches remain explicit errors.
This binds bytes on disk, not loaded-code authenticity or mathematical truth.
See [source binding](docs/SOURCE-BINDING.md) for the exact scope and regression.

The mapper accepts the separate `fm-evidence-paper/1` schema. It does not infer
judgments from a research receipt. Its `supported` status means support under
supplied judgments at the stated scope, not authenticated truth. All generated
papers remain `draft_not_scientifically_accepted`; an exit code of zero means
mapping/rendering completed, not scientific acceptance. See
[the mapper contract](docs/EVIDENCE-PAPER.md).

The catalog's group identification and supplied splitting are assumptions.
Characters, dimensions, and Hom spaces are not actual maps, geometry or existence
proofs. This software does not validate a physical model, prove arbitrary research
claims, authenticate reviewers, or establish a productivity speedup.

## Checks and source packaging

```sh
python3 -S -B -m unittest discover -s tests -t .
python3 -S -B -O -m unittest discover -s tests -t .
python3 -S -B tools/package_source.py ../foundation-math-candidate.zip
```

Packaging uses an explicit manifest, verifies the exact file set and every hash,
and writes a deterministic source ZIP outside the tree. Existing output files are
never overwritten. This is a source distribution, not a wheel or a tested pip
installation. Run checks with suitable CPU, address-space and wall-time limits;
see [verification](docs/VERIFICATION.md) for the bounded candidate checks.

## Exact scalar control certificates

`fm_control` adds model-conditional one-step safe-action intervals and a
two-model observation-ambiguity checker. See [scope and proof](docs/SCALAR-CONTROL.md).
This is not a physical simulator, general controller or equipment-safety approval.

## Documentation

- [Requirements](docs/requirements/requirements.md)
- [Architecture](docs/architecture/)
- [Verification matrix](docs/verification/verification-matrix.md)
- [Configuration management](docs/configuration/configuration-management.md)
- [Local process interfaces](docs/icd/icd-stdio.md)
- [Release checklist](docs/RELEASE-CHECKLIST.md)

## Related projects

[Foundation Engine](https://github.com/Akilleez-QA/foundation-engine) and
[Cstack](https://github.com/Akilleez-QA/cstack) are related projects.
This checkout contains no Cstack adapter; its selected historical vendor subset
does not establish compatibility with a current host.

## Layout

| Path | Contents |
|---|---|
| `fm_research/` | Exact kernels, receipts and dependency accounting |
| `fm_mapper/` | Supplied evidence judgments and draft reports |
| `fm_control/` | Exact scalar one-step certificates |
| `vendor/foundation-math-v014/` | Selected historical character and split-bundle sources |
| `tests/` | Synthetic standard-library tests |
| `tools/` | Explicit-manifest source packager |
| `docs/` | Contracts, requirements, design and verification records |

## Contributing

See [Contributing](CONTRIBUTING.md), [Support](SUPPORT.md), and the
[Code of conduct](CODE_OF_CONDUCT.md). Report sensitive issues through
[Security](SECURITY.md).

## Development and provenance

Copyright (c) 2026 Refrigeration.AI. The first-party source, tests, synthetic examples,
tooling, documentation and metadata listed in `SOURCE-MANIFEST.json`, including
the selected v0.14 source subset, are licensed under GNU GPL **version 3 only**
(SPDX: `GPL-3.0-only`), not "or later". See [LICENSE](LICENSE),
[NOTICE.md](NOTICE.md) for the exact scope, and [PROVENANCE.md](PROVENANCE.md).
The software is supplied without warranty. The license document itself retains
the Free Software Foundation notice and verbatim-copy permission.

The intended release process promotes an explicitly selected, tested development
snapshot after review; it is not a blanket directory sync. See
[the release checklist](docs/RELEASE-CHECKLIST.md).

## License

This project is available under the GNU General Public License v3.0 only (GPL-3.0-only). If you want to use it to create a product or service under different terms, commercial licenses are available from Refrigeration.AI. Contact craig@nh3.biz.
