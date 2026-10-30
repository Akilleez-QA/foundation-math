"""Exact virtual characters of the pinned, physically labeled SL2(F5) table.

The table's identification with the group is an input assumption. Symmetric
powers support only W and Wp: the catalog supplies no power maps or class orders.
"""
from dataclasses import dataclass
from fractions import Fraction
from . import vendor
from character_ring.contract import LABELS
from character_ring.producer import VirtualCharacter, catalog, class_values, tensor

_CAT = catalog()
ALIASES = {"W'": 'Wp', 'Wprime': 'Wp'}
DIMS = dict(zip(LABELS, _CAT['dimensions']))
CENTER_SIGN = dict(zip(LABELS, _CAT['center_signs']))


def label(name):
    """Normalize a physical label, preserving distinct same-dimension irreps."""
    if type(name) is not str:
        raise TypeError('Irrep label must be a string')
    name = ALIASES.get(name, name)
    if name not in LABELS:
        raise KeyError(f'Unknown irrep {name!r}; valid labels: {", ".join(LABELS)}')
    return name


def _integer(value):
    if type(value) is not int:
        raise TypeError('Expected an exact integer')
    return value


def _degree(value):
    _integer(value)
    if not 0 <= value <= 256:
        raise ValueError('Degree must be in [0, 256] (vendor symmetric-power scope)')
    return value


@dataclass(frozen=True)
class Rep:
    """Immutable integral multiplicities in LABELS order, with vendor bit bounds."""
    multiplicities: tuple = (0,) * len(LABELS)

    def __post_init__(self):
        values = tuple(self.multiplicities)
        for value in values:
            _integer(value)
        VirtualCharacter(values)
        object.__setattr__(self, 'multiplicities', values)

    def __add__(self, other):
        if not isinstance(other, Rep):
            return NotImplemented
        return Rep(tuple(a + b for a, b in zip(self.multiplicities, other.multiplicities)))

    def __sub__(self, other):
        if not isinstance(other, Rep):
            return NotImplemented
        return self + other * -1

    def __mul__(self, scalar):
        _integer(scalar)
        return Rep(tuple(scalar * a for a in self.multiplicities))

    __rmul__ = __mul__

    def tensor(self, other):
        if not isinstance(other, Rep):
            raise TypeError('Tensor product requires a Rep')
        result = tensor(VirtualCharacter(self.multiplicities),
                        VirtualCharacter(other.multiplicities), _CAT)
        return Rep(result.multiplicities)

    __matmul__ = tensor

    def sym(self, n):
        """Sym^n of W or Wp, 0 <= n <= 256, via determinant-one recurrence."""
        _degree(n)
        if self not in (irrep('W'), irrep('Wp')):
            raise NotImplementedError('Symmetric powers supported only for W and Wp')
        previous, current = Rep(), irrep('1')
        for _ in range(n):
            previous, current = current, self @ current - previous
        return current

    @property
    def dim(self):
        return sum(m * d for m, d in zip(self.multiplicities, _CAT['dimensions']))

    @property
    def is_genuine(self):
        return all(m >= 0 for m in self.multiplicities)

    def decompose(self):
        return {name: m for name, m in zip(LABELS, self.multiplicities) if m}

    def __str__(self):
        terms = []
        for name, m in self.decompose().items():
            term = name if abs(m) == 1 else f'{abs(m)}*{name}'
            terms.append(('-' if m < 0 else '+') + term)
        return ''.join(terms).lstrip('+') or '0'


def irrep(name):
    name = label(name)
    return Rep(tuple(int(x == name) for x in LABELS))


def sym_W(n):
    return irrep('W').sym(n)


def invariant_count(rep):
    """Trivial multiplicity (signed for virtual characters)."""
    if not isinstance(rep, Rep):
        raise TypeError('Expected a Rep')
    return rep.multiplicities[0]


def invariant_degrees(max_degree):
    """Inclusive list of (degree, nonzero invariant multiplicity)."""
    _degree(max_degree)
    return [(d, n) for d in range(max_degree + 1) if (n := invariant_count(sym_W(d)))]


def molien_check(max_degree=60):
    """Check coefficients through max_degree against (1+t^30)/((1-t^12)(1-t^20))."""
    _degree(max_degree)
    expected = [0] * (max_degree + 1)
    for offset in (0, 30):
        for a in range(offset, max_degree + 1, 12):
            for d in range(a, max_degree + 1, 20):
                expected[d] += 1
    return all(invariant_count(sym_W(d)) == n for d, n in enumerate(expected))


def character_values(rep):
    """Exact (a,b) values representing a+b*sqrt(5), in catalog class order."""
    if not isinstance(rep, Rep):
        raise TypeError('Expected a Rep')
    return tuple((Fraction(a, b), Fraction(c, d)) for a, b, c, d in
                 class_values(VirtualCharacter(rep.multiplicities), _CAT))


def inner(rep1, rep2):
    """Real-character inner product from class sizes, independent of fusion."""
    rational = irrational = Fraction(0)
    for cls, (a, b), (c, d) in zip(_CAT['classes'], character_values(rep1),
                                  character_values(rep2)):
        weight = Fraction(cls['size'], _CAT['group_order'])
        rational += weight * (a * c + 5 * b * d)
        irrational += weight * (a * d + b * c)
    if irrational or rational.denominator != 1:
        raise RuntimeError('Catalog inner product is not integral')
    return rational


def distinguish(a, b):
    """Class indices separating two irreducible labels."""
    return [i for i, (x, y) in enumerate(zip(character_values(irrep(a)),
                                            character_values(irrep(b)))) if x != y]
