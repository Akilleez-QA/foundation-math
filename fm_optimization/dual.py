from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json


MAX_DIMENSION = 16
MAX_INEQUALITIES = 128
MAX_EQUALITIES = 64
INPUT_BITS = 256
WITNESS_BITS = 4096
ARITHMETIC_BITS = 8192


class Unsupported(ValueError):
    pass


class InvalidCertificate(ValueError):
    pass


def _rational(value, bits):
    if type(value) not in (int, Fraction):
        raise Unsupported('Exact int or Fraction required')
    result = Fraction(value)
    if max(abs(result.numerator).bit_length(), result.denominator.bit_length()) > bits:
        raise Unsupported('Rational resource bound exceeded')
    return result


def _tuple(value, maximum):
    if type(value) is not tuple or len(value) > maximum:
        raise Unsupported('Bounded immutable tuple required')
    return value


def _vector(value, length, bits):
    _tuple(value, length)
    if len(value) != length:
        raise Unsupported('Vector dimension mismatch')
    return tuple(_rational(entry, bits) for entry in value)


def _sum(values):
    result = Fraction(0)
    for value in values:
        result = _rational(result + value, ARITHMETIC_BITS)
    return result


@dataclass(frozen=True)
class LinearProgram:
    context: str
    dimension: int
    inequalities: tuple
    equalities: tuple
    objective: tuple
    offset: object = 0

    def __post_init__(self):
        _program(self)


@dataclass(frozen=True)
class DualBound:
    program_digest: str
    inequality_multipliers: tuple
    equality_multipliers: tuple
    upper_bound: object


def _program(program):
    if type(program) is not LinearProgram:
        raise Unsupported('LinearProgram required')
    if (type(program.context) is not str or not program.context.strip()
            or len(program.context) > 128):
        raise Unsupported('Nonempty bounded context required')
    if type(program.dimension) is not int or not 1 <= program.dimension <= MAX_DIMENSION:
        raise Unsupported('Unsupported dimension')
    _tuple(program.inequalities, MAX_INEQUALITIES)
    _tuple(program.equalities, MAX_EQUALITIES)
    inequalities = tuple(_vector(row, program.dimension + 1, INPUT_BITS)
                         for row in program.inequalities)
    equalities = tuple(_vector(row, program.dimension + 1, INPUT_BITS)
                       for row in program.equalities)
    objective = _vector(program.objective, program.dimension, INPUT_BITS)
    offset = _rational(program.offset, INPUT_BITS)
    return inequalities, equalities, objective, offset


def program_digest(program):
    inequalities, equalities, objective, offset = _program(program)
    encode = lambda vector: [[x.numerator, x.denominator] for x in vector]
    payload = ['fm-linear-program/1', program.context, program.dimension,
               [encode(row) for row in inequalities],
               [encode(row) for row in equalities], encode(objective), encode((offset,))]
    raw = json.dumps(payload, ensure_ascii=True, separators=(',', ':')).encode()
    return sha256(raw).hexdigest()


def _combination(inequalities, equalities, y, z, dimension):
    return tuple(_sum([weight * row[j] for row, weight in zip(inequalities, y)]
                      + [weight * row[j] for row, weight in zip(equalities, z)])
                 for j in range(dimension + 1))


def verify_dual_bound(expected, certificate):
    inequalities, equalities, objective, offset = _program(expected)
    digest = program_digest(expected)
    if type(certificate) is not DualBound:
        return False
    try:
        if type(certificate.program_digest) is not str or certificate.program_digest != digest:
            return False
        y = _vector(certificate.inequality_multipliers, len(inequalities), WITNESS_BITS)
        z = _vector(certificate.equality_multipliers, len(equalities), WITNESS_BITS)
        upper = _rational(certificate.upper_bound, ARITHMETIC_BITS)
        if any(value < 0 for value in y):
            return False
        combined = _combination(inequalities, equalities, y, z, expected.dimension)
        return combined[:-1] == objective and _sum((offset, combined[-1])) == upper
    except Unsupported:
        return False


def augment_box(program, lower, upper):
    _program(program)
    lower = _vector(lower, program.dimension, INPUT_BITS)
    upper = _vector(upper, program.dimension, INPUT_BITS)
    if any(lo > hi for lo, hi in zip(lower, upper)):
        raise Unsupported('Box lower endpoint exceeds upper endpoint')
    upper_rows = tuple(tuple(int(i == j) for j in range(program.dimension)) + (upper[i],)
                       for i in range(program.dimension))
    lower_rows = tuple(tuple(-int(i == j) for j in range(program.dimension)) + (-lower[i],)
                       for i in range(program.dimension))
    return LinearProgram(program.context, program.dimension,
                         program.inequalities + upper_rows + lower_rows,
                         program.equalities, program.objective, program.offset)


def repair_dual(program, inequality_candidates, equality_candidates,
                equality_correction=None, box=None):
    inequalities, equalities, objective, offset = _program(program)
    y0 = _vector(inequality_candidates, len(inequalities), WITNESS_BITS)
    y = tuple(max(Fraction(0), value) for value in y0)
    z0 = _vector(equality_candidates, len(equalities), WITNESS_BITS)
    if equality_correction is None:
        correction = (Fraction(0),) * len(equalities)
    else:
        correction = _vector(equality_correction, len(equalities), WITNESS_BITS)
    z = tuple(_rational(a + b, WITNESS_BITS) for a, b in zip(z0, correction))
    combined = _combination(inequalities, equalities, y, z, program.dimension)
    residual = tuple(_rational(c - entry, WITNESS_BITS)
                     for c, entry in zip(objective, combined[:-1]))
    if box is None:
        if any(residual):
            raise InvalidCertificate('Nonzero residual requires an explicit box')
        expected = program
    else:
        _tuple(box, 2)
        if len(box) != 2:
            raise Unsupported('Box requires lower and upper vectors')
        expected = augment_box(program, box[0], box[1])
        positive = tuple(max(Fraction(0), value) for value in residual)
        negative = tuple(max(Fraction(0), -value) for value in residual)
        y = y + positive + negative
    new_inequalities, new_equalities, _, _ = _program(expected)
    value = _sum((offset, _combination(new_inequalities, new_equalities, y, z,
                                      program.dimension)[-1]))
    certificate = DualBound(program_digest(expected), y, z, value)
    if not verify_dual_bound(expected, certificate):
        raise InvalidCertificate('Repaired witness did not verify')
    return certificate


def verify_attainment(expected, certificate, point):
    inequalities, equalities, objective, offset = _program(expected)
    if not verify_dual_bound(expected, certificate):
        return False
    try:
        point = _vector(point, expected.dimension, WITNESS_BITS)
        evaluate = lambda row: _sum(a * x for a, x in zip(row[:-1], point))
        if any(evaluate(row) > row[-1] for row in inequalities):
            return False
        if any(evaluate(row) != row[-1] for row in equalities):
            return False
        value = _sum((offset, _sum(a * x for a, x in zip(objective, point))))
        return value == certificate.upper_bound
    except Unsupported:
        return False
