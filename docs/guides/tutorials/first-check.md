# Tutorial: your first finite check

This tutorial takes about five minutes. You write a small ProblemSpec, run it, see one claim refuted, and see how a refuted prerequisite blocks a dependent claim. You need Python 3.10 or later and a clone of this repository. Nothing is installed.

Run every command from the repository root.

## 1. Make a scratch folder

```sh
work=$(mktemp -d)
```

## 2. Write a ProblemSpec

Save this as `$work/first.json`. It has two computed claims. The second depends on the first.

```sh
cat > "$work/first.json" <<'EOF'
{
  "schema": "fm-research-problem/1",
  "problem_id": "tutorial-first-check",
  "title": "Tutorial: a first finite check",
  "objective": "Learn how claims, checks and dependencies are gated.",
  "repo": {"name": "local", "commit": "not-recorded"},
  "roles": {"builder": "me", "reviewer": "me", "verifier": "local kernels"},
  "assumptions": ["The pinned catalog's identification with SL2(F5) is assumed."],
  "exclusions": ["No research claim is made."],
  "claims": [
    {"id": "w-squared", "statement": "W tensor W decomposes as 1 + A.", "kind": "computed",
     "depends_on": [], "check": {"kernel": "twoi.decompose_tensor", "args": {"factors": ["W", "W"]}, "expect": "1+A"}},
    {"id": "rank-two", "statement": "The matrix [[1, 2], [3, 4]] has rank 2 over Q.", "kind": "computed",
     "depends_on": ["w-squared"], "check": {"kernel": "rank", "args": {"field": "Q", "rows": [[1, 2], [3, 4]]}, "expect": 2}}
  ]
}
EOF
```

Every field is required. Numbers must be integers or `"n/d"` strings; a float such as `0.5` is rejected. The [data dictionary](../../data/data-dictionary.md#12-problemspec-kernels-kernels-in-fm_researchproblempy) lists every kernel and its arguments.

## 3. Run it

```sh
python3 -S -B -m fm_research check "$work/first.json"
echo "exit $?"
```

You get one JSON line per claim. Both have `"status": "certified"` and an `evidence` record with `"verdict": "PASS"`. The exit status is 0.

`certified` means the finite check passed and every prerequisite is certified or cited. It does not mean the claim's prose is proved.

## 4. Make the first claim wrong

```sh
sed 's/"expect": "1+A"/"expect": "1+W"/' "$work/first.json" > "$work/wrong.json"
python3 -S -B -m fm_research check "$work/wrong.json"
echo "exit $?"
```

Now `w-squared` is `refuted` (verdict `FAIL`). `rank-two` still passes its own check (verdict `PASS`), but its status is `blocked`, because its prerequisite is not certified. The exit status is 1.

## 5. Keep the receipts

```sh
python3 -S -B -m fm_research check "$work/first.json" --claim rank-two --evidence-out "$work/evidence.jsonl"
wc -l < "$work/evidence.jsonl"
```

Only `rank-two` is printed, but its prerequisite `w-squared` is also run, so the receipt file has 2 lines. Each receipt carries `kernel_source_sha256`. If any of the selected mathematical source files change, an old receipt no longer matches and the gate reports `unchecked` ([source binding](../../SOURCE-BINDING.md)).

## Next steps

- Map supplied evidence judgments into a draft report: [mapper contract](../../EVIDENCE-PAPER.md), then run `python3 -S -B -m fm_mapper examples/evidence-mapper/legacy-conditional.json`.
- Use the exact certificate APIs from Python: [Python API ICD](../../icd/icd-python-api.md).
- If something fails: [troubleshooting](../how-to/troubleshooting.md).

Last run end to end: 2026-11-08 at baseline commit `53a58dd`, Python 3.14.9, Linux. Step 3 printed two certified records (exit 0); step 4 printed `refuted` and `blocked` (exit 1); step 5 wrote 2 lines (exit 0).
