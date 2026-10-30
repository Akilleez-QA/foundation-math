"""Exact finite matrix ranks and independently checked minor certificates."""
from dataclasses import asdict, dataclass
from fractions import Fraction
from hashlib import sha256
import json
from .field import QuadraticElement, rational


@dataclass(frozen=True)
class RankCertificate:
    field: str
    rows: int
    cols: int
    rank: int
    pivot_rows: tuple
    pivot_cols: tuple
    matrix_sha256: str
    modulus: int | None = None

    def to_dict(self):
        return asdict(self)


def _prepare(rows, field, modulus):
    a = [list(row) for row in rows]
    n = len(a[0]) if a else 0
    if any(len(row) != n for row in a):
        raise ValueError("ragged matrix")
    p = modulus
    if field == 'F_p':
        # Complete trial division for p <= 10^12; larger moduli are unsupported.
        if type(p) is not int:
            raise TypeError("integer modulus required")
        if not 2 <= p <= 10**12:
            raise ValueError("prime modulus must be in [2, 10^12]")
        k = 2
        while k*k <= p:
            if p % k == 0:
                raise ValueError("modulus must be prime")
            k += 1
        def coerce(x):
            if type(x) is not int:
                raise TypeError("F_p entries must be integers")
            return x % p
    else:
        if p is not None:
            raise ValueError("modulus is only valid for F_p")
        if field == 'Q':
            coerce = rational
        elif field.startswith('Q(sqrt') and field.endswith(')'):
            d = int(field[6:-1].strip())
            def coerce(x):
                if isinstance(x, QuadraticElement):
                    if x.d != d:
                        raise ValueError("different quadratic fields")
                    return x
                return QuadraticElement(rational(x), 0, d)
            coerce(0)  # Validate the radicand even for empty matrices.
        else:
            raise ValueError("unsupported field")
    def encode(x):
        if isinstance(x, QuadraticElement):
            return [str(x.a), str(x.b), str(x.d)]
        if isinstance(x, Fraction):
            return f'{x.numerator}/{x.denominator}'
        rational(x)
        return x
    encoded = [[encode(x) for x in row] for row in a]
    digest = sha256(json.dumps(encoded, separators=(',', ':')).encode()).hexdigest()
    return [[coerce(x) for x in row] for row in a], n, digest


def _divide(x, y, p):
    return x * pow(y, -1, p) % p if p else x / y


def rank_exact(rows, field='Q', modulus=None):
    """Row elimination over Q, Q(sqrt d), or F_p with bounded prime validation."""
    a, n, digest = _prepare(rows, field, modulus)
    m, ids, pr, pc = len(a), list(range(len(a))), [], []
    for c in range(n):
        r = len(pr)
        pivot = next((i for i in range(r, m) if a[i][c] != 0), None)
        if pivot is None:
            continue
        a[r], a[pivot] = a[pivot], a[r]
        ids[r], ids[pivot] = ids[pivot], ids[r]
        for i in range(r + 1, m):
            factor = _divide(a[i][c], a[r][c], modulus)
            a[i] = [x - factor*y for x, y in zip(a[i], a[r])]
            if modulus:
                a[i] = [x % modulus for x in a[i]]
        pr.append(ids[r])
        pc.append(c)
    return RankCertificate(field, m, n, len(pr), tuple(pr), tuple(pc), digest, modulus)


def _det(a, p, quadratic):
    """Bareiss determinant over Q/F_p; ordinary elimination over quadratic fields."""
    a = [row[:] for row in a]
    previous, sign = Fraction(1) if not p else 1, 1
    for k in range(len(a) - 1):
        r = next((i for i in range(k, len(a)) if a[i][k] != 0), None)
        if r is None:
            return 0
        if r != k:
            a[k], a[r], sign = a[r], a[k], -sign
        pivot = a[k][k]
        for i in range(k + 1, len(a)):
            factor = _divide(a[i][k], pivot, p) if quadratic else None
            for j in range(k + 1, len(a)):
                a[i][j] = (a[i][j] - factor*a[k][j] if quadratic else
                           _divide(pivot*a[i][j] - a[i][k]*a[k][j], previous, p))
            a[i][k] = 0
        previous = pivot
    if quadratic:
        result = sign
        for i in range(len(a)):
            result *= a[i][i]
        return result
    return sign*a[-1][-1] if a else 1


def verify_rank_certificate(rows, cert, field=None, modulus=None):
    """Check hash, nonsingular witness, and upper bound via a transpose basis."""
    try:
        if field is not None and field != cert.field:
            return False
        if modulus is not None and modulus != cert.modulus:
            return False
        a, n, digest = _prepare(rows, cert.field, cert.modulus)
        r = cert.rank
        if (cert.rows != len(a) or cert.cols != n or digest != cert.matrix_sha256
                or type(r) is not int or not 0 <= r <= min(len(a), n)):
            return False
        for pivots, bound in ((cert.pivot_rows, len(a)), (cert.pivot_cols, n)):
            if (len(pivots) != r or len(set(pivots)) != r or
                    any(type(i) is not int or not 0 <= i < bound for i in pivots)):
                return False
        minor = [[a[i][j] for j in cert.pivot_cols] for i in cert.pivot_rows]
        if _det(minor, cert.modulus, cert.field != 'Q' and not cert.modulus) == 0:
            return False
        basis = {}
        for column in reversed(list(zip(*a))):
            v = list(column)
            for i in range(len(v)):
                if v[i] == 0:
                    continue
                if i not in basis:
                    basis[i] = [_divide(x, v[i], cert.modulus) for x in v]
                    break
                v = [x - v[i]*y for x, y in zip(v, basis[i])]
                if cert.modulus:
                    v = [x % cert.modulus for x in v]
        return len(basis) == r
    except (ValueError, TypeError, AttributeError, IndexError, ZeroDivisionError):
        return False


def rank_mod_p(rows, p):
    """Return integer-matrix rank over F_p."""
    return rank_exact(rows, 'F_p', p).rank


def rank_over_Q_and_mod_p(rows, primes):
    """Return prime->rank; for integer matrices each is <= rank over Q."""
    rows = [list(row) for row in rows]
    if any(type(x) is not int for row in rows for x in row):
        raise TypeError("integer matrix required")
    return {p: rank_mod_p(rows, p) for p in primes}
