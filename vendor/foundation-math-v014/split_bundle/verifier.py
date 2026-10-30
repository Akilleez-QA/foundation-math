"""Separate checker. Never imports split-bundle contract/producer or fusion producer.

Uses independently audited exact class functions and weighted inner products,
not producer fusion multiplicities or producer cohomology branches.
"""
import hashlib,json
from character_ring.verifier import check_catalog,q,plus,times,scaled,total,symmetric,decompose,encoded
LABELS=('1','W','A','S4','D','T6','P','Wp','V')
DIMS=(1,2,3,4,5,6,4,2,3)
SIGNS=(1,-1,1,-1,1,-1,1,-1,1)
PIN='84ceb37bc32d10c4908e5b5f1f2f5994082074f2c2a9f36c846347750c79fa74'
SCOPE='formal_supplied_split_bundle_arithmetic_only'
class VerificationError(ValueError):
    def __init__(self,code,message):self.code=code;super().__init__(message)
def require(ok,code,message):
    if not ok:raise VerificationError(code,message)
def serial(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
def sha(obj):return hashlib.sha256(serial(obj).encode('ascii')).hexdigest()
def guarded_wire(obj,limit):
    pending=[(obj,0)];n=0
    while pending:
        val,depth=pending.pop();n+=1
        require(depth<16 and n<=8192,'E_BUDGET','Data bounds exceeded')
        k=type(val);require(k in (dict,list,str,int,type(None)),'E_TYPE','Exact JSON values required')
        if k in (dict,list):
            require(len(val)+len(pending)+n<=8192,'E_BUDGET','Too many data values')
            if k is dict:require(all(type(key) is str and len(key)<=256 for key in val),'E_TYPE','Invalid key')
            pending.extend((v,depth+1) for v in (val.values() if k is dict else val))
        elif k is str:require(len(val)<=256,'E_BUDGET','String too long')
        elif k is int:require(abs(val).bit_length()<=300,'E_BUDGET','Integer too large')
    s=serial(obj).encode('ascii');require(len(s)<=limit,'E_BUDGET','JSON byte budget exceeded');return s
def shape(x,names):require(type(x) is dict and set(x)==set(names),'E_SCHEMA','Unexpected object shape')
def blocks(x):
    require(type(x) is list and len(x)<=32,'E_SCHEMA','Bundle block-list required; maximum32')
    for b in x:
        shape(b,('irrep','twist','multiplicity'))
        require(type(b['irrep']) is str and b['irrep'] in LABELS,'E_SCHEMA','Invalid physical label')
        require(type(b['twist']) is int and -64<=b['twist']<=64,'E_SCHEMA','Invalid block twist')
        require(type(b['multiplicity']) is int and 0<=b['multiplicity']<=1000000,'E_SCHEMA','Invalid nonnegative multiplicity')
def validate_request(req):
    wire=guarded_wire(req,65536)
    require(type(req) is dict and req.get('operation') in ('cohomology','hom'),'E_SCHEMA','Invalid operation')
    op=req['operation'];shape(req,('schema','operation','bundle','twists') if op=='cohomology' else ('schema','operation','source','target'))
    require(type(req['schema']) is str and req['schema']=='fm-split-bundle-request-v1','E_SCHEMA','Invalid schema')
    if op=='hom':blocks(req['source']);blocks(req['target'])
    else:
        blocks(req['bundle']);ts=req['twists']
        require(type(ts) is list and 1<=len(ts)<=32,'E_SCHEMA','Invalid requested twist list')
        require(all(type(t) is int and -64<=t<=64 for t in ts),'E_SCHEMA','Invalid requested twist')
        require(len(set(ts))==len(ts),'E_SCHEMA','Repeated requested twist')
    return json.loads(wire)
def stats(bs):
    dim=[DIMS[LABELS.index(b['irrep'])]*b['multiplicity'] for b in bs]
    return {'rank':sum(dim),'degree':sum(d*b['twist'] for d,b in zip(dim,bs))}
def verify(expected_request,certificate):
    req=validate_request(expected_request);wire=guarded_wire(certificate,262144);table=check_catalog()
    sym_cache={}
    def s(n,j):
        key=(n,j)
        if key not in sym_cache:sym_cache[key]=symmetric(n,table[1][j])
        return sym_cache[key]
    def describe(ch,genuine):
        m=decompose(ch,table);require(all(abs(v).bit_length()<=128 for v in m),'E_BUDGET','Output coefficient too large')
        require(not genuine or min(m)>=0,'E_CHARACTER','Cohomology must be genuine')
        parity={SIGNS[i] for i,x in enumerate(m) if x}
        return {'multiplicities':m,'dimension':sum(d*x for d,x in zip(DIMS,m)),'classification':'genuine' if min(m)>=0 else 'proper_virtual','center_parity':'zero' if not parity else 'even' if parity=={1} else 'odd' if parity=={-1} else 'mixed','even_dimension':sum(DIMS[i]*m[i] for i in range(9) if SIGNS[i]>0),'odd_dimension':sum(DIMS[i]*m[i] for i in range(9) if SIGNS[i]<0),'negative_multiplicities':{LABELS[i]:m[i] for i in range(9) if m[i]<0},'class_values':[encoded(v) for v in ch]}
    if req['operation']=='cohomology':
        st=stats(req['bundle']);rows=[]
        for t in req['twists']:
            cohs=[]
            for cohomological_degree in (0,1):
                ch=[]
                for j in range(9):
                    terms=[]
                    for b in req['bundle']:
                        degree=b['twist']+t
                        symmetric_degree=degree if cohomological_degree==0 else -degree-2
                        if symmetric_degree>=0:
                            terms.append(scaled(b['multiplicity'],times(table[LABELS.index(b['irrep'])][j],s(symmetric_degree,j))))
                    ch.append(total(terms))
                cohs.append(tuple(ch))
            h0,h1=cohs;e=tuple(plus(x,scaled(-1,y)) for x,y in zip(h0,h1))
            a,b,c=describe(h0,True),describe(h1,True),describe(e,False)
            require(c['dimension']==st['degree']+(t+1)*st['rank'],'E_RIEMANN_ROCH','Signed dimension fails Riemann-Roch')
            rows.append({'twist':t,'rank':st['rank'],'degree':st['degree']+t*st['rank'],'h0':a,'h1':b,'euler':c})
        result={'operation':'cohomology','bundle':st,'twists':rows}
    else:
        ch=[]
        for j in range(9):
            terms=[]
            for a in req['source']:
                for b in req['target']:
                    d=b['twist']-a['twist']
                    if d>=0:
                        terms.append(scaled(a['multiplicity']*b['multiplicity'],times(times(table[LABELS.index(a['irrep'])][j],table[LABELS.index(b['irrep'])][j]),s(d,j))))
            ch.append(total(terms))
        h=describe(tuple(ch),True)
        result={'operation':'hom','source':stats(req['source']),'target':stats(req['target']),'hom_character':h,'equivariant_hom_dimension':h['multiplicities'][0],'conclusion':'dimension_of_equivariant_map_space_only_no_map_rank_or_embedding_claim'}
    expected={'schema':'fm-split-bundle-certificate-v1','catalog_sha256':PIN,'request_sha256':sha(req),'request':req,'result':result,'scope':SCOPE,'assumptions':{'group':'SL2(F5) over C','catalog_identification':'fixed_physical_marking_assumed_not_proved','base':'P(W) with determinant-one W and standard O(1) linearization','splitting':'supplied_formal_equivariant_direct_sum_assumed','geometry':'no_active_research_bundle_identification_or_map_rank_inference'}}
    require(wire.decode('ascii')==serial(expected),'E_CERTIFICATE','Certificate differs from independently derived external-request result')
    return {'schema':'fm-split-bundle-verification-v1','status':'verified_arithmetic','catalog_sha256':PIN,'request_sha256':sha(req),'certificate_sha256':sha(certificate),'result':result,'scope':SCOPE,'runtime_acceptance':False,'lean_proof':False,'geometric_realization':False}
