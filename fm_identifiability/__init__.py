from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json


MAX_DIMENSION = 32
MAX_ROWS = 64
MAX_INPUT_BITS = 256
MAX_WORK_BITS = 16384


def _scalar(value):
    if type(value) not in (int, Fraction):
        raise ValueError('Expected a built-in int or Fraction')
    result = Fraction(value.numerator, value.denominator)
    if max(abs(result.numerator).bit_length(), result.denominator.bit_length()) > MAX_INPUT_BITS:
        raise ValueError('Input rational exceeds bit limit')
    return result


def _vector(value, length=None, maximum=MAX_DIMENSION):
    if type(value) is not tuple or len(value) > maximum:
        raise ValueError('Expected a bounded immutable tuple')
    if length is not None and len(value) != length:
        raise ValueError('Vector length mismatch')
    return tuple(_scalar(item) for item in value)


def _matrix(value, width):
    if type(value) is not tuple or len(value) > MAX_ROWS:
        raise ValueError('Expected a bounded tuple of rows')
    return tuple(_vector(row, width) for row in value)


def _bounded(value):
    if max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > MAX_WORK_BITS:
        raise ValueError('Intermediate rational exceeds bit limit')
    return value


def _dot(left, right):
    total = Fraction(0)
    for a, b in zip(left, right):
        total = _bounded(total + _bounded(a * b))
    return total


def _digest(fields):
    def encode(value):
        if type(value) is tuple:
            return [encode(item) for item in value]
        return [value.numerator, value.denominator]
    payload = ['fm-identifiability/1', encode(fields)]
    return hashlib.sha256(json.dumps(payload, separators=(',', ':')).encode('ascii')).hexdigest()


@dataclass(frozen=True, slots=True, init=False)
class Model:
    C: tuple
    z: tuple
    L: tuple
    h: tuple
    q: tuple
    d: Fraction
    digest: str

    def __init__(self, C, z, L, h, q, d=0):
        q = _vector(q)
        C, L = _matrix(C, len(q)), _matrix(L, len(q))
        z = _vector(z, len(C), MAX_ROWS)
        h = _vector(h, len(L), MAX_ROWS)
        d = _scalar(d)
        fields = (C, z, L, h, q, d)
        for name, value in zip(('C', 'z', 'L', 'h', 'q', 'd'), fields):
            object.__setattr__(self, name, value)
        object.__setattr__(self, 'digest', _digest(fields))


def _model(model):
    if type(model) is not Model:
        raise ValueError('Expected an exact Model')
    checked = Model(model.C, model.z, model.L, model.h, model.q, model.d)
    if type(model.digest) is not str or model.digest != checked.digest:
        raise ValueError('Model binding mismatch')
    return checked


def _binding(value):
    if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('Expected a canonical model digest')
    return value


@dataclass(frozen=True, slots=True)
class PairWitness:
    model_digest: str
    first: tuple
    second: tuple

    def __post_init__(self):
        _binding(self.model_digest)
        object.__setattr__(self, 'first', _vector(self.first))
        object.__setattr__(self, 'second', _vector(self.second))


@dataclass(frozen=True, slots=True)
class ConstancyWitness:
    model_digest: str
    anchor: tuple
    multipliers: tuple

    def __post_init__(self):
        _binding(self.model_digest)
        object.__setattr__(self, 'anchor', _vector(self.anchor))
        object.__setattr__(self, 'multipliers', _vector(self.multipliers, maximum=MAX_ROWS))


@dataclass(frozen=True, slots=True)
class PairResult:
    model_digest: str
    status: str
    values: tuple | None


@dataclass(frozen=True, slots=True)
class ConstancyResult:
    model_digest: str
    status: str
    value: Fraction | None


def _feasible(model, point):
    return (all(_dot(row, point) == target for row, target in zip(model.C, model.z))
            and all(_dot(row, point) <= bound for row, bound in zip(model.L, model.h)))


def _witness(model, witness, expected_type):
    if type(witness) is not expected_type:
        raise ValueError('Unexpected witness type')
    if _binding(witness.model_digest) != model.digest:
        raise ValueError('Witness belongs to a different model')


def verify_pair(expected_model, witness):
    model = _model(expected_model)
    _witness(model, witness, PairWitness)
    first = _vector(witness.first, len(model.q))
    second = _vector(witness.second, len(model.q))
    if not _feasible(model, first) or not _feasible(model, second):
        return PairResult(model.digest, 'invalid_witness', None)
    values = tuple(_bounded(model.d + _dot(model.q, point)) for point in (first, second))
    status = 'same_query' if values[0] == values[1] else 'query_distinct'
    return PairResult(model.digest, status, values)


def verify_constancy(expected_model, witness):
    model = _model(expected_model)
    _witness(model, witness, ConstancyWitness)
    anchor = _vector(witness.anchor, len(model.q))
    multipliers = _vector(witness.multipliers, len(model.C), MAX_ROWS)
    if not _feasible(model, anchor):
        return ConstancyResult(model.digest, 'invalid_witness', None)
    for j, target in enumerate(model.q):
        if _dot(multipliers, tuple(row[j] for row in model.C)) != target:
            return ConstancyResult(model.digest, 'invalid_witness', None)
    value = _bounded(model.d + _dot(multipliers, model.z))
    return ConstancyResult(model.digest, 'constant_on_fiber', value)
