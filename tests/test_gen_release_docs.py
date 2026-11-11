import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from tools import gen_release_docs as gen

REF_A = ('tests/test_x.py', 'XTests', 'test_a')
REF_B = ('tests/test_x.py', 'XTests', 'test_b')


def suite(outcomes, exit_=0, ran=None):
    return {'command': 'python3 -m unittest', 'exit': exit_, 'ran': len(outcomes) if ran is None else ran,
            'outcomes': dict(outcomes), 'log_sha256': '0' * 64}


def record(**changes):
    d = {
        'commit': 'a' * 40, 'tree': 'b' * 40, 'commit_date': '2026-11-09', 'generated': '2026-11-09 00:00 UTC',
        'candidate': 'synthetic', 'tags': [], 'commits': ['aaaaaaa 2026-11-09 synthetic'],
        'environment': 'Linux x86_64; Python 3.12',
        'normal': suite({REF_A: 'ok', REF_B: 'ok'}), 'optimized': suite({REF_A: 'ok', REF_B: 'ok'}),
        'trace_problems': [], 'trace': {'traced_requirements': 1, 'requirements': 1, 'untested_gaps': 0},
        'statuses': {'Implemented': 1}, 'gaps': [], 'tbd': [],
        'coverage': {'command': 'trace', 'exit': 0, 'rows': [], 'lines': 0, 'percent': 0.0},
        'code_rules': ([], []), 'ruff': None,
        'gitleaks': {'command': 'gitleaks git', 'version': '8', 'exit': 0, 'summary': 'no leaks found'},
        'package': {'first': {'file_count': 1, 'sha256': 'c' * 64, 'bytes': 1},
                    'rebuild_identical': True, 'extracted_rebuild_identical': True},
        'manifest_sha256': 'd' * 64, 'manifest_rows': 1, 'catalog_sha256': 'e' * 64,
        'issues': None, 'prs': None, 'lines': {}, 'requirement_by_test': {},
    }
    d.update(changes)
    return d


PASS_TEXT = 'all automated checks passed'
CLEAN_TEXT = 'None. Every test passed'


class ReleaseRecordSuccessTests(unittest.TestCase):
    def assertDeviation(self, d, *fragments):
        report = gen.str_report(d, '1')
        self.assertNotIn(PASS_TEXT, report)
        self.assertNotIn(CLEAN_TEXT, report)
        self.assertNotIn('No failure was accepted.', report)
        self.assertTrue(gen.deviations(d))
        section = report.split('## 4. Problems and deviations', 1)[1].split('## 5. Metrics', 1)[0]
        for fragment in fragments:
            self.assertIn(fragment, section)
        return report

    def test_clean_record_passes(self):
        d = record()
        report = gen.str_report(d, '1')
        self.assertEqual(gen.deviations(d), [])
        self.assertIn(PASS_TEXT, report)
        self.assertIn(CLEAN_TEXT, report)

    def test_reproduced_finding_skips_and_gitleaks_exit_one(self):
        d = record(normal=suite({REF_A: 'ok', REF_B: 'skipped'}), optimized=suite({REF_A: 'ok', REF_B: 'skipped'}),
                   gitleaks={'command': 'gitleaks git', 'version': '8', 'exit': 1, 'summary': 'leaks found: 1'})
        report = self.assertDeviation(d, 'test_b` skipped', 'Secret scan', 'exit 1')
        self.assertNotIn('was skipped, and', report)

    def test_skipped_test_is_a_deviation(self):
        self.assertDeviation(record(optimized=suite({REF_A: 'ok', REF_B: 'skipped'})), 'Optimized suite', 'test_b` skipped')

    def test_expected_failure_and_unexpected_success_are_deviations(self):
        d = record(normal=suite({REF_A: 'expected failure', REF_B: 'unexpected success'}))
        self.assertDeviation(d, 'test_a` expected failure', 'test_b` unexpected success')

    def test_failed_coverage_run_is_a_deviation(self):
        coverage = dict(record()['coverage'], exit=1)
        self.assertDeviation(record(coverage=coverage), 'Coverage run', 'exit 1')

    def test_failed_secret_scan_is_a_deviation(self):
        leaks = {'command': 'gitleaks git', 'version': '8', 'exit': 1, 'summary': 'leaks found: 2'}
        self.assertDeviation(record(gitleaks=leaks), 'Secret scan', 'leaks found: 2')

    def test_missing_secret_scan_is_a_deviation(self):
        self.assertDeviation(record(gitleaks=None), 'Secret scan', 'not run')

    def test_failed_reproducibility_comparison_is_a_deviation(self):
        base = record()['package']
        self.assertDeviation(record(package=dict(base, rebuild_identical=False)), 'same tree')
        self.assertDeviation(record(package=dict(base, extracted_rebuild_identical=False)), 'extracted ZIP')

    def test_unparsed_or_empty_suite_is_a_deviation(self):
        self.assertDeviation(record(normal=suite({REF_A: 'ok'}, ran=2)), '1 parsed outcomes for 2 tests run')
        self.assertDeviation(record(optimized=suite({}, ran=0)), '0 parsed outcomes for 0 tests run')

    def test_unit_run_keeps_full_non_ok_outcomes(self):
        stderr = '\n'.join([
            "test_a (tests.test_x.XTests.test_a) ... skipped 'synthetic reason'",
            'test_b (tests.test_x.XTests.test_b) ... expected failure',
            'test_c (tests.test_x.XTests.test_c) ... unexpected success',
            'test_d (tests.test_x.XTests.test_d) ... ok',
            '', 'Ran 4 tests in 0.001s', '', 'OK (skipped=1, expected failures=1, unexpected successes=1)', ''])
        done = subprocess.CompletedProcess([], 1, stdout='', stderr=stderr)
        with mock.patch.object(gen, 'run', return_value=done):
            result = gen.unit_run(False)
        self.assertEqual(result['ran'], 4)
        self.assertEqual(sorted(result['outcomes'].values()), ['expected failure', 'ok', 'skipped', 'unexpected success'])

    def test_main_exit_status_follows_deviations(self):
        for changes, expected in (({}, 0), ({'gitleaks': None}, 1),
                                  ({'normal': suite({REF_A: 'ok', REF_B: 'skipped'})}, 1)):
            with self.subTest(changes=sorted(changes)), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                for index in ('docs/verification/reports/README.md', 'docs/releases/README.md'):
                    (root / index).parent.mkdir(parents=True)
                    (root / index).write_text('| Record | Candidate | Commit |\n|---|---|---|\n')
                (root / 'CHANGELOG.md').write_text('# Changelog\n\n## [Unreleased]\n\n- Synthetic.\n')
                with mock.patch.object(gen, 'ROOT', root), mock.patch.object(gen, 'collect', return_value=record(**changes)), \
                        contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(gen.main(['--pr', '1', '--gitleaks', '']), expected)


if __name__ == '__main__':
    unittest.main()
