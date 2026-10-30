"""Build a deterministic, explicit-allowlist source ZIP using only the stdlib."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

EXCLUDED_FILES = frozenset({'AGENTS.md', 'CHANGELOG.md', 'CODE_OF_CONDUCT.md', 'SECURITY.md', 'SUPPORT.md'})
EXCLUDED_DIRECTORY = '.github'


def excluded(relative):
    return relative in EXCLUDED_FILES or relative.split('/', 1)[0] == EXCLUDED_DIRECTORY


def checked_files(root):
    manifest = json.loads((root / 'SOURCE-MANIFEST.json').read_text())
    rows = manifest['files']
    paths = [row['path'] for row in rows]
    if len(paths) != len(set(paths)):
        raise ValueError('Duplicate source manifest path')
    expected = set(paths) | {'SOURCE-MANIFEST.json'}
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() or p.is_symlink()}
    actual = {path for path in actual if not excluded(path)}
    if expected != actual:
        raise ValueError('Exact source file-set mismatch')
    for row in rows:
        relative = PurePosixPath(row['path'])
        if relative.is_absolute() or '..' in relative.parts or '\\' in row['path']:
            raise ValueError('Non-contained source path')
        path = root / relative
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != root.parent):
            raise ValueError('Symlink is not an allowed source')
        data = path.read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Source pin mismatch: ' + row['path'])
    return sorted(expected)


def build(root, output):
    root, output = root.resolve(), output.resolve()
    if output.is_relative_to(root):
        raise ValueError('Archive output must be outside source root')
    paths = checked_files(root)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_STORED) as archive:
        for relative in paths:
            entry = zipfile.ZipInfo('foundation-math/' + relative, date_time=(2026, 10, 26, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, (root / relative).read_bytes())
    return {'file_count': len(paths), 'bytes': output.stat().st_size,
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(Path(__file__).resolve().parents[1], args.output), sort_keys=True))
