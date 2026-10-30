"""Integer fusion producer; verifier independently evaluates exact class functions."""
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import hashlib,json
from .contract import BUDGETS,CATALOG_SHA256,LABELS,DomainError,canonical,digest,need,parse_request
DIM=(1,2,3,4,5,6,4,2,3)
PARITY=(1,-1,1,-1,1,-1,1,-1,1)
ZERO=(0,)*9
ONE=(1,)+(0,)*8
@dataclass(frozen=True)
class VirtualCharacter:
    multiplicities: tuple[int,...]
    def __post_init__(self):
        need(type(self.multiplicities) is tuple and len(self.multiplicities)==9,'E_TYPE','Character requires a nine-integer tuple')
        need(all(type(v) is int for v in self.multiplicities),'E_TYPE','Character multiplicities must be exact integers')
        need(all(abs(v).bit_length()<=256 for v in self.multiplicities),'E_BUDGET','Intermediate coefficient bit budget exceeded')
    @property
    def classification(self):return 'genuine' if min(self.multiplicities)>=0 else 'proper_virtual'
    def add(self,other):return VirtualCharacter(tuple(a+b for a,b in zip(self.multiplicities,other.multiplicities)))
    def subtract(self,other):return VirtualCharacter(tuple(a-b for a,b in zip(self.multiplicities,other.multiplicities)))

def catalog():
    try:
        with Path(__file__).with_name('catalog.json').open('rb') as f:raw=f.read(65537)
    except OSError as e:raise DomainError('E_CATALOG','Fixed catalog unavailable') from e
    need(hashlib.sha256(raw).hexdigest()==CATALOG_SHA256,'E_CATALOG','Fixed catalog digest mismatch')
    return json.loads(raw)
def tensor(a,b,cat):
    out=[0]*9
    for i,x in enumerate(a.multiplicities):
        for j,y in enumerate(b.multiplicities):
            for k,n in enumerate(cat['fusion'][i][j]):out[k]+=x*y*n
    return VirtualCharacter(tuple(out))
def evaluate(node,cat):
    if node.op=='irrep':return VirtualCharacter(tuple(int(i==node.value) for i in range(9)))
    if node.op=='virtual':return VirtualCharacter(node.value)
    if node.op=='symmetric_power':
        a,b=VirtualCharacter(ZERO),VirtualCharacter(ONE)
        w=VirtualCharacter((0,1,0,0,0,0,0,0,0))
        for _ in range(node.value):a,b=b,tensor(w,b,cat).subtract(a)
        return b
    a,b=evaluate(node.left,cat),evaluate(node.right,cat)
    if node.op=='add':return a.add(b)
    if node.op=='subtract':return a.subtract(b)
    return tensor(a,b,cat)
def summarize(v):
    m=v.multiplicities
    signs={PARITY[i] for i in range(9) if m[i]}
    return {'multiplicities':list(m),'dimension':sum(a*b for a,b in zip(m,DIM)), 'classification':v.classification,'center_parity':'zero' if not signs else 'even' if signs=={1} else 'odd' if signs=={-1} else 'mixed','even_dimension':sum(m[i]*DIM[i] for i in range(9) if PARITY[i]==1),'odd_dimension':sum(m[i]*DIM[i] for i in range(9) if PARITY[i]==-1),'negative_multiplicities':{LABELS[i]:m[i] for i in range(9) if m[i]<0}}
def class_values(v,cat):
    out=[]
    for c in range(9):
        a=b=Fraction(0)
        for i,n in enumerate(v.multiplicities):
            p,q,r,s=cat['characters'][i][c];a+=n*Fraction(p,q);b+=n*Fraction(r,s)
        out.append([a.numerator,a.denominator,b.numerator,b.denominator])
    return out
def calculate(request:dict)->dict:
    req=parse_request(request);cat=catalog();v=evaluate(req.root,cat)
    need(req.classification in ('any',v.classification),'E_EXPECTATION','Requested classification does not hold')
    need(req.equals is None or req.equals==v.multiplicities,'E_EXPECTATION','Requested decomposition does not hold')
    return {'schema':'fm-character-certificate-v1','catalog_sha256':CATALOG_SHA256,'request_sha256':digest(req.raw),'request':req.raw,'result':summarize(v),'class_values':class_values(v,cat),'scope':'universal_representation_arithmetic_only'}
