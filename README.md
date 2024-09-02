# Python Expression Lenses

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

## Basic usage


```python
from exprlens import arg

# Lens for getting the first item in the first argument from a call:
first = arg[0]  

# Getter can be accessed using the `get` method or by calling (`__call__`):
assert first.get([0, 1, 2, 3]) == first([0, 1, 2, 3]) == 0

# Setter can be accessed using the `set` method.
assert first.set([0, 1, 2, 3], val=42) == [42, 1, 2, 3]
```

## Expressions


```python
from exprlens import arg

# Lens that first grabs the first two items in the first argument and adds them:
plusfirsts = arg[0] + arg[1]  

# Note that once expression lenses are constructed, `set` can no longer be used on them.
# plusfirsts.set([1, 2, 3, 4], val=42)  # Raises an exception.

assert plusfirsts([1, 2, 3, 4]) == 3

# Literals/constants: Expression lenses can involve literals/constants.
plusone = arg + 1
assert list(map(plusone, [1, 2, 3])) == [2, 3, 4]
```

## Validation


```python
from exprlens import args, kwargs

# Lenses can be validate on construction:
args[0] # ok
# args["something"] # error

kwargs["something"] # ok
# kwargs[0] # error

# Lenses can be validated on use:

# Lens that gets a key from the first argument, thus the first argument must be a mapping:
firstkey = arg["something"]
firstkey.get({"something": 42}) # ok

# Will fail if the first argument is not a mapping:
# firstkey.get([1,2,3]) # error
```

## Boolean expressions (TODO)

Python does not allow overriding boolean operators (`and`, `or`, `not`) (see
relevant [rejected PEP](https://peps.python.org/pep-0335/)) so lenses
corresponding to expressions with boolean operators cannot be created by writing
python directly, i.e. `lens[0] and lens[1]`. Instead you can make use of
`Expr.conjunction`, `Expr.disjunction`, and `Expr.negation` static methods to
construct these. Alternatively you can use `Expr.of_string` static method
to construct it from python code, e.g. `Expr.of_string("lens[0] and
lens[1]")`.



```python
from exprlens import Expr, lens

assert Expr.conjunction(lens[0], lens[1]) == Expr.of_string("lens[0] and lens[1]")
```

## Serialization (TODO)


```python
from exprlens import Expr
from ast import parse

assert repr(plusone) == "(args[0] + 1)"

assert plusone.pyast == parse(repr(plusone), mode="eval")
assert plusone == Expr.of_string(repr(plusone))
```
