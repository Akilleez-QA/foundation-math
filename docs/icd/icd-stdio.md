# Interface control: local processes and a stdio adapter

## Implemented boundary

This source subset contains no stdio adapter, JSON-RPC server, tool inventory,
`initialize`, `tools/list` or `tools/call` implementation. An external adapter's
protocol and pin-verification behavior cannot be specified from this code.
The following are the implemented CLI interfaces available to a process caller.
They accept file paths through arguments, not requests on standard input.

| Interface | Invocation from repository root | Input | Standard output |
|---|---|---|---|
| Research | `python3 -B -m fm_research check SPEC [--claim ID] [--evidence-out PATH]` | `fm-research-problem/1` JSON file | One JSON object per selected claim |
| Mapper | `python3 -B -m fm_mapper BUNDLE [--artifact-root DIR] [--json-out PATH] [--paper-out PATH]` | `fm-evidence-paper/1` JSON file and declared artifacts | Indented map JSON, or delivery summary when `--json-out` is set |

## Research contract

ProblemSpec has exactly `schema`, `problem_id`, `title`, `objective`, `repo`,
`roles`, `assumptions`, `exclusions`, `claims`. Each claim has `id`, `statement`,
`kind`, `depends_on`, `check`; kinds are `computed`, `cited`, `argued`.
Computed checks have `kernel`, `args`, `expect`; other kinds have a null check.
Floats and nonfinite JSON numbers are rejected.

Registered kernels: `twoi.decompose_sym_W`, `twoi.decompose_tensor`,
`twoi.invariant_count_sym_W`, `twoi.distinct`, `rank`, `p1.h0_dim`, `p1.h1_dim`.
The synthetic `examples/research-regression.problem.json` shows argument shapes.
Rank JSON supports `Q`, `Q(sqrt5)` and `F_p`; rationals use integers or `n/d`
strings, and quadratic entries may use pairs of rational coefficients.

Each output record has `claim_id`, `status`, `evidence` (null for noncomputed
claims). Evidence fields are `claim_id`, `kernel`, `args_sha256`, `expected`,
`observed`, `verdict`, `output_sha256`, `kernel_source_sha256`,
`fm_research_commit`, `python_version`. Verdicts are `PASS`, `FAIL`, `ERROR`.
`--claim` includes transitive computed prerequisites for execution but prints
only selected claims. `--evidence-out` writes computed receipts as JSON lines
and can replace an existing file.

Exit 0 means at least one selected computed claim exists and all selected
computed claims are certified. Exit 1 covers other completed selections.
Caught input/runtime errors and argument errors exit 2 with diagnostics on stderr.
Certification is conditional on admitted dependencies, not theorem acceptance.

## Mapper contract

The mapper emits `fm-evidence-map/1` JSON. Without `--artifact-root`, artifact
paths resolve relative to the bundle's parent. Bundle size and aggregate artifact
bytes are each limited to 8 MiB; resolved artifact paths must stay within the root.
Missing bytes remain missing evidence. Optional output files must be fresh and
distinct from inputs and one another; created files are not transactional as a pair.

Exit 0 means mapping/rendering completed regardless of scientific disposition.
Caught errors exit 2 and write `Mapper error (not a scientific refutation): ...`
to stderr. The [existing mapper contract](../EVIDENCE-PAPER.md) defines the
schema, judgment checks, dispositions and rendering qualifications in detail.
