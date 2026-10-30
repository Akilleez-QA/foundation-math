"""New synthetic source-packaging boundary checks."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from tools.package_source import build, checked_files


class SourcePackageTests(unittest.TestCase):
    def prepare(self, base):
        root = base / 'source'
        root.mkdir()
        (root / 'sample.txt').write_bytes(b'Synthetic packaging fixture.\n')
        raw = (root / 'sample.txt').read_bytes()
        (root / 'SOURCE-MANIFEST.json').write_text(json.dumps({'files': [
            {'path': 'sample.txt', 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}]}))
        return root

    def test_identical_archives_and_manifest_members(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = self.prepare(base)
            a, b = build(root, base / 'one.zip'), build(root, base / 'two.zip')
            self.assertEqual(a, b)
            self.assertEqual((base / 'one.zip').read_bytes(), (base / 'two.zip').read_bytes())
            with zipfile.ZipFile(base / 'one.zip') as archive:
                self.assertEqual(archive.namelist(), ['foundation-math/SOURCE-MANIFEST.json', 'foundation-math/sample.txt'])
            with self.assertRaises(FileExistsError):
                build(root, base / 'one.zip')

    def test_changed_or_unlisted_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = self.prepare(base)
            (root / 'extra.txt').write_text('Not allowlisted')
            with self.assertRaises(ValueError):
                checked_files(root)
            (root / 'extra.txt').unlink()
            (root / 'sample.txt').write_bytes(b'Tampered')
            with self.assertRaises(ValueError):
                checked_files(root)

    def test_symlink_rejected_and_output_must_be_outside(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = self.prepare(base)
            with self.assertRaises(ValueError):
                build(root, root / 'recursive.zip')
            raw = (root / 'sample.txt').read_bytes()
            (root / 'sample.txt').unlink()
            (base / 'elsewhere').write_bytes(raw)
            (root / 'sample.txt').symlink_to(base / 'elsewhere')
            with self.assertRaises(ValueError):
                checked_files(root)
