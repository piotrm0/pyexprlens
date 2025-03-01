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
# Basic identity lens can be imported as "_", "arg", or "ident":
from exprlens import _

# Lenses implement call:
assert _(42) == 42

assert (_+1)(1) == 2

assert (_[0]+_[1])([1,2]) == 3

# Lenses can alternatives to lambdas:
assert list(map(_+1, [1,2,3])) == [2,3,4]
```

## Get and set


```python
# Lens for getting the first item in the first argument from a call:
first = _[0]

# Getter can be accessed using the `get` method or by calling (`__call__`):
assert first.get([0, 1, 2, 3]) == first([0, 1, 2, 3]) == 0

# Setter can be accessed using the `set` method.
assert first.set([0, 1, 2, 3], val=42) == [42, 1, 2, 3]
```

## Predefined basic lenses


```python
from exprlens import (
    arg,
    kwargs,
    _,
    args,
    argskwargs,
    ArgsKwargs,
    ident,
    lens,
    arguments,
    all,
)

# All positional arguments:
assert args.get(42) == (42,)

# All keyword arguments:
assert kwargs.get(hello="there") == {"hello": "there"}

# All arguments, stored as `ArgsKwargs` object:
assert argskwargs.get(42, hello="there") == ArgsKwargs(
    args=(42,), kwargs={"hello": "there"}
)

# argskwargs, arguments, and all are aliases with different representations:
assert type(argskwargs) is type(arguments) is type(all)

# Only positional or keyword argument:
assert arg.get(42) == 42
assert arg.get(hello="there") == "there"
# arg.get(1,2) # error if more than one argument is given

# lens, arg, ident, and "_" are aliases with different representations:
assert type(arg) is type(ident) is type(lens) is type(_)
```

## Lense iterators


```python
from exprlens.valid import (
    ValidDict,
    ValidMapping,
    ValidTuple,
    ValidList,
    ValidSequence,
    ValidJSON,
)

seq = [1, 2, 3, 4]
# Lenses for each element in a sequence:
value_lenses = list(ValidSequence.elements(seq))
assert value_lenses[0].get(seq) == 1
assert value_lenses[1].get(seq) == 2
assert value_lenses[2].get(seq) == 3

# Elements can be set:
# Set the value at index 1 to 42:
assert value_lenses[1].set(seq, val=42) == [1, 42, 3, 4]

# Indices in a sequence:
seq = [1, 2, 3, 4]
index_lenses = list(ValidSequence.indices(seq))
assert index_lenses[0].get(seq) == 0
assert index_lenses[1].get(seq) == 1
assert index_lenses[2].get(seq) == 2

# Indices can be set:
# Index of element 1 to 3 thus copying the value at index 1 to index 3:
# Items at old index is spliced out.
assert index_lenses[1].set(seq, val=3) == [1, 3, 2]

# Values in a mapping:
mapping = {"a": 1, "b": 2}
value_lenses = list(ValidMapping.values(mapping))
assert value_lenses[0].get(mapping) == 1
assert value_lenses[1].get(mapping) == 2

# Values can be set:
# Set the value of key 'a' to 42:
assert value_lenses[0].set(mapping, val=42) == {"a": 42, "b": 2}

# Keys in a mapping:
key_lenses = list(ValidMapping.keys(mapping))
assert key_lenses[0].get(mapping) == "a"
assert key_lenses[1].get(mapping) == "b"

# Keys can be set:
# Key 'a' to 'c' thus renaming the key:
assert key_lenses[0].set(mapping, val="c") == {"c": 42, "b": 2}

# JSON-like objects:
obj = {"baseint": 1, "seqofints": [1, 2, 3], "seqofstrs": ["a", "b", "c"]}

# Get all lenses to JSON values including sequences and dictionaries:
for l in ValidJSON.all_values(obj):
    print(l, l.get(obj))

# Get lenses only to base JSON values (int, str, bool, None):
for l in ValidJSON.base_values(obj):
    print(l, l.get(obj))

# Get lenses only to values of the specified type, here int:
for l in ValidJSON.of_type(obj, int):
    print(l, l.get(obj))
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
args[0]  # ok
# args["something"] # error

kwargs["something"]  # ok
# kwargs[0] # error

# Lenses can be validated on use:

# Lens that gets a key from the first argument, thus the first argument must be a mapping:
firstkey = arg["something"]
firstkey.get({"something": 42})  # ok

# Will fail if the first argument is not a mapping:
# firstkey.get([1,2,3]) # error
```

## Boolean expressions

Python does not allow overriding boolean operators (`and`, `or`, `not`) (see
relevant [rejected PEP](https://peps.python.org/pep-0335/)) so lenses
corresponding to expressions with boolean operators cannot be created by writing
python directly, i.e. `lens[0] and lens[1]`. Instead you can make use of
`Lens.conjunction`, `Lens.disjunction`, and `Lens.negation` static methods to
construct these. Alternatively you can use `Lens.of_string` static method
to construct it from python code, e.g. `Lens.of_string("lens[0] and
lens[1]")`.



```python
from exprlens import Lens, lens

# Conjunction:
both = Lens.of_string("lens[0] and lens[1]")

assert Lens.conjunction(lens[0], lens[1]) == both

assert both([1, 2, 3, 4]) == 2

# Disjunction:
either = Lens.of_string("lens[0] or lens[1]")

assert Lens.disjunction(lens[0], lens[1]) == either

assert either([1, 2, 3, 4]) == 1

# Logical negation:
not_second = Lens.of_string("not lens[1]")

assert Lens.negation(lens[1]) == not_second

assert not_second([1, 2, 3, 4]) == False
```

## Serialization


```python
from exprlens import Lens, arg
from ast import parse, dump

plusone = arg + 1
assert repr(plusone) == "(arg + 1)"

assert dump(plusone.pyast) == dump(parse(str(plusone), mode="eval"))
assert plusone == Lens.of_string(str(plusone))
```
