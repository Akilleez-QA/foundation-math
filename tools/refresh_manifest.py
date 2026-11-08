import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from tools.package_source import excluded

MANIFEST = 'SOURCE-MANIFEST.json'


def tracked(root):
    output = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root)
    return sorted(p for p in output.decode('utf-8').split('\0') if p)


def refresh(root, check_only=False):
    root = Path(root)
    manifest_path = root / MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    rows = {row['path']: row for row in manifest['files']}
    wanted = [p for p in tracked(root) if p != MANIFEST and not excluded(p)]
    changes = []
    for path in sorted(set(rows) - set(wanted)):
        changes.append('removed ' + path)
        del rows[path]
    for path in wanted:
        data = (root / path).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        row = rows.get(path)
        if row is None:
            rows[path] = {'bytes': len(data), 'path': path, 'sha256': digest}
            changes.append('added ' + path)
        elif row['sha256'] != digest or row['bytes'] != len(data):
            if row.get('byte_preserved'):
                raise ValueError('Byte-preserved source changed: ' + path)
            row['bytes'], row['sha256'] = len(data), digest
            changes.append('updated ' + path)
    manifest['files'] = [rows[p] for p in sorted(rows)]
    if changes and not check_only:
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return changes


def main(argv=None):
    parser = argparse.ArgumentParser(description='Rehash SOURCE-MANIFEST.json rows from the committed Git file list.')
    parser.add_argument('--check', action='store_true', help='report differences without writing')
    args = parser.parse_args(argv)
    changes = refresh(Path(__file__).resolve().parents[1], args.check)
    for change in changes:
        print(change)
    return 1 if args.check and changes else 0


if __name__ == '__main__':
    sys.exit(main())
