# Python Expression Lenses (exprlens)

Python expressions to/from lenses. This library focuses on constructing lenses
from python expressions, targeting function bindings as the primary container to
get/set from/to. Such lenses can be serialized into strings which are valid python expressions (and thus can be deserialized using the python expression parser).

## Alternatives

This package has very specific goals which are not considerations in the theory of lenses. Consider these alternatives for more general lens usage:

- [lenses](https://python-lenses.readthedocs.io/en/latest/tutorial/intro.html) -
  more general and feature rich lenses implementation based on lenses in
  Haskell.
- [pylens](https://pythonhosted.org/pylens/) - simpler
- [simplelens](https://pypi.org/project/simplelens/) - unknown functionality

## Basic Usage

```python
from exprlens import arg

first = arg[0] # lens for getting the first item in the first argument from a call

# Getter can be accessed using the `get` method or by calling (`__call__`):
assert first.get([0,1,2,3]) == first([0,1,2,3]) == 0

# Setter can be accessed using the `set` method:
assert first.set([0,1,2,3], val=42) == [42, 1, 2, 3]

# Setters mutate the input:
l = [0,1,2,3]
first.set(l, val=42)
assert l == [42, 1, 2, 3]

# Setters fail if the given object is not mutable:
first.set((0,1,2,3), val=42) # error

# Non-mutable version of `set` is `replace`:
assert first.replace((0,1,2,3), val=42) == (42, 1, 2, 3)

# Replace does not modify the given object:
l = [0,1,2,3]
first.replace(l, val=42)
assert l == [0, 1, 2, 3]
```

## Expressions
```python
# lens that first grabs the first two items in the first argument and adds them:
plusfirsts = arg[0] + arg[1] 

assert plusfirsts([1,2,3,4]) == 3

# Note that arithmetic expression (plus here) lenses do not allow `set` to be used on them.
plusfirsts.set([1,2,3,4], val=42) # error
```

### Boolean expressions

Python does not allow overriding boolean operators (`and`, `or`, `not`) (see
relevant [rejected PEP](https://peps.python.org/pep-0335/)) so lenses
corresponding to expressions with boolean operators cannot be created by writing
python directly, i.e. `lens[0] and lens[1]`. Instead you can make use of
`Expr.conjunction`, `Expr.disjunction`, and `Expr.negation` static methods to
construct these. Alternatively you can use `Expr.of_string` static method
to construct it from python code, e.g. `Expr.of_string("lens[0] and
lens[1]")`.

```python
assert Expr.conjunction(lens[0], lens[1]) == Expr.of_string("lens[0] and lens[1]")
```

## Constants

Expression lenses can involve constants.

```python
plusone = arg + 1
plusone(3) == 4
```

## Serialization
```python
from exprlens import Expr
from ast import parse

assert repr(plusone) == "arg + 1"

assert plusone.pyast == parse(repr(plusone), mode="eval")
assert plusone == Expr.of_string(repr(plusone))
```