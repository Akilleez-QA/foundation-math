# Release checklist

1. Confirm GPL-3.0-only selection, the exact first-party scope in NOTICE.md,
   provenance and retained notices. Recheck new third-party material before inclusion.
2. Select source by explicit file list. Inspect every selected text file and any
   nested payload; do not infer clearance from a regex scan or absence of hits.
3. Assemble a fresh source-only tree. Bind its exact file set and bytes to the
   manifest. Preserve historical artifacts separately, without relabeling them.
4. Review API changes, dependency semantics and evidence claim boundaries.
5. Run the scoped normal and optimized checks under declared resource limits.
   Record actual exits, failures, interruptions and never-run stages.
6. Package from the allowlist. Rebuild and compare bytes. Extract into a clean
   directory and verify the same source pins and selected checks there.
7. Obtain independent exact-candidate release-boundary review. Tests and hashes
   alone are not publication clearance or scientific acceptance.
8. Only after the owner authorizes publication, promote that tested candidate.
   Verify the public commit and its exact-head checks. Do not claim a public
   release from local packaging or a README-only repository.

This process is intended for tested promotions of development snapshots. It does
not configure a schedule, deployment, credentials, hosted CI, or public writes.

## This source-binding candidate

GPL-3.0-only remains unchanged. Relative to the public licensed baseline, this
candidate changes only the research source fingerprint and dependency list,
adds six synthetic regression methods and updates related docs/metadata. Exact
source-delta review, bounded checks, archive reproduction and remote publication
verification remain distinct steps. Historical receipts are not relabeled.
