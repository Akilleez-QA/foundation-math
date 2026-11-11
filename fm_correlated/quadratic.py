from fractions import Fraction
import json
import re

SCHEMA = "fm-correlated-quadratic/1"
LIMITS = {"bytes": 65536, "depth": 16, "nodes": 4096, "dimension": 4,
          "latent": 4, "scenarios": 6, "rows": 8,
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
    keys(obj, "schema model budget point probes", "root")
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

    def full_pair(raw):
        keys(raw, "scenario u a c", "realized pair")
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
    return {"schema": SCHEMA + "/receipt", "status": "verified_conditional_algebra",
            "scope": model["scope"], "budget": textq(budget), "row_feasible_point": True,
            "probes": probe_results, "operations": ar.operations,
            "premises": "Image exactness or outer coverage and the interpretation of fixed coordinates, metric and rows are caller premises. Only model admission, point row feasibility and supplied realized-pair probes are checked; no application validity or optimizer computation is established."}
