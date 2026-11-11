import argparse
import ast
import dataclasses
import importlib
import json
from pathlib import Path
import re
import sys

from tools.package_source import excluded

SRS = 'docs/requirements/requirements.md'
SDD = 'docs/architecture/architecture.md'
VM = 'docs/verification/verification-matrix.md'
DD = 'docs/data/data-dictionary.md'
REQ = re.compile(r'REQ-MATH-\d{3}')
GAP = re.compile(r'GAP-MATH-\d{3}')
TEST_REF = re.compile(r'(tests/[A-Za-z0-9_/]+\.py)::([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)')
LINK = re.compile(r'(?<!!)\[[^\]]*\]\(([^)\s]+)\)')
DD_MODULES = (
    'fm_research.field', 'fm_research.rank', 'fm_research.twoi', 'fm_research.p1',
    'fm_research.problem', 'fm_research.vendor', 'fm_mapper.core', 'fm_control.scalar',
    'fm_certificates.affine', 'fm_identifiability', 'fm_enclosures.numerical',
)
DD_SKIP = frozenset({'main'})


def _text(root, relative):
    return (root / relative).read_text(encoding='utf-8')


def requirements(root):
    text = _text(root, SRS)
    records = {}
    parts = re.split(r'^### ', text, flags=re.M)
    for part in parts[1:]:
        heading, _, body = part.partition('\n')
        match = re.match(r'(REQ-MATH-\d{3}) — \S', heading)
        if not match:
            continue
        rid = match.group(1)
        body = re.split(r'^## ', body, flags=re.M)[0]
        fields = dict(re.findall(r'^- ([A-Za-z ]+): (.+)$', body, flags=re.M))
        statement = body.split('\n- ', 1)[0]
        records.setdefault(rid, []).append({'statement': statement, 'fields': fields})
    gaps = GAP.findall(text)
    return records, gaps


def _table_rows(text, after=None, before=None):
    if after is not None:
        text = text.split(after, 1)[1] if after in text else ''
    if before is not None:
        text = text.split(before, 1)[0]
    rows = []
    for line in text.splitlines():
        if line.startswith('|') and not re.match(r'^\|\s*-', line):
            rows.append([cell.strip() for cell in line.strip().strip('|').split('|')])
    return rows


def matrix(root):
    text = _text(root, VM)
    traced = {}
    for row in _table_rows(text, before='## Tests without a requirement'):
        if row and REQ.fullmatch(row[0]):
            traced.setdefault(row[0], []).append(row)
    unassigned = set()
    for row in _table_rows(text, after='## Tests without a requirement', before='## Change history'):
        for ref in TEST_REF.findall(' '.join(row)):
            unassigned.add(ref)
    return traced, unassigned


def test_inventory(root):
    found = set()
    for path in sorted((root / 'tests').glob('test_*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        relative = path.relative_to(root).as_posix()
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith('test'):
                        found.add((relative, node.name, item.name))
    return found


def design(root):
    allocated = set()
    infrastructure = []
    unallocated = []
    text = _text(root, SDD)
    for row in _table_rows(text, after='## 4. Components', before='## 5.'):
        if len(row) < 5 or row[0] == 'Component':
            continue
        ids = REQ.findall(row[-1])
        if ids:
            allocated.update(ids)
        elif 'infrastructure' in row[-1].lower():
            infrastructure.append(row[0])
        else:
            unallocated.append(row[0])
    return allocated, infrastructure, unallocated


def _slug(heading):
    heading = re.sub(r'[^\w\- ]', '', heading.strip().lower())
    return heading.replace(' ', '-')


def _anchors(path):
    seen, anchors = {}, set()
    fenced = False
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('```'):
            fenced = not fenced
        if fenced or not line.startswith('#'):
            continue
        slug = _slug(line.lstrip('#'))
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        anchors.add(slug if count == 0 else f'{slug}-{count}')
    return anchors


def markdown_files(root):
    return sorted(p for p in root.rglob('*.md') if '.git' not in p.relative_to(root).parts)


def dead_links(root):
    problems = []
    for path in markdown_files(root):
        fenced = False
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if line.startswith('```'):
                fenced = not fenced
            if fenced:
                continue
            for target in LINK.findall(re.sub(r'`[^`]*`', '', line)):
                if re.match(r'[a-z]+:', target):
                    continue
                file_part, _, anchor = target.partition('#')
                resolved = (path.parent / file_part).resolve() if file_part else path
                where = f'{path.relative_to(root).as_posix()}:{number}: {target}'
                try:
                    relative = resolved.relative_to(root.resolve()).as_posix()
                except ValueError:
                    problems.append('link leaves repository: ' + where)
                    continue
                if not resolved.exists():
                    if not excluded(relative):
                        problems.append('dead link: ' + where)
                    continue
                if anchor and resolved.suffix == '.md' and anchor not in _anchors(resolved):
                    problems.append('dead anchor: ' + where)
    return problems


def dictionary_names():
    names = set()
    for module_name in DD_MODULES:
        module = importlib.import_module(module_name)
        for name, value in vars(module).items():
            if name.startswith('_') or name in DD_SKIP:
                continue
            defined = getattr(value, '__module__', None) == module.__name__
            constant = name.isupper() and isinstance(value, (int, str, tuple, dict, frozenset, set))
            if defined or constant:
                names.add(name)
                if dataclasses.is_dataclass(value) and isinstance(value, type):
                    names.update(f.name for f in dataclasses.fields(value))
    problem = importlib.import_module('fm_research.problem')
    names.update(problem.KERNELS)
    from character_ring import contract as character_contract
    from split_bundle import contract as split_contract
    names.update(character_contract.BUDGETS)
    names.update(split_contract.BUDGETS)
    names.update(json.loads(Path(importlib.import_module('fm_research.vendor').VENDOR,
                                 'character_ring/catalog.json').read_text()))
    return names


def check(root):
    root = Path(root)
    problems = []
    records, gaps = requirements(root)
    traced, unassigned = matrix(root)
    tests = test_inventory(root)
    allocated, infrastructure, unallocated = design(root)
    for rid, items in sorted(records.items()):
        if len(items) != 1:
            problems.append(f'{rid}: defined {len(items)} times')
            continue
        item = items[0]
        if len(re.findall(r'\bshall\b', item['statement'])) != 1:
            problems.append(f'{rid}: statement must contain exactly one "shall"')
        for field in ('Rationale', 'Derivation', 'Allocated to', 'Verification', 'Status'):
            if field not in item['fields']:
                problems.append(f'{rid}: missing field {field}')
        for path in re.findall(r'`([^`]+)`', item['fields'].get('Derivation', '')):
            if not (root / path.split('::')[0]).exists():
                problems.append(f'{rid}: derivation path does not exist: {path}')
        if item['fields'].get('Status', '').startswith('Deleted'):
            continue
        if rid not in traced:
            problems.append(f'{rid}: no verification-matrix row')
        if rid not in allocated:
            problems.append(f'{rid}: not allocated to any design component')
    for rid, rows in sorted(traced.items()):
        if rid not in records:
            problems.append(f'{rid}: matrix row for an undefined requirement')
        for row in rows:
            method = row[1] if len(row) > 1 else ''
            refs = TEST_REF.findall(' '.join(row))
            if 'T' in method.split('/') and not refs:
                problems.append(f'{rid}: method T without a test reference')
            if not refs and not any(m in method for m in ('I', 'A', 'D')):
                problems.append(f'{rid}: row names no test, inspection or analysis')
            for ref in refs:
                if ref not in tests:
                    problems.append(f'{rid}: referenced test does not exist: {"::".join((ref[0], ref[1] + "." + ref[2]))}')
    for rid in sorted(allocated - set(records)):
        problems.append(f'{rid}: allocated in design but undefined')
    for name in unallocated:
        problems.append(f'design component implements no requirement and is not infrastructure: {name}')
    referenced = {ref for rows in traced.values() for row in rows for ref in TEST_REF.findall(' '.join(row))}
    for ref in sorted(unassigned - tests):
        problems.append('listed test does not exist: ' + '::'.join((ref[0], ref[1] + '.' + ref[2])))
    for ref in sorted(tests - referenced - unassigned):
        problems.append('test traces to no requirement and is not classified: ' + '::'.join((ref[0], ref[1] + '.' + ref[2])))
    if len(gaps) != len(set(gaps)):
        problems.append('duplicate GAP-MATH identifier in requirements')
    traced_text = _text(root, VM).split('## Tests without a requirement')[0]
    for gap in sorted(set(gaps) & set(GAP.findall(traced_text))):
        problems.append(f'{gap}: untested gap appears as a traced matrix row')
    dictionary = _text(root, DD)
    for name in sorted(dictionary_names()):
        if f'`{name}`' not in dictionary:
            problems.append(f'data dictionary does not define `{name}`')
    problems.extend(dead_links(root))
    summary = {
        'requirements': len(records),
        'traced_requirements': len(set(records) & set(traced)),
        'untested_gaps': len(set(gaps)),
        'tests': len(tests),
        'tests_traced': len(tests & referenced),
        'tests_supporting': len(tests & unassigned - referenced),
        'design_infrastructure_components': len(infrastructure),
        'markdown_files': len(markdown_files(root)),
        'problems': len(problems),
    }
    return problems, summary


def main(argv=None):
    parser = argparse.ArgumentParser(description='Check requirement traceability, data-dictionary coverage and Markdown links.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    problems, summary = check(args.root)
    for problem in problems:
        print(problem, file=sys.stderr)
    print(json.dumps(summary, sort_keys=True))
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
