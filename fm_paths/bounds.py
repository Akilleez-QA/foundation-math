from fractions import Fraction
from itertools import combinations


_INPUT_BITS = 512
_RECEIPT_BITS = 32768
_MAX_RECORDS = 32
_MAX_POINTS = 4096
_MAX_PAIRS = 200000


def _rational(value, bits=_INPUT_BITS):
    if type(value) not in (int, str, Fraction):
        raise ValueError("expected int, Fraction or rational string")
    if type(value) is str and len(value) > (256 if bits == _INPUT_BITS else 10000):
        raise ValueError("rational string limit exceeded")
    try:
        value = Fraction(value)
    except (ValueError, ZeroDivisionError):
        raise ValueError("invalid rational") from None
    if max(value.numerator.bit_length(), value.denominator.bit_length()) > bits:
        raise ValueError("rational bit limit exceeded")
    return value


def _sequence(value, maximum, size=None):
    if type(value) not in (tuple, list) or len(value) > maximum:
        raise ValueError("invalid or oversized sequence")
    if size is not None and len(value) != size:
        raise ValueError("wrong sequence length")
    return value


def _band(value):
    pair = tuple(_rational(v) for v in _sequence(value, 2, 2))
    if pair[0] > pair[1]:
        raise ValueError("reversed interval")
    return pair


def _problem(records, horizon, up, down):
    horizon, up, down = map(_rational, (horizon, up, down))
    if min(horizon, up, down) < 0:
        raise ValueError("negative horizon or rate")
    records = _sequence(records, _MAX_RECORDS)
    if not records:
        raise ValueError("at least one interval constraint required")
    result = []
    for record in records:
        start, end, lower, upper = map(_rational, _sequence(record, 4, 4))
        if not 0 <= start <= end <= horizon or lower > upper:
            raise ValueError("invalid interval constraint")
        result.append((start, end, lower, upper))
    return tuple(result), horizon, up, down


def _branches(problem, time):
    records, _, up, down = problem
    lower = [a - up * max(s - time, 0) - down * max(time - e, 0)
             for s, e, a, b in records]
    upper = [b + down * max(s - time, 0) + up * max(time - e, 0)
             for s, e, a, b in records]
    return lower, upper


def _integral(points, values):
    return sum(((b - a) * (x + y) / 2
                for a, b, x, y in zip(points, points[1:], values, values[1:])),
               Fraction(0))


def _within_result_limit(value):
    if type(value) is Fraction:
        return max(value.numerator.bit_length(), value.denominator.bit_length()) <= _RECEIPT_BITS
    if type(value) is dict:
        return all(_within_result_limit(item) for item in value.values())
    if type(value) in (tuple, list):
        return all(_within_result_limit(item) for item in value)
    return True


def _result(value):
    if not _within_result_limit(value):
        return {"status": "resource_unresolved", "reason": "generated rational limit"}
    return value


def certify_path_bounds(records, horizon, up, down, integral_band=None, max_pairs=_MAX_PAIRS):
    if type(max_pairs) is not int or not 0 <= max_pairs <= _MAX_PAIRS:
        raise ValueError("invalid pair limit")
    problem = _problem(records, horizon, up, down)
    band = None if integral_band is None else _band(integral_band)
    records, horizon, _, _ = problem
    ends = sorted({Fraction(0), horizon} | {v for row in records for v in row[:2]})
    count = 2 * len(records)
    if (len(ends) - 1) * count * (count - 1) // 2 > max_pairs:
        return {"status": "resource_unresolved", "reason": "pair limit"}
    points = set(ends)
    for start, end in zip(ends, ends[1:]):
        left = sum(_branches(problem, start), [])
        right = sum(_branches(problem, end), [])
        lines = [(a, (b - a) / (end - start)) for a, b in zip(left, right)]
        for (a, slope), (b, other) in combinations(lines, 2):
            if slope != other:
                crossing = start + (b - a) / (slope - other)
                if start < crossing < end:
                    points.add(crossing)
                    if len(points) > _MAX_POINTS:
                        return {"status": "resource_unresolved", "reason": "subdivision limit"}
    points = sorted(points)
    lower, upper = [], []
    for time in points:
        lows, highs = _branches(problem, time)
        low, high = max(lows), min(highs)
        if low > high:
            return _result({"status": "infeasible", "time": time,
                            "lower_index": lows.index(low), "upper_index": highs.index(high),
                            "lower": low, "upper": high})
        lower.append(low)
        upper.append(high)
    active = []
    for start, end in zip(points, points[1:]):
        lows, highs = _branches(problem, (start + end) / 2)
        active.append((lows.index(max(lows)), highs.index(min(highs))))
    low_integral, high_integral = _integral(points, lower), _integral(points, upper)
    result = {"status": "feasible", "points": points, "lower": lower, "upper": upper,
              "active": active, "integrals": (low_integral, high_integral)}
    if band is not None:
        target = max(low_integral, band[0])
        if target > min(high_integral, band[1]):
            result["integral_status"] = "excluded"
        else:
            theta = Fraction(0) if low_integral == high_integral else (
                (target - low_integral) / (high_integral - low_integral))
            result.update(integral_status="attained", theta=theta, target=target,
                          path=[(1 - theta) * a + theta * b for a, b in zip(lower, upper)])
    return _result(result)


def _receipt_rational(value):
    return _rational(value, _RECEIPT_BITS)


def _index(value, count):
    if type(value) is not int or not 0 <= value < count:
        raise ValueError("invalid branch index")
    return value


def verify_path_bounds(records, horizon, up, down, receipt, integral_band=None):
    problem = _problem(records, horizon, up, down)
    records, horizon, up, down = problem
    band = None if integral_band is None else _band(integral_band)
    if type(receipt) is not dict:
        raise ValueError("expected receipt dictionary")
    status = receipt.get("status")
    if status == "infeasible":
        required = {"status", "time", "lower_index", "upper_index", "lower", "upper"}
        if set(receipt) != required:
            raise ValueError("invalid infeasibility receipt fields")
        time, lower, upper = map(_receipt_rational, (receipt["time"], receipt["lower"], receipt["upper"]))
        li, ui = (_index(receipt[key], len(records)) for key in ("lower_index", "upper_index"))
        lows, highs = _branches(problem, time)
        if not 0 <= time <= horizon or lower != lows[li] or upper != highs[ui] or lower <= upper:
            raise ValueError("invalid contradiction witness")
        return True
    if status != "feasible":
        raise ValueError("no mathematical certificate")
    required = {"status", "points", "lower", "upper", "active", "integrals"}
    if band is not None:
        required.add("integral_status")
        if receipt.get("integral_status") == "attained":
            required.update(("theta", "target", "path"))
    if set(receipt) != required:
        raise ValueError("invalid feasible receipt fields")
    points = list(map(_receipt_rational, _sequence(receipt["points"], _MAX_POINTS)))
    lower = list(map(_receipt_rational, _sequence(receipt["lower"], _MAX_POINTS)))
    upper = list(map(_receipt_rational, _sequence(receipt["upper"], _MAX_POINTS)))
    active = _sequence(receipt["active"], _MAX_POINTS)
    integrals = tuple(map(_receipt_rational, _sequence(receipt["integrals"], 2, 2)))
    if (not points or points[0] != 0 or points[-1] != horizon
            or len(lower) != len(points) or len(upper) != len(points)
            or len(active) != len(points) - 1
            or any(a >= b for a, b in zip(points, points[1:]))
            or not {v for row in records for v in row[:2]}.issubset(points)):
        raise ValueError("invalid subdivision")
    for time, low, high in zip(points, lower, upper):
        lows, highs = _branches(problem, time)
        if low != max(lows) or high != min(highs) or low > high:
            raise ValueError("invalid envelope node")
    for k, (start, end) in enumerate(zip(points, points[1:])):
        li, ui = (_index(value, len(records)) for value in _sequence(active[k], 2, 2))
        for time, j in ((start, k), (end, k + 1)):
            lows, highs = _branches(problem, time)
            if lows[li] != lower[j] or highs[ui] != upper[j]:
                raise ValueError("no common tight branch on cell")
        for values in (lower, upper):
            if not -down * (end - start) <= values[k + 1] - values[k] <= up * (end - start):
                raise ValueError("invalid directed slope")
    if integrals != (_integral(points, lower), _integral(points, upper)):
        raise ValueError("invalid integral extrema")
    if band is not None:
        if receipt["integral_status"] == "excluded":
            if not (band[1] < integrals[0] or band[0] > integrals[1]):
                raise ValueError("invalid integral exclusion")
        elif receipt["integral_status"] == "attained":
            theta, target = map(_receipt_rational, (receipt["theta"], receipt["target"]))
            path = list(map(_receipt_rational, _sequence(receipt["path"], _MAX_POINTS)))
            if (not 0 <= theta <= 1 or not band[0] <= target <= band[1]
                    or path != [(1 - theta) * a + theta * b for a, b in zip(lower, upper)]
                    or _integral(points, path) != target):
                raise ValueError("invalid integral witness")
        else:
            raise ValueError("missing integral conclusion")
    return True
