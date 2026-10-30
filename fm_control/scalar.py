"""Exact scalar one-step certificates. Explicit affine model only; not a physical simulator."""
from fractions import Fraction as Q


def interval(lo, hi):
    lo, hi = Q(lo), Q(hi)
    if lo > hi:
        raise ValueError('empty interval')
    return lo, hi


def normalized(bounds):
    if not isinstance(bounds, (tuple, list)) or len(bounds) != 2:
        raise ValueError('expected two interval endpoints')
    try:
        return interval(*bounds)
    except (TypeError, ValueError, OverflowError, ZeroDivisionError) as exc:
        raise ValueError('invalid interval endpoints') from exc


def intersection(*sets):
    if any(s is None for s in sets):
        return None
    sets = [normalized(s) for s in sets]
    lo, hi = max(s[0] for s in sets), min(s[1] for s in sets)
    return None if lo > hi else (lo, hi)


def safe_actions(x, gain, drift, target, admissible):
    """Exact actions for x_next=x+gain*u+drift, closed scalar intervals."""
    target, admissible = normalized(target), normalized(admissible)
    x, gain, drift = Q(x), Q(gain), Q(drift)
    offset = x + drift
    if not gain:
        return admissible if target[0] <= offset <= target[1] else None
    endpoints = ((target[0]-offset)/gain, (target[1]-offset)/gain)
    return intersection(interval(min(endpoints), max(endpoints)), admissible)


def obstruction(models, observed, noise_bound, target, admissible):
    """Validate two explicit current-state witnesses and exact disjoint actions.

    Measurement is y=x+e, |e|<=noise_bound. This is a one-step, scalar,
    discrete-time claim only: not continuous-time safety or trajectory evidence.
    """
    target, admissible = normalized(target), normalized(admissible)
    if len(models) != 2 or Q(noise_bound) < 0:
        raise ValueError('two models and nonnegative noise required')
    observed, noise_bound = Q(observed), Q(noise_bound)
    sets = []
    for x, gain, drift in models:
        x = Q(x)
        if not target[0] <= x <= target[1]:
            return False
        if abs(observed-x) > noise_bound:
            return False
        actions = safe_actions(x, gain, drift, target, admissible)
        if actions is None:
            return False  # Exclude a model already individually uncontrollable.
        sets.append(actions)
    return intersection(*sets) is None
