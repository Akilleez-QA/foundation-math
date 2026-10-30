from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from fm_mapper import SchemaError, digest, load_bundle, map_evidence, read_artifacts, render_paper, validate_bundle
from tests.mapper_helpers import bundle, node, judge, rebind
ROOT = Path(__file__).resolve().parents[1]
THEOREM_CHECKS = dict(statement_correspondence='passed', assumptions_audited='passed', dependencies_complete='passed')

class MapperTests(unittest.TestCase):
    def test_positive_exact_result_and_unknown_cost(self):
        b, data = bundle(); r = map_evidence(b, data)
        self.assertEqual(r['claims']['result']['disposition'], 'supported')
        self.assertEqual(r['claims']['result']['supported_scope'], 'finite_computation')
        self.assertIsNone(r['costs'][0]['value'])
        self.assertEqual(r['paper_state'], 'draft_not_scientifically_accepted')
        self.assertEqual(r['summary']['proposed_claims'], 1)
        self.assertIn('unknown', render_paper(b, data))

    def test_valid_conditional_legacy_certification_preserved(self):
        b = load_bundle(ROOT/'examples/evidence-mapper/legacy-conditional.json')
        data = read_artifacts(b, ROOT/'examples/evidence-mapper'); r = map_evidence(b, data); c = r['claims']['result']
        self.assertEqual(c['disposition'], 'conditional')
        self.assertEqual(c['supported_scope'], 'finite_computation')
        self.assertEqual(c['legacy_statuses'], {'ev': 'certified'})
        self.assertTrue(any('Cited premise' in x for x in c['conditions']))
        self.assertIn('certified', render_paper(b, data))

    def test_legacy_label_alone_cannot_promote(self):
        b, data = bundle(); b['judgments'] = []; b['evidence'][0]['legacy_status'] = 'certified'
        c = map_evidence(b, data)['claims']['result']
        self.assertEqual(c['disposition'], 'unsupported')
        self.assertEqual(c['legacy_statuses'], {'ev': 'certified'})

    def test_no_hash_or_test_or_review_count_promotes_theorem(self):
        for kind in ('metadata', 'test_report', 'review_report', 'exact_computation'):
            with self.subTest(kind=kind):
                b, data = bundle(kind=kind, scope='intended_theorem'); b['judgments'][0]['checks'] = THEOREM_CHECKS
                b['evidence'][0]['description'] = 'One million passing tests, 10 reviews, hashes match.'; rebind(b)
                c = map_evidence(b, data)['claims']['result']
                self.assertEqual(c['disposition'], 'unbound')
                self.assertIn('evidence_kind_does_not_support_scope', c['judgment_audit'][0]['reasons'])

    def test_positive_argument_with_explicit_complete_checks(self):
        b, data = bundle(kind='argument', scope='intended_theorem'); b['judgments'][0]['checks'] = THEOREM_CHECKS
        self.assertEqual(map_evidence(b, data)['claims']['result']['disposition'], 'supported')

    def test_formal_check_does_not_infer_informal_correspondence(self):
        b, data = bundle(kind='formal_proof', scope='formal_statement'); b['judgments'][0]['checks'] = {'axioms_audited': 'passed'}
        self.assertEqual(map_evidence(b, data)['claims']['result']['disposition'], 'supported')
        b['claims'][0]['scope'] = 'intended_theorem'; j = b['judgments'][0]; j['scope'] = 'intended_theorem'; rebind(b)
        self.assertEqual(map_evidence(b, data)['claims']['result']['disposition'], 'unbound')
        j['checks'].update(THEOREM_CHECKS)
        self.assertEqual(map_evidence(b, data)['claims']['result']['disposition'], 'supported')

    def test_numerical_vs_empirical_and_valid_empirical_control(self):
        b, data = bundle(kind='numerical_verification', scope='numerical_verification')
        self.assertEqual(map_evidence(b, data)['claims']['result']['disposition'], 'supported')
        b['claims'][0]['scope'] = 'empirical_validation'; b['judgments'][0]['scope'] = 'empirical_validation'
        b['judgments'][0]['checks'] = dict(quantity_semantics='passed', empirical_scope='passed', uncertainty='passed'); rebind(b)
        self.assertEqual(map_evidence(b, data)['claims']['result']['disposition'], 'unbound')
        b['evidence'][0]['kind'] = 'empirical_validation'; rebind(b)
        self.assertEqual(map_evidence(b, data)['claims']['result']['disposition'], 'supported')

    def test_requested_upgrade_visibly_narrowed_to_supplied_finding(self):
        b, data = bundle(); b['claims'][0]['scope'] = 'intended_theorem'; b['claims'][0]['statement'] = 'The full theorem is proved.'
        b['judgments'][0]['supported_statement'] = 'A fixed finite calculation was checked.'; rebind(b)
        r = map_evidence(b, data); c = r['claims']['result']; paper = render_paper(b, data)
        self.assertEqual(c['disposition'], 'narrowed'); self.assertEqual(c['supported_scope'], 'finite_computation')
        self.assertIn('The full theorem is proved', paper); self.assertIn('A fixed finite calculation was checked', paper)
        self.assertIn('Disposition: narrowed', paper)

    def test_positive_refuted_and_inconclusive_results_retained(self):
        for decision, expected in [('refutes', 'refuted'), ('inconclusive', 'inconclusive')]:
            b, data = bundle(); b['judgments'][0]['decision'] = decision; r = map_evidence(b, data)
            self.assertEqual(r['claims']['result']['disposition'], expected); self.assertIn('Claim result', render_paper(b, data))

    def test_conflicting_same_scope_judgments_not_majority_vote(self):
        b, data = bundle()
        for i in range(9): judge(b, 'result', id='copy-' + str(i))
        judge(b, 'result', decision='refutes', id='refuting'); c = map_evidence(b, data)['claims']['result']
        self.assertEqual(c['disposition'], 'conflicting'); self.assertEqual(c['evidence_families'], ['synthetic-family'])

    def test_duplicate_evidence_and_reviews_do_not_inflate_claim_count(self):
        b, data = bundle(); before = map_evidence(b, data)
        for i in range(20):
            e = deepcopy(b['evidence'][0]); e['id'] = 'copy-' + str(i); b['evidence'].append(e); b['claims'][0]['evidence_ids'].append(e['id'])
        rebind(b)
        for i in range(20): judge(b, 'result', id='review-' + str(i))
        after = map_evidence(b, data)
        self.assertEqual(before['summary'], after['summary']); self.assertEqual(after['claims']['result']['evidence_families'], ['synthetic-family'])

    def test_exact_problem_statement_assumption_evidence_and_artifact_binding(self):
        mutations = [lambda b: b['problem'].update(revision='different'),lambda b: b['problem'].update(objective='Different intended outcome'),lambda b: b['claims'][0].update(statement='Changed theorem'),lambda b: b['claims'][0]['assumptions'].append('Extra assumption'),lambda b: b['claims'][0]['exclusions'].append('Extra exclusion'),lambda b: b['evidence'][0].update(description='Changed reported observation'),lambda b: b['artifacts'][0].update(sha256='0'*64)]
        for mutate in mutations:
            b, data = bundle(); mutate(b); c = map_evidence(b, data)['claims']['result']
            self.assertEqual(c['disposition'], 'unbound'); self.assertIn('stale_or_inexact_binding', c['judgment_audit'][0]['reasons'])

    def test_tampered_and_missing_bytes_do_not_authenticate(self):
        b, data = bundle()
        for supplied, expected in [({}, 'missing'), ({'record': b'changed'}, 'mismatch')]:
            r = map_evidence(b, supplied); self.assertEqual(r['artifact_integrity']['record']['state'], expected)
            self.assertEqual(r['claims']['result']['disposition'], 'unbound')
        self.assertEqual(map_evidence(b)['claims']['result']['disposition'], 'unbound')

    def test_refuted_transitive_ancestor_blocks_cited_chain(self):
        b, data = bundle(); b['claims'][0]['depends_on'] = ['middle']
        mid = node('middle', scope='cited'); mid['depends_on'] = ['bad']; mid['evidence_ids'] = ['citation']
        bad = node('bad'); b['claims'] += [mid, bad]; b['evidence'].append(dict(b['evidence'][0], id='citation', kind='citation'))
        b['paper']['claim_ids'] += ['middle', 'bad']; judge(b, 'middle'); judge(b, 'bad', decision='refutes'); rebind(b)
        r = map_evidence(b, data); self.assertEqual(r['claims']['bad']['disposition'], 'refuted')
        self.assertEqual(r['claims']['middle']['disposition'], 'blocked'); self.assertEqual(r['claims']['result']['disposition'], 'blocked')

    def test_open_obligation_blocking_and_explicit_discharge_positive(self):
        b, data = bundle(); o = node('needed', obligation=True); b['obligations'] = [o]; b['claims'][0]['obligations'] = ['needed']; rebind(b)
        self.assertEqual(map_evidence(b, data)['claims']['result']['disposition'], 'blocked')
        judge(b, 'needed', target_type='obligation'); r = map_evidence(b, data)
        self.assertEqual(r['claims']['result']['disposition'], 'supported'); self.assertEqual(r['obligations']['needed']['disposition'], 'supported')
        self.assertEqual(r['summary']['obligations_open'], 0)

    def test_conditional_obligation_is_not_unconditional_discharge(self):
        b, data = bundle(); o = node('needed', obligation=True); b['obligations'] = [o]; b['claims'][0]['obligations'] = ['needed']
        judge(b, 'needed', target_type='obligation', conditions=['Unverified hypothesis']); rebind(b); r = map_evidence(b, data)
        self.assertEqual(r['obligations']['needed']['disposition'], 'conditional'); self.assertEqual(r['claims']['result']['disposition'], 'blocked')

    def test_conditions_cannot_be_erased_by_another_review(self):
        b, data = bundle(); b['judgments'][0]['conditions'] = ['Missing source correspondence']; judge(b, 'result', id='apparently-clean')
        self.assertEqual(map_evidence(b, data)['claims']['result']['conditions'], ['Missing source correspondence'])

    def test_unconditional_theorem_rejects_conditional_premise(self):
        b, data = bundle(kind='argument', scope='intended_theorem'); b['judgments'][0]['checks'] = THEOREM_CHECKS
        b['claims'][0]['assumptions'] = ['Unestablished external hypothesis']; rebind(b)
        self.assertEqual(map_evidence(b, data)['claims']['result']['disposition'], 'blocked')
        b['claims'][0]['scope'] = 'conditional_theorem'; b['judgments'][0]['scope'] = 'conditional_theorem'; rebind(b)
        self.assertEqual(map_evidence(b, data)['claims']['result']['disposition'], 'conditional')

    def test_condition_empty_conditional_theorem_cannot_promote_descendant(self):
        b, data = bundle(kind='argument', scope='intended_theorem')
        b['judgments'][0]['checks'] = THEOREM_CHECKS
        conditional = node('conditional-premise', scope='conditional_theorem')
        b['claims'].append(conditional); b['claims'][0]['depends_on'] = ['conditional-premise']
        b['paper']['claim_ids'].append('conditional-premise')
        judge(b,'conditional-premise',checks=THEOREM_CHECKS); rebind(b)
        r = map_evidence(b,data)
        self.assertEqual(r['claims']['conditional-premise']['disposition'],'conditional')
        self.assertEqual(r['claims']['result']['disposition'],'blocked')
        self.assertTrue(any('is conditional' in x for x in r['claims']['result']['conditions']))

    def test_cycles_dangling_duplicates_and_unknown_fields_rejected(self):
        mutators = [lambda b: b['claims'][0]['depends_on'].append('result'),lambda b: b['claims'][0]['depends_on'].append('missing'),lambda b: b['claims'].append(deepcopy(b['claims'][0])),lambda b: b['claims'][0].update(hidden=True),lambda b: b['claims'][0].update(scope=[]),lambda b: b['claims'][0]['evidence_ids'].append('ev'),lambda b: b['judgments'][0].update(target_type='made-up')]
        for mutate in mutators:
            b, _ = bundle(); mutate(b)
            with self.assertRaises(SchemaError): validate_bundle(b)

    def test_paper_omissions_and_duplicate_claims_rejected(self):
        for ids in ([], ['result', 'result']):
            b, _ = bundle(); b['paper']['claim_ids'] = ids
            with self.assertRaises(SchemaError): load_bundle(b)

    def test_json_duplicate_keys_nonfinite_and_boolean_costs_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'bad.json'
            for raw in ('{"schema":"x","schema":"y"}', '{"a":NaN}', '{"a":Infinity}'):
                p.write_text(raw)
                with self.assertRaises(SchemaError): load_bundle(p)
        for cost in (True, -1, float('inf'), float('nan')):
            b, _ = bundle(); b['costs'][0]['value'] = cost
            with self.assertRaises(SchemaError): load_bundle(b)

    def test_determinism_and_no_input_mutation(self):
        b, data = bundle(); before = deepcopy(b); a = map_evidence(b, data); z = map_evidence(b, data)
        self.assertEqual(b, before); self.assertEqual(a, z); self.assertEqual(render_paper(b,data).encode(), render_paper(b,data).encode())
        self.assertEqual(digest(a), digest(z)); self.assertEqual(digest(dict(reversed(list(b.items())))), digest(b))

    def test_path_escape_and_symlink_escape_rejected(self):
        for path in ('../escape', '/absolute', 'a/../../escape', 'a\\b'):
            b, _ = bundle(); b['artifacts'][0]['path'] = path
            with self.assertRaises(SchemaError): load_bundle(b)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'root'; root.mkdir(); (Path(tmp)/'elsewhere').write_bytes(b'outside'); (root/'record.txt').symlink_to(Path(tmp)/'elsewhere')
            b, _ = bundle()
            with self.assertRaises(SchemaError): read_artifacts(b, root)

    def test_markup_cannot_inject_an_accepted_heading(self):
        b, data = bundle(); b['claims'][0]['statement'] = '# ACCEPTED\n<script>alert(1)</script>'
        b['judgments'][0]['supported_statement'] = b['claims'][0]['statement']; rebind(b); paper = render_paper(b, data)
        self.assertNotIn('<script>', paper); self.assertNotIn('\n# ACCEPTED', paper); self.assertIn('&lt;script&gt;', paper)

    def test_all_attempts_including_failed_cancelled_duplicate_are_preserved(self):
        b, data = bundle()
        for outcome in ('successful', 'failed', 'inconclusive', 'cancelled', 'duplicate', 'not_run'):
            b['attempts'].append(dict(id=outcome,claim_ids=['result'],outcome=outcome,artifact_ids=['record'],note='Synthetic attempt'))
        r = map_evidence(b, data); self.assertEqual(r['summary']['attempts_recorded'], 6)
        for a in b['attempts']: self.assertIn('Attempt `' + a['id'] + '`', render_paper(b, data))

    def test_cli_new_outputs_and_refusal_to_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'map.json'; paper = Path(tmp)/'draft.md'
            cmd = [sys.executable, '-S', '-B', *(['-O'] if not __debug__ else []), '-m', 'fm_mapper', str(ROOT/'examples/evidence-mapper/legacy-conditional.json'), '--json-out', str(out), '--paper-out', str(paper)]
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True); self.assertEqual(p.returncode, 0, p.stderr)
            r = json.loads(out.read_text()); self.assertEqual(r['claims']['result']['disposition'], 'conditional')
            self.assertFalse(json.loads(p.stdout)['scientific_acceptance']); before = out.read_bytes()
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True); self.assertEqual(p.returncode, 2)
            self.assertEqual(out.read_bytes(), before); self.assertIn('Output already exists', p.stderr)

    def test_cli_cannot_replace_input(self):
        bpath = ROOT/'examples/evidence-mapper/legacy-conditional.json'; before=bpath.read_bytes()
        p = subprocess.run([sys.executable,'-S','-B',*(['-O'] if not __debug__ else []),'-m','fm_mapper',str(bpath),'--json-out',str(bpath)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(p.returncode,2); self.assertEqual(bpath.read_bytes(),before)

    def test_renderer_rejects_mutated_map_report_instead_of_input(self):
        b, data = bundle(); r = map_evidence(b,data)
        r['claims']['result']['statement'] = 'Forged manuscript-only claim'
        with self.assertRaises(SchemaError): render_paper(r,data)

    def test_disclosed_title_regression_cannot_assert_blocked_validation(self):
        b, data = bundle(kind='numerical_verification', scope='empirical_validation')
        b['paper']['title'] = 'This real device’s force law and operating predictions are experimentally validated'
        b['claims'][0]['statement'] = b['paper']['title']
        b['judgments'][0]['supported_statement'] = b['claims'][0]['statement']
        b['judgments'][0]['checks'] = dict(quantity_semantics='passed',empirical_scope='passed',uncertainty='passed')
        o = node('empirical-obligation', scope='empirical_validation', obligation=True)
        b['obligations'] = [o]; b['claims'][0]['obligations'] = ['empirical-obligation']
        judge(b,'empirical-obligation',target_type='obligation',checks=b['judgments'][0]['checks']); rebind(b)
        r=map_evidence(b,data); paper=render_paper(b,data)
        self.assertEqual(r['claims']['result']['disposition'],'blocked')
        self.assertEqual(r['obligations']['empirical-obligation']['disposition'],'unbound')
        self.assertEqual(paper.splitlines()[0], '# Foundation Math evidence report')
        self.assertIn('Caller-proposed paper title (unverified metadata, not an accepted claim):',paper)
        self.assertIn('> This real device’s force law and operating predictions are experimentally validated',paper)
        self.assertNotIn('# '+b['paper']['title'],paper)
        self.assertIn('Disposition: blocked',paper)

    def test_raw_prose_surfaces_are_explicitly_supplied_not_result_headings(self):
        b,data=bundle()
        b['paper']['title']='UNSUPPORTED TITLE'
        b['problem']['title']='UNSUPPORTED PROBLEM TITLE'
        b['problem']['objective']='UNSUPPORTED OBJECTIVE'
        b['artifacts'][0]['description']='UNSUPPORTED ARTIFACT DESCRIPTION'
        b['evidence'][0]['description']='UNSUPPORTED EVIDENCE DESCRIPTION'
        b['evidence'][0]['provenance']='UNSUPPORTED PROVENANCE'
        b['judgments'][0]['rationale']='UNSUPPORTED RATIONALE'
        b['paper']['limitations']=['UNSUPPORTED LIMITATION']
        rebind(b); paper=render_paper(b,data)
        checks={'UNSUPPORTED TITLE':'Caller-proposed paper title','UNSUPPORTED PROBLEM TITLE':'Caller-proposed problem title','UNSUPPORTED OBJECTIVE':'Caller-proposed objective','UNSUPPORTED ARTIFACT DESCRIPTION':'caller-supplied artifact description','UNSUPPORTED EVIDENCE DESCRIPTION':'Caller-supplied evidence description','UNSUPPORTED PROVENANCE':'Caller-supplied provenance','UNSUPPORTED RATIONALE':'Caller-supplied rationale','UNSUPPORTED LIMITATION':'Submitted annotation'}
        for text,label in checks.items():
            self.assertIn(text,paper); self.assertIn(label,paper)
            self.assertFalse(any(line.startswith('#') and text in line for line in paper.splitlines()))
        self.assertEqual(map_evidence(b,data)['claims']['result']['disposition'],'supported')

    def test_cr_and_bidi_cannot_hide_title_qualification_or_inject_heading(self):
        b,data=bundle(); b['paper']['title']='submitted\r# ACCEPTED\r\n# VALIDATED\u202e'
        paper=render_paper(b,data)
        self.assertNotIn('\r',paper); self.assertNotIn('\u202e',paper)
        self.assertNotIn('\n# ACCEPTED',paper); self.assertNotIn('\n# VALIDATED',paper)
        self.assertIn('u202e',paper)
        self.assertEqual(paper.splitlines()[0],'# Foundation Math evidence report')

    def test_empty_cost_list_is_unknown_not_free(self):
        b, data=bundle(); b['costs']=[]; self.assertIn('total cost is unknown', render_paper(b,data))

if __name__ == '__main__': unittest.main()
