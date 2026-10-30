"""Formal supplied equivariant split bundles on P(W), not geometric realization.

Uses the vendor bounds: 32 blocks/twists, twists in [-64,64], multiplicity
in [0,1000000]. Hom returns the character of all maps, not a chosen map's rank.
"""
from dataclasses import asdict, dataclass
from .twoi import Rep, label, _integer
from split_bundle.producer import calculate


@dataclass(frozen=True)
class Block:
    """One multiplicity of O(twist) tensor the specified physical irrep."""
    irrep: str
    twist: int
    multiplicity: int = 1

    def __post_init__(self):
        object.__setattr__(self, 'irrep', label(self.irrep))
        _integer(self.twist)
        _integer(self.multiplicity)
        if not -64 <= self.twist <= 64 or not 0 <= self.multiplicity <= 1000000:
            raise ValueError('Block exceeds vendor twist/multiplicity bounds')


def cohomology(blocks, twists):
    """Return {t: {h0, h1, h0_dim, h1_dim, rank, degree}}.

    Rank and degree describe the original bundle F, so Euler dimension at t is
    rank*(t+1)+degree. Both cohomology values are Rep instances for F(t).
    """
    twists = list(twists)
    for t in twists:
        _integer(t)
    result = calculate({'schema': 'fm-split-bundle-request-v1', 'operation': 'cohomology',
                        'bundle': [asdict(b) for b in blocks], 'twists': twists})['result']
    rows = {}
    for row in result['twists']:
        h0, h1 = (Rep(tuple(row[h]['multiplicities'])) for h in ('h0', 'h1'))
        rows[row['twist']] = dict(result['bundle'], h0=h0, h1=h1,
                                  h0_dim=h0.dim, h1_dim=h1.dim)
    return rows


def hom(source, target):
    """Character of H^0(source* tensor target); trivial part gives equivariant Hom."""
    result = calculate({'schema': 'fm-split-bundle-request-v1', 'operation': 'hom',
                        'source': [asdict(b) for b in source],
                        'target': [asdict(b) for b in target]})['result']
    return Rep(tuple(result['hom_character']['multiplicities']))
