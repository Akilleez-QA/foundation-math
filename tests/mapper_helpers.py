"""Synthetic caller judgments for mapper tests, not mathematical execution receipts."""
import hashlib
from fm_mapper import binding_for


def node(id='result', statement='The supplied finite record reports 2 + 2 = 4.', scope='finite_computation', obligation=False):
    n = dict(id=id, statement=statement, scope=scope, depends_on=[], evidence_ids=['ev'], assumptions=[], exclusions=[])
    if not obligation:
        n['obligations'] = []
    return n


def bundle(kind='exact_computation', scope='finite_computation'):
    raw = b'Synthetic fixture receipt, supplied for mapper contract tests only.\n'
    b = dict(schema='fm-evidence-paper/1',
             problem=dict(id='synthetic', revision='1', title='Synthetic mapper fixture', objective='Retain precisely scoped supplied findings.'),
             artifacts=[dict(id='record', path='record.txt', sha256=hashlib.sha256(raw).hexdigest(), description='Synthetic source record')],
             evidence=[dict(id='ev', kind=kind, artifact_ids=['record'], description='Caller-supplied finite finding', provenance='Synthetic unit-test input; not real proof evidence', family='synthetic-family', legacy_status=None)],
             obligations=[], claims=[node(scope=scope)], judgments=[], attempts=[],
             costs=[dict(id='total_cost', value=None, unit='USD', coverage='Unknown, not measured', source_artifact_ids=[])],
             paper=dict(title='Synthetic evidence draft', claim_ids=['result'], limitations=['Synthetic input only.']))
    judge(b, 'result', scope=scope)
    return b, {'record': raw}


def judge(b, target_id, target_type='claim', scope=None, decision='supports', conditions=None, checks=None, statement=None, id=None):
    target = next(n for n in b['claims' if target_type == 'claim' else 'obligations'] if n['id'] == target_id)
    j = dict(id=id or 'judgment-' + target_id, target_type=target_type, target_id=target_id,
             binding=binding_for(b, target_type, target_id, target['evidence_ids']),
             decision=decision, scope=scope or target['scope'], supported_statement=statement or target['statement'],
             evidence_ids=list(target['evidence_ids']), conditions=conditions or [], checks=checks or {},
             assessor='Synthetic fixture author', method='Explicit supplied assessment', family='synthetic-family',
             rationale='Tests the mapper contract, not mathematical truth.')
    b['judgments'].append(j)
    return j


def rebind(b):
    for j in b['judgments']:
        j['binding'] = binding_for(b, j['target_type'], j['target_id'], j['evidence_ids'])
