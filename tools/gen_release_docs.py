import argparse
import ast
import datetime
import hashlib
import io
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tokenize

from tools import check_trace
from tools.package_source import build

ROOT = Path(__file__).resolve().parents[1]
DISCLAIMER = (
    '> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&page_name=all), '
    '[NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the '
    '[NASA Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) '
    'documentation guidance. This is not a NASA compliance determination or certification. The software '
    'classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent '
    'verification and validation, or hazard analysis is asserted. The document describes the implementation '
    'inspected at the baseline commit.'
)
VERBOSE = re.compile(r'^(test\w*) \(([\w.]+)\)(?: \.\.\.)? (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)$')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def run(command, **kwargs):
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, **kwargs)


def unit_run(optimized):
    command = [sys.executable, '-S', '-B', *(['-O'] if optimized else []), '-m', 'unittest',
               'discover', '-s', 'tests', '-t', '.', '-v']
    result = run(command)
    outcomes = {}
    for line in result.stderr.splitlines():
        match = VERBOSE.match(line)
        if match:
            name, dotted, outcome = match.groups()
            module, cls, method = dotted.rsplit('.', 2)
            outcomes[(module.replace('.', '/') + '.py', cls, method)] = outcome.split()[0]
    total = re.search(r'^Ran (\d+) tests?', result.stderr, flags=re.M)
    return {
        'command': ' '.join(['python3' if c == sys.executable else c for c in command]),
        'exit': result.returncode,
        'ran': int(total.group(1)) if total else 0,
        'outcomes': outcomes,
        'log_sha256': hashlib.sha256(result.stderr.encode()).hexdigest(),
    }


def coverage():
    with tempfile.TemporaryDirectory() as tmp:
        ignore = sorted({sys.prefix, sys.base_prefix, sys.exec_prefix})
        command = [sys.executable, '-S', '-B', '-m', 'trace', '--count', '--summary', '-C', tmp,
                   *[f'--ignore-dir={p}' for p in ignore], '--module', 'unittest', 'discover', '-s', 'tests', '-t', '.']
        result = run(command)
    rows = []
    for line in result.stdout.splitlines():
        match = re.match(r'^\s*(\d+)\s+([\d.]+)%\s+(\S+)\s+\((.+)\)$', line)
        if match and Path(match.group(4)).resolve().is_relative_to(ROOT):
            relative = Path(match.group(4)).resolve().relative_to(ROOT).as_posix()
            if not relative.startswith('tests/'):
                rows.append((relative, int(match.group(1)), float(match.group(2))))
    lines = sum(r[1] for r in rows)
    covered = sum(r[1] * r[2] / 100 for r in rows)
    return {'command': 'python3 -S -B -m trace --count --summary -C <tmp> --ignore-dir=<python prefix> --module unittest discover -s tests -t .',
            'exit': result.returncode, 'rows': sorted(rows), 'lines': lines,
            'percent': round(100 * covered / lines, 1) if lines else 0.0}


def python_files():
    return [p for p in git('ls-files', '*.py').splitlines() if p]


def code_rules():
    comments, docstrings = [], []
    for relative in python_files():
        source = (ROOT / relative).read_text(encoding='utf-8')
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT:
                comments.append(f'{relative}:{token.start[0]}')
        tree = ast.parse(source)
        for node in [tree, *ast.walk(tree)]:
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if ast.get_docstring(node, clean=False) is not None:
                    docstrings.append(relative)
    return comments, docstrings


def ruff(binary):
    if not binary:
        return None
    command = [binary, 'check', '--no-cache', '--isolated', '--select', 'E9,F', '--target-version', 'py310',
               '--output-format', 'concise', '--exit-zero', '.']
    result = run(command)
    findings = [line for line in result.stdout.splitlines() if re.match(r'^\S+:\d+:\d+: ', line)]
    version = run([binary, '--version']).stdout.strip()
    return {'command': 'ruff check --no-cache --isolated --select E9,F --target-version py310 .',
            'version': version, 'findings': findings}


def gitleaks(binary):
    if not binary:
        return None
    result = run([binary, 'git', '--no-banner', '--redact', '-c', '.gitleaks.toml', '--log-opts=HEAD', '.'])
    version = run([binary, 'version']).stdout.strip()
    return {'command': 'gitleaks git --no-banner --redact -c .gitleaks.toml --log-opts=HEAD .',
            'version': version, 'exit': result.returncode,
            'summary': ' '.join(re.sub(r'\x1b\[[0-9;]*m', '', l).split(None, 1)[-1]
                                for l in result.stderr.splitlines()[-2:])}


def package():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        source = tmp / 'source'
        source.mkdir()
        archive = subprocess.run(['git', 'archive', 'HEAD'], cwd=ROOT, capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(source, filter='data')
        first = build(source, tmp / 'first.zip')
        second = build(source, tmp / 'second.zip')
        same = (tmp / 'first.zip').read_bytes() == (tmp / 'second.zip').read_bytes()
        extracted = tmp / 'extracted'
        shutil.unpack_archive(tmp / 'first.zip', extracted)
        third = build(extracted / 'foundation-math', tmp / 'third.zip')
        same_extracted = (tmp / 'first.zip').read_bytes() == (tmp / 'third.zip').read_bytes()
    return {'first': first, 'rebuild_identical': same and first == second,
            'extracted_rebuild_identical': same_extracted and first == third}


def gh(*args):
    if not shutil.which('gh'):
        return None
    result = run(['gh', *args])
    return json.loads(result.stdout) if result.returncode == 0 else None


def line_counts():
    counts = {}
    for relative in git('ls-files').splitlines():
        suffix = Path(relative).suffix or Path(relative).name
        if suffix in ('.png',):
            continue
        counts.setdefault(suffix, [0, 0])
        counts[suffix][0] += 1
        counts[suffix][1] += len((ROOT / relative).read_bytes().splitlines())
    return dict(sorted(counts.items()))


def requirement_by_test():
    traced, _ = check_trace.matrix(ROOT)
    mapping = {}
    for rid, rows in traced.items():
        for row in rows:
            for ref in check_trace.TEST_REF.findall(' '.join(row)):
                mapping.setdefault(ref, set()).add(rid)
    return mapping


def header(title, doc_id, commit, date, applies, pr):
    return '\n'.join([
        f'# Foundation Math {title}', '',
        '| Field | Value |', '|---|---|',
        f'| Document ID | {doc_id} |', '| Version | 1.0 |', '| Status | Baselined |',
        '| Owner | Akilleez-QA maintainer |', f'| Date | {date} |', f'| Baseline commit | {commit} |',
        f'| Applies to | {applies} |',
        '| Classification | Self-assessed Class E analog; not safety-critical (see [SMP §1](../../plan/software-management-plan.md#1-software-classification-self-assessed)) |',
        '', DISCLAIMER, '',
        f'Generated by `python3 -S -B -m tools.gen_release_docs --pr {pr}` at commit `{commit}`. Do not edit by hand; rerun the generator.', '',
    ])


def history(date, commit, pr):
    return '\n'.join(['## Change history', '', '| Version | Date | Commit | Change | Reviewed in |',
                      '|---|---|---|---|---|', f'| 1.0 | {date} | `{commit[:7]}` | Generated initial record | PR #{pr} |', ''])


def collect(args):
    if git('status', '--porcelain'):
        raise SystemExit('Working tree is not clean; commit before generating release records.')
    meta = json.loads((ROOT / 'PACKAGE.json').read_text())
    problems, trace_summary = check_trace.check(ROOT)
    records, gaps = check_trace.requirements(ROOT)
    statuses = {}
    for items in records.values():
        status = items[0]['fields'].get('Status', 'missing')
        statuses[status] = statuses.get(status, 0) + 1
    srs = (ROOT / check_trace.SRS).read_text(encoding='utf-8')
    issues = gh('issue', 'list', '-R', args.repo, '--state', 'all', '--limit', '500', '--json', 'number,state,title,labels')
    prs = gh('pr', 'list', '-R', args.repo, '--state', 'merged', '--limit', '500', '--json', 'number,reviews,comments')
    return {
        'commit': git('rev-parse', 'HEAD'),
        'tree': git('rev-parse', 'HEAD^{tree}'),
        'commit_date': git('show', '-s', '--format=%cs', 'HEAD'),
        'generated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'candidate': meta['candidate'],
        'tags': git('tag', '--list').split(),
        'commits': git('log', '--format=%h %cs %s').splitlines(),
        'environment': f'{platform.system()} {platform.release()} {platform.machine()}; Python {platform.python_version()}',
        'normal': unit_run(False),
        'optimized': unit_run(True),
        'trace_problems': problems,
        'trace': trace_summary,
        'statuses': statuses,
        'gaps': sorted(set(gaps)),
        'tbd': sorted(set(re.findall(r'TBD-MATH-\d{3}', srs))),
        'coverage': coverage(),
        'code_rules': code_rules(),
        'ruff': ruff(args.ruff),
        'gitleaks': gitleaks(args.gitleaks),
        'package': package(),
        'manifest_sha256': hashlib.sha256((ROOT / 'SOURCE-MANIFEST.json').read_bytes()).hexdigest(),
        'manifest_rows': len(json.loads((ROOT / 'SOURCE-MANIFEST.json').read_text())['files']),
        'catalog_sha256': json.loads((ROOT / 'SOURCE-MANIFEST.json').read_text())['catalog_sha256'],
        'issues': issues,
        'prs': prs,
        'lines': line_counts(),
        'requirement_by_test': requirement_by_test(),
    }


def severity_counts(issues, state):
    counts = {}
    for issue in issues or []:
        if issue['state'] != state:
            continue
        labels = [l['name'] for l in issue['labels'] if re.fullmatch(r'S[1-4]', l['name'])]
        key = labels[0] if labels else 'unlabelled'
        counts[key] = counts.get(key, 0) + 1
    return counts


def str_report(d, pr):
    c = d['commit']
    n, o = d['normal'], d['optimized']
    passed = lambda run_: sum(v == 'ok' for v in run_['outcomes'].values())
    failed = lambda run_: sum(v in ('FAIL', 'ERROR') for v in run_['outcomes'].values())
    skipped = lambda run_: sum(v == 'skipped' for v in run_['outcomes'].values())
    ok = n['exit'] == 0 and o['exit'] == 0 and not d['trace_problems']
    lines = [header(f'test report STR-{d["candidate"]}', f'FMATH-STR-{d["candidate"]}', c, d['commit_date'],
                    f'foundation-math source candidate `{d["candidate"]}` at commit `{c[:7]}` (no release tag exists)', pr)]
    lines += ['## 1. Summary', '',
              f'- Conclusion: {"all automated checks passed" if ok else "at least one automated check failed; see section 4"} at commit `{c}`.',
              f'- Normal suite: {passed(n)} passed, {failed(n)} failed, {skipped(n)} skipped of {n["ran"]} run (exit {n["exit"]}).',
              f'- Optimized suite (`-O`): {passed(o)} passed, {failed(o)} failed, {skipped(o)} skipped of {o["ran"]} run (exit {o["exit"]}).',
              f'- Trace check: {d["trace"]["traced_requirements"]} of {d["trace"]["requirements"]} requirements traced; {d["trace"]["untested_gaps"]} untested requirement gaps listed in the SRS; {len(d["trace_problems"])} trace problems.',
              '- Remaining deficiencies: the untested requirement gaps in [SRS §9](../../requirements/requirements.md#9-untested-behaviour-requirement-gaps); the code findings in the [assurance record](../../assurance/assurance-record.md).',
              '- Test-environment impact: one local Linux machine and one Python version per run. GitHub CI runs Python 3.12 on `ubuntu-latest`; see the [test plan](../test-plan.md#3-test-environment).',
              '', '## 2. Test log', '', '| Item | Value |', '|---|---|',
              f'| Commit | `{c}` (tree `{d["tree"]}`) |', f'| Tag | {", ".join(d["tags"]) or "none; the repository has no tags"} |',
              f'| Generated | {d["generated"]} |', f'| Environment | {d["environment"]} |',
              '| Run by | operator, local `tools/gen_release_docs.py` |',
              f'| Normal command / log SHA-256 | `{n["command"]}` / `{n["log_sha256"]}` |',
              f'| Optimized command / log SHA-256 | `{o["command"]}` / `{o["log_sha256"]}` |',
              '', '## 3. Results', '',
              'One row per test method. Requirements come from the [verification matrix](../verification-matrix.md); "supporting" means the test is classified there without a requirement.', '',
              '| Test | Requirements | Normal | Optimized |', '|---|---|---|---|']
    tests = sorted(set(n['outcomes']) | set(o['outcomes']))
    for ref in tests:
        reqs = ', '.join(sorted(d['requirement_by_test'].get(ref, ()))) or 'supporting'
        lines.append(f'| `{ref[0]}::{ref[1]}.{ref[2]}` | {reqs} | {n["outcomes"].get(ref, "not run")} | {o["outcomes"].get(ref, "not run")} |')
    lines += ['', '## 4. Problems and deviations', '']
    problems = [f'| Normal suite | exit {n["exit"]} | — | Investigate |'] if n['exit'] else []
    problems += [f'| Optimized suite | exit {o["exit"]} | — | Investigate |'] if o['exit'] else []
    problems += [f'| Trace check | {p} | — | Fix docs |' for p in d['trace_problems']]
    if problems:
        lines += ['| Item | Description | Issue | Disposition |', '|---|---|---|---|', *problems]
    else:
        lines.append('None. No test failed, errored or was skipped, and the trace check reported no problems.')
    cov = d['coverage']
    issues = d['issues']
    open_sev = severity_counts(issues, 'OPEN')
    closed = sum(1 for i in issues or [] if i['state'] == 'CLOSED')
    prs = d['prs']
    reviewed = sum(1 for p in prs or [] if p['reviews'] or p['comments'])
    comments, docstrings = d['code_rules']
    r = d['ruff']
    lines += ['', '## 5. Metrics', '', 'Every value below was produced by the generator at the commit above.', '',
              '| Measure | Value | Command |', '|---|---|---|',
              f'| Tests run / passed / failed / skipped (normal) | {n["ran"]} / {passed(n)} / {failed(n)} / {skipped(n)} | `{n["command"]}` |',
              f'| Tests run / passed / failed / skipped (optimized) | {o["ran"]} / {passed(o)} / {failed(o)} / {skipped(o)} | `{o["command"]}` |',
              f'| Requirements total / traced / untested gaps / TBD | {d["trace"]["requirements"]} / {d["trace"]["traced_requirements"]} / {len(d["gaps"])} / {len(d["tbd"])} | `python3 -S -B -m tools.check_trace` |',
              f'| Requirement status counts | {", ".join(f"{k}: {v}" for k, v in sorted(d["statuses"].items()))} | SRS parse |',
              '| Requirement changes since previous tag | not applicable: no previous tag | `git tag --list` |',
              f'| Issues open by severity | {json.dumps(open_sev, sort_keys=True) if issues is not None else "not queried"} | `gh issue list --state all` |',
              f'| Issues closed (all time) | {closed if issues is not None else "not queried"} | `gh issue list --state all` |',
              f'| PRs merged / with review or comment activity | {len(prs) if prs is not None else "not queried"} / {reviewed if prs is not None else "not queried"} | `gh pr list --state merged` |',
              f'| Static analysis: ruff pyflakes and syntax rules (E9, F) | {len(r["findings"]) if r else "not run"} findings | `{r["command"] if r else "ruff not supplied"}` ({r["version"] if r else "n/a"}) |',
              f'| Code rule: `#` comments in tracked Python | {len(comments)} | tokenize scan in generator |',
              f'| Code rule: docstrings in tracked Python | {len(docstrings)} in {len(set(docstrings))} files | ast scan in generator |',
              f'| Secret scan | {d["gitleaks"]["summary"] if d["gitleaks"] else "not run"} (exit {d["gitleaks"]["exit"] if d["gitleaks"] else "n/a"}) | `{d["gitleaks"]["command"] if d["gitleaks"] else "gitleaks not supplied"}` |',
              f'| Line coverage of non-test Python (in-process only) | {cov["percent"]}% of {cov["lines"]} executable lines (exit {cov["exit"]}) | `{cov["command"]}` |',
              f'| Tracked files / lines by type | {"; ".join(f"{k} {v[0]} files, {v[1]} lines" for k, v in d["lines"].items())} | `git ls-files` line count |',
              '', 'Coverage counts only code executed inside the test process. CLI subprocesses started by tests are not counted. Per-module values:', '',
              '| Module | Executable lines | Covered |', '|---|---|---|']
    lines += [f'| `{path}` | {count} | {pct}% |' for path, count, pct in cov['rows']]
    if r and r['findings']:
        lines += ['', 'Ruff findings (recorded, not fixed in this record):', '', '```text', *r['findings'], '```']
    lines += ['', '## 6. Rationale for decisions', '',
              'No failure was accepted. Results apply only to the commit and environment above; they do not transfer to a later tree. '
              'Author tests are not independent review or mathematical acceptance.', '', history(d['commit_date'], c, pr)]
    return '\n'.join(lines)


def vdd_report(d, pr):
    c = d['commit']
    p = d['package']
    changelog = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
    unreleased = changelog.split('## [Unreleased]', 1)[1].split('\n## ', 1)[0].strip() if '## [Unreleased]' in changelog else 'No Unreleased section.'
    lines = [header(f'version description VDD-{d["candidate"]}', f'FMATH-VDD-{d["candidate"]}', c, d['commit_date'],
                    f'foundation-math source candidate `{d["candidate"]}` at commit `{c[:7]}` (no release tag exists)', pr)]
    lines += ['## 1. Identification', '', '| Item | Value |', '|---|---|',
              '| Name | foundation-math |', f'| Version | source candidate `{d["candidate"]}` (from `PACKAGE.json`; not a SemVer release) |',
              f'| Tag | {", ".join(d["tags"]) or "none; no tag has been authorized"} |', f'| Commit | `{c}` |',
              '| Previous tag | none |', f'| Commit date | {d["commit_date"]} |',
              '', '## 2. Contents', '',
              f'- Explicit-allowlist source ZIP built from `git archive HEAD`: {p["first"]["file_count"]} files including `SOURCE-MANIFEST.json`.',
              '- Runtime packages: `fm_research`, `fm_mapper`, `fm_control`, `fm_certificates`, `fm_identifiability`, `fm_enclosures`.',
              '- Selected historical vendor subset `vendor/foundation-math-v014/` (character ring and split bundle; not the full v0.14 distribution).',
              '- Synthetic examples, unit tests, packaging and documentation tools, and the documentation tree.',
              '- Excluded from the ZIP by `tools/package_source.py`: `.github/`, `AGENTS.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`.',
              '', '## 3. Build and install', '',
              'No installation step exists. Python 3.10 or later with the standard library is the only requirement. Build the source ZIP with the [source packaging guide](../guides/how-to/source-package.md):', '',
              '```sh', 'package_work=$(mktemp -d)', 'mkdir "$package_work/source"', 'git archive HEAD | tar -x -C "$package_work/source"',
              'python3 -S -B "$package_work/source/tools/package_source.py" "$package_work/first.zip"', '```',
              '', '## 4. Integrity', '', '| Artifact / manifest | SHA-256 | Notes |', '|---|---|---|',
              f'| Source ZIP from `git archive {c[:7]}` | `{p["first"]["sha256"]}` | {p["first"]["bytes"]} bytes; rebuild identical: {p["rebuild_identical"]}; rebuild from extracted ZIP identical: {p["extracted_rebuild_identical"]} |',
              f'| `SOURCE-MANIFEST.json` | `{d["manifest_sha256"]}` | {d["manifest_rows"]} rows; the manifest is not self-pinned, so this external digest binds it |',
              f'| `vendor/foundation-math-v014/character_ring/catalog.json` | `{d["catalog_sha256"]}` | Pinned in `character_ring/contract.py` and in the manifest |',
              '', '## 5. Changes', '',
              'No previous tag exists, so this first record lists the whole history. CHANGELOG `[Unreleased]` section at this commit:', '',
              *['> ' + l if l else '>' for l in unreleased.splitlines()], '',
              f'Commits reachable from `{c[:7]}` ({len(d["commits"])}):', '', '```text', *d['commits'], '```',
              '', '## 6. Open problems and workarounds', '']
    open_issues = [i for i in d['issues'] or [] if i['state'] == 'OPEN']
    if d['issues'] is None:
        lines.append('GitHub issues were not queried (gh unavailable).')
    elif open_issues:
        lines += ['| Issue | Severity | Title |', '|---|---|---|']
        lines += [f'| #{i["number"]} | {",".join(l["name"] for l in i["labels"]) or "unlabelled"} | {i["title"]} |' for i in open_issues]
    else:
        lines.append('No GitHub issues are open. Known defects and untested behaviour are recorded in the [assurance record](../assurance/assurance-record.md) and [SRS §9](../requirements/requirements.md#9-untested-behaviour-requirement-gaps).')
    lines += ['', '## 7. Documentation baseline', '',
              f'Control documents in `docs/` were checked against main at baseline commit `53a58dde072b1d3f92836a1365f88f364b880a33` and are contained in commit `{c[:7]}`. See the [documentation index](../README.md).',
              '', '## 8. Verification and scans', '',
              f'- Test report: [STR-{d["candidate"]}](../verification/reports/STR-{d["candidate"]}.md) (same commit).',
              f'- Secret scan: {d["gitleaks"]["summary"] if d["gitleaks"] else "not run locally"}; GitHub CI also runs the Gitleaks job.',
              f'- Static analysis: {len(d["ruff"]["findings"]) if d["ruff"] else "not run"} ruff E9/F findings; details in the STR.',
              '', history(d['commit_date'], c, pr)]
    return '\n'.join(lines).replace('](../../plan/software-management-plan.md', '](../plan/software-management-plan.md')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Generate the STR and VDD for the current source candidate.')
    parser.add_argument('--pr', required=True, help='pull request number that reviews the records')
    parser.add_argument('--repo', default='Akilleez-QA/foundation-math')
    parser.add_argument('--ruff', help='ruff binary (optional)')
    parser.add_argument('--gitleaks', default=shutil.which('gitleaks'), help='gitleaks binary (optional)')
    args = parser.parse_args(argv)
    data = collect(args)
    str_path = ROOT / f'docs/verification/reports/STR-{data["candidate"]}.md'
    vdd_path = ROOT / f'docs/releases/VDD-{data["candidate"]}.md'
    str_path.parent.mkdir(parents=True, exist_ok=True)
    vdd_path.parent.mkdir(parents=True, exist_ok=True)
    str_path.write_text(str_report(data, args.pr), encoding='utf-8')
    vdd_path.write_text(vdd_report(data, args.pr), encoding='utf-8')
    for index, path in ((str_path.parent / 'README.md', str_path), (vdd_path.parent / 'README.md', vdd_path)):
        row = f'| [{path.stem}]({path.name}) | `{data["candidate"]}` | `{data["commit"][:7]}` |'
        text = index.read_text(encoding='utf-8')
        lines = [l for l in text.splitlines() if not l.startswith(f'| [{path.stem}]')]
        index.write_text('\n'.join(lines + [row]) + '\n', encoding='utf-8')
    print(json.dumps({'str': str_path.relative_to(ROOT).as_posix(), 'vdd': vdd_path.relative_to(ROOT).as_posix(),
                      'normal_exit': data['normal']['exit'], 'optimized_exit': data['optimized']['exit'],
                      'trace_problems': len(data['trace_problems'])}, sort_keys=True))
    return 0 if data['normal']['exit'] == 0 and data['optimized']['exit'] == 0 and not data['trace_problems'] else 1


if __name__ == '__main__':
    sys.exit(main())
