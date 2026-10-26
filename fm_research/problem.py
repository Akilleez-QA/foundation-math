"""Finite exact checks and dependency accounting, not proofs of research prose."""
from dataclasses import asdict, dataclass
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import platform
import re
import subprocess
from . import p1, rank, twoi, vendor
from .field import Q5


def _no_float(value):
    raise TypeError('ProblemSpec admits no floats or nonfinite numbers')


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _hash(value):
    return sha256(_json(value).encode()).hexdigest()


def _matches(kernel, value, expected):
    if 'decompose' in kernel and type(value) is str and type(expected) is str:
        return sorted(value.split('+')) == sorted(expected.split('+'))
    return _json(value) == _json(expected)


def _fields(value, names):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        raise ValueError('Unexpected or missing fields: ' + names)


def _text(value):
    if type(value) is not str or not value.strip():
        raise ValueError('Nonempty text required')


def _id(value):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_.:][A-Za-z0-9_.:-]{0,127}', value):
        raise ValueError('Invalid bounded identifier')


def _tensor(factors):
    result = twoi.irrep('1')
    if type(factors) is not list:
        raise TypeError('factors must be a list')
    for factor in factors:
        if isinstance(factor, dict):
            _fields(factor, 'sym_W')
        result = result @ (twoi.sym_W(factor['sym_W']) if isinstance(factor, dict) else twoi.irrep(factor))
    return str(result)


def _rational(value):
    if type(value) is int:
        return Fraction(value)
    if type(value) is not str or not re.fullmatch(r'-?\d+/[1-9]\d*', value):
        raise TypeError('Expected integer or n/d string')
    return Fraction(value)


def _rank(field, rows, p=None):
    if field not in ('Q', 'Q(sqrt5)', 'F_p'):
        raise ValueError('Unsupported field')
    def entry(x):
        if field == 'Q(sqrt5)' and type(x) is list and len(x) == 2:
            return Q5(*map(_rational, x))
        q = _rational(x)
        return q.numerator * pow(q.denominator, -1, p) % p if field == 'F_p' else q
    matrix = [[entry(x) for x in row] for row in rows]
    cert = rank.rank_exact(matrix, field, p)
    if not rank.verify_rank_certificate(matrix, cert):
        raise ValueError('Rank certificate verification failed')
    return {'rank': cert.rank, 'certificate': cert.to_dict()}


def _cohomology(blocks, twist, degree):
    return p1.cohomology([p1.Block(**b) for b in blocks], [twist])[twist][degree]


KERNELS = {
    'twoi.decompose_sym_W': lambda n: str(twoi.sym_W(n)),
    'twoi.decompose_tensor': _tensor,
    'twoi.invariant_count_sym_W': lambda degree: twoi.invariant_count(twoi.sym_W(degree)),
    'twoi.distinct': lambda a, b: bool(twoi.distinguish(a, b)),
    'rank': _rank,
    'p1.h0_dim': lambda blocks, twist: _cohomology(blocks, twist, 'h0_dim'),
    'p1.h1_dim': lambda blocks, twist: _cohomology(blocks, twist, 'h1_dim'),
}


def _ordered(spec):
    pending = {c['id']: c for c in spec['claims']}
    done = set()
    while pending:
        ready = [c for c in pending.values() if set(c['depends_on']) <= done]
        if not ready:
            raise ValueError('Unknown dependency or cycle')
        for c in ready:
            done.add(c['id'])
            del pending[c['id']]
            yield c


def load_spec(source):
    """Read JSON or detach a dict; validate shape and DAG without running checks."""
    raw = json.dumps(source) if isinstance(source, dict) else Path(source).read_text()
    spec = json.loads(raw, parse_float=_no_float, parse_constant=_no_float)
    _fields(spec, 'schema problem_id title objective repo roles assumptions exclusions claims')
    if spec['schema'] != 'fm-research-problem/1':
        raise ValueError('Unsupported ProblemSpec schema')
    _id(spec['problem_id'])
    for key in ('title', 'objective'):
        _text(spec[key])
    for key, names in (('repo', 'name commit'), ('roles', 'builder reviewer verifier')):
        _fields(spec[key], names)
        for value in spec[key].values():
            _text(value)
    for key in ('assumptions', 'exclusions', 'claims'):
        if type(spec[key]) is not list:
            raise TypeError(key + ' must be an array')
    for value in spec['assumptions'] + spec['exclusions']:
        _text(value)
    ids = set()
    for c in spec['claims']:
        _fields(c, 'id statement kind depends_on check')
        _id(c['id'])
        _text(c['statement'])
        if c['id'] in ids or c['kind'] not in ('computed', 'cited', 'argued'):
            raise ValueError('Duplicate id or invalid kind')
        ids.add(c['id'])
        if type(c['depends_on']) is not list:
            raise TypeError('depends_on must be an array')
        for dep in c['depends_on']:
            _id(dep)
        if c['kind'] == 'computed':
            check = c['check']
            _fields(check, 'kernel args expect')
            if type(check['kernel']) is not str or check['kernel'] not in KERNELS:
                raise ValueError('Unknown kernel')
            expected_type = str if 'decompose' in check['kernel'] else bool if check['kernel'] == 'twoi.distinct' else int
            if type(check['args']) is not dict or type(check['expect']) is not expected_type:
                raise TypeError('Invalid check arguments or expectation type')
        elif c['check'] is not None:
            raise ValueError('Only computed claims carry checks')
    list(_ordered(spec))
    return spec


def _source_hash():
    """Bind the research module bytes (sorted filenames) and pinned catalog hash."""
    h = sha256(vendor.catalog_sha256().encode())
    for path in sorted(Path(__file__).parent.glob('*.py')):
        h.update(path.name.encode() + b'\0' + path.read_bytes() + b'\0')
    return h.hexdigest()


@dataclass(frozen=True)
class Evidence:
    claim_id: str
    kernel: str
    args_sha256: str
    expected: object
    observed: object
    verdict: str
    output_sha256: str
    kernel_source_sha256: str
    fm_research_commit: str
    python_version: str

    def to_dict(self):
        return asdict(self)


def run_check(claim):
    """Execute only a fixed exact kernel; rank output includes its checked witness."""
    c = json.loads(json.dumps(claim), parse_float=_no_float, parse_constant=_no_float)
    if c['kind'] != 'computed':
        raise ValueError('Only computed claims can run')
    check = c['check']
    try:
        observed = KERNELS[check['kernel']](**check['args'])
        value = observed['rank'] if check['kernel'] == 'rank' else observed
        verdict = 'PASS' if _matches(check['kernel'], value, check['expect']) else 'FAIL'
    except (ValueError, TypeError, KeyError, ArithmeticError, RuntimeError) as exc:
        observed, verdict = {'error': type(exc).__name__, 'message': str(exc)}, 'ERROR'
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=vendor.VENDOR.parent.parent,
                                         stderr=subprocess.DEVNULL, text=True, timeout=5).strip()
    except (OSError, subprocess.SubprocessError):
        commit = 'unknown'
    return Evidence(c['id'], check['kernel'], _hash(check['args']), check['expect'], observed,
                    verdict, _hash(observed), _source_hash(), commit, platform.python_version())


def gate(spec, evidence_by_claim):
    """Consume trusted local evidence with integrity checks; hashes are not signatures."""
    statuses, ancestors = {}, {}
    source = _source_hash()
    for c in _ordered(load_spec(spec)):
        ancestors[c['id']] = set(c['depends_on']).union(*(ancestors[d] for d in c['depends_on']))
        status = c['kind']
        if status == 'computed':
            status, e, check = 'unchecked', evidence_by_claim.get(c['id']), c['check']
            e = e.to_dict() if isinstance(e, Evidence) else e
            if (isinstance(e, dict) and e.get('claim_id') == c['id'] and e.get('kernel') == check['kernel']
                    and e.get('args_sha256') == _hash(check['args']) and _json(e.get('expected')) == _json(check['expect'])
                    and e.get('output_sha256') == _hash(e.get('observed')) and e.get('kernel_source_sha256') == source):
                value = e['observed'].get('rank') if check['kernel'] == 'rank' and isinstance(e['observed'], dict) else e['observed']
                matches = _matches(check['kernel'], value, check['expect'])
                if e.get('verdict') == 'FAIL' and not matches:
                    status = 'refuted'
                elif e.get('verdict') == 'PASS' and matches:
                    status = 'certified' if all(statuses[d] in ('certified', 'cited') for d in ancestors[c['id']]) else 'blocked'
        statuses[c['id']] = status
    return statuses
