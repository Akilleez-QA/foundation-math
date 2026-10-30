"""Independent checker: standard library only; imports no producer/contract code.

The fixed table's identification with the marked group is a mathematical input.
Orthogonality checks algebraic consistency, not that identification.
"""
from fractions import Fraction as F
from pathlib import Path
import hashlib,json
LABELS=('1','W','A','S4','D','T6','P','Wp','V')
DIMS=(1,2,3,4,5,6,4,2,3)
SIGNS=(1,-1,1,-1,1,-1,1,-1,1)
PIN='84ceb37bc32d10c4908e5b5f1f2f5994082074f2c2a9f36c846347750c79fa74'
SIZES=(1,1,30,20,20,12,12,12,12)
_AUDITED_TABLE=None
class VerificationError(ValueError):
    def __init__(self,code,message):self.code=code;super().__init__(message)
def require(ok,code,message):
    if not ok:raise VerificationError(code,message)
def serial(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
def sha(obj):return hashlib.sha256(serial(obj).encode('ascii')).hexdigest()
def q(a=0,b=0):return (F(a),F(b))
def plus(x,y):return (x[0]+y[0],x[1]+y[1])
def times(x,y):return (x[0]*y[0]+5*x[1]*y[1],x[0]*y[1]+x[1]*y[0])
def scaled(c,x):return (c*x[0],c*x[1])
def total(xs):
    out=q()
    for x in xs:out=plus(out,x)
    return out
def symmetric(n,x):
    prev,cur=q(),q(1)
    for _ in range(n):prev,cur=cur,plus(times(x,cur),scaled(-1,prev))
    return cur
def inner(a,b):return total(scaled(F(s,120),times(x,y)) for s,x,y in zip(SIZES,a,b))
def combine(m,table):return tuple(total(scaled(m[i],table[i][j]) for i in range(9)) for j in range(9))
def encoded(x):return [x[0].numerator,x[0].denominator,x[1].numerator,x[1].denominator]
def decompose(ch,table):
    out=[]
    for row in table:
        a,b=inner(ch,row)
        require(b==0 and a.denominator==1,'E_CHARACTER','Class function has nonintegral irreducible multiplicity')
        n=int(a);require(abs(n).bit_length()<=256,'E_BUDGET','Intermediate coefficient bit budget exceeded');out.append(n)
    require(combine(out,table)==ch,'E_CHARACTER','Class function does not reconstruct')
    return out

def check_catalog(raw=None):
    global _AUDITED_TABLE
    if raw is None:
        try:
            with Path(__file__).with_name('catalog.json').open('rb') as f:raw=f.read(65537)
        except OSError as e:raise VerificationError('E_CATALOG','Fixed catalog unavailable') from e
    require(type(raw) is bytes and len(raw)<=65536,'E_CATALOG','Catalog byte budget exceeded')
    require(hashlib.sha256(raw).hexdigest()==PIN,'E_CATALOG','Fixed catalog digest mismatch')
    if _AUDITED_TABLE is not None:return _AUDITED_TABLE
    c=json.loads(raw)
    require(tuple(c['labels'])==LABELS and tuple(c['dimensions'])==DIMS and tuple(c['center_signs'])==SIGNS,'E_CATALOG','Fixed physical labels mismatch')
    require(c['group_order']==sum(SIZES)==120 and tuple(x['size'] for x in c['classes'])==SIZES,'E_CATALOG','Class weights mismatch')
    table=tuple(tuple((F(a,b),F(d,e)) for a,b,d,e in row) for row in c['characters'])
    trace=(q(2),q(-2),q(0),q(1),q(-1),q(F(1,2),F(1,2)),q(F(-1,2),F(-1,2)),q(F(1,2),F(-1,2)),q(F(-1,2),F(1,2)))
    require(table[1]==trace,'E_CATALOG','Physical W trace mismatch')
    require(tuple(encoded(t) for t in trace)==tuple(x['W_trace'] for x in c['classes']),'E_CATALOG','Class trace metadata mismatch')
    for i in range(9):
        require(table[i][0]==q(DIMS[i]) and table[i][1]==q(SIGNS[i]*DIMS[i]),'E_CATALOG','Dimension/center mismatch')
        for j in range(9):require(inner(table[i],table[j])==q(int(i==j)),'E_CATALOG','Table not orthonormal')
    require(sum(d*d for d in DIMS)==120,'E_CATALOG','Squared dimensions mismatch')
    for n in range(6):require(table[n]==tuple(symmetric(n,x) for x in trace),'E_CATALOG','Physical symmetric-power marking mismatch')
    require(table[6]==tuple(q(n) for n in (4,4,0,1,1,-1,-1,-1,-1)),'E_CATALOG','Physical P mismatch')
    require(table[7]==tuple(plus(times(x,p),scaled(-1,t)) for x,p,t in zip(trace,table[6],table[5])),'E_CATALOG','Physical Wp mismatch')
    require(table[8]==tuple(plus(symmetric(6,x),scaled(-1,p)) for x,p in zip(trace,table[6])),'E_CATALOG','Physical V mismatch')
    for i in range(9):
        for j in range(9):
            m=decompose(tuple(times(x,y) for x,y in zip(table[i],table[j])),table)
            require(m==c['fusion'][i][j] and min(m)>=0,'E_CATALOG','Fusion disagrees with class inner products')
            require(sum(m[k]*DIMS[k] for k in range(9))==DIMS[i]*DIMS[j],'E_CATALOG','Fusion dimension mismatch')
            require(all(not m[k] or SIGNS[k]==SIGNS[i]*SIGNS[j] for k in range(9)),'E_CATALOG','Fusion center mismatch')
    _AUDITED_TABLE=table
    return table

def shape(x,names):require(type(x) is dict and all(type(k) is str for k in x) and set(x)==set(names),'E_SCHEMA','Unexpected object keys or object type')
def vector(x,bits):
    require(type(x) is dict and all(type(k) is str for k in x) and set(x)<=set(LABELS),'E_SCHEMA','Unknown physical label or decomposition type')
    for n,v in x.items():
        require(type(v) is int and v!=0,'E_TYPE','Sparse coefficients must be nonzero exact integers')
        require(abs(v).bit_length()<=bits,'E_BUDGET','Coefficient bit budget exceeded')
    return [x.get(n,0) for n in LABELS]
def validate_request(req):
    shape(req,('schema','expression','expectation'))
    require(type(req['schema']) is str and req['schema']=='fm-character-request-v1','E_SCHEMA','Unknown request schema')
    count=0
    def visit(x,depth):
        nonlocal count
        count+=1;require(count<=127 and depth<=16,'E_BUDGET','Expression node or depth budget exceeded')
        require(type(x) is dict and all(type(k) is str for k in x) and type(x.get('op')) is str,'E_SCHEMA','Expression needs an operation')
        op=x['op']
        if op=='irrep':
            shape(x,('op','label'));require(type(x['label']) is str and x['label'] in LABELS,'E_SCHEMA','Unknown physical label')
        elif op=='virtual':shape(x,('op','coefficients'));vector(x['coefficients'],63)
        elif op=='symmetric_power':
            shape(x,('op','degree'));require(type(x['degree']) is int,'E_TYPE','Degree must be an exact integer');require(0<=x['degree']<=256,'E_BUDGET','Symmetric degree must be in [0,256]')
        else:
            require(op in ('add','subtract','tensor'),'E_SCHEMA','Unknown operation');shape(x,('op','left','right'));visit(x['left'],depth+1);visit(x['right'],depth+1)
    visit(req['expression'],1)
    shape(req['expectation'],('classification','equals'));e=req['expectation']
    require(type(e['classification']) is str and e['classification'] in ('any','genuine','proper_virtual'),'E_SCHEMA','Unknown expected classification')
    if e['equals'] is not None:vector(e['equals'],256)
    require(len(serial(req).encode('ascii'))<=65536,'E_BUDGET','Canonical request byte budget exceeded')

def evaluate_class_expression(expr,table):
    op=expr['op']
    if op=='irrep':ch=table[LABELS.index(expr['label'])]
    elif op=='virtual':ch=combine(vector(expr['coefficients'],63),table)
    elif op=='symmetric_power':ch=tuple(symmetric(expr['degree'],x) for x in table[1])
    else:
        left=evaluate_class_expression(expr['left'],table)[0];right=evaluate_class_expression(expr['right'],table)[0]
        if op=='tensor':ch=tuple(times(a,b) for a,b in zip(left,right))
        else:ch=tuple(plus(a,scaled(1 if op=='add' else -1,b)) for a,b in zip(left,right))
    for a,b in ch:
        require(max(abs(a.numerator).bit_length(),a.denominator.bit_length(),abs(b.numerator).bit_length(),b.denominator.bit_length())<=272,'E_BUDGET','Intermediate field component bit budget exceeded')
    return ch,decompose(ch,table)
def certificate_wire(obj):
    # In-memory API is also data-only: no subclasses, bool, float or custom keys.
    stack=[(obj,1)];count=0;wire_bytes=0
    def reserve(n):
        nonlocal wire_bytes
        wire_bytes+=n
        require(wire_bytes<=262144,'E_BUDGET','Canonical certificate byte budget exceeded')
    def reserve_string(text):
        # Cheap lower bound rejects huge caller-owned strings before scanning.
        require(len(text)+wire_bytes+2<=262144,'E_BUDGET','Canonical certificate byte budget exceeded')
        reserve(2)
        for ch in text:
            n=ord(ch)
            reserve(2 if ch in '\"\\\b\f\n\r\t' else 6 if n<32 or 127<=n<=65535 else 12 if n>65535 else 1)
    while stack:
        item,depth=stack.pop();count+=1
        require(depth<=32 and count<=8192,'E_BUDGET','Certificate data depth/value budget exceeded')
        kind=type(item)
        require(kind in (dict,list,str,int,type(None)),'E_CERTIFICATE','Certificate must contain exact JSON data types')
        if kind is dict:
            require(all(type(k) is str for k in item),'E_CERTIFICATE','Certificate keys must be exact strings')
            require(len(stack)+len(item)<=8192-count,'E_BUDGET','Certificate data value budget exceeded')
            reserve(2+max(0,len(item)-1)+len(item))
            for key in item:reserve_string(key)
            stack.extend((v,depth+1) for v in item.values())
        elif kind is list:
            require(len(stack)+len(item)<=8192-count,'E_BUDGET','Certificate data value budget exceeded')
            reserve(2+max(0,len(item)-1))
            stack.extend((v,depth+1) for v in item)
        elif kind is str:reserve_string(item)
        elif kind is type(None):reserve(4)
        elif kind is int:
            require(abs(item).bit_length()<=300 and len(str(abs(item)))<=90,'E_BUDGET','Certificate integer digit budget exceeded')
            reserve(len(str(item)))
    try:wire=serial(obj).encode('ascii')
    except (TypeError,ValueError,RecursionError) as e:raise VerificationError('E_CERTIFICATE','Certificate is not JSON data') from e
    require(len(wire)==wire_bytes,'E_INTERNAL','Certificate JSON byte accounting mismatch')
    return wire

def verify(expected_request:dict,certificate:dict)->dict:
    validate_request(expected_request)
    # This detached request is independent of any request embedded in a certificate.
    req=json.loads(serial(expected_request))
    require(type(certificate) is dict,'E_CERTIFICATE','Certificate must be an object')
    wire=certificate_wire(certificate)
    require(len(wire)<=262144,'E_BUDGET','Canonical certificate byte budget exceeded')
    table=check_catalog();ch,m=evaluate_class_expression(req['expression'],table)
    classification='genuine' if all(x>=0 for x in m) else 'proper_virtual'
    e=req['expectation']
    require(e['classification'] in ('any',classification),'E_EXPECTATION','Requested classification does not hold')
    require(e['equals'] is None or vector(e['equals'],256)==m,'E_EXPECTATION','Requested decomposition does not hold')
    parity={SIGNS[i] for i in range(9) if m[i]}
    result={'multiplicities':m,'dimension':sum(DIMS[i]*m[i] for i in range(9)),'classification':classification,'center_parity':'zero' if not parity else 'even' if parity=={1} else 'odd' if parity=={-1} else 'mixed','even_dimension':sum(DIMS[i]*m[i] for i in range(9) if SIGNS[i]==1),'odd_dimension':sum(DIMS[i]*m[i] for i in range(9) if SIGNS[i]==-1),'negative_multiplicities':{LABELS[i]:m[i] for i in range(9) if m[i]<0}}
    expected={'schema':'fm-character-certificate-v1','catalog_sha256':PIN,'request_sha256':sha(req),'request':req,'result':result,'class_values':[encoded(x) for x in ch],'scope':'universal_representation_arithmetic_only'}
    # Serialized comparison distinguishes bool from integer and rejects extra keys,
    # noncanonical rationals, changed provenance, mismatched requests and scope.
    require(wire.decode('ascii')==serial(expected),'E_CERTIFICATE','Certificate does not match the external request and fixed catalog')
    return {'schema':'fm-character-verification-v1','status':'verified_arithmetic','catalog_sha256':PIN,'request_sha256':sha(req),'certificate_sha256':sha(certificate),'result':result,'scope':'universal_representation_arithmetic_only','runtime_acceptance':False,'lean_proof':False}
