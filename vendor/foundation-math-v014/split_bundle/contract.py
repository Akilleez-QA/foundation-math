"""Data-only bounded formal-splitting requests. Not an object recognition API."""
import hashlib,json
from pathlib import Path
from character_ring.contract import DomainError,load_json as _load_json
LABELS=('1','W','A','S4','D','T6','P','Wp','V')
PIN='84ceb37bc32d10c4908e5b5f1f2f5994082074f2c2a9f36c846347750c79fa74'
BUDGETS={'request_bytes':65536,'certificate_bytes':262144,'blocks_per_bundle':32,'requested_twists':32,'absolute_block_twist':64,'absolute_requested_twist':64,'multiplicity':1000000,'symmetric_degree':128,'result_bits':128,'data_depth':16,'data_values':8192,'string_length':256,'integer_bits':300}
SCOPE='formal_supplied_split_bundle_arithmetic_only'
ASSUMPTIONS={'group':'SL2(F5) over C','catalog_identification':'fixed_physical_marking_assumed_not_proved','base':'P(W) with determinant-one W and standard O(1) linearization','splitting':'supplied_formal_equivariant_direct_sum_assumed','geometry':'no_active_research_bundle_identification_or_map_rank_inference'}
def need(ok,code,message):
    if not ok:raise DomainError(code,message)
def serial(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
def digest(obj):return hashlib.sha256(serial(obj).encode('ascii')).hexdigest()
def data_guard(obj,limit):
    stack=[(obj,1)];count=0
    while stack:
        value,depth=stack.pop();count+=1
        need(depth<=16 and count<=8192,'E_BUDGET','Data depth/value budget exceeded')
        kind=type(value);need(kind in (dict,list,str,int,type(None)),'E_TYPE','Only exact JSON data types accepted')
        if kind is dict:
            need(len(value)<=8192-count-len(stack),'E_BUDGET','Data value budget exceeded')
            need(all(type(k) is str and len(k)<=256 for k in value),'E_TYPE','Invalid object keys')
            stack.extend((v,depth+1) for v in value.values())
        elif kind is list:
            need(len(value)<=8192-count-len(stack),'E_BUDGET','Data value budget exceeded')
            stack.extend((v,depth+1) for v in value)
        elif kind is str:need(len(value)<=256,'E_BUDGET','String length budget exceeded')
        elif kind is int:need(abs(value).bit_length()<=300,'E_BUDGET','Integer bit budget exceeded')
    wire=serial(obj).encode('ascii');need(len(wire)<=limit,'E_BUDGET','Canonical JSON byte budget exceeded');return wire

def load_json(raw,limit):
    need(type(raw) is bytes,'E_TYPE','JSON bytes required')
    need(len(raw)<=limit,'E_BUDGET','JSON byte budget exceeded')
    depth=0;quoted=False;escaped=False
    for byte in raw:
        if quoted:
            if escaped:escaped=False
            elif byte==92:escaped=True
            elif byte==34:quoted=False
        elif byte==34:quoted=True
        elif byte in (91,123):
            depth+=1;need(depth<=16,'E_BUDGET','JSON nesting budget exceeded')
        elif byte in (93,125):depth-=1
    obj=_load_json(raw,limit);data_guard(obj,limit);return obj

def read_json(path,limit):
    try:
        with Path(path).open('rb') as f:raw=f.read(limit+1)
    except (OSError,ValueError) as e:raise DomainError('E_IO','Cannot read input file') from e
    return load_json(raw,limit)

def keys(obj,wanted):need(type(obj) is dict and set(obj)==set(wanted),'E_SCHEMA','Unexpected object keys')
def integer(x,lo,hi):
    need(type(x) is int,'E_TYPE','Exact integer required');need(lo<=x<=hi,'E_BUDGET','Integer outside finite domain')
def bundle(x):
    need(type(x) is list,'E_TYPE','Bundle must be a block list');need(len(x)<=32,'E_BUDGET','At most 32 blocks per bundle')
    for b in x:
        keys(b,('irrep','twist','multiplicity'));need(type(b['irrep']) is str and b['irrep'] in LABELS,'E_SCHEMA','Unknown physical irrep')
        integer(b['twist'],-64,64);integer(b['multiplicity'],0,1000000)
def parse_request(obj):
    wire=data_guard(obj,65536)
    need(type(obj) is dict and type(obj.get('operation')) is str,'E_SCHEMA','Request operation required')
    op=obj['operation'];need(op in ('cohomology','hom'),'E_SCHEMA','Unknown operation')
    keys(obj,('schema','operation','bundle','twists') if op=='cohomology' else ('schema','operation','source','target'))
    need(obj['schema']=='fm-split-bundle-request-v1','E_SCHEMA','Unknown request schema')
    if op=='cohomology':
        bundle(obj['bundle']);ts=obj['twists'];need(type(ts) is list,'E_TYPE','Twists must be a list');need(1<=len(ts)<=32,'E_BUDGET','Require 1..32 twists')
        for t in ts:integer(t,-64,64)
        need(len(set(ts))==len(ts),'E_SCHEMA','Requested twists must be distinct')
    else:bundle(obj['source']);bundle(obj['target'])
    return json.loads(wire)
