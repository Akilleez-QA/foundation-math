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

Support is best effort; this policy promises no supported-version window,
response deadline, or bounty. Identify the exact commit rather than assuming
an older candidate is covered. Ordinary correctness defects without sensitive
security implications can use the bug report form.

Finite check receipts and model-conditional certificates have the limits described
in [README.md](README.md). A passing check is not scientific acceptance or
physical equipment-safety approval.
