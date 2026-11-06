from dataclasses import dataclass
from fractions import Fraction
import re
from math import gcd


MAX_DIMENSION = 16
MAX_INPUT_BITS = 256
MAX_TEXT_LENGTH = 160
MAX_INTERMEDIATE_BITS = 16384
_RATIONAL = re.compile(r"[+-]?[0-9]+(?:/[0-9]+)?", re.ASCII)


class EnclosureLimitError(ValueError):
    pass


def _bounded(value, limit):
    if type(value) is not Fraction or type(value.numerator) is not int or type(value.denominator) is not int:
        raise ValueError("invalid rational representation")
    if value.denominator <= 0:
        raise ValueError("denominator must be positive")
    if value.numerator.bit_length() > limit or value.denominator.bit_length() > limit:
        raise EnclosureLimitError("rational bit limit exceeded")
    if gcd(value.numerator, value.denominator) != 1:
        raise ValueError("rational representation must be reduced")
    return value


def _rational(value):
    if type(value) is int:
        if value.bit_length() > MAX_INPUT_BITS:
            raise EnclosureLimitError("input bit limit exceeded")
        return Fraction(value)
    if type(value) is Fraction:
        return _bounded(value, MAX_INPUT_BITS)
    if type(value) is not str:
        raise ValueError("expected an exact integer, Fraction, or rational string")
    if len(value) > MAX_TEXT_LENGTH:
        raise EnclosureLimitError("rational text limit exceeded")
    if _RATIONAL.fullmatch(value) is None:
        raise ValueError("expected ASCII integer or positive-denominator ratio")
    parts = value.split("/")
    numerator = int(parts[0])
    denominator = int(parts[1]) if len(parts) == 2 else 1
    if denominator == 0:
        raise ValueError("denominator must be positive")
    if max(numerator.bit_length(), denominator.bit_length()) > MAX_INPUT_BITS:
        raise EnclosureLimitError("input bit limit exceeded")
    return Fraction(numerator, denominator)


def _sequence(value, length):
    if type(value) not in (tuple, list) or len(value) != length:
        raise ValueError("expected a list or tuple of the required length")
    return value


def _interval(value):
    pair = _sequence(value, 2)
    lower, upper = (_rational(v) for v in pair)
    if lower > upper:
        raise ValueError("interval endpoints are reversed")
    return lower, upper


def _add(left, right):
    return _bounded(left + right, MAX_INTERMEDIATE_BITS)


def _multiply(left, right):
    return _bounded(left * right, MAX_INTERMEDIATE_BITS)


def _maximum_absolute(pair):
    return max(abs(pair[0]), abs(pair[1]))


def _minimum_absolute(pair):
    if pair[0] <= 0 <= pair[1]:
        return Fraction(0)
    return min(abs(pair[0]), abs(pair[1]))


@dataclass(frozen=True, slots=True)
class LinearResidualEnclosure:
    residuals: tuple
    residual_norm_upper: Fraction
    dominance_margin: Fraction
    forward_error_upper: object
    forward_status: str


def enclose_linear_residual(matrix, candidate, rhs):
    if type(matrix) not in (tuple, list):
        raise ValueError("matrix must be a list or tuple")
    dimension = len(matrix)
    if not 1 <= dimension <= MAX_DIMENSION:
        raise EnclosureLimitError("matrix dimension must be between 1 and 16")
    rows = tuple(tuple(_interval(v) for v in _sequence(row, dimension)) for row in matrix)
    vector = tuple(_rational(v) for v in _sequence(candidate, dimension))
    bounds = tuple(_interval(v) for v in _sequence(rhs, dimension))
    residuals = []
    margins = []
    for i, row in enumerate(rows):
        lower = -bounds[i][1]
        upper = -bounds[i][0]
        off_diagonal = Fraction(0)
        for j, (pair, coordinate) in enumerate(zip(row, vector)):
            products = (_multiply(pair[0], coordinate), _multiply(pair[1], coordinate))
            lower = _add(lower, min(products))
            upper = _add(upper, max(products))
            if i != j:
                off_diagonal = _add(off_diagonal, _maximum_absolute(pair))
        residuals.append((lower, upper))
        margins.append(_add(_minimum_absolute(row[i]), -off_diagonal))
    norm = max(_maximum_absolute(pair) for pair in residuals)
    beta = min(margins)
    forward = _bounded(norm / beta, MAX_INTERMEDIATE_BITS) if beta > 0 else None
    status = "bounded" if beta > 0 else "unresolved"
    return LinearResidualEnclosure(tuple(residuals), norm, beta, forward, status)


def verify_linear_residual(enclosure, matrix, candidate, rhs):
    if type(enclosure) is not LinearResidualEnclosure:
        return False
    try:
        if type(enclosure.residuals) is not tuple:
            return False
        if not 1 <= len(enclosure.residuals) <= MAX_DIMENSION:
            return False
        for pair in enclosure.residuals:
            if type(pair) is not tuple or len(pair) != 2:
                return False
            for endpoint in pair:
                if type(endpoint) is not Fraction:
                    return False
                _bounded(endpoint, MAX_INTERMEDIATE_BITS)
        for value in (enclosure.residual_norm_upper, enclosure.dominance_margin):
            if type(value) is not Fraction:
                return False
            _bounded(value, MAX_INTERMEDIATE_BITS)
        if enclosure.forward_error_upper is not None:
            if type(enclosure.forward_error_upper) is not Fraction:
                return False
            _bounded(enclosure.forward_error_upper, MAX_INTERMEDIATE_BITS)
        if type(enclosure.forward_status) is not str:
            return False
        return enclosure == enclose_linear_residual(matrix, candidate, rhs)
    except (ValueError, TypeError, AttributeError):
        return False
