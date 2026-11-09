# Check research claims and write them up

Besides the exact-checking library described in the [README](../../../README.md),
Foundation Math ships three smaller parts from its original research use. This page
shows how to use each one. All three run from the repository root with Python 3.10
or newer and nothing installed.

| Part | What it does | Contract |
|---|---|---|
| `fm_research` (command line) | Checks claims files with exact kernels for matrix rank over Q, Q(√5) and prime fields, characters of the finite group SL2(F5), and cohomology dimensions of supplied split bundles | [Source binding](../../SOURCE-BINDING.md) |
| `fm_mapper` (command line) | Takes your own verdict on each claim (`supports`, `refutes` or `inconclusive`) and writes a draft paper whose wording matches that support. It reports; it does not judge | [Evidence mapper](../../EVIDENCE-PAPER.md) |
| `fm_control` (Python) | One-step safe-action intervals for a scalar linear model | [Scalar control](../../SCALAR-CONTROL.md) |

`vendor/foundation-math-v014/` holds the SL2(F5) character and split-bundle code
that `fm_research` imports, kept byte-for-byte from release v0.14
([provenance](../../../PROVENANCE.md)).

## Check a claims file with `fm_research`

`fm_research` reads a problem file of claims. Each computed claim names a kernel,
its arguments and the answer the producer expects. This one, from
[the shipped example](../../../examples/research-regression.problem.json), says the matrix
`[[√5, 0], [0, 3]]` has rank 2 (a plain number is rational; a pair `[a, b]` means
`a + b√5`):

```json
{
  "id": "rank-q5",
  "statement": "The supplied diagonal quadratic-field matrix has rank two.",
  "kind": "computed",
  "depends_on": [],
  "check": {"kernel": "rank", "args": {"field": "Q(sqrt5)", "rows": [[[0, 1], 0], [0, 3]]}, "expect": 2}
}
```

```sh
python3 -S -B -m fm_research check examples/research-regression.problem.json --claim rank-q5
```

```text
{"claim_id": "rank-q5", "status": "certified", "evidence": {"kernel": "rank",
 "expected": 2, "observed": {"rank": 2, "certificate": {"field": "Q(sqrt5)",
 "pivot_rows": [0, 1], "pivot_cols": [0, 1], ...}}, "verdict": "PASS",
 "args_sha256": "2ec6140c...", "kernel_source_sha256": "a9652c11...", ...}}
```

(Output trimmed and wrapped.) The command runs the kernel, records the
arguments hash, the observed answer and a hash of the kernel source, then grades
the claim. `verdict` is the raw comparison with `expect`; `status` is the claim's
standing. Change `"expect": 2` to `1` and it comes back `refuted`.

| `status` | Meaning |
|---|---|
| `certified` | The check passed and every claim it depends on is `certified` or `cited` |
| `refuted` | The check failed |
| `blocked` | The check passed, but a claim it depends on is not certified |
| `unchecked` | The recorded evidence did not match the claim or the current source files |
| `cited`, `argued` | Not computed: a cited source or an argument, passed through as labelled and never upgraded |

The exit code is 0 only when every computed claim you asked about is `certified`,
1 otherwise (including when you asked only about `cited` or `argued` claims), and
2 when the input is malformed. Run the whole example file to see three
`certified` claims and one `argued`.

## Write up claims with `fm_mapper`

```sh
python3 -S -B -m fm_mapper examples/evidence-mapper/legacy-conditional.json
```

The mapper reads a JSON bundle of claims, hashed source files and your judgment
of each claim, checks the file hashes, and prints a JSON summary. Add
`--json-out FILE` and `--paper-out FILE` (fresh paths; the mapper refuses to
overwrite an existing file and exits 2) to save the summary and a Markdown draft. It reports support under
the judgments you supplied: every paper it writes is marked
`draft_not_scientifically_accepted`, and exit code 0 means mapping and rendering
finished, not that any claim is accepted. Schema and API:
[evidence mapper](../../EVIDENCE-PAPER.md).

## Scalar one-step control with `fm_control`

`fm_control` computes, with exact fractions, the interval of actions that keep one
step of a scalar affine model inside a target set, and checks whether one
observation leaves two candidate models with no action that is safe for both. It is arithmetic for one step: it commands
nothing, converts no units and is not a controller or simulator. Interface and
proof: [scalar control](../../SCALAR-CONTROL.md).
