from fractions import Fraction
import re


MAX_OBSERVATIONS = 128
MAX_RATIONAL_BITS = 256
MAX_RATIONAL_TEXT = 160
_RATIONAL = re.compile(r'[+-]?[0-9]+(?:/[1-9][0-9]*)?\Z')


def _rational(value):
    if type(value) is int:
        if value.bit_length() > MAX_RATIONAL_BITS:
            raise ValueError('rational exceeds bit limit')
        result = Fraction(value)
    elif type(value) is Fraction:
        result = value
    elif type(value) is str:
        if len(value) > MAX_RATIONAL_TEXT or not _RATIONAL.fullmatch(value):
            raise ValueError('expected integer or integer/positive-integer text')
        result = Fraction(value)
    else:
        raise ValueError('expected int, Fraction, or rational text')
    if max(result.numerator.bit_length(), result.denominator.bit_length()) > MAX_RATIONAL_BITS:
        raise ValueError('rational exceeds bit limit')
    return result


def interval(bounds):
    if type(bounds) not in (list, tuple) or len(bounds) != 2:
        raise ValueError('expected a pair of endpoints')
    lo, hi = map(_rational, bounds)
    if lo > hi:
        raise ValueError('reversed interval')
    return lo, hi


def intersection(intervals):
    if type(intervals) not in (list, tuple) or not 1 <= len(intervals) <= MAX_OBSERVATIONS:
        raise ValueError('expected one to 128 intervals')
    bounds = [interval(value) for value in intervals]
    lo = max(value[0] for value in bounds)
    hi = min(value[1] for value in bounds)
    return None if lo > hi else (lo, hi)


def _inputs(horizon, observations):
    horizon = interval(horizon)
    if type(observations) not in (list, tuple) or len(observations) > MAX_OBSERVATIONS:
        raise ValueError('expected at most 128 observations')
    parsed = []
    for observation in observations:
        if type(observation) not in (list, tuple) or len(observation) != 2:
            raise ValueError('each observation needs time and value intervals')
        parsed.append((interval(observation[0]), interval(observation[1])))
    return horizon, parsed


def _pair(bounds):
    return [str(bounds[0]), str(bounds[1])]


def analyze_history(horizon, observations):
    horizon, observations = _inputs(horizon, observations)
    endpoints = set(horizon)
    for (lo, hi), _ in observations:
        if lo <= horizon[1] and hi >= horizon[0]:
            endpoints.update((max(lo, horizon[0]), min(hi, horizon[1])))
    endpoints = sorted(endpoints)
    cells = []
    for i, point in enumerate(endpoints):
        cells.append(('point', point, point, point))
        if i + 1 < len(endpoints):
            right = endpoints[i + 1]
            cells.append(('open', point, right, (point + right) / 2))
    results = []
    for kind, lo, hi, witness in cells:
        active = [i for i, (time, _) in enumerate(observations) if time[0] <= witness <= time[1]]
        common = intersection([observations[i][1] for i in active]) if active else None
        status = 'missing' if not active else 'contradictory' if common is None else 'consistent'
        results.append({'kind': kind, 'bounds': _pair((lo, hi)), 'witness': str(witness),
                        'active': active, 'status': status,
                        'intersection': None if common is None else _pair(common)})
    missing = sum(cell['status'] == 'missing' for cell in results)
    contradictory = any(cell['status'] == 'contradictory' for cell in results)
    coverage = 'none' if missing == len(results) else 'full' if missing == 0 else 'partial'
    consistency = 'contradictory' if contradictory else 'undetermined' if missing else 'consistent'
    return {'schema': 'fm-interval-history/1', 'horizon': _pair(horizon),
            'observations': [{'time': _pair(time), 'value': _pair(value)} for time, value in observations],
            'coverage': coverage, 'consistency': consistency, 'cells': results}


def _same(actual, expected):
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return (len(actual) == len(expected) and all(type(key) is str for key in actual)
                and actual.keys() == expected.keys()
                and all(_same(actual[key], value) for key, value in expected.items()))
    if type(expected) is list:
        return len(actual) == len(expected) and all(_same(a, b) for a, b in zip(actual, expected))
    return actual == expected


def verify_history(horizon, observations, receipt):
    try:
        expected = analyze_history(horizon, observations)
    except (ValueError, TypeError, OverflowError, ZeroDivisionError):
        return False
    return _same(receipt, expected)
