"""Exact arithmetic in quadratic number fields with squarefree radicands."""
from dataclasses import dataclass
from fractions import Fraction


def rational(value):
    """Accept only integers and Fractions, never approximate inputs."""
    if not isinstance(value, (int, Fraction)):
        raise TypeError("expected int or Fraction")
    return Fraction(value)


@dataclass(frozen=True, eq=False)
class QuadraticElement:
    """An immutable a + b*sqrt(d), for squarefree integer d != 0, 1."""
    a: Fraction
    b: Fraction = Fraction(0)
    d: int = 5

    def __post_init__(self):
        if type(self.d) is not int:
            raise TypeError("d must be an integer")
        if self.d in (0, 1):
            raise ValueError("d must define a quadratic field")
        k = 2
        while k * k <= abs(self.d):
            if self.d % (k * k) == 0:
                raise ValueError("d must be squarefree")
            k += 1
        object.__setattr__(self, 'a', rational(self.a))
        object.__setattr__(self, 'b', rational(self.b))

    def _coerce(self, other):
        if isinstance(other, QuadraticElement):
            if self.d != other.d:
                raise ValueError("different quadratic fields")
            return other
        return QuadraticElement(rational(other), 0, self.d)

    def __add__(self, other):
        v = self._coerce(other)
        return QuadraticElement(self.a + v.a, self.b + v.b, self.d)

    __radd__ = __add__

    def __neg__(self):
        return QuadraticElement(-self.a, -self.b, self.d)

    def __sub__(self, other):
        return self + -self._coerce(other)

    def __rsub__(self, other):
        return self._coerce(other) + -self

    def __mul__(self, other):
        v = self._coerce(other)
        return QuadraticElement(self.a*v.a + self.d*self.b*v.b,
                                self.a*v.b + self.b*v.a, self.d)

    __rmul__ = __mul__

    def conjugate(self):
        return QuadraticElement(self.a, -self.b, self.d)

    def norm(self):
        return self.a*self.a - self.d*self.b*self.b

    def inverse(self):
        n = self.norm()
        if not n:
            raise ZeroDivisionError("zero has no inverse")
        return QuadraticElement(self.a/n, -self.b/n, self.d)

    def __truediv__(self, other):
        return self * self._coerce(other).inverse()

    def __rtruediv__(self, other):
        return self._coerce(other) * self.inverse()

    def __pow__(self, n):
        if type(n) is not int:
            raise TypeError("integer exponent required")
        if n < 0:
            return self.inverse() ** -n
        result, base = self._coerce(1), self
        while n:
            if n % 2:
                result *= base
            base *= base
            n //= 2
        return result

    def __eq__(self, other):
        v = self._coerce(other)
        return self.a == v.a and self.b == v.b

    def __hash__(self):
        return hash(self.a) if not self.b else hash((self.a, self.b, self.d))

    def is_zero(self):
        return not self.a and not self.b

    def __repr__(self):
        return f"{self.a}{'+' if self.b >= 0 else ''}{self.b}*sqrt{self.d}"


def Q5(a, b=0):
    """Construct an element of Q(sqrt5)."""
    return QuadraticElement(a, b, 5)


GOLDEN = Q5(Fraction(1, 2), Fraction(1, 2))
