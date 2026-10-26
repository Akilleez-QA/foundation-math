"""Strict data-only request boundary and explicit finite budgets."""
from dataclasses import dataclass
import hashlib,json
from pathlib import Path
from typing import Literal
LABELS=('1','W','A','S4','D','T6','P','Wp','V')
CATALOG_SHA256='84ceb37bc32d10c4908e5b5f1f2f5994082074f2c2a9f36c846347750c79fa74'
BUDGETS={'request_bytes':65536,'certificate_bytes':262144,'nodes':127,'depth':16,'symmetric_degree':256,'input_coefficient_bits':63,'result_coefficient_bits':256,'field_component_bits':272,'json_integer_digits':90,'certificate_data_depth':32,'certificate_data_values':8192}
SCHEMA='fm-character-request-v1'
class DomainError(ValueError):
    def __init__(self,code,message):self.code=code;super().__init__(message)
def need(ok,code,message):
    if not ok:raise DomainError(code,message)
def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
def digest(obj):return hashlib.sha256(canonical(obj).encode('ascii')).hexdigest()
def load_json(raw,limit):
    need(type(raw) is bytes,'E_TYPE','JSON input must be bytes')
    need(len(raw)<=limit,'E_BUDGET','JSON byte budget exceeded')
    def pairs(items):
        d={}
        for k,v in items:
            need(k not in d,'E_JSON','Duplicate JSON object key');d[k]=v
        return d
    def integer(s):
        need(len(s.lstrip('-'))<=BUDGETS['json_integer_digits'],'E_BUDGET','JSON integer digit budget exceeded');return int(s)
    def no_float(s):raise DomainError('E_TYPE','Only exact JSON integers are accepted')
    try:return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_int=integer,parse_float=no_float,parse_constant=no_float)
    except (UnicodeError,json.JSONDecodeError,RecursionError) as e:raise DomainError('E_JSON','Malformed JSON') from e

def read_json(path,limit):
    try:
        with Path(path).open('rb') as f:raw=f.read(limit+1)
    except (OSError,ValueError) as e:raise DomainError('E_IO','Cannot read input file') from e
    return load_json(raw,limit)
def keys(obj,wanted):need(type(obj) is dict and all(type(k) is str for k in obj) and set(obj)==set(wanted),'E_SCHEMA','Unexpected object keys or object type')
def coeffs(obj,bits):
    need(type(obj) is dict and all(type(k) is str for k in obj) and set(obj)<=set(LABELS),'E_SCHEMA','Unknown physical label or non-object decomposition')
    for n,v in obj.items():
        need(type(v) is int and v!=0,'E_TYPE','Sparse coefficients must be nonzero exact integers')
        need(abs(v).bit_length()<=bits,'E_BUDGET','Coefficient bit budget exceeded')
    return tuple(obj.get(n,0) for n in LABELS)
@dataclass(frozen=True)
class Node:
    op: str
    value: object=None
    left: 'Node | None'=None
    right: 'Node | None'=None
@dataclass(frozen=True)
class Request:
    raw: dict
    root: Node
    classification: Literal['any','genuine','proper_virtual']
    equals: tuple[int,...] | None

def parse_request(obj):
    keys(obj,('schema','expression','expectation'))
    need(type(obj['schema']) is str and obj['schema']==SCHEMA,'E_SCHEMA','Unknown request schema')
    count=0
    def walk(x,depth):
        nonlocal count
        count+=1
        need(depth<=BUDGETS['depth'] and count<=BUDGETS['nodes'],'E_BUDGET','Expression node or depth budget exceeded')
        need(type(x) is dict and all(type(k) is str for k in x) and type(x.get('op')) is str,'E_SCHEMA','Expression needs an operation')
        op=x['op']
        if op=='irrep':
            keys(x,('op','label'));need(type(x['label']) is str and x['label'] in LABELS,'E_SCHEMA','Unknown physical label')
            return Node(op,LABELS.index(x['label']))
        if op=='virtual':
            keys(x,('op','coefficients'));return Node(op,coeffs(x['coefficients'],63))
        if op=='symmetric_power':
            keys(x,('op','degree'));d=x['degree']
            need(type(d) is int,'E_TYPE','Degree must be an exact integer')
            need(0<=d<=256,'E_BUDGET','Symmetric degree must be in [0,256]')
            return Node(op,d)
        need(op in ('add','subtract','tensor'),'E_SCHEMA','Unknown operation')
        keys(x,('op','left','right'))
        return Node(op,None,walk(x['left'],depth+1),walk(x['right'],depth+1))
    root=walk(obj['expression'],1)
    e=obj['expectation'];keys(e,('classification','equals'))
    need(type(e['classification']) is str and e['classification'] in ('any','genuine','proper_virtual'),'E_SCHEMA','Unknown expected classification')
    eq=None if e['equals'] is None else coeffs(e['equals'],256)
    # A canonical JSON round-trip detaches caller-owned mutable dictionaries.
    wire=canonical(obj)
    need(len(wire.encode('ascii'))<=BUDGETS['request_bytes'],'E_BUDGET','Canonical request byte budget exceeded')
    raw=json.loads(wire)
    return Request(raw,root,e['classification'],eq)
