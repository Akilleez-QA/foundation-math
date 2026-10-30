"""Finite check integration, dependency failures, integrity and CLI regressions."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from fm_research.problem import load_spec, run_check, gate

BASE = Path(__file__).resolve().parents[1]
EXAMPLE = BASE / 'examples/research-regression.problem.json'
FALSE = BASE / 'tests/fixtures/false-claim.problem.json'


class ProblemTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_spec(EXAMPLE)
        self.claims = self.spec['claims']
        self.evidence = {c['id']: run_check(c) for c in self.claims if c['kind'] == 'computed'}

    def test_example_and_hashes(self):
        statuses = gate(self.spec, self.evidence)
        for c in self.claims[:-1]:
            self.assertEqual(statuses[c['id']], 'certified')
            self.assertEqual(self.evidence[c['id']].to_dict(), run_check(c).to_dict())
        self.assertEqual(statuses['research-argument'], 'argued')
        self.assertEqual(self.evidence['rank-q5'].observed['certificate']['rank'], 2)
        for key, value in [('args_sha256', 'bad'), ('output_sha256', 'bad'), ('kernel_source_sha256', 'bad'), ('expected', 'bad'), ('observed', 'bad')]:
            ev = dict(self.evidence, sym2=replace(self.evidence['sym2'], **{key: value}))
            self.assertEqual(gate(self.spec, ev)['sym2'], 'unchecked')

    def test_dependencies(self):
        self.claims[0]['check']['expect'] = 'wrong'
        self.claims[1]['depends_on'] = ['sym2']
        self.evidence['sym2'] = run_check(self.claims[0])
        statuses = gate(self.spec, self.evidence)
        self.assertEqual((statuses['sym2'], statuses['sym3']), ('refuted', 'blocked'))
        self.claims[-1]['depends_on'] = []
        self.claims[1]['depends_on'] = ['research-argument']
        self.assertEqual(gate(self.spec, self.evidence)['sym3'], 'blocked')
        self.claims[-1]['kind'] = 'cited'
        self.assertEqual(gate(self.spec, self.evidence)['sym3'], 'certified')
        self.claims[-1]['depends_on'] = ['sym2']
        self.assertEqual(gate(self.spec, self.evidence)['sym3'], 'blocked')
        self.assertEqual(gate(self.spec, {})['sym2'], 'unchecked')

    def test_validation(self):
        for update in [dict(depends_on=['sym2']), dict(depends_on=['missing']), dict(kind='bogus'),
                       dict(check=None), dict(check=dict(kernel='os.system', args={}, expect=1))]:
            spec = deepcopy(self.spec)
            spec['claims'][0].update(update)
            with self.assertRaises((ValueError, TypeError)):
                load_spec(spec)
        self.spec['claims'].append(deepcopy(self.claims[0]))
        with self.assertRaises(ValueError): load_spec(self.spec)
        for value in (1.5, float('nan'), float('inf')):
            spec = load_spec(EXAMPLE)
            spec['repo']['extra'] = value
            with self.assertRaises(TypeError): load_spec(spec)
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'float.json'
                path.write_text(json.dumps(spec))
                with self.assertRaises(TypeError): load_spec(path)

    def test_other_kernels_and_errors(self):
        c = deepcopy(self.claims[0])
        for kernel, args, expect in [('p1.h0_dim', dict(blocks=[dict(irrep='1', twist=2, multiplicity=1)], twist=0), 3),
                                     ('p1.h1_dim', dict(blocks=[dict(irrep='1', twist=-2, multiplicity=1)], twist=0), 1),
                                     ('rank', dict(field='Q', rows=[['1/2', 1], [1, 2]]), 1)]:
            c['check'] = dict(kernel=kernel, args=args, expect=expect)
            self.assertEqual(run_check(c).verdict, 'PASS')
        c['check']['args']['field'] = 'invalid'
        self.assertEqual(run_check(c).verdict, 'ERROR')

    def test_standalone_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'evidence.jsonl'
            for path, flags, code in [(EXAMPLE, [], 0), (FALSE, [], 1), (EXAMPLE, ['--claim', 'rank-q5'], 0), (EXAMPLE, ['--claim', 'missing'], 2)]:
                result = subprocess.run([sys.executable, '-S', '-B', *(['-O'] if not __debug__ else []), '-m', 'fm_research', 'check', str(path), '--evidence-out', str(out), *flags], cwd=BASE, capture_output=True, text=True)
                self.assertEqual(result.returncode, code, result.stderr)
            self.assertEqual(json.loads(out.read_text())['verdict'], 'PASS')
