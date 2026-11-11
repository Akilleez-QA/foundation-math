<!-- Peer-review record, SWEHB 5.03 tailored. NPR SWE-087, 088, 089. -->

## Why

Describe the problem, use case, and related issue or reproduction (Fixes #, Refs #).

## What

Explain the resulting behavior, affected components, assumptions, and compatibility.
For documentation or config changes, identify the policy or workflow affected.

## Requirements, design and interface impact

- Requirements added, changed or deleted (REQ-MATH-###), or why none change:
- SDD / ICD / data dictionary updated: yes / no / not needed
- Verification matrix updated: yes / not needed
- `SOURCE-MANIFEST.json` refreshed (`python3 -S -B -m tools.refresh_manifest`): yes / not needed

## Verification

List the exact candidate commit, commands, resource limits, exit statuses, and
failed or unrun checks. Run both suites after edits:
`python3 -S -B -m unittest discover -s tests -t .` and the same with `-O`.
Distinguish software checks, independent review, and scientific acceptance.

## Peer review record

- Reviewers: <human approver>, <agent reviewers> (agent review is not independent)
- Review type: code / docs / requirements / design
- Findings: <count by severity; list or link resolved threads>
- Outcome: approved / changes requested / re-review

## Contribution checks

- [ ] I followed CONTRIBUTING.md and AGENTS.md.
- [ ] Tests and documentation cover the change, or I explained why they do not apply.
- [ ] I preserved evidence-status meanings and documented assumptions and limits.
- [ ] I did not weaken checks or change expected results to obtain a pass.
- [ ] Contributions meet GPL-3.0-only terms; third-party licenses and notices are preserved.
- [ ] No secrets, private research data, code comments, or docstrings were added.
- [ ] The change has one concern and stays under 400 changed lines, or explains its scope.
- [ ] AI-assisted work includes an Assisted-by commit trailer, if applicable.

## Documentation checklist

<!-- For documentation pull requests, paste the Cstack family DOC-CHECKLIST here and tick it. For code pull requests, tick the line below. -->

- [ ] Docs whose derivation paths this PR touches are updated or confirmed still accurate.
