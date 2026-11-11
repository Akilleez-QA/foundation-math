from pathlib import Path
import shutil
import tempfile
import unittest

from tools.check_trace import DD, SRS, VM, check

ROOT = Path(__file__).resolve().parents[1]


class TraceCheckTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / 'copy'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('.git', '__pycache__'))

    def tearDown(self):
        self.temporary.cleanup()

    def edit(self, relative, old, new):
        path = self.root / relative
        text = path.read_text(encoding='utf-8')
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding='utf-8')

    def problems(self):
        return check(self.root)[0]

    def test_repository_trace_is_clean(self):
        problems, summary = check(ROOT)
        self.assertEqual(problems, [])
        self.assertEqual(summary['requirements'], summary['traced_requirements'])
        self.assertGreater(summary['requirements'], 0)

    def test_untraced_requirement_is_reported(self):
        self.edit(VM, '| REQ-MATH-016 |', '| REQ-MATH-916 |')
        problems = self.problems()
        self.assertIn('REQ-MATH-016: no verification-matrix row', problems)
        self.assertIn('REQ-MATH-916: matrix row for an undefined requirement', problems)

    def test_missing_test_reference_is_reported(self):
        self.edit(VM, 'AffineCertificateTests.test_strict_infeasibility_and_touching`',
                  'AffineCertificateTests.test_absent`')
        self.assertTrue(any('referenced test does not exist' in p and 'test_absent' in p
                            for p in self.problems()))

    def test_unclassified_test_is_reported(self):
        path = self.root / 'tests/test_extra_trace_fixture.py'
        path.write_text('import unittest\n\n\nclass Extra(unittest.TestCase):\n'
                        '    def test_unlisted(self):\n        pass\n', encoding='utf-8')
        self.assertIn('test traces to no requirement and is not classified: '
                      'tests/test_extra_trace_fixture.py::Extra.test_unlisted', self.problems())

    def test_dead_link_is_reported(self):
        self.edit(SRS, '](../verification/verification-matrix.md)', '](../verification/absent.md)')
        self.assertTrue(any(p.startswith('dead link: docs/requirements/requirements.md')
                            for p in self.problems()))

    def test_missing_dictionary_name_is_reported(self):
        path = self.root / DD
        text = path.read_text(encoding='utf-8')
        self.assertIn('`verify_linear_residual`', text)
        path.write_text(text.replace('`verify_linear_residual`', 'verify-linear-residual'), encoding='utf-8')
        self.assertIn('data dictionary does not define `verify_linear_residual`', self.problems())
