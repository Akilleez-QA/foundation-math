"""Synthetic source-identity tests; mutated files are not executed or imported."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from fm_research import problem, vendor

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'fm_research/' + name for name in
    ('__init__.py', '__main__.py', 'field.py', 'p1.py', 'problem.py', 'rank.py', 'twoi.py', 'vendor.py')
} | {
    'vendor/foundation-math-v014/' + name for name in
    ('character_ring/__init__.py', 'character_ring/contract.py',
     'character_ring/producer.py', 'character_ring/verifier.py', 'character_ring/catalog.json',
     'split_bundle/__init__.py', 'split_bundle/contract.py',
     'split_bundle/producer.py', 'split_bundle/verifier.py')
}


class SourceBindingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.copy = Path(self.temporary.name) / 'selected'
        for relative in sorted(EXPECTED):
            out = self.copy / relative
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes((ROOT / relative).read_bytes())
        for patcher in (patch.object(problem, '__file__', str(self.copy / 'fm_research/problem.py')),
                        patch.object(vendor, 'VENDOR', self.copy / 'vendor/foundation-math-v014')):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.spec = problem.load_spec(ROOT / 'examples/research-regression.problem.json')
        self.spec['claims'] = [self.spec['claims'][0]]
        self.claim = self.spec['claims'][0]
        self.receipt = problem.run_check(self.claim)
        self.old = {self.claim['id']: self.receipt}
        self.assertEqual(problem.gate(self.spec, self.old)[self.claim['id']], 'certified')

    def test_explicit_selected_source_closure_is_complete(self):
        self.assertEqual(set(problem._SOURCE_FILES), EXPECTED)
        self.assertEqual(len(problem._SOURCE_FILES), len(EXPECTED))
        manifest = json.loads((ROOT / 'SOURCE-MANIFEST.json').read_text())
        selected = {row['path'] for row in manifest['files'] if
                    row['path'].startswith(('fm_research/', 'vendor/foundation-math-v014/'))}
        self.assertEqual(EXPECTED, selected)

    def test_each_selected_python_dependency_stales_prior_receipt(self):
        before = problem._source_hash()
        for relative in sorted(EXPECTED):
            if not relative.endswith('.py'):
                continue
            with self.subTest(relative=relative):
                path = self.copy / relative
                original = path.read_bytes()
                try:
                    path.write_bytes(original + b'\n# Inert source-identity regression mutation.\n')
                    self.assertNotEqual(problem._source_hash(), before)
                    self.assertEqual(problem.gate(self.spec, self.old)[self.claim['id']], 'unchecked')
                finally:
                    path.write_bytes(original)
                self.assertEqual(problem._source_hash(), before)
                self.assertEqual(problem.gate(self.spec, self.old)[self.claim['id']], 'certified')

    def test_pinned_catalog_change_rejects_instead_of_admitting_old_receipt(self):
        path = self.copy / 'vendor/foundation-math-v014/character_ring/catalog.json'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(RuntimeError, 'catalog SHA256 mismatch'):
            problem._source_hash()
        with self.assertRaisesRegex(RuntimeError, 'catalog SHA256 mismatch'):
            problem.gate(self.spec, self.old)

    def test_missing_selected_dependency_fails_closed(self):
        for relative in sorted(EXPECTED):
            with self.subTest(relative=relative):
                path = self.copy / relative
                original = path.read_bytes()
                try:
                    path.unlink()
                    with self.assertRaises(OSError):
                        problem.gate(self.spec, self.old)
                finally:
                    path.write_bytes(original)

    def test_identity_is_deterministic_across_order_and_location(self):
        expected = problem._source_hash()
        self.assertEqual(expected, problem._source_hash())
        with patch.object(problem, '_SOURCE_FILES', tuple(reversed(problem._SOURCE_FILES))):
            self.assertEqual(expected, problem._source_hash())
        relocated = Path(self.temporary.name) / 'relocated'
        for relative in reversed(sorted(EXPECTED)):
            out = relocated / relative
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes((self.copy / relative).read_bytes())
        with patch.object(problem, '__file__', str(relocated / 'fm_research/problem.py')), \
             patch.object(vendor, 'VENDOR', relocated / 'vendor/foundation-math-v014'):
            self.assertEqual(expected, problem._source_hash())
            self.assertEqual(problem.gate(self.spec, self.old)[self.claim['id']], 'certified')
        legacy = hashlib.sha256(vendor.catalog_sha256().encode())
        for path in sorted((self.copy / 'fm_research').glob('*.py')):
            legacy.update(path.name.encode() + b'\0' + path.read_bytes() + b'\0')
        self.assertNotEqual(expected, legacy.hexdigest())
        altered = self.receipt.to_dict()
        altered['kernel_source_sha256'] = legacy.hexdigest()
        self.assertEqual(problem.gate(self.spec, {self.claim['id']: altered})[self.claim['id']], 'unchecked')

    def test_unrelated_material_does_not_enter_math_source_identity(self):
        expected = problem._source_hash()
        for relative in ('docs/note.md', 'tests/helper.py', 'fm_mapper/core.py',
                         'vendor/foundation-math-v014/unselected_tool.py'):
            path = self.copy / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Synthetic unrelated data, never executed.\n')
        self.assertEqual(expected, problem._source_hash())
