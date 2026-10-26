"""Producer uses the vendored accepted integer-fusion character engine only."""
from character_ring.producer import VirtualCharacter,tensor,catalog,class_values,summarize
from .contract import PIN,SCOPE,ASSUMPTIONS,LABELS,need,parse_request,digest,data_guard
DIMS=(1,2,3,4,5,6,4,2,3)
ZERO=VirtualCharacter((0,)*9)
ONE=VirtualCharacter((1,)+(0,)*8)
W=VirtualCharacter((0,1,0,0,0,0,0,0,0))
def scaled(n,v):
    m=tuple(n*x for x in v.multiplicities);need(all(abs(x).bit_length()<=128 for x in m),'E_BUDGET','Result coefficient budget exceeded');return VirtualCharacter(m)
def irrep(label):return VirtualCharacter(tuple(int(x==label) for x in LABELS))
def stats(blocks):
    return {'rank':sum(DIMS[LABELS.index(b['irrep'])]*b['multiplicity'] for b in blocks),'degree':sum(DIMS[LABELS.index(b['irrep'])]*b['multiplicity']*b['twist'] for b in blocks)}
def calculate(request):
    req=parse_request(request);cat=catalog();syms=[ONE]
    def sym(n):
        while len(syms)<=n:
            d=len(syms);syms.append(tensor(W,syms[-1],cat).subtract(syms[-2] if d>=2 else ZERO))
        return syms[n]
    def describe(ch):return dict(summarize(ch),class_values=class_values(ch,cat))
    if req['operation']=='cohomology':
        base=stats(req['bundle']);rows=[]
        for t in req['twists']:
            h0=h1=ZERO
            for b in req['bundle']:
                n=b['twist']+t
                if n==-1 or b['multiplicity']==0:continue
                ch=scaled(b['multiplicity'],tensor(irrep(b['irrep']),sym(n if n>=0 else -n-2),cat))
                if n>=0:h0=h0.add(ch)
                else:h1=h1.add(ch)
            e=h0.subtract(h1)
            rows.append({'twist':t,'rank':base['rank'],'degree':base['degree']+t*base['rank'],'h0':describe(h0),'h1':describe(h1),'euler':describe(e)})
        result={'operation':'cohomology','bundle':base,'twists':rows}
    else:
        h=ZERO
        for a in req['source']:
            for b in req['target']:
                n=b['twist']-a['twist'];m=a['multiplicity']*b['multiplicity']
                if n<0 or m==0:continue
                # Every catalog irrep has real character and is self-dual.
                ch=tensor(tensor(irrep(a['irrep']),irrep(b['irrep']),cat),sym(n),cat)
                h=h.add(scaled(m,ch))
        result={'operation':'hom','source':stats(req['source']),'target':stats(req['target']),'hom_character':describe(h),'equivariant_hom_dimension':h.multiplicities[0],'conclusion':'dimension_of_equivariant_map_space_only_no_map_rank_or_embedding_claim'}
    cert={'schema':'fm-split-bundle-certificate-v1','catalog_sha256':PIN,'request_sha256':digest(req),'request':req,'result':result,'scope':SCOPE,'assumptions':ASSUMPTIONS.copy()}
    data_guard(cert,262144);return cert
