from fractions import Fraction
import json
import re
import sys

SCHEMA = "fm-correlated-quadratic/1"
LIMITS = {"bytes": 65536, "depth": 16, "nodes": 4096, "dimension": 4,
          "latent": 4, "scenarios": 6, "rows": 8, "pairs": 12,
          "probes": 12, "input_bits": 96, "intermediate_bits": 4096,
          "operations": 200000}


class Invalid(ValueError):
    pass


class Limit(Invalid):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def keys(obj, expected, label):
    require(type(obj) is dict and set(obj) == set(expected.split()),
            label + ": unexpected or missing fields")


class Arithmetic:
    def __init__(self):
        self.operations = 0

    def bounded(self, value):
        if max(value.numerator.bit_length(), value.denominator.bit_length()) > LIMITS["intermediate_bits"]:
            raise Limit("intermediate rational size limit")
        return value

    def op(self, a, b, name):
        self.operations += 1
        if self.operations > LIMITS["operations"]:
            raise Limit("arithmetic operation limit")
        self.bounded(a)
        self.bounded(b)
        if name == "+":
            value = a + b
        elif name == "-":
            value = a - b
        elif name == "*":
            value = a * b
        else:
            require(b != 0, "division by zero")
            value = a / b
        return self.bounded(value)

    def add(self, a, b): return self.op(a, b, "+")
    def sub(self, a, b): return self.op(a, b, "-")
    def mul(self, a, b): return self.op(a, b, "*")
    def div(self, a, b): return self.op(a, b, "/")

    def dot(self, x, y):
        require(len(x) == len(y), "dot shape")
        value = Fraction(0)
        for a, b in zip(x, y):
            value = self.add(value, self.mul(a, b))
        return value

    def mv(self, matrix, x): return [self.dot(row, x) for row in matrix]
    def quad(self, matrix, x): return self.dot(x, self.mv(matrix, x))

    def psd(self, matrix, strict=False):
        n = len(matrix)
        require(all(len(r) == n for r in matrix), "PSD shape")
        require(all(matrix[i][j] == matrix[j][i] for i in range(n) for j in range(n)),
                "matrix is not symmetric")
        a = [row[:] for row in matrix]
        for i in range(n):
            pivot = a[i][i]
            if pivot < 0 or (strict and pivot == 0):
                return False
            if pivot == 0:
                if any(a[i][j] != 0 for j in range(i + 1, n)):
                    return False
                continue
            for j in range(i + 1, n):
                for k in range(j, n):
                    a[j][k] = self.sub(a[j][k], self.div(self.mul(a[j][i], a[i][k]), pivot))
                    a[k][j] = a[j][k]
        return True


def rational(value):
    require(type(value) in (int, str), "rational must be an integer or fraction string")
    if type(value) is int:
        n, d = value, 1
    else:
        require(len(value) <= 64 and re.fullmatch(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?", value),
                "invalid rational syntax")
        parts = value.split("/")
        n, d = int(parts[0]), int(parts[1]) if len(parts) == 2 else 1
    if max(n.bit_length(), d.bit_length()) > LIMITS["input_bits"]:
        raise Limit("input rational size limit")
    return Fraction(n, d)


def vector(value, n, label):
    require(type(value) is list and len(value) == n, label + ": vector shape")
    return [rational(x) for x in value]


def matrix(value, m, n, label):
    require(type(value) is list and len(value) == m, label + ": matrix shape")
    return [vector(row, n, label) for row in value]


def reject_number(_):
    raise Invalid("only integer JSON numbers are permitted")


def parse_integer(token):
    if len(token) > 30:
        raise Limit("JSON integer length limit")
    return int(token)


def unique_object(items):
    result = {}
    for k, v in items:
        require(k not in result, "duplicate JSON field")
        result[k] = v
    return result


def decode(data):
    require(type(data) in (str, bytes), "input must be JSON text or bytes")
    if len(data) > LIMITS["bytes"]:
        raise Limit("input byte limit")
    if type(data) is bytes:
        data = data.decode("utf-8")
    if len(data.encode("utf-8")) > LIMITS["bytes"]:
        raise Limit("input byte limit")
    depth, quoted, escaped = 0, False, False
    for c in data:
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif c in "[{":
            depth += 1
            if depth > LIMITS["depth"]:
                raise Limit("JSON nesting limit")
        elif c in "]}":
            depth -= 1
    value = json.loads(data, parse_int=parse_integer, parse_float=reject_number,
                       parse_constant=reject_number, object_pairs_hook=unique_object)
    pending, nodes = [value], 0
    while pending:
        item = pending.pop()
        nodes += 1
        if nodes > LIMITS["nodes"]:
            raise Limit("JSON node limit")
        if type(item) is dict:
            pending.extend(item.values())
        elif type(item) is list:
            pending.extend(item)
    return value


def textq(value):
    return str(value)


def verify(data):
    obj = decode(data)
    keys(obj, "schema model budget point upper lower probes offset_nonnegative", "root")
    require(obj["schema"] == SCHEMA, "unsupported schema")
    model = obj["model"]
    keys(model, "metric B d scenarios scope", "model")
    require(model["scope"] in ("exact_joint_image", "outer_joint_image"), "invalid scope")
    require(type(model["metric"]) is list, "metric shape")
    n = len(model["metric"])
    require(n <= LIMITS["dimension"], "point dimension limit")
    ar = Arithmetic()
    metric = matrix(model["metric"], n, n, "metric")
    require(ar.psd(metric, strict=True), "metric must be positive definite")
    require(type(model["d"]) is list and len(model["d"]) <= LIMITS["rows"], "row limit")
    nr = len(model["d"])
    rows = matrix(model["B"], nr, n, "rows")
    bounds = vector(model["d"], nr, "row bounds")
    point = vector(obj["point"], n, "point")
    require(all(x <= d for x, d in zip(ar.mv(rows, point), bounds)),
            "supplied point is not row-feasible; no nonvacuity receipt")
    budget = rational(obj["budget"])
    raw_scenarios = model["scenarios"]
    require(type(raw_scenarios) is list and 1 <= len(raw_scenarios) <= LIMITS["scenarios"],
            "scenario count")
    scenarios = []
    for s in raw_scenarios:
        keys(s, "p L a0 b Q", "scenario")
        require(type(s["b"]) is list and len(s["b"]) <= LIMITS["latent"], "latent dimension limit")
        k = len(s["b"])
        p, L = vector(s["p"], n, "p"), matrix(s["L"], n, k, "L")
        a0, b, Q = rational(s["a0"]), vector(s["b"], k, "b"), matrix(s["Q"], k, k, "Q")
        require(all(Q[i][j] == Q[j][i] for i in range(k) for j in range(k)), "Q must be symmetric")
        z = [ar.sub(w, pp) for w, pp in zip(point, p)]
        cols = [[L[i][j] for i in range(n)] for j in range(k)]
        H = [[ar.add(ar.dot(cols[i], ar.mv(metric, cols[j])), Q[i][j])
              for j in range(k)] for i in range(k)]
        g = [ar.sub(b[i], ar.dot(cols[i], ar.mv(metric, z))) for i in range(k)]
        q = ar.add(a0, ar.quad(metric, z))
        scenarios.append(dict(p=p, L=L, a0=a0, b=b, Q=Q, k=k, H=H, g=g, q=q))

    def bound_witness(raw, q, g, H):
        keys(raw, "lambda y bound", "upper witness")
        k = len(g)
        lam, y, bound = rational(raw["lambda"]), vector(raw["y"], k, "y"), rational(raw["bound"])
        require(lam >= 0, "lambda must be nonnegative")
        K = [[ar.sub(lam if i == j else Fraction(0), H[i][j]) for j in range(k)] for i in range(k)]
        require(ar.psd(K), "lambda I-H is not PSD")
        require(ar.mv(K, y) == g, "singular range/linear-system witness fails")
        value = ar.add(ar.add(q, lam), ar.dot(g, y))
        require(bound >= value, "upper bound understates witness")
        return bound

    upper = None
    if obj["upper"] is not None:
        require(type(obj["upper"]) is list and len(obj["upper"]) == len(scenarios), "one upper per scenario required")
        upper = max(bound_witness(raw, s["q"], s["g"], s["H"])
                    for raw, s in zip(obj["upper"], scenarios))
    offsets_checked = False
    if obj["offset_nonnegative"] is not None:
        raw_offsets = obj["offset_nonnegative"]
        require(type(raw_offsets) is list and len(raw_offsets) == len(scenarios), "one offset witness per scenario required")
        for raw, s in zip(raw_offsets, scenarios):
            neg = lambda x: ar.sub(Fraction(0), x)
            value = bound_witness(raw, neg(s["a0"]), [neg(x) for x in s["b"]],
                                  [[neg(x) for x in row] for row in s["Q"]])
            require(value <= 0, "offset nonnegativity not certified")
        offsets_checked = True

    def full_pair(raw, weighted=False):
        keys(raw, "scenario u a c weight" if weighted else "scenario u a c", "realized pair")
        index = raw["scenario"]
        require(type(index) is int and 0 <= index < len(scenarios), "scenario index")
        s = scenarios[index]
        u = vector(raw["u"], s["k"], "latent preimage")
        require(ar.dot(u, u) <= 1, "preimage lies outside the unit ball")
        c = vector(raw["c"], n, "realized center")
        a = rational(raw["a"])
        expected_c = [ar.add(p, lu) for p, lu in zip(s["p"], ar.mv(s["L"], u))]
        expected_a = ar.add(ar.add(s["a0"], ar.mul(Fraction(2), ar.dot(s["b"], u))), ar.quad(s["Q"], u))
        require(c == expected_c and a == expected_a, "full offset/center pair has no supplied common latent preimage")
        residual = [ar.sub(w, cc) for w, cc in zip(point, c)]
        return a, c, ar.add(a, ar.quad(metric, residual))

    probes = obj["probes"]
    require(type(probes) is list and len(probes) <= LIMITS["probes"], "probe count")
    probe_results = []
    for raw in probes:
        _, _, cost = full_pair(raw)
        probe_results.append({"cost": textq(cost), "defeats_supplied_point": cost > budget,
                              "scope": model["scope"], "global_exclusion": False})
    lower = None
    if obj["lower"] is not None:
        raw = obj["lower"]
        keys(raw, "pairs mu v bound", "lower witness")
        pairs = raw["pairs"]
        require(type(pairs) is list and 1 <= len(pairs) <= LIMITS["pairs"], "lower pair count")
        mu, v = vector(raw["mu"], nr, "mu"), vector(raw["v"], n, "v")
        require(all(x >= 0 for x in mu), "row multipliers must be nonnegative")
        cbar, constant, weight_sum = [Fraction(0) for _ in range(n)], Fraction(0), Fraction(0)
        for pair in pairs:
            a, c, _ = full_pair(pair, weighted=True)
            weight = rational(pair["weight"])
            require(weight >= 0, "simplex weights must be nonnegative")
            weight_sum = ar.add(weight_sum, weight)
            cbar = [ar.add(x, ar.mul(weight, cc)) for x, cc in zip(cbar, c)]
            constant = ar.add(constant, ar.mul(weight, ar.add(a, ar.quad(metric, c))))
        require(weight_sum == 1, "simplex weights must sum exactly to one")
        correction = [ar.div(ar.dot([row[j] for row in rows], mu), Fraction(2)) for j in range(n)]
        rhs = [ar.sub(mc, corr) for mc, corr in zip(ar.mv(metric, cbar), correction)]
        require(ar.mv(metric, v) == rhs, "global lower stationarity identity fails")
        value = ar.sub(ar.sub(constant, ar.dot(mu, bounds)), ar.quad(metric, v))
        lower = rational(raw["bound"])
        require(lower <= value, "lower bound overstates witness")
    exact = model["scope"] == "exact_joint_image"
    gap = None if upper is None or lower is None else ar.sub(upper, lower)
    require(gap is None or gap >= 0, "inconsistent verified bounds")
    return {"schema": SCHEMA + "/receipt", "status": "verified_conditional_algebra",
            "scope": model["scope"], "budget": textq(budget), "row_feasible_point": True,
            "upper": None if upper is None else textq(upper),
            "lower": None if lower is None else textq(lower),
            "point_admitted_by_upper": upper is not None and upper <= budget,
            "target_globally_excluded": exact and lower is not None and lower > budget,
            "outer_image_globally_excluded": not exact and lower is not None and lower > budget,
            "represented_bound_gap": None if gap is None else textq(gap),
            "offsets_proved_nonnegative": offsets_checked, "probes": probe_results,
            "operations": ar.operations,
            "premises": "Image exactness or outer coverage and fixed coordinates, metric and rows are caller premises. No application validity or optimizer computation is established."}


def main():
    try:
        require(len(sys.argv) == 2, "usage: python -m fm_correlated INPUT.json (or - for stdin)")
        if sys.argv[1] == "-":
            data = sys.stdin.buffer.read(LIMITS["bytes"] + 1)
        else:
            with open(sys.argv[1], "rb") as handle:
                data = handle.read(LIMITS["bytes"] + 1)
        result = verify(data)
    except (Invalid, OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        print(json.dumps({"status": "rejected_or_unresolved", "reason": str(error)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0

