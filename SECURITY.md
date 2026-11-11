# Security reporting

Do not put vulnerability details, credentials, personal data, or private research
files in a public issue or pull request.

Use GitHub private vulnerability reporting: open this repository's
[Security tab](https://github.com/Akilleez-QA/foundation-math/security) and choose
**Report a vulnerability** when available. Private vulnerability reporting was
reported disabled by the GitHub API on 2026-10-30. If the option is unavailable,
open a minimal [issue](https://github.com/Akilleez-QA/foundation-math/issues)
asking the maintainer for a private reporting channel. Include **no vulnerability
description, affected input, reproduction, or exploit**; wait for the private
channel before sending details. Do not infer a security contact from commit history.

In the private report, include:

- The affected commit and component.
- A minimal reproduction with synthetic data and exact commands.
- Python version, operating system, resource limits, and relevant error output.
- Expected and actual behavior, security impact, and any proposed mitigation.

Limit testing to systems and data you own or are authorized to assess. This policy
does not authorize third-party testing or disruptive research workloads. Discuss
disclosure with the maintainer before publishing working exploit details.

## Supported versions

Derived from `git tag --list`, which is empty at 2026-11-08: no release tag exists.

| Version | Supported |
|---|---|
| Latest `main` commit | Yes, best effort |
| Any earlier commit or source candidate | No |

Support is best effort; this policy promises no response deadline or bounty.
Identify the exact commit rather than assuming an older candidate is covered. Ordinary correctness defects without sensitive
security implications can use the bug report form.

Finite check receipts and model-conditional certificates have the limits described
in [README.md](README.md). A passing check is not scientific acceptance or
physical equipment-safety approval.

## Security posture

Foundation Math has no network access, credentials, plugins or external solvers.
The CLIs read only caller-named files and create only fresh caller-named outputs;
mapper artifact paths cannot escape their root. JSON inputs reject floats,
nonfinite numbers and (for the mapper) duplicate keys, and all inputs have size
and bit limits. The Python APIs trust their in-process caller and are not
sandboxes. CI runs Gitleaks on every push and pull request. Details:
[software management plan §7](docs/plan/software-management-plan.md#7-security-privacy-and-secure-coding).
