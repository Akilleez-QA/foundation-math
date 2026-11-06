from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json


MAX_DIMENSION = 16
MAX_INEQUALITIES = 128
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
    return tuple(_rational(x, bits) for x in value)


@dataclass(frozen=True)
class AffineSystem:
    context: str
    dimension: int
    inequalities: tuple

    def __post_init__(self):
        _system(self)


@dataclass(frozen=True)
class Implication:
    system_digest: str
    target: tuple
    multipliers: tuple


@dataclass(frozen=True)
class Infeasibility:
    system_digest: str
    multipliers: tuple


def _system(system):
    if type(system) is not AffineSystem:
        raise Unsupported('AffineSystem required')
    if (type(system.context) is not str or not system.context.strip()
            or len(system.context) > 128):
        raise Unsupported('Nonempty bounded context required')
    if type(system.dimension) is not int or not 1 <= system.dimension <= MAX_DIMENSION:
        raise Unsupported('Unsupported dimension')
    _tuple(system.inequalities, MAX_INEQUALITIES)
    return tuple(_vector(row, system.dimension + 1, INPUT_BITS)
                 for row in system.inequalities)


def system_digest(system):
    rows = _system(system)
    payload = ['fm-affine-system/1', system.context, system.dimension,
               [[[x.numerator, x.denominator] for x in row] for row in rows]]
    raw = json.dumps(payload, ensure_ascii=True, separators=(',', ':')).encode()
    return sha256(raw).hexdigest()


def _combination(system, multipliers):
    rows = _system(system)
    weights = _vector(multipliers, len(rows), WITNESS_BITS)
    if any(weight < 0 for weight in weights):
        raise InvalidCertificate('Nonnegative multipliers required')
    result = [Fraction(0)] * (system.dimension + 1)
    for row, weight in zip(rows, weights):
        for j, entry in enumerate(row):
            result[j] = _rational(result[j] + weight * entry, ARITHMETIC_BITS)
    return tuple(result)


def verify_implication(system, certificate):
    expected_digest = system_digest(system)
    if type(certificate) is not Implication:
        return False
    try:
        if type(certificate.system_digest) is not str or certificate.system_digest != expected_digest:
            return False
        target = _vector(certificate.target, system.dimension + 1, INPUT_BITS)
        result = _combination(system, certificate.multipliers)
        return result[:-1] == target[:-1] and result[-1] >= target[-1]
    except (Unsupported, InvalidCertificate):
        return False


def verify_infeasibility(system, certificate):
    expected_digest = system_digest(system)
    if type(certificate) is not Infeasibility:
        return False
    try:
        if type(certificate.system_digest) is not str or certificate.system_digest != expected_digest:
            return False
        result = _combination(system, certificate.multipliers)
        return not any(result[:-1]) and result[-1] > 0
    except (Unsupported, InvalidCertificate):
        return False


def make_implication(system, target, multipliers):
    candidate = Implication(system_digest(system), target, multipliers)
    if not verify_implication(system, candidate):
        raise InvalidCertificate('Supplied implication witness did not verify')
    return candidate


def make_infeasibility(system, multipliers):
    candidate = Infeasibility(system_digest(system), multipliers)
    if not verify_infeasibility(system, candidate):
        raise InvalidCertificate('Supplied infeasibility witness did not verify')
    return candidate


def compose_implications(system, inner, outer):
    _system(system)
    _tuple(inner, MAX_INEQUALITIES)
    if any(not verify_implication(system, proof) for proof in inner):
        raise InvalidCertificate('Every intermediate implication must verify')
    intermediate = AffineSystem(system.context, system.dimension,
                                tuple(proof.target for proof in inner))
    if not verify_implication(intermediate, outer):
        raise InvalidCertificate('Outer implication must bind the exact intermediate system')
    combined = [Fraction(0)] * len(system.inequalities)
    for weight, proof in zip(outer.multipliers, inner):
        weight = _rational(weight, WITNESS_BITS)
        for j, multiplier in enumerate(proof.multipliers):
            combined[j] = _rational(combined[j] + weight * multiplier, ARITHMETIC_BITS)
    result = tuple(_rational(x, WITNESS_BITS) for x in combined)
    return make_implication(system, outer.target, result)
