from dataclasses import dataclass
from fractions import Fraction
from math import comb, factorial

__all__ = ['Continuation', 'ReachableSet', 'TargetResult', 'RowResult']


def _q(value):
    if type(value) not in (int, Fraction):
        raise ValueError('Expected an exact int or Fraction')
    value = Fraction(value)
    if max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > 128:
        raise ValueError('Input numerator and denominator are limited to 128 bits')
    return value


def _seq(value):
    if type(value) not in (list, tuple):
        raise ValueError('Expected a list or tuple')
    return value


def _vector(value, size=None):
    _seq(value)
    if not 1 <= len(value) <= 4 or (size is not None and len(value) != size):
        raise ValueError('Expected matching dimensions between 1 and 4')
    return tuple(_q(x) for x in value)


def _matrix(value, rows=None, columns=None):
    _seq(value)
    if not 1 <= len(value) <= 4 or (rows is not None and len(value) != rows):
        raise ValueError('Expected matching matrix rows between 1 and 4')
    result = tuple(_vector(row, columns) for row in value)
    if len({len(row) for row in result}) != 1:
        raise ValueError('Ragged matrix')
    return result


def _zeros(n, m):
    return tuple((Fraction(0),) * m for _ in range(n))


def _identity(n):
    return tuple(tuple(Fraction(int(i == j)) for j in range(n)) for i in range(n))


def _tr(a):
    return tuple(zip(*a))


def _scale(a, factor):
    return tuple(tuple(factor * x for x in row) for row in a)


def _add(a, b):
    return tuple(tuple(x + y for x, y in zip(ar, br)) for ar, br in zip(a, b))


def _mul(a, b):
    return tuple(tuple(sum((x*y for x, y in zip(row, column)), Fraction(0))
                       for column in _tr(b)) for row in a)


def _column(v):
    return tuple((x,) for x in v)


def _flat(a):
    return tuple(row[0] for row in a)


def _solve(a, b):
    n, width = len(a), len(b[0])
    work = [list(left) + list(right) for left, right in zip(a, b)]
    pivot_columns = []
    for column in range(n):
        row = len(pivot_columns)
        pivot = next((i for i in range(row, n) if work[i][column]), None)
        if pivot is None:
            continue
        work[row], work[pivot] = work[pivot], work[row]
        divisor = work[row][column]
        work[row] = [x/divisor for x in work[row]]
        for i in range(n):
            if i != row:
                factor = work[i][column]
                work[i] = [x-factor*y for x, y in zip(work[i], work[row])]
        pivot_columns.append(column)
    if any(not any(row[:n]) and any(row[n:]) for row in work):
        return None
    result = [[Fraction(0)] * width for _ in range(n)]
    for row, column in enumerate(pivot_columns):
        result[column] = work[row][n:]
    return tuple(tuple(row) for row in result)


def _spd(a):
    if a != _tr(a):
        return False
    work = [list(row) for row in a]
    for pivot in range(len(a)):
        if work[pivot][pivot] <= 0:
            return False
        for i in range(pivot+1, len(a)):
            for j in range(pivot+1, len(a)):
                work[i][j] -= work[i][pivot]*work[pivot][j]/work[pivot][pivot]
    return True


def _polynomial(value, rows, columns):
    _seq(value)
    if not 1 <= len(value) <= 4:
        raise ValueError('Polynomial coefficient count must be between 1 and 4')
    return tuple(_matrix(c, rows, columns) for c in value)


def _product(a, b):
    result = [_zeros(len(a[0]), len(b[0][0])) for _ in range(len(a)+len(b)-1)]
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i+j] = _add(result[i+j], _mul(x, y))
    return tuple(result)


def _integrate(p, lo, hi):
    result = _zeros(len(p[0]), len(p[0][0]))
    for degree, coefficient in enumerate(p, 1):
        result = _add(result, _scale(coefficient, (hi**degree-lo**degree)/degree))
    return result


def _gram(a, weight, b, lo, hi):
    return _integrate(_product(_product(a, (weight,)), tuple(_tr(c) for c in b)), lo, hi)


def _exp(powers, t):
    result = _zeros(len(powers[0]), len(powers[0]))
    for degree, power in enumerate(powers):
        result = _add(result, _scale(power, t**degree/Fraction(factorial(degree))))
    return result


def _kernel(powers, B, t):
    result = [_zeros(len(B), len(B[0])) for _ in powers]
    for degree, power in enumerate(powers):
        for j in range(degree+1):
            factor = Fraction(comb(degree, j)*(-1)**j, factorial(degree))*t**(degree-j)
            result[j] = _add(result[j], _scale(_mul(power, B), factor))
    return tuple(result)


@dataclass(frozen=True)
class TargetResult:
    reachable: bool
    reason: str
    extra_cost: object
    minimum_total_cost: object


@dataclass(frozen=True)
class RowResult:
    contained: bool
    center: Fraction
    radius_squared: Fraction
    signed_slack: Fraction


@dataclass(frozen=True)
class ReachableSet:
    time: Fraction
    center: tuple
    shape: tuple
    reserve: Fraction
    minimum_total_cost: Fraction

    def target(self, value):
        value = _vector(value, len(self.center))
        delta = _column(tuple(x-y for x, y in zip(value, self.center)))
        solution = _solve(self.shape, delta)
        if solution is None:
            return TargetResult(False, 'outside_range', None, None)
        cost = _mul(_tr(delta), solution)[0][0]
        inside = cost <= self.reserve
        return TargetResult(inside, 'reachable' if inside else 'over_budget',
                            cost, self.minimum_total_cost+cost)

    def row(self, coefficients, bound):
        a = _column(_vector(coefficients, len(self.center)))
        bound = _q(bound)
        center = _mul(_tr(a), _column(self.center))[0][0]
        radius = self.reserve * _mul(_mul(_tr(a), self.shape), a)[0][0]
        slack = bound-center
        return RowResult(slack >= 0 and slack*slack >= radius, center, radius, slack)


class Continuation:
    def __init__(self, *, H, B, initial, R, D, moment, budget, end, cut, prefix):
        H = _matrix(H)
        n = len(H)
        H = _matrix(H, n, n)
        B = _matrix(B, n)
        m = len(B[0])
        initial = _column(_vector(initial, n))
        R = _matrix(R, m, m)
        if not _spd(R):
            raise ValueError('R must be symmetric positive definite')
        residual = _column(_vector(moment))
        D = _polynomial(D, len(residual), m)
        budget, end, cut = _q(budget), _q(end), _q(cut)
        if budget < 0 or end <= 0 or not 0 <= cut <= end:
            raise ValueError('Require budget >= 0, end > 0 and 0 <= cut <= end')
        powers = [_identity(n)]
        for degree in range(1, n+1):
            power = _mul(powers[-1], H)
            if not any(x for row in power for x in row):
                break
            powers.append(power)
        else:
            raise ValueError('H must be nilpotent of order at most its dimension')
        _seq(prefix)
        if len(prefix) > 8:
            raise ValueError('At most eight prefix pieces are supported')
        pieces, last = [], Fraction(0)
        for piece in prefix:
            _seq(piece)
            if len(piece) != 3:
                raise ValueError('Each piece must be (lo, hi, coefficients)')
            lo, hi = _q(piece[0]), _q(piece[1])
            if lo != last or not lo < hi <= cut:
                raise ValueError('Prefix pieces must exactly tile [0, cut]')
            coefficients = _seq(piece[2])
            if not 1 <= len(coefficients) <= 4:
                raise ValueError('Prefix degree must be at most three')
            polynomial = tuple(_column(_vector(c, m)) for c in coefficients)
            pieces.append((lo, hi, polynomial))
            last = hi
        if last != cut:
            raise ValueError('A complete fixed prefix is required')
        state = _mul(_exp(powers, cut), initial)
        kernel = _kernel(powers, B, cut)
        spent = Fraction(0)
        for lo, hi, polynomial in pieces:
            state = _add(state, _integrate(_product(kernel, polynomial), lo, hi))
            residual = _add(residual, _scale(_integrate(_product(D, polynomial), lo, hi), -1))
            spent += _gram(tuple(_tr(c) for c in polynomial), R,
                           tuple(_tr(c) for c in polynomial), lo, hi)[0][0]
        inverse = _solve(R, _identity(m))
        gram = _gram(D, inverse, D, cut, end)
        alpha = _solve(gram, residual)
        self.end, self.cut, self.budget = end, cut, budget
        self.spent_cost, self.state, self.moment_residual = spent, _flat(state), _flat(residual)
        self.tail_gram = gram
        self.minimum_tail_cost = self.minimum_total_cost = self.reserve = None
        self._powers, self._B, self._D, self._inverse = tuple(powers), B, D, inverse
        self._alpha = alpha
        if alpha is None:
            self.status = 'no_continuation_moment_range'
        else:
            cost = _mul(_tr(residual), alpha)[0][0]
            self.minimum_tail_cost, self.minimum_total_cost = cost, spent+cost
            self.reserve = budget-spent-cost
            self.status = 'feasible' if self.reserve >= 0 else 'no_continuation_budget'

    def future(self, time):
        time = _q(time)
        if not self.cut <= time <= self.end:
            raise ValueError('Query must lie in [cut, end]')
        if self.status != 'feasible':
            raise ValueError('Fixed prefix has no admissible continuation')
        kernel = _kernel(self._powers, self._B, time)
        W = _gram(kernel, self._inverse, kernel, self.cut, time)
        V = _gram(kernel, self._inverse, self._D, self.cut, time)
        quotient = _solve(self.tail_gram, _tr(V))
        if quotient is None:
            raise ArithmeticError('Conditional Gram range identity failed')
        center = _add(_mul(_exp(self._powers, time-self.cut), _column(self.state)),
                      _mul(V, self._alpha))
        shape = _add(W, _scale(_mul(V, quotient), -1))
        return ReachableSet(time, _flat(center), shape, self.reserve, self.minimum_total_cost)

    def minimum_tail_value(self, time):
        time = _q(time)
        if not self.cut <= time <= self.end or self._alpha is None:
            raise ValueError('No minimum-norm representative at this time')
        polynomial = _product((self._inverse,), tuple(_tr(c) for c in self._D))
        value = _zeros(len(self._B[0]), 1)
        for degree, coefficient in enumerate(polynomial):
            value = _add(value, _scale(_mul(coefficient, self._alpha), time**degree))
        return _flat(value)
