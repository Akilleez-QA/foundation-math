from fractions import Fraction
import json
import re
import sys

MAX_DIM = 8
MAX_SCENARIOS = 8
MAX_ROWS = 16
MAX_INPUT_BITS = 512
MAX_ARITH_BITS = 4096
MAX_OPS = 150000
MAX_JSON_BYTES = 131072


class Invalid(ValueError):
    pass


class Limit(Exception):
    pass


class Exact:
    def __init__(self):
        self.operations = 0

    def bound(self, value, bits=MAX_ARITH_BITS):
        self.operations += 1
        if self.operations > MAX_OPS:
            raise Limit('arithmetic operation limit')
        if max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > bits:
            raise Limit('rational bit limit')
        return value

    def read(self, value):
        if type(value) is int:
            if abs(value).bit_length() > MAX_INPUT_BITS:
                raise Limit('input integer bit limit')
            return self.bound(Fraction(value), MAX_INPUT_BITS)
        if type(value) is Fraction:
            return self.bound(value, MAX_INPUT_BITS)
        if type(value) is str:
            if len(value) > 320:
                raise Limit('rational text length limit')
            if not re.fullmatch(r'[+-]?[0-9]+(?:/[1-9][0-9]*)?', value):
                raise Invalid('scalars must be exact integers or rational strings')
            return self.bound(Fraction(value), MAX_INPUT_BITS)
        raise Invalid('scalars must be int, Fraction, or rational string; no floats or booleans')

    def add(self, x, y):
        return self.bound(x + y)

    def sub(self, x, y):
        return self.bound(x - y)

    def mul(self, x, y):
        return self.bound(x * y)

    def div(self, x, y):
        return self.bound(x / y)

    def dot(self, x, y):
        if len(x) != len(y):
            raise Invalid('internal vector dimension mismatch')
        total = Fraction(0)
        for i in range(len(x)):
            total = self.add(total, self.mul(x[i], y[i]))
        return total

    def mv(self, matrix, vector):
        return [self.dot(row, vector) for row in matrix]

    def quad(self, matrix, vector):
        return self.dot(vector, self.mv(matrix, vector))

    def subtract(self, x, y):
        return [self.sub(x[i], y[i]) for i in range(len(x))]

    def linear_system(self, matrix, rhs, dimension):


        count = len(matrix)
        rows = [matrix[i][:] + [rhs[i]] for i in range(count)]
        transform = [[Fraction(i == j) for j in range(count)] for i in range(count)]
        pivots = []
        for column in range(dimension):
            pivot_row = next((i for i in range(len(pivots), count) if rows[i][column]), None)
            if pivot_row is None:
                continue
            target = len(pivots)
            rows[target], rows[pivot_row] = rows[pivot_row], rows[target]
            transform[target], transform[pivot_row] = transform[pivot_row], transform[target]
            scale = rows[target][column]
            rows[target] = [self.div(x, scale) for x in rows[target]]
            transform[target] = [self.div(x, scale) for x in transform[target]]
            for i in range(count):
                if i == target:
                    continue
                scale = rows[i][column]
                rows[i] = [self.sub(x, self.mul(scale, y)) for x, y in zip(rows[i], rows[target])]
                transform[i] = [self.sub(x, self.mul(scale, y)) for x, y in zip(transform[i], transform[target])]
            pivots.append(column)
        for i, row in enumerate(rows):
            if not any(row[:dimension]) and row[dimension]:
                return None, transform[i]
        solution = [Fraction(0)] * dimension
        for i, column in enumerate(pivots):
            solution[column] = rows[i][dimension]
        return solution, None


def require_list(value):
    if type(value) is not list:
        raise Invalid('containers must be built-in lists')
    return value


def require_keys(value, required, optional=()):
    if type(value) is not dict or len(value) > len(required) + len(optional) or not set(required) <= set(value) or set(value) - set(required) - set(optional):
        raise Invalid('missing or unsupported dictionary keys')


def vector(arithmetic, value, size):
    if len(require_list(value)) != size:
        raise Invalid('vector dimension mismatch')
    return [arithmetic.read(x) for x in value]


def matrix(arithmetic, value, columns):
    return [vector(arithmetic, row, columns) for row in require_list(value)]


def check_spd(arithmetic, metric):
    size = len(metric)
    if any(metric[i][j] != metric[j][i] for i in range(size) for j in range(size)):
        raise Invalid('one shared symmetric positive-definite metric is required')

    work = [row[:] for row in metric]
    for k in range(size):
        pivot = work[k][k]
        if pivot <= 0:
            raise Invalid('one shared symmetric positive-definite metric is required')
        for i in range(k + 1, size):
            for j in range(k + 1, size):
                work[i][j] = arithmetic.sub(work[i][j], arithmetic.div(arithmetic.mul(work[i][k], work[k][j]), pivot))


def parse_problem(arithmetic, problem):
    require_keys(problem, ('metric', 'equalities', 'rows', 'bounds', 'level', 'scenarios'))
    n = len(require_list(problem['metric']))
    q = len(require_list(problem['equalities']))
    m = len(require_list(problem['rows']))
    count = len(require_list(problem['scenarios']))
    if n > MAX_DIM or q > MAX_DIM or m > MAX_ROWS or count > MAX_SCENARIOS:
        raise Limit('dimension or scenario count limit')
    if count == 0:
        raise Invalid('at least one scenario is required')
    M = matrix(arithmetic, problem['metric'], n)
    N = matrix(arithmetic, problem['equalities'], n)
    L = matrix(arithmetic, problem['rows'], n)
    beta = vector(arithmetic, problem['bounds'], m)
    E = arithmetic.read(problem['level'])
    check_spd(arithmetic, M)
    scenarios = []
    seen = set()
    for entry in problem['scenarios']:
        require_keys(entry, ('id', 'constant', 'center', 'target', 'row_offset'))
        label = entry['id']
        if type(label) is not str or not 0 < len(label) <= 128 or label in seen:
            raise Invalid('scenario IDs must be unique nonempty strings of at most 128 characters')
        seen.add(label)
        cost = arithmetic.read(entry['constant'])
        scenarios.append({'id': label, 'constant': cost,
                          'center': vector(arithmetic, entry['center'], n),
                          'target': vector(arithmetic, entry['target'], q),
                          'row_offset': vector(arithmetic, entry['row_offset'], m)})
    return M, N, L, beta, E, scenarios


def weighted_columns(arithmetic, matrix_value, weights, dimension):
    return [arithmetic.dot(weights, [row[j] for row in matrix_value]) for j in range(dimension)]


def primal_check(arithmetic, M, N, L, beta, E, scenarios, raw):
    point = vector(arithmetic, raw, len(M))
    targets = [arithmetic.subtract(point, h['center']) for h in scenarios]
    costs = [arithmetic.add(h['constant'], arithmetic.quad(M, v)) for h, v in zip(scenarios, targets)]
    common_rows = arithmetic.mv(L, point)
    outputs = [[arithmetic.add(h['row_offset'][j], common_rows[j]) for j in range(len(L))] for h in scenarios]
    equalities_ok = all(arithmetic.mv(N, v) == h['target'] for h, v in zip(scenarios, targets))
    rows_ok = all(output[j] <= beta[j] for output in outputs for j in range(len(L)))
    upper = max(costs)
    geometry_ok = equalities_ok and rows_ok
    return {'point': point, 'scenario_displacements': targets,
            'scenario_total_costs': costs, 'scenario_outputs': outputs,
            'equalities_satisfied': equalities_ok, 'rows_satisfied': rows_ok,
            'row_feasible': geometry_ok, 'upper_bound': upper,
            'within_level': upper <= E, 'proves_feasible': geometry_ok and upper <= E}


def dual_check(arithmetic, M, N, L, d, htarget, scenarios, raw):
    require_keys(raw, ('scenario_weights', 'row_multipliers', 'equality_multipliers'))
    weights = vector(arithmetic, raw['scenario_weights'], len(scenarios))
    mu = vector(arithmetic, raw['row_multipliers'], len(L))
    nu = vector(arithmetic, raw['equality_multipliers'], len(N))
    if any(x < 0 for x in weights) or arithmetic.dot(weights, [Fraction(1)] * len(weights)) != 1:
        raise Invalid('scenario weights must be nonnegative and sum exactly to one')
    if any(x < 0 for x in mu):
        raise Invalid('row multipliers must be nonnegative')
    centers = [item['center'] for item in scenarios]
    center = weighted_columns(arithmetic, centers, weights, len(M))
    nt = weighted_columns(arithmetic, N, nu, len(M))
    lt = weighted_columns(arithmetic, L, mu, len(M))
    normal = [arithmetic.add(x, y) for x, y in zip(nt, lt)]
    riesz, _ = arithmetic.linear_system(M, normal, len(M))
    minimizer = [arithmetic.sub(center[j], arithmetic.div(riesz[j], Fraction(2))) for j in range(len(M))]
    constants = [arithmetic.add(item['constant'], arithmetic.quad(M, item['center'])) for item in scenarios]
    lower = arithmetic.sub(arithmetic.sub(arithmetic.sub(arithmetic.dot(weights, constants),
                           arithmetic.dot(mu, d)), arithmetic.dot(nu, htarget)), arithmetic.quad(M, minimizer))
    return {'valid': True, 'scenario_weights': weights, 'row_multipliers': mu,
            'equality_multipliers': nu, 'weighted_center': center, 'combined_normal': normal,
            'lagrangian_minimizer': minimizer, 'lower_bound': lower}


def farkas_check(arithmetic, N, L, d, htarget, dimension, raw):
    require_keys(raw, ('row_multipliers', 'equality_multipliers'))
    mu = vector(arithmetic, raw['row_multipliers'], len(L))
    nu = vector(arithmetic, raw['equality_multipliers'], len(N))
    if any(x < 0 for x in mu):
        raise Invalid('Farkas row multipliers must be nonnegative')
    normal = [arithmetic.add(x, y) for x, y in zip(
              weighted_columns(arithmetic, N, nu, dimension),
              weighted_columns(arithmetic, L, mu, dimension))]
    value = arithmetic.add(arithmetic.dot(nu, htarget), arithmetic.dot(mu, d))
    valid = not any(normal) and value < 0
    return {'valid': valid, 'row_multipliers': mu, 'equality_multipliers': nu,
            'combined_normal': normal, 'strict_value': value}


def _verify(arithmetic, problem, witness):
    M, N, L, beta, E, scenarios = parse_problem(arithmetic, problem)
    n = len(M)
    targets = [[arithmetic.add(x, y) for x, y in zip(item['target'], arithmetic.mv(N, item['center']))] for item in scenarios]
    output = {'status': 'unresolved', 'reason': 'no decisive valid witness supplied',
              'level': E, 'scenarios': scenarios, 'common_equality_targets': targets,
              'row_feasibility': 'not_established', 'witness_checks': {}}
    if any(target != targets[0] for target in targets):
        output.update(status='infeasible', reason='common equality targets disagree', row_feasibility='proved_empty',
                      obstruction={'kind': 'incompatible_common_equalities', 'targets': targets})
        return output
    htarget = targets[0]
    _, annihilator = arithmetic.linear_system(N, htarget, n)
    if annihilator is not None:
        check = weighted_columns(arithmetic, N, annihilator, n)
        value = arithmetic.dot(annihilator, htarget)
        if any(check) or value == 0:
            raise Invalid('internal equality inconsistency witness failed')
        output.update(status='infeasible', reason='common equality target is outside the exact range', row_feasibility='proved_empty',
                      obstruction={'kind': 'equality_range', 'left_null_multiplier': annihilator, 'target_pairing': value})
        return output
    d = [arithmetic.sub(beta[j], max(item['row_offset'][j] for item in scenarios)) for j in range(len(L))]
    output['tightened_common_rows'] = d
    if witness is None:
        return output
    try:
        require_keys(witness, (), ('point', 'dual', 'farkas'))
    except Invalid as error:
        output['witness_checks']['input'] = {'valid': False, 'error': str(error)}
        return output
    checks = output['witness_checks']
    callbacks = {
        'point': lambda raw: primal_check(arithmetic, M, N, L, beta, E, scenarios, raw),
        'dual': lambda raw: dual_check(arithmetic, M, N, L, d, htarget, scenarios, raw),
        'farkas': lambda raw: farkas_check(arithmetic, N, L, d, htarget, n, raw),
    }
    for kind, callback in callbacks.items():
        if kind in witness:
            try:
                checks[kind] = callback(witness[kind])
            except Invalid as error:
                checks[kind] = {'valid': False, 'error': str(error)}
    primal = checks.get('point', {})
    dual = checks.get('dual', {})
    farkas = checks.get('farkas', {})
    if primal.get('row_feasible'):
        output['row_feasibility'] = 'proved_nonempty'
    if farkas.get('valid'):
        output.update(status='infeasible', reason='Farkas witness proves finite rows inconsistent with equalities',
                      row_feasibility='proved_empty')
        return output
    if dual.get('valid') and primal.get('row_feasible'):
        gradient = arithmetic.mv(M, arithmetic.subtract(primal['point'], dual['weighted_center']))
        stationarity = [arithmetic.add(arithmetic.mul(Fraction(2), x), y) for x, y in zip(gradient, dual['combined_normal'])]
        scenario_products = [arithmetic.mul(weight, arithmetic.sub(cost, primal['upper_bound']))
                             for weight, cost in zip(dual['scenario_weights'], primal['scenario_total_costs'])]
        row_products = [arithmetic.mul(mu, arithmetic.sub(value, bound)) for mu, value, bound in
                        zip(dual['row_multipliers'], arithmetic.mv(L, primal['point']), d)]
        kkt = not any(stationarity + scenario_products + row_products) and primal['upper_bound'] == dual['lower_bound']
        output['kkt'] = {'verified': kkt, 'stationarity_residual': stationarity,
                         'scenario_complementarity': scenario_products, 'row_complementarity': row_products,
                         'duality_gap': arithmetic.sub(primal['upper_bound'], dual['lower_bound'])}
        if kkt:
            output['exact_threshold'] = primal['upper_bound']
    if primal.get('proves_feasible'):
        output.update(status='feasible', reason='one supplied common point satisfies every scenario, finite row and level')
    elif dual.get('valid') and dual['lower_bound'] > E:
        output.update(status='infeasible', reason='strict dual lower bound excludes every row-feasible common point')
    return output


def certify(problem, witness=None):


    arithmetic = Exact()
    try:
        result = _verify(arithmetic, problem, witness)
    except Invalid as error:
        result = {'status': 'invalid_input', 'reason': str(error)}
    except Limit as error:
        result = {'status': 'unresolved', 'reason': str(error)}
    result.update(arithmetic_operations=arithmetic.operations,
                  schema='fm-quadratic-minimax/1',
                  scope='declared finite rational quadratic system',
                  optimization_search='not_performed')
    return result


def jsonable(value):
    if type(value) is Fraction:
        return str(value)
    if type(value) is dict:
        return {key: jsonable(item) for key, item in value.items()}
    if type(value) is list:
        return [jsonable(item) for item in value]
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid('duplicate JSON key')
        result[key] = value
    return result


def main():

    try:
        raw = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
        if len(raw) > MAX_JSON_BYTES:
            raise Limit('JSON byte limit')
        request = json.loads(raw, object_pairs_hook=unique_object)
        require_keys(request, ('problem',), ('witness',))
        result = certify(request['problem'], request.get('witness'))
    except Limit as error:
        result = {'status': 'unresolved', 'reason': str(error)}
    except (Invalid, ValueError, UnicodeError, RecursionError) as error:
        result = {'status': 'invalid_input', 'reason': str(error)}
    result.setdefault('schema', 'fm-quadratic-minimax/1')
    print(json.dumps(jsonable(result), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
