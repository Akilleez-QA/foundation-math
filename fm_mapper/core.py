"""Standalone evidence-to-draft contract v1. No solvers, plugins or execution hooks.

A judgment is supplied semantic input, not an authenticated reviewer or inferred truth.
Hashes detect changed bytes/contracts, not honest provenance or correct mathematics.
"""
import hashlib
import html
import json
import math
from pathlib import Path
import re

SCHEMA = 'fm-evidence-paper/1'
SCOPES = {'artifact_record', 'cited', 'finite_computation', 'reviewed_argument',
          'formal_statement', 'conditional_theorem', 'intended_theorem',
          'numerical_verification', 'empirical_validation'}
SUPPORT = {
    'artifact': {'artifact_record'}, 'citation': {'cited'},
    'exact_computation': {'finite_computation'},
    'argument': {'reviewed_argument', 'conditional_theorem', 'intended_theorem'},
    'formal_proof': {'formal_statement', 'conditional_theorem', 'intended_theorem'},
    'numerical_verification': {'numerical_verification'},
    'empirical_validation': {'empirical_validation'},
    'test_report': set(), 'review_report': set(), 'metadata': set(),
}
CHECKS = {'statement_correspondence', 'assumptions_audited', 'dependencies_complete',
          'axioms_audited', 'quantity_semantics', 'empirical_scope', 'uncertainty'}
REQUIRED = {
    'formal_statement': {'axioms_audited'},
    'conditional_theorem': {'statement_correspondence', 'assumptions_audited', 'dependencies_complete'},
    'intended_theorem': {'statement_correspondence', 'assumptions_audited', 'dependencies_complete'},
    'empirical_validation': {'quantity_semantics', 'empirical_scope', 'uncertainty'},
}
MAX_BYTES = 8 * 1024 * 1024
MAX_ITEMS = 1000


class SchemaError(ValueError):
    """Malformed/ambiguous contract, never a scientific refutation."""


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    """SHA-256 of exact UTF-8 canonical JSON; lists retain their order."""
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()


def _pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise SchemaError('Duplicate JSON key: ' + k)
        out[k] = v
    return out


def _invalid_constant(value):
    raise SchemaError('Nonfinite JSON number: ' + value)


def load_bundle(source):
    """Load a path or detach a JSON-compatible dict, then validate, without I/O on artifacts."""
    if isinstance(source, dict):
        try:
            raw = canonical_json(source)
        except (ValueError, TypeError) as e:
            raise SchemaError(str(e)) from e
    else:
        path = Path(source)
        if path.stat().st_size > MAX_BYTES:
            raise SchemaError('Bundle exceeds 8 MiB')
        raw = path.read_text(encoding='utf-8')
    if len(raw.encode('utf-8')) > MAX_BYTES:
        raise SchemaError('Bundle exceeds 8 MiB')
    try:
        value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_invalid_constant)
    except (ValueError, RecursionError) as e:
        raise SchemaError(str(e)) from e
    validate_bundle(value)
    return value


def _fields(v, names, where):
    if type(v) is not dict or set(v) != set(names.split()):
        raise SchemaError(where + ': expected fields ' + names)


def _text(v, where):
    if type(v) is not str or not v.strip() or len(v) > 32768:
        raise SchemaError(where + ': expected bounded nonempty text')


def _id(v):
    if type(v) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', v):
        raise SchemaError('Invalid identifier')


def _hash(v):
    if type(v) is not str or not re.fullmatch('[0-9a-f]{64}', v):
        raise SchemaError('Invalid SHA-256')


def _list(v, where):
    if type(v) is not list or len(v) > MAX_ITEMS:
        raise SchemaError(where + ': expected bounded array')


def _refs(v, allowed, where):
    _list(v, where)
    if any(type(x) is not str for x in v) or len(v) != len(set(v)) or not set(v) <= set(allowed):
        raise SchemaError(where + ': duplicate or unknown reference')


def _texts(v, where):
    _list(v, where)
    for x in v:
        _text(x, where)


def _index(items, where):
    _list(items, where)
    result = {}
    for item in items:
        if type(item) is not dict or 'id' not in item:
            raise SchemaError(where + ': records require id')
        _id(item['id'])
        if item['id'] in result:
            raise SchemaError(where + ': duplicate id')
        result[item['id']] = item
    return result


def _order(nodes, field):
    pending, ordered = dict(nodes), []
    while pending:
        ready = sorted(k for k, n in pending.items() if set(n[field]) <= set(ordered))
        if not ready:
            raise SchemaError('Dependency graph has a cycle or unknown node')
        for k in ready:
            ordered.append(k)
            del pending[k]
    return ordered


def _validate_bundle(b):
    _fields(b, 'schema problem artifacts evidence obligations claims judgments attempts costs paper', 'bundle')
    if b['schema'] != SCHEMA:
        raise SchemaError('Unsupported schema')
    _fields(b['problem'], 'id revision title objective', 'problem')
    _id(b['problem']['id'])
    for k in ('revision', 'title', 'objective'):
        _text(b['problem'][k], 'problem.' + k)
    artifacts = _index(b['artifacts'], 'artifacts')
    evidence = _index(b['evidence'], 'evidence')
    claims = _index(b['claims'], 'claims')
    obligations = _index(b['obligations'], 'obligations')
    judgments = _index(b['judgments'], 'judgments')
    for a in artifacts.values():
        _fields(a, 'id path sha256 description', 'artifact')
        _hash(a['sha256'])
        _text(a['description'], 'artifact.description')
        _text(a['path'], 'artifact.path')
        p = Path(a['path'])
        if p.is_absolute() or '..' in p.parts or '\\' in a['path']:
            raise SchemaError('Artifact paths must be relative and contained')
    for e in evidence.values():
        _fields(e, 'id kind artifact_ids description provenance family legacy_status', 'evidence')
        if e['kind'] not in SUPPORT:
            raise SchemaError('Unknown evidence kind')
        _refs(e['artifact_ids'], artifacts, 'evidence.artifact_ids')
        if not e['artifact_ids']:
            raise SchemaError('Evidence needs at least one pinned artifact')
        for k in ('description', 'provenance', 'family'):
            _text(e[k], 'evidence.' + k)
        if e['legacy_status'] not in (None, 'certified', 'cited', 'argued', 'refuted', 'blocked', 'unchecked'):
            raise SchemaError('Unknown legacy status')
    for kind, nodes in [('claim', claims), ('obligation', obligations)]:
        for n in nodes.values():
            names = 'id statement scope depends_on evidence_ids assumptions exclusions'
            if kind == 'claim':
                names += ' obligations'
            _fields(n, names, kind)
            _text(n['statement'], kind + '.statement')
            if n['scope'] not in SCOPES:
                raise SchemaError('Unknown requested scope')
            _refs(n['depends_on'], nodes, kind + '.depends_on')
            _refs(n['evidence_ids'], evidence, kind + '.evidence_ids')
            for k in ('assumptions', 'exclusions'):
                _texts(n[k], kind + '.' + k)
            if kind == 'claim':
                _refs(n['obligations'], obligations, 'claim.obligations')
        _order(nodes, 'depends_on')
    for j in judgments.values():
        _fields(j, 'id target_type target_id binding decision scope supported_statement evidence_ids conditions checks assessor method family rationale', 'judgment')
        nodes = claims if j['target_type'] == 'claim' else obligations if j['target_type'] == 'obligation' else None
        if nodes is None or j['target_id'] not in nodes:
            raise SchemaError('Unknown judgment target')
        if j['decision'] not in {'supports', 'refutes', 'inconclusive'} or j['scope'] not in SCOPES:
            raise SchemaError('Unknown judgment decision/scope')
        _refs(j['evidence_ids'], evidence, 'judgment.evidence_ids')
        if not set(j['evidence_ids']) <= set(nodes[j['target_id']]['evidence_ids']):
            raise SchemaError('Judgment evidence not declared by target')
        _fields(j['binding'], 'problem_sha256 target_sha256 evidence_sha256 artifacts_sha256', 'binding')
        for k in ('problem_sha256', 'target_sha256'):
            _hash(j['binding'][k])
        for k in ('evidence_sha256', 'artifacts_sha256'):
            if type(j['binding'][k]) is not dict:
                raise SchemaError('Binding hash map required')
            for name, h in j['binding'][k].items():
                _id(name)
                _hash(h)
        for k in ('supported_statement', 'assessor', 'method', 'family', 'rationale'):
            _text(j[k], 'judgment.' + k)
        _texts(j['conditions'], 'judgment.conditions')
        if type(j['checks']) is not dict or not set(j['checks']) <= CHECKS or any(v not in {'passed', 'failed', 'unknown'} for v in j['checks'].values()):
            raise SchemaError('Invalid explicit semantic checks')
    attempts = _index(b['attempts'], 'attempts')
    for a in attempts.values():
        _fields(a, 'id claim_ids outcome artifact_ids note', 'attempt')
        _refs(a['claim_ids'], claims, 'attempt.claim_ids')
        _refs(a['artifact_ids'], artifacts, 'attempt.artifact_ids')
        if a['outcome'] not in {'successful', 'failed', 'inconclusive', 'cancelled', 'duplicate', 'not_run'}:
            raise SchemaError('Invalid attempt outcome')
        _text(a['note'], 'attempt.note')
    _list(b['costs'], 'costs')
    seen_costs = set()
    for c in b['costs']:
        _fields(c, 'id value unit coverage source_artifact_ids', 'cost')
        _id(c['id'])
        if c['id'] in seen_costs:
            raise SchemaError('Duplicate cost id')
        seen_costs.add(c['id'])
        v = c['value']
        if v is not None and (type(v) not in (int, float) or not math.isfinite(v) or v < 0):
            raise SchemaError('Cost must be nonnegative finite number or null (unknown)')
        for k in ('unit', 'coverage'):
            _text(c[k], 'cost.' + k)
        _refs(c['source_artifact_ids'], artifacts, 'cost.source_artifact_ids')
    _fields(b['paper'], 'title claim_ids limitations', 'paper')
    _text(b['paper']['title'], 'paper.title')
    _refs(b['paper']['claim_ids'], claims, 'paper.claim_ids')
    if set(b['paper']['claim_ids']) != set(claims):
        raise SchemaError('Draft must include every proposed claim, including failures')
    _texts(b['paper']['limitations'], 'paper.limitations')
    return b


def validate_bundle(bundle):
    """Validate the closed v1 schema, references and DAGs; never infer semantics."""
    try:
        return _validate_bundle(bundle)
    except SchemaError:
        raise
    except (TypeError, KeyError, ValueError, RecursionError) as e:
        raise SchemaError('Malformed contract: ' + str(e)) from e


def binding_for(b, target_type, target_id, evidence_ids):
    """Authoring helper only: identity pinning does not supply semantic judgments."""
    plural = {'claim': 'claims', 'obligation': 'obligations'}[target_type]
    target = next(n for n in b[plural] if n['id'] == target_id)
    ev = {e['id']: e for e in b['evidence']}
    artifacts = {a['id']: a for a in b['artifacts']}
    ids = {aid for eid in evidence_ids for aid in ev[eid]['artifact_ids']}
    return {'problem_sha256': digest(b['problem']), 'target_sha256': digest(target),
            'evidence_sha256': {eid: digest(ev[eid]) for eid in sorted(evidence_ids)},
            'artifacts_sha256': {aid: artifacts[aid]['sha256'] for aid in sorted(ids)}}


def read_artifacts(b, root):
    """Read named files only, 8 MiB aggregate, contained by resolved root; never execute."""
    root = Path(root).resolve()
    data, total = {}, 0
    for a in sorted(b['artifacts'], key=lambda a: a['id']):
        p = (root / a['path']).resolve()
        if not p.is_relative_to(root):
            raise SchemaError('Artifact escapes root (including symlink)')
        try:
            size = p.stat().st_size
            if not p.is_file() or size + total > MAX_BYTES:
                raise SchemaError('Artifact is not a bounded regular file')
            raw = p.read_bytes()
            total += len(raw)
            if total > MAX_BYTES:
                raise SchemaError('Artifact byte budget exceeded')
            data[a['id']] = raw
        except FileNotFoundError:
            pass
    return data


def map_evidence(bundle, artifact_bytes=None):
    """Pure mapping. Missing bytes never authenticate evidence; all proposed claims survive.

    artifact_bytes maps artifact ID to bytes. No source code is imported or executed.
    A supported result means the supplied judgment passed this contract, not that
    this mapper independently proved it. Numerical and empirical scopes never coerce.
    """
    b = load_bundle(bundle)
    artifact_bytes = {} if artifact_bytes is None else artifact_bytes
    if type(artifact_bytes) is not dict or any(type(x) is not bytes for x in artifact_bytes.values()):
        raise SchemaError('artifact_bytes must map IDs to bytes')
    artifacts = {a['id']: a for a in b['artifacts']}
    if not set(artifact_bytes) <= set(artifacts) or sum(map(len, artifact_bytes.values())) > MAX_BYTES:
        raise SchemaError('Unknown or oversized supplied artifact bytes')
    integrity = {}
    for aid, a in sorted(artifacts.items()):
        actual = hashlib.sha256(artifact_bytes[aid]).hexdigest() if aid in artifact_bytes else None
        integrity[aid] = {'declared_sha256': a['sha256'], 'observed_sha256': actual,
                          'state': 'missing' if actual is None else 'matched' if actual == a['sha256'] else 'mismatch'}
    ev = {e['id']: e for e in b['evidence']}
    js = sorted(b['judgments'], key=lambda j: j['id'])

    def evaluate(nodes_list, target_type, obligation_results=None):
        nodes = {n['id']: n for n in nodes_list}
        results = {}
        for nid in _order(nodes, 'depends_on'):
            n = nodes[nid]
            audits, good = [], []
            for j in [x for x in js if x['target_type'] == target_type and x['target_id'] == nid]:
                reasons = []
                expected = binding_for(b, target_type, nid, j['evidence_ids'])
                if j['binding'] != expected:
                    reasons.append('stale_or_inexact_binding')
                if any(integrity[aid]['state'] != 'matched' for aid in expected['artifacts_sha256']):
                    reasons.append('artifact_bytes_missing_or_mismatched')
                if not j['evidence_ids']:
                    reasons.append('no_evidence')
                if not any(j['scope'] in SUPPORT[ev[eid]['kind']] for eid in j['evidence_ids']):
                    reasons.append('evidence_kind_does_not_support_scope')
                needed = set(REQUIRED.get(j['scope'], set()))
                if any(ev[eid]['kind'] == 'formal_proof' for eid in j['evidence_ids']) and j['scope'] in {'conditional_theorem', 'intended_theorem'}:
                    needed.add('axioms_audited')
                if j['decision'] == 'supports' and any(j['checks'].get(k) != 'passed' for k in needed):
                    reasons.append('required_semantic_check_not_passed')
                if j['decision'] == 'supports' and any(v == 'failed' for v in j['checks'].values()):
                    reasons.append('explicit_semantic_check_failed')
                audits.append({'id': j['id'], 'usable': not reasons, 'reasons': reasons,
                               'decision': j['decision'], 'scope': j['scope']})
                if not reasons:
                    good.append(j)
            support = [j for j in good if j['decision'] == 'supports']
            refutes = [j for j in good if j['decision'] == 'refutes' and j['scope'] == n['scope'] and j['supported_statement'] == n['statement']]
            deps = [results[x] for x in n['depends_on']]
            required = [obligation_results[x] for x in n.get('obligations', [])]
            conditions = set(n['assumptions'])
            for d in deps:
                conditions.update(d['conditions'])
                if d['supported_scope'] == 'cited':
                    conditions.add('Cited premise ' + d['id'] + ' is retained as a premise, not proved here.')
                elif d['disposition'] == 'conditional':
                    conditions.add('Dependency ' + d['id'] + ' is conditional; its qualification is not discharged here.')
            blocked = [d['id'] for d in deps if d['disposition'] not in {'supported', 'conditional'}]
            open_obligations = [d['id'] for d in required if d['disposition'] != 'supported' or d['supported_scope'] != d['requested_scope']]
            exact = [j for j in support if j['scope'] == n['scope'] and j['supported_statement'] == n['statement']]
            selected = exact[0] if exact else support[0] if support else None
            if selected:
                for j in support:
                    if j['scope'] == selected['scope'] and j['supported_statement'] == selected['supported_statement']:
                        conditions.update(j['conditions'])
            if refutes and exact:
                disposition = 'conflicting'
            elif refutes:
                disposition = 'refuted'
            elif blocked or open_obligations:
                disposition = 'blocked'
            elif not selected:
                disposition = 'unbound' if audits and not good else 'inconclusive' if good else 'unsupported'
            elif not exact:
                disposition = 'narrowed'
            elif conditions or n['scope'] in {'cited', 'conditional_theorem'}:
                disposition = 'conditional'
            else:
                disposition = 'supported'
            if selected and n['scope'] == 'intended_theorem' and conditions and disposition == 'conditional':
                disposition = 'blocked'
            results[nid] = {
                'id': nid, 'target_type': target_type, 'target_sha256': digest(n),
                'statement': n['statement'], 'requested_scope': n['scope'], 'disposition': disposition,
                'supported_scope': selected['scope'] if selected else None,
                'supported_statement': selected['supported_statement'] if selected else None,
                'selected_judgment_id': selected['id'] if selected else None,
                'conditions': sorted(conditions), 'exclusions': list(n['exclusions']),
                'depends_on': list(n['depends_on']), 'blocked_dependencies': blocked,
                'obligations': list(n.get('obligations', [])), 'open_obligations': open_obligations,
                'evidence_ids': list(n['evidence_ids']), 'judgment_audit': audits,
                'evidence_families': sorted({ev[eid]['family'] for eid in n['evidence_ids']}),
                'legacy_statuses': {eid: ev[eid]['legacy_status'] for eid in n['evidence_ids'] if ev[eid]['legacy_status'] is not None},
            }
        return results

    obligations = evaluate(b['obligations'], 'obligation')
    claims = evaluate(b['claims'], 'claim', obligations)
    counts = {}
    for c in claims.values():
        counts[c['disposition']] = counts.get(c['disposition'], 0) + 1
    return {'schema': 'fm-evidence-map/1', 'bundle_sha256': digest(b), 'problem_sha256': digest(b['problem']),
            'problem': b['problem'], 'paper_state': 'draft_not_scientifically_accepted',
            'truth_boundary': 'All semantic judgments are caller-supplied; identity checks are not truth, independence or authorization checks.',
            'claims': claims, 'obligations': obligations, 'artifact_integrity': integrity,
            'artifacts': b['artifacts'], 'evidence': b['evidence'], 'judgments': b['judgments'],
            'attempts': b['attempts'], 'costs': b['costs'], 'paper': b['paper'],
            'summary': {'proposed_claims': len(claims), 'dispositions': counts,
                        'attempts_recorded': len(b['attempts']),
                        'cost_coverage': 'Declared sensors only; absent sensors and total cost remain unknown.',
                        'obligations_open': sum(o['disposition'] != 'supported' for o in obligations.values()),
                        'costs_unknown': sum(c['value'] is None for c in b['costs'])},
            'limitations': ['No computation/proof was rerun. No automatic truth oracle or reviewer authentication.',
                            'All counts are bookkeeping, not a benchmark, comparative improvement, or scientific acceptance.',
                            'Legacy certified means conditional finite checking with certified/cited ancestors; it is not changed.',
                            'A formal statement check is not automatically the intended theorem. Numerical verification is not empirical validation.',
                            'This local draft is not publication permission; release/privacy/license review is separate.']}


def _safe(value):
    text = str(value).replace('\r\n', '\n').replace('\r', '\n')
    bidi = {0x061c, 0x200e, 0x200f, *range(0x202a, 0x202f), *range(0x2066, 0x206a)}
    text = ''.join(('\\u%04x' % ord(ch)) if ord(ch) in bidi or (ord(ch) < 32 and ch not in '\n\t') or 0x7f <= ord(ch) <= 0x9f else ch for ch in text)
    text = html.escape(text, quote=False)
    return re.sub(r'([\\`*_{}\[\]()#+.!|>~-])', r'\\\1', text).replace('\n', '\n> ')


def _render_report(report):
    """Private renderer; callers enter through render_paper and a fresh mapping."""
    lines = ['# Foundation Math evidence report', '',
             '**Draft evidence report — not a complete or accepted scientific paper.**', '',
             '## Submitted metadata — unverified', '',
             'Caller-proposed paper title (unverified metadata, not an accepted claim):',
             '> ' + _safe(report['paper']['title']), '',
             'Caller-proposed problem title (unverified metadata):',
             '> ' + _safe(report['problem']['title']), '',
             'Caller-proposed objective (unverified metadata, not an achieved outcome):',
             '> ' + _safe(report['problem']['objective']), '',
             'Problem ID: `' + report['problem']['id'] + '`; revision: ' + _safe(report['problem']['revision']),
             '', 'Bundle SHA-256: `' + report['bundle_sha256'] + '`', '',
             '## Method and trust boundary', '', report['truth_boundary'], '',
             'No solver or historical workload is run. Explicit semantic judgments are mapped to exact identities; hashes check identity only.', '',
             '## Claim catalog']
    for cid in report['paper']['claim_ids']:
        c = report['claims'][cid]
        lines += ['', '### Claim ' + cid, '', '**Disposition: ' + c['disposition'] + '**; requested scope: `' + c['requested_scope'] + '`.',
                  '', 'Caller-proposed statement (not established by inclusion):', '> ' + _safe(c['statement']), '',
                  'Target SHA-256: `' + c['target_sha256'] + '`']
        if c['supported_statement'] is not None:
            lines += ['', 'Supplied scoped finding (`' + c['supported_scope'] + '`), subject to the disposition and conditions above/below:',
                      '> ' + _safe(c['supported_statement']), '', 'Judgment: `' + c['selected_judgment_id'] + '`.']
        for label, key in [('Supplied conditions / assumptions', 'conditions'), ('Supplied exclusions', 'exclusions'),
                           ('Dependencies', 'depends_on'), ('Blocked dependencies', 'blocked_dependencies'),
                           ('Required obligations', 'obligations'), ('Open obligations', 'open_obligations'),
                           ('Evidence references', 'evidence_ids'), ('Evidence families (not independent-vote counts)', 'evidence_families')]:
            lines += ['', label + ': ' + (', '.join(_safe(x) for x in c[key]) or 'none declared') + '.']
        for audit in c['judgment_audit']:
            lines += ['- Judgment `' + audit['id'] + '`: ' + ('usable supplied judgment' if audit['usable'] else 'NOT usable: ' + ', '.join(audit['reasons'])) + '.']
        if c['legacy_statuses']:
            lines += ['- Legacy statuses retained without promotion: ' + _safe(canonical_json(c['legacy_statuses'])) + '.']
    lines += ['', '## Obligation ledger']
    for o in report['obligations'].values():
        lines += ['', '- `' + o['id'] + '` — **' + o['disposition'] + '**; scope `' + o['requested_scope'] + '`.',
                  '  Caller-proposed obligation statement: ' + _safe(o['statement']), '  Identity: `' + o['target_sha256'] + '`.',
                  '  Evidence: ' + (', '.join(o['evidence_ids']) or 'none') + '; judgment: ' + (o['selected_judgment_id'] or 'none') + '.',
                  '  Supplied conditions: ' + (', '.join(_safe(x) for x in o['conditions']) or 'none declared') + '.',
                  '  Blocked dependencies: ' + (', '.join(o['blocked_dependencies']) or 'none') + '.',
                  '  Dependencies: ' + (', '.join(o['depends_on']) or 'none') + '.',
                  '  Supplied exclusions: ' + (', '.join(_safe(x) for x in o['exclusions']) or 'none declared') + '.',
                  '  Judgment audit: ' + _safe(canonical_json(o['judgment_audit'])) + '.']
    if not report['obligations']:
        lines += ['', 'No obligations declared; this is a caller assertion, not a completeness finding.']
    lines += ['', '## Artifacts and citations']
    for a in sorted(report['artifacts'], key=lambda a: a['id']):
        lines += ['', '- `' + a['id'] + '` — caller-supplied artifact description: ' + _safe(a['description']),
                  '  Path: ' + _safe(a['path']) + '; SHA-256: `' + a['sha256'] + '`; integrity: **' + report['artifact_integrity'][a['id']]['state'] + '**.']
    lines += ['', '## Evidence and semantic judgment provenance']
    for e in sorted(report['evidence'], key=lambda e: e['id']):
        lines += ['', '- `' + e['id'] + '`; kind `' + e['kind'] + '`; artifacts: ' + ', '.join(e['artifact_ids']) + '.',
                  '  Caller-supplied evidence description: ' + _safe(e['description']), '  Caller-supplied provenance: ' + _safe(e['provenance']), '  Declared family: ' + _safe(e['family']) + '.']
    for j in sorted(report['judgments'], key=lambda j: j['id']):
        lines += ['', '- Judgment `' + j['id'] + '`; target `' + j['target_type'] + ':' + j['target_id'] + '`; decision `' + j['decision'] + '`.',
                  '  Supplied by: ' + _safe(j['assessor']) + '; method: ' + _safe(j['method']) + '; family: ' + _safe(j['family']) + '.',
                  '  Caller-supplied assessed statement: ' + _safe(j['supported_statement']),
                  '  Assessed scope: ' + j['scope'] + '; conditions: ' + (', '.join(_safe(x) for x in j['conditions']) or 'none declared') + '.',
                  '  Evidence IDs: ' + (', '.join(j['evidence_ids']) or 'none') + '.',
                  '  Caller-supplied rationale: ' + _safe(j['rationale']), '  Explicit checks: ' + _safe(canonical_json(j['checks'])) + '.',
                  '  Exact binding: ' + _safe(canonical_json(j['binding'])) + '.']
    lines += ['', '## Reported attempts and cost coverage — caller-supplied records']
    for a in report['attempts']:
        lines += ['- Attempt `' + a['id'] + '` — ' + a['outcome'] + '; claims: ' + ', '.join(a['claim_ids']) + '; ' + _safe(a['note']) + '.']
    for c in report['costs']:
        lines += ['- `' + c['id'] + '`: ' + ('**unknown**' if c['value'] is None else str(c['value'])) + ' ' + _safe(c['unit']) + '; coverage: ' + _safe(c['coverage']) + '; sources: ' + (', '.join(c['source_artifact_ids']) or 'none') + '.']
    if not report['costs']:
        lines += ['- No cost measurements supplied; total cost is unknown.']
    lines += ['', 'Costs cover only named intervals/sensors. Unlisted costs are unknown, not zero.']
    lines += ['', '## Limitations and unresolved work']
    lines += ['- ' + _safe(x) for x in report['limitations']]
    lines += ['', '### Caller-supplied limitations — unverified prose', '',
              'These submitted annotations do not override any structured claim disposition.']
    lines += ['- Submitted annotation: ' + _safe(x) for x in report['paper']['limitations']]
    lines += ['', '**Rendering success is not theorem acceptance, proof completion, empirical validation, or paper acceptance.**', '']
    return '\n'.join(lines)


def render_paper(bundle, artifact_bytes=None):
    """Map the original bundle anew, then render. Never accept mutable output statuses.

    The same bundle and bytes yield the same report/draft. Supplying a map report
    instead of an input bundle is a schema error, preventing manuscript-only edits
    from bypassing the identity/semantic gate.
    """
    return _render_report(map_evidence(bundle, artifact_bytes))
