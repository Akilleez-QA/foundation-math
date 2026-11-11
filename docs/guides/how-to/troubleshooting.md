# How to troubleshoot errors and exit codes

Each row below was reproduced at baseline commit `53a58dd` unless the "Seen" column says otherwise. Messages are printed on standard error.

## Exit codes

| Program | Exit | Meaning |
|---|---|---|
| `fm_research check` | 0 | At least one selected computed claim, and all selected computed claims are `certified` |
| `fm_research check` | 1 | Run completed, but a selected computed claim is `refuted`, `blocked` or `unchecked`, or no computed claim was selected |
| `fm_research check` | 2 | Input or argument error; nothing was gated |
| `fm_mapper` | 0 | Mapping (and rendering, if asked) completed. This says nothing about scientific acceptance |
| `fm_mapper` | 2 | Input, path or output error. Not a scientific refutation |
| `tools/package_source.py` | 1 (Python traceback) | Manifest or file-set check failed; no archive written |
| `tools.check_trace` | 1 | At least one documentation trace problem |

## Messages

| Message | Cause | Fix | Seen |
|---|---|---|---|
| `ValueError: Unexpected or missing fields: schema problem_id ...` | The ProblemSpec (or a nested object) has a missing or extra field | Supply exactly the listed fields ([data dictionary §2.1](../../data/data-dictionary.md#21-problemspec-fm-research-problem1-and-research-outputs)) | yes |
| `ValueError: Unsupported ProblemSpec schema` | `schema` is not `fm-research-problem/1` | Fix the schema string | code |
| `TypeError: ProblemSpec admits no floats or nonfinite numbers` | A float, `NaN` or `Infinity` appears anywhere | Use integers or `"n/d"` strings | yes |
| `ValueError: Unknown dependency or cycle` | `depends_on` names a missing claim or forms a cycle | Fix the dependency graph | yes |
| `ValueError: Unknown kernel` | `check.kernel` is not one of the seven registered kernels | Use a name from the data dictionary §1.2 | code |
| `TypeError: Invalid check arguments or expectation type` | `expect` has the wrong JSON type (string for decompositions, boolean for `twoi.distinct`, integer otherwise) | Fix `expect` | code |
| `KeyError: 'missing'` | `--claim` names a claim that is not in the spec | Use an existing claim id | yes |
| Record with `"verdict": "ERROR"` and `"observed": {"error": ..., "message": ...}` | The kernel rejected its arguments (for example degree 257, twist 65, modulus above 10^12) | Fix `check.args`; the claim stays `unchecked` | yes |
| `RuntimeError: Pinned character catalog SHA256 mismatch` | `vendor/foundation-math-v014/character_ring/catalog.json` bytes changed | Restore the file from Git | test |
| `Mapper error (not a scientific refutation): [Errno 2] No such file or directory: ...` | Bundle path wrong | Fix the path | yes |
| `Mapper error (not a scientific refutation): Output already exists; choose a fresh path` | `--json-out` or `--paper-out` exists | Choose a new path; existing files are never overwritten | yes |
| `Mapper error (not a scientific refutation): Output path would replace an input or duplicate another output` | An output equals the bundle, an artifact, or the other output | Choose distinct paths | test |
| `ValueError: Exact source file-set mismatch` (packager) | Run inside a Git checkout (`.git` is not allowlisted) or a file is not in the manifest | Export with `git archive` first ([source packaging](source-package.md)); for a new file run `python3 -S -B -m tools.refresh_manifest` and commit | yes |
| `ValueError: Source pin mismatch: <path>` (packager) | A committed file changed but the manifest row did not | `python3 -S -B -m tools.refresh_manifest`, commit, export again | code |
| `ValueError: Byte-preserved source changed: <path>` (refresh tool) | A file marked `byte_preserved: true` was edited | Restore it, or set the flag to `false` by hand with a recorded reason | code |

"code" means the message was read from the source but not reproduced; "test" means a unit test triggers it.

## Recovering

There is no state to back up or repair. Inputs are your files; outputs are new files. To recover from a bad run, delete the outputs you named and run again. To get back to a known-good tree, check out the last commit whose test report passed ([test reports](../../verification/reports/README.md)).
