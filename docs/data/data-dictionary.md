# Foundation Math data dictionary

| Field | Value |
|---|---|
| Document ID | FMATH-DD |
| Version | 1.0 |
| Status | Baselined |
| Owner | Akilleez-QA maintainer |
| Date | 2026-11-08 |
| Baseline commit | 53a58dde072b1d3f92836a1365f88f364b880a33 |
| Applies to | foundation-math main at baseline commit |
| Classification | Self-assessed Class E analog; not safety-critical (see [SMP §1](../plan/software-management-plan.md#1-software-classification-self-assessed)) |

> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&page_name=all), [NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the [NASA Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) documentation guidance. This is not a NASA compliance determination or certification. The software classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent verification and validation, or hazard analysis is asserted. The document describes the implementation inspected at the baseline commit.

Generation and check: the tables are written from the source at the baseline commit. `python3 -S -B -m tools.check_trace` (run by both test suites through `tests/test_trace.py`) fails if any public function, class, dataclass field, upper-case constant, ProblemSpec kernel, vendor budget key or catalog key in the modules it scans is missing from this file. The scanned modules are listed in `DD_MODULES` in `tools/check_trace.py`.

Not applicable: channelization, rate-group, raw or calibrated sensor, telemetry, data-recorder and partitioning data. The software has no hardware or telemetry interfaces.

## Conventions

| Convention | Meaning |
|---|---|
| Units | Foundation Math is pure mathematics. Unless a row says otherwise, every number is **dimensionless**: an exact rational, an integer count or a multiplicity. Limits are given in **bits** (of a numerator or denominator, `int.bit_length()`), **bytes**, **characters**, **rows**, **coordinates** or **items**. The only module whose numbers can carry physical units is `fm_control`; there the caller declares the units (see §2.5) |
| Exact rational | A Python `int` or `fractions.Fraction`. JSON inputs use integers or `"n/d"` strings. Floats, NaN and infinity are rejected except where §2.5 says otherwise |
| SHA-256 digest | 64 lower-case hexadecimal characters |
| Canonical JSON | `json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)`; the mapper uses `ensure_ascii=False` and UTF-8 |
| Identifier | ProblemSpec: `[A-Za-z0-9_.:][A-Za-z0-9_.:-]{0,127}`. Mapper: `[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}` |
| Irrep labels | `LABELS` = `'1', 'W', 'A', 'S4', 'D', 'T6', 'P', 'Wp', 'V'` (physical labels of the nine irreducible characters of SL2(F5)) |

## 1. Tools and commands

### 1.1 Command-line programs

| Name | Purpose | Parameters | Result | Restrictions | Source |
|---|---|---|---|---|---|
| `python3 -S -B -m fm_research check SPEC` | Run the finite checks in a ProblemSpec and gate the claims | `SPEC` path to an `fm-research-problem/1` file; `--claim ID` select one claim (its computed prerequisites still run); `--evidence-out PATH` write computed receipts as JSON lines (replaces an existing file) | One JSON object per selected claim on stdout; exit 0, 1 or 2 ([ICD](../icd/icd-stdio.md#research-contract)) | Reads only `SPEC`; writes only `PATH` | `fm_research/__main__.py` |
| `python3 -S -B -m fm_mapper BUNDLE` | Map supplied evidence judgments and render a draft | `BUNDLE` path to an `fm-evidence-paper/1` file; `--artifact-root DIR` (default: the bundle's directory); `--json-out PATH`; `--paper-out PATH` | Map JSON on stdout, or a delivery summary when `--json-out` is given; exit 0 or 2 ([ICD](../icd/icd-stdio.md#mapper-contract)) | Output paths must not exist, must differ from each other and from every input | `fm_mapper/__main__.py` |
| `python3 -S -B tools/package_source.py OUTPUT` | Build the source ZIP | `OUTPUT` fresh path outside the tree | JSON `{"bytes", "file_count", "sha256"}` on stdout | Fails in a Git checkout (`.git` is not allowlisted) | `tools/package_source.py` |
| `python3 -S -B -m tools.check_trace` | Documentation trace check | `--root DIR` (default: repository) | Problems on stderr, JSON summary on stdout; exit 1 on any problem | — | `tools/check_trace.py` |
| `python3 -S -B -m tools.refresh_manifest` | Rehash `SOURCE-MANIFEST.json` from `git ls-files` | `--check` report only, exit 1 if anything would change | Lines `added`, `updated`, `removed` | Refuses to change a `byte_preserved` row | `tools/refresh_manifest.py` |
| `python3 -S -B -m tools.gen_release_docs --pr N` | Write the STR and VDD | `--pr` reviewing PR number; `--repo`; `--ruff PATH`; `--gitleaks PATH` | Two Markdown files under `docs/`; JSON on stdout with `str`, `vdd`, `normal_exit`, `optimized_exit`, `trace_problems` and `deviations` (the number of deviations, REQ-MATH-029) | Clean working tree required; queries GitHub with `gh` when present; exit 1 when any deviation is found, including a skipped test or a Gitleaks scan that was not run | `tools/gen_release_docs.py` |

### 1.2 ProblemSpec kernels (`KERNELS` in `fm_research/problem.py`)

Every kernel input and output is dimensionless. "Expect type" is the JSON type `load_spec` requires for `check.expect`.

| Kernel | Arguments (`check.args`) | Output (`observed`) | Expect type | Restrictions | Source |
|---|---|---|---|---|---|
| `twoi.decompose_sym_W` | `n`: integer degree | String decomposition of Sym^n W, e.g. `"A"`, `"2*W+S4"` | string | 0 ≤ n ≤ 256; terms compared without regard to order | `fm_research/twoi.py` `sym_W` |
| `twoi.decompose_tensor` | `factors`: list of labels or `{"sym_W": n}` objects | String decomposition of the tensor product | string | Labels from `LABELS` or aliases | `fm_research/problem.py` `_tensor` |
| `twoi.invariant_count_sym_W` | `degree`: integer | Multiplicity of the trivial irrep `1` in Sym^degree W (count) | integer | 0 ≤ degree ≤ 256 | `fm_research/twoi.py` `invariant_count` |
| `twoi.distinct` | `a`, `b`: labels | `true` if some conjugacy class separates the two characters | boolean | Labels from `LABELS` | `fm_research/twoi.py` `distinguish` |
| `rank` | `field`: `"Q"`, `"Q(sqrt5)"` or `"F_p"`; `rows`: list of equal-length lists of entries; `p`: prime, only for `F_p` | `{"rank": r, "certificate": RankCertificate}`; `expect` is compared with `r` | integer | Entries: integers or `"n/d"` strings; for Q(sqrt5) also `[a, b]` meaning a + b·sqrt5; for F_p entries are reduced mod p; 2 ≤ p ≤ 10^12 and prime | `fm_research/problem.py` `_rank` |
| `p1.h0_dim` | `blocks`: list of `{"irrep", "twist", "multiplicity"}`; `twist`: integer t | Complex dimension of H^0(P(W), F(t)) (count) | integer | Vendor bounds: ≤ 32 blocks, twists in [−64, 64], multiplicity in [0, 1,000,000] | `fm_research/p1.py` `cohomology` |
| `p1.h1_dim` | as `p1.h0_dim` | Complex dimension of H^1(P(W), F(t)) (count) | integer | as `p1.h0_dim` | `fm_research/p1.py` `cohomology` |

A kernel exception is recorded as `observed = {"error": <type name>, "message": <text>}` with verdict `ERROR`.

### 1.3 Python library entry points

Signatures and return types are in the [Python API ICD](../icd/icd-python-api.md). One line each here so every name has a definition.

| Module | Name | Meaning |
|---|---|---|
| `fm_research.field` | `rational` | Convert `int` or `Fraction` to `Fraction`; raise `TypeError` for anything else |
| | `QuadraticElement` | Immutable a + b·sqrt(d) |
| | `Q5` | Construct an element of Q(sqrt5) |
| | `GOLDEN` | The golden ratio (1 + sqrt5)/2 as a `Q5` element |
| `fm_research.rank` | `rank_exact` | Rank and certificate over Q, Q(sqrt d) or F_p |
| | `verify_rank_certificate` | Check a `RankCertificate` against a matrix; returns bool |
| | `rank_mod_p` | Rank of an integer matrix over F_p |
| | `rank_over_Q_and_mod_p` | Mapping prime → rank mod p for an integer matrix |
| `fm_research.twoi` | `label` | Normalize a label using `ALIASES`; raise `KeyError` if unknown |
| | `irrep` | `Rep` of one irreducible label |
| | `sym_W` | Sym^n of W as a `Rep` |
| | `invariant_count` | Multiplicity of the trivial irrep in a `Rep` (signed for virtual characters) |
| | `invariant_degrees` | List of (degree, nonzero invariant multiplicity) up to a maximum degree |
| | `molien_check` | Compare invariant counts with (1 + t^30)/((1 − t^12)(1 − t^20)) up to a degree |
| | `character_values` | Exact (a, b) pairs, a + b·sqrt5, of a `Rep` in catalog class order |
| | `inner` | Character inner product from class sizes; raises if not an integer |
| | `distinguish` | Class indices where two irreducible characters differ |
| `fm_research.p1` | `cohomology` | Formal H^0 and H^1 of a split bundle at given twists |
| | `hom` | Character of H^0(source* ⊗ target) |
| `fm_research.problem` | `load_spec` | Read and validate a ProblemSpec (path or dict) |
| | `run_check` | Run one computed claim's kernel and return `Evidence` |
| | `gate` | Assign a status to every claim from supplied evidence |
| `fm_research.vendor` | `catalog_sha256` | Recompute and check the catalog digest against `CATALOG_SHA256` |
| `fm_mapper` | `canonical_json`, `digest` | Canonical JSON text and its SHA-256 |
| | `load_bundle`, `validate_bundle` | Load (path or dict) and validate an evidence bundle |
| | `binding_for` | Build the identity pins for a judgment; it does not create judgments |
| | `read_artifacts` | Read declared artifact bytes under a root, contained and size-limited |
| | `map_evidence` | Produce the `fm-evidence-map/1` report |
| | `render_paper` | Produce the Markdown draft from the original bundle |
| `fm_control.scalar` | `interval` | Build a closed interval (lo, hi) of `Fraction`; raise if lo > hi |
| | `normalized` | Validate a two-endpoint interval; raise `ValueError` otherwise |
| | `intersection` | Intersect intervals; `None` if empty or any input is `None` |
| | `safe_actions` | Exact action interval keeping x + gain·u + drift inside the target |
| | `obstruction` | True when two compatible models have disjoint safe-action sets |
| `fm_certificates` | `system_digest` | Versioned SHA-256 of an `AffineSystem` |
| | `verify_implication`, `verify_infeasibility` | Check a certificate; return bool |
| | `make_implication`, `make_infeasibility` | Check a supplied witness and return a certificate, or raise `InvalidCertificate` |
| | `compose_implications` | Compose inner and outer implications into one direct certificate |
| `fm_identifiability` | `verify_pair`, `verify_constancy` | Check a witness against an expected `Model` |
| `fm_enclosures` | `enclose_linear_residual` | Compute a `LinearResidualEnclosure` |
| | `verify_linear_residual` | Recompute and compare; return bool |

## 2. Data elements

### 2.1 ProblemSpec (`fm-research-problem/1`) and research outputs

All fields are required; no others are allowed. Validated by `load_spec` in `fm_research/problem.py`.

| Name | Type | Units | Range / limits | Meaning |
|---|---|---|---|---|
| `schema` | string | — | exactly `fm-research-problem/1` | Format identifier |
| `problem_id` | string | — | identifier | Problem identity |
| `title`, `objective` | string | — | nonempty | Caller prose; not checked |
| `repo` | object `{name, commit}` | — | nonempty strings | Caller-declared source; not verified |
| `roles` | object `{builder, reviewer, verifier}` | — | nonempty strings | Caller-declared roles; not authenticated |
| `assumptions`, `exclusions` | array of strings | — | nonempty strings | Caller prose |
| `claims` | array of claim objects | — | unique ids; dependency graph acyclic | Claims to gate |
| claim `id` | string | — | identifier, unique | Claim identity |
| claim `statement` | string | — | nonempty | Caller prose; not proved |
| claim `kind` | string | — | `computed`, `cited`, `argued` | How the claim is admitted |
| claim `depends_on` | array of ids | — | each id defined; no cycle | Prerequisites |
| claim `check` | object `{kernel, args, expect}` or `null` | — | object only for `computed` | Finite check (§1.2) |

Output record per selected claim (stdout):

| Name | Type | Units | Range | Meaning |
|---|---|---|---|---|
| `claim_id` | string | — | claim id | Which claim |
| `status` | string | — | `certified`, `refuted`, `blocked`, `unchecked`, `cited`, `argued` | Gate result. `certified`: check passed with matching receipt and all ancestors certified or cited. `refuted`: verdict FAIL and value mismatch. `blocked`: check passed but an ancestor is not certified or cited. `unchecked`: no valid receipt (missing, altered, stale or ERROR) |
| `evidence` | `Evidence` object or `null` | — | — | Receipt for computed claims |

`Evidence` record (dataclass in `fm_research/problem.py`):

| Field | Type | Units | Meaning |
|---|---|---|---|
| `claim_id` | string | — | Claim the receipt belongs to |
| `kernel` | string | — | Kernel name from `KERNELS` |
| `args_sha256` | SHA-256 | — | Digest of canonical JSON of `check.args` |
| `expected` | JSON value | dimensionless | Copy of `check.expect` |
| `observed` | JSON value | dimensionless | Kernel output, or `{"error", "message"}` |
| `verdict` | string | — | `PASS`, `FAIL` or `ERROR` |
| `output_sha256` | SHA-256 | — | Digest of canonical JSON of `observed` |
| `kernel_source_sha256` | SHA-256 | — | `fm-research-source/2` identity of the 17 selected source files ([source binding](../SOURCE-BINDING.md)) |
| `fm_research_commit` | string | — | Output of `git rev-parse HEAD` run in the repository directory, or `unknown`. See defect D1 in the [assurance record](../assurance/assurance-record.md): it can name an enclosing repository |
| `python_version` | string | — | `platform.python_version()` |

`RankCertificate` (dataclass in `fm_research/rank.py`):

| Field | Type | Units | Meaning |
|---|---|---|---|
| `field` | string | — | `Q`, `Q(sqrt d)` or `F_p` |
| `rows`, `cols` | integer | count | Matrix shape |
| `rank` | integer | count | Claimed rank, 0 ≤ rank ≤ min(rows, cols) |
| `pivot_rows`, `pivot_cols` | tuple of integers | index | Rows and columns of a nonsingular rank × rank minor |
| `matrix_sha256` | SHA-256 | — | Digest of the compact JSON encoding of the input entries |
| `modulus` | integer or null | — | Prime p for F_p, otherwise null |

### 2.2 Characters and bundles

| Name | Type | Units | Range / limits | Meaning | Defined in |
|---|---|---|---|---|---|
| `QuadraticElement` fields `a`, `b`, `d` | `Fraction`, `Fraction`, `int` | dimensionless | `d` squarefree, not 0 or 1 | The number a + b·sqrt(d) | `fm_research/field.py` |
| `Rep` field `multiplicities` | tuple of 9 integers | multiplicity | each at most 256 bits (vendor `VirtualCharacter`) | Virtual character in `LABELS` order | `fm_research/twoi.py` |
| `ALIASES` | dict | — | `W'` and `Wprime` → `Wp` | Accepted alternative labels | `fm_research/twoi.py` |
| `DIMS` | dict | count | 1, 2, 3, 4, 5, 6, 4, 2, 3 | Dimension of each irrep | `fm_research/twoi.py` (from catalog) |
| `CENTER_SIGN` | dict | — | ±1 | Scalar by which the central element acts | `fm_research/twoi.py` (from catalog) |
| `Block` fields `irrep`, `twist`, `multiplicity` | string, int, int | twist: degree of O(t); multiplicity: count | twist in [−64, 64]; multiplicity in [0, 1,000,000] | One summand multiplicity·(O(twist) ⊗ irrep) | `fm_research/p1.py` |
| `cohomology` row keys | dict | — | `h0`, `h1` (`Rep`), `h0_dim`, `h1_dim`, `rank`, `degree` (integers, counts) | rank and degree describe the original bundle F | `fm_research/p1.py` |

### 2.3 Evidence mapper (`fm-evidence-paper/1` in, `fm-evidence-map/1` out)

The full closed input schema, scopes, checks and dispositions are defined in the [mapper contract](../EVIDENCE-PAPER.md). Every field there is required; this table lists the constants and outputs that the code defines.

| Name | Type | Units | Value / range | Meaning | Defined in |
|---|---|---|---|---|---|
| `SCHEMA` | string | — | `fm-evidence-paper/1` | Required bundle schema | `fm_mapper/core.py` |
| `SCOPES` | set of strings | — | nine scopes, e.g. `finite_computation`, `empirical_validation` | Allowed judgment scopes | `fm_mapper/core.py` |
| `SUPPORT` | dict | — | evidence kind → allowed supported scopes | Which evidence kinds can support which scopes | `fm_mapper/core.py` |
| `CHECKS` | set of strings | — | seven check names | Allowed judgment `checks` keys | `fm_mapper/core.py` |
| `REQUIRED` | dict | — | scope → checks that must be `passed` | Checks required per scope | `fm_mapper/core.py` |
| `SchemaError` | exception | — | subclass of `ValueError` | Malformed or ambiguous input; never a scientific refutation | `fm_mapper/core.py` |
| Map output keys | object | — | `schema`, `bundle_sha256`, `problem_sha256`, `problem`, `paper_state`, `truth_boundary`, `claims`, `obligations`, `artifact_integrity`, `artifacts`, `evidence`, `judgments`, `attempts`, `costs`, `paper`, `summary`, `limitations` | `paper_state` is always `draft_not_scientifically_accepted` | `fm_mapper/core.py` `map_evidence` |
| `summary` keys | object | count | `proposed_claims`, `dispositions`, `attempts_recorded`, `obligations_open`, `costs_unknown`, `cost_coverage` | Bookkeeping counts, not a benchmark | `fm_mapper/core.py` |
| Cost `value` | number or null | caller-declared in the cost's `unit` field | finite, ≥ 0; null = unknown | Reported as supplied, never extrapolated | [mapper contract](../EVIDENCE-PAPER.md) |

### 2.4 Affine certificates (`fm_certificates`)

A row `(a_1, …, a_n, c)` means the inequality a·x + c ≤ 0 over real x. All values dimensionless exact rationals.

| Name | Type | Units | Range / limits | Meaning |
|---|---|---|---|---|
| `AffineSystem` field `context` | string | — | nonempty after strip, ≤ 128 characters | Caller label bound into the digest |
| `AffineSystem` field `dimension` | int | coordinates | 1 to `MAX_DIMENSION` (16) | Number of real coordinates n |
| `AffineSystem` field `inequalities` | tuple of tuples | — | ≤ `MAX_INEQUALITIES` (128) rows of n + 1 values, each ≤ `INPUT_BITS` | Rows (coefficients then constant) |
| `Implication` field `system_digest` | SHA-256 | — | must equal `system_digest(system)` | Statement binding |
| `Implication` field `target` | tuple | — | n + 1 values ≤ `INPUT_BITS` | Target row b·x + d ≤ 0 |
| `Implication` / `Infeasibility` field `multipliers` | tuple | — | one per row, ≥ 0, ≤ `WITNESS_BITS` | Nonnegative combination weights |
| `Unsupported` | exception | — | subclass of `ValueError` | Input outside the supported shape or limits |
| `InvalidCertificate` | exception | — | subclass of `ValueError` | Supplied witness did not verify |

### 2.5 Scalar control (`fm_control.scalar`)

The model is x_next = x + gain·u + drift with measurement y = x + e, |e| ≤ noise_bound. Values are converted with `Fraction(value)`, so a float becomes its exact binary value; use integers, `Fraction` or decimal strings such as `"0.1"` for decimal intent.

| Parameter | Type | Units | Meaning |
|---|---|---|---|
| `x` | rational | caller's state unit | Current state |
| `gain` | rational | state unit per action unit | Effect of one action unit on the next state |
| `drift` | rational | state unit | Additive change per step |
| `target` | interval (lo, hi) | state unit | Safe set for x_next |
| `admissible` | interval (lo, hi) | action unit | Allowed actions u |
| `observed` | rational | state unit | Measurement y |
| `noise_bound` | rational ≥ 0 | state unit | Bound on |e| |
| `models` | sequence of exactly two `(x, gain, drift)` | as above | Candidate models |

State, target, drift, observation and noise must share one unit; gain·action must have that unit. No unit conversion or dimensional analysis is done; gauge and absolute pressures, for example, must not be mixed.

### 2.6 Affine-query witnesses (`fm_identifiability`)

The fiber is F = {x : C x = z, L x ≤ h} and the query is f(x) = d + q·x. All values dimensionless exact rationals in built-in tuples.

| Name | Type | Units | Range / limits | Meaning |
|---|---|---|---|---|
| `Model` field `C` | tuple of rows | — | ≤ `MAX_ROWS` (64) rows of length n | Equality coefficients |
| `Model` field `z` | tuple | — | one per row of `C` | Equality right-hand side |
| `Model` field `L` | tuple of rows | — | ≤ 64 rows of length n | Inequality coefficients |
| `Model` field `h` | tuple | — | one per row of `L` | Inequality bounds |
| `Model` field `q` | tuple | coordinates | n ≤ `MAX_DIMENSION` (32) | Query coefficients |
| `Model` field `d` | rational | — | ≤ `MAX_INPUT_BITS` | Query offset (default 0) |
| `Model` field `digest` | SHA-256 | — | computed | `fm-identifiability/1` digest of C, z, L, h, q, d |
| `PairWitness` fields `model_digest`, `first`, `second` | SHA-256, tuple, tuple | — | points of length n | Two supplied points |
| `ConstancyWitness` fields `model_digest`, `anchor`, `multipliers` | SHA-256, tuple, tuple | — | anchor length n; one multiplier per row of `C` | Feasible anchor and λ with λC = q |
| `PairResult` fields `model_digest`, `status`, `values` | SHA-256, string, tuple or None | — | `query_distinct`, `same_query`, `invalid_witness` | Result; `values` are f at both points |
| `ConstancyResult` fields `model_digest`, `status`, `value` | SHA-256, string, `Fraction` or None | — | `constant_on_fiber`, `invalid_witness` | Result; `value` = d + λz |

Every input rational is limited to `MAX_INPUT_BITS` (256) and every intermediate to `MAX_WORK_BITS` (16,384).

### 2.7 Interval residual enclosures (`fm_enclosures`)

| Name | Type | Units | Range / limits | Meaning |
|---|---|---|---|---|
| `matrix` argument | list/tuple of rows of `(lower, upper)` | dimensionless | square, 1 to `MAX_DIMENSION` (16) | Independent interval coefficients of A |
| `candidate` argument | list/tuple of rationals | dimensionless | length n | Fixed vector x |
| `rhs` argument | list/tuple of `(lower, upper)` | dimensionless | length n | Independent interval right-hand side b |
| `LinearResidualEnclosure` field `residuals` | tuple of `(Fraction, Fraction)` | dimensionless | one per row | Sharp range of (A x − b)_i |
| field `residual_norm_upper` | `Fraction` | dimensionless | ≥ 0 | Largest absolute residual endpoint R |
| field `dominance_margin` | `Fraction` | dimensionless | any sign | β = min_i (min_abs(A_ii) − Σ_{j≠i} max_abs(A_ij)) |
| field `forward_error_upper` | `Fraction` or None | dimensionless | R/β when β > 0 | Bound on the infinity-norm distance to the exact solution |
| field `forward_status` | string | — | `bounded`, `unresolved` | Whether the bound exists |
| `EnclosureLimitError` | exception | — | subclass of `ValueError` | Dimension, text or bit limit exceeded |

Rational inputs: `int`, reduced `Fraction`, or ASCII strings matching `[+-]?[0-9]+(?:/[0-9]+)?` with a positive denominator.

## 3. Records and files

| Record / file | Format | Schema | Producer | Consumer | Retention |
|---|---|---|---|---|---|
| ProblemSpec file | JSON | `fm-research-problem/1` (§2.1) | Caller | `fm_research` | Caller's |
| Research stdout | JSON lines | §2.1 output record | `fm_research` | Caller | Not stored |
| `--evidence-out` file | JSON lines, one `Evidence` per computed claim in spec order | §2.1 | `fm_research` | Caller, `gate` | Caller's; replaced on rerun |
| Evidence bundle | JSON, UTF-8, ≤ 8 MiB | `fm-evidence-paper/1` ([contract](../EVIDENCE-PAPER.md)) | Caller | `fm_mapper` | Caller's |
| Artifacts | any bytes, ≤ 8 MiB in total | SHA-256 declared in the bundle | Caller | `fm_mapper` | Caller's |
| Map JSON | JSON, indented, sorted keys | `fm-evidence-map/1` (§2.3) | `fm_mapper` | Caller | Fresh file only |
| Paper | Markdown | heading `# Foundation Math evidence report` | `fm_mapper` | Caller | Fresh file only |
| `SOURCE-MANIFEST.json` | JSON | `foundation-math-explicit-source-manifest/1`: `candidate`, `catalog_sha256`, `files` (rows `path`, `bytes`, `sha256`, optional `byte_preserved`, `source_sha256`, `source_git_blob_sha1`), `license`, `license_scope`, `release_kind`, `schema`, `self_binding`, `source_binding_format` | `tools/refresh_manifest.py` | `tools/package_source.py` | In Git |
| `PACKAGE.json` | JSON | release metadata: `name`, `candidate`, `distribution`, `python_requires`, `dependencies`, `license`, `capabilities`, `scientific_acceptance`, `release_kind`, `source_binding_format` | Maintainer | Readers, VDD generator | In Git |
| Source ZIP | ZIP, stored, entries under `foundation-math/`, timestamp 2026-10-26 00:00:00, mode 0644 | manifest file set | `tools/package_source.py` | Release | Caller's |
| Vendor requests and certificates | JSON | `fm-character-request-v1`, `fm-character-certificate-v1`, `fm-split-bundle-request-v1`, `fm-split-bundle-certificate-v1` | `fm_research` internally | vendor producers and verifiers | Not stored |

## 4. Reference data provenance

Foundation Math embeds one reference data table. Every other data file is synthetic.

| Table | Source (edition/date) | Units | Transformation | Validation test |
|---|---|---|---|---|
| `vendor/foundation-math-v014/character_ring/catalog.json` — character table of SL2(F5) | First-party Foundation Math v0.14 selected source subset, byte-preserved (manifest row `byte_preserved: true`). SHA-256 `84ceb37bc32d10c4908e5b5f1f2f5994082074f2c2a9f36c846347750c79fa74`, pinned as `CATALOG_SHA256` in `character_ring/contract.py` and `catalog_sha256` in the manifest. The repository records no external bibliographic source; the file's own `mathematical_input` field says the identification of the table with the group is assumed, not proved | Dimensionless (exact complex character values in Q(sqrt5); integer class sizes and multiplicities) | None; read as is after the digest check | `tests/test_kernels.py::SmallKernelTests.test_low_degree_characters_and_catalog_pin` runs the vendor `check_catalog`, which checks the pin, the labels, dimensions and center signs, class sizes summing to 120, the W trace, orthonormality of all 81 character pairs, the sum of squared dimensions, the symmetric-power marking of the first six irreps, P, Wp, V, and every fusion entry against class inner products |
| `examples/research-regression.problem.json` | Synthetic, authored for the repository | dimensionless | — | `tests/test_problem.py` |
| `examples/evidence-mapper/legacy-conditional.json`, `record.txt` | Synthetic, byte-preserved from the corrected mapper v2 (see [PROVENANCE.md](../../PROVENANCE.md)) | — | — | `tests/test_mapper.py` |
| `tests/fixtures/false-claim.problem.json` | Synthetic, deliberately false expectation | dimensionless | — | `tests/test_problem.py::ProblemTests.test_standalone_cli` |

Catalog fields:

| Key | Type | Units | Meaning |
|---|---|---|---|
| `schema` | string | — | `fm-sl2f5-catalog-v1` |
| `group` | string | — | `SL2(F5)` |
| `group_order` | integer | count | 120 |
| `labels` | 9 strings | — | Physical irrep labels, equal to `LABELS` |
| `dimensions` | 9 integers | count | 1, 2, 3, 4, 5, 6, 4, 2, 3 |
| `center_signs` | 9 integers | — | ±1 action of the central element |
| `classes` | 9 objects `{id, size, W_trace}` | size: count of elements | Conjugacy classes (`identity`, `center`, `order4`, `trace1`, `trace_minus1`, `trace_phi`, `trace_minus_phi`, `trace_phi_conjugate`, `trace_minus_phi_conjugate`); sizes 1, 1, 30, 20, 20, 12, 12, 12, 12; `W_trace` encoded like `characters` |
| `characters` | 9 × 9 × 4 integers | dimensionless | Entry `[p, q, r, s]` is the value p/q + (r/s)·sqrt5 of irrep i on class j |
| `fusion` | 9 × 9 × 9 integers | multiplicity | `fusion[i][j][k]` = multiplicity of irrep k in irrep i ⊗ irrep j |
| `mathematical_input` | string | — | Statement that the identification with the group is an assumption |

## 5. Configuration keys

Not applicable. The software reads no configuration file and no environment variable. Behaviour is set only by command-line arguments (§1.1) and function parameters (§1.3). `vendor.py` locates the vendor directory as `VENDOR` by walking up from its own file to the first parent containing `vendor/foundation-math-v014`.

## 6. Operational limits

| Limit | Value | Enforced in | Test |
|---|---|---|---|
| Symmetric-power degree | 0–256 | `fm_research/twoi.py` `_degree`; vendor `symmetric_degree` | Gap GAP-MATH-002 (upper bound untested) |
| F_p modulus | prime in [2, 10^12] | `fm_research/rank.py` `_prepare` | composite case in `test_new_small_rank_witnesses_and_tampering`; bound is GAP-MATH-004 |
| Bundle block twist / multiplicity | [−64, 64] / [0, 1,000,000] | `fm_research/p1.py` `Block`; vendor contract | GAP-MATH-003 |
| ProblemSpec identifiers | ≤ 128 characters | `fm_research/problem.py` `_id` | `test_validation` |
| Mapper `MAX_BYTES` | 8,388,608 bytes (bundle; and artifacts in total) | `fm_mapper/core.py` | GAP-MATH-005 |
| Mapper `MAX_ITEMS` | 1,000 items per collection | `fm_mapper/core.py` | GAP-MATH-005 |
| Mapper text | 32,768 characters | `fm_mapper/core.py` `_text` | GAP-MATH-005 |
| Affine `MAX_DIMENSION` | 16 coordinates | `fm_certificates/affine.py` | `test_inclusive_resource_limits` |
| Affine `MAX_INEQUALITIES` | 128 rows (and 128 inner proofs in composition) | `fm_certificates/affine.py` | `test_inclusive_resource_limits` |
| Affine `INPUT_BITS` | 256 bits | `fm_certificates/affine.py` | `test_inclusive_resource_limits` |
| Affine `WITNESS_BITS` | 4,096 bits | `fm_certificates/affine.py` | `test_malformed_and_exact_type_boundaries` (2^4096 rejected) |
| Affine `ARITHMETIC_BITS` | 8,192 bits | `fm_certificates/affine.py` | none (GAP-MATH-012) |
| Query `MAX_DIMENSION` | 32 coordinates | `fm_identifiability/__init__.py` | `test_limit_boundaries`, `test_bad_types_dimensions_and_limits` |
| Query `MAX_ROWS` | 64 equality rows, 64 inequality rows | `fm_identifiability/__init__.py` | `test_limit_boundaries` |
| Query `MAX_INPUT_BITS` | 256 bits | `fm_identifiability/__init__.py` | `test_limit_boundaries` |
| Query `MAX_WORK_BITS` | 16,384 bits | `fm_identifiability/__init__.py` | `test_intermediate_resource_limit` |
| Enclosure `MAX_DIMENSION` | 16 | `fm_enclosures/numerical.py` | `test_shapes_and_limits` |
| Enclosure `MAX_INPUT_BITS` | 256 bits | `fm_enclosures/numerical.py` | `test_shapes_and_limits`, `test_bad_rationals` |
| Enclosure `MAX_TEXT_LENGTH` | 160 characters | `fm_enclosures/numerical.py` | `test_bad_rationals` |
| Enclosure `MAX_INTERMEDIATE_BITS` | 16,384 bits | `fm_enclosures/numerical.py` | `test_intermediate_limit` |
| `git rev-parse` timeout | 5 seconds | `fm_research/problem.py` `run_check` | none |

Vendor budgets (constants in the byte-preserved vendor contracts; units in brackets):

| Character ring `BUDGETS` key | Value | Split bundle `BUDGETS` key | Value |
|---|---|---|---|
| `request_bytes` | 65,536 [bytes] | `request_bytes` | 65,536 [bytes] |
| `certificate_bytes` | 262,144 [bytes] | `certificate_bytes` | 262,144 [bytes] |
| `nodes` | 127 [expression nodes] | `blocks_per_bundle` | 32 [blocks] |
| `depth` | 16 [expression depth] | `requested_twists` | 32 [twists] |
| `symmetric_degree` | 256 [degree] | `symmetric_degree` | 128 [degree] |
| `input_coefficient_bits` | 63 [bits] | `absolute_block_twist` | 64 [degree] |
| `result_coefficient_bits` | 256 [bits] | `absolute_requested_twist` | 64 [degree] |
| `field_component_bits` | 272 [bits] | `multiplicity` | 1,000,000 [count] |
| `json_integer_digits` | 90 [digits] | `result_bits` | 128 [bits] |
| `certificate_data_depth` | 32 [nesting] | `data_depth` | 16 [nesting] |
| `certificate_data_values` | 8,192 [values] | `data_values` | 8,192 [values] |
| | | `string_length` | 256 [characters] |
| | | `integer_bits` | 300 [bits] |

## Change history

| Version | Date | Commit | Change | Reviewed in |
|---|---|---|---|---|
| 1.0 | 2026-11-08 | `53a58dd` | Initial data dictionary | PR #30 |
