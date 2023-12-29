from __future__ import annotations

import abc
import copy
from typing import Any, Callable, Dict, Generic, Iterable, List, Optional, Tuple, TypeVar, Union
import pydantic

A = TypeVar("A")
B = TypeVar("B")
T = TypeVar("T")
R = TypeVar("R")
Q = TypeVar("Q")

"""
class Gettable(Generic[T, R], abc.ABC):
    @abc.abstractmethod
    def get(self, obj: T) -> R:
        pass

class Settable(Generic[T, R]):
    @abc.abstractmethod
    def set(self, obj: T, val: R) -> T:
        pass

class Replacable(Generic[T, R], abc.ABC):
    @abc.abstractmethod
    def replace(self, obj: T, val: R) -> T:
        pass
"""


def make_binop(imp, sym):
    imp.__sumbol__ = sym

    def func(self, other):
        if isinstance(other, Lens):
            return Binop(lhs=self, rhs=other, binop=imp)
        else:
            return Binop(lhs=self, rhs=Literal(val=other), binop=imp)

    return func

def make_unop(imp, sym):
    imp.__sumbol__ = sym

    def func(self):
        return Unop(lhs=self, unop=imp)

    return func

class Lenses():
    @staticmethod
    def dict_items(d: Dict) -> Iterable[Lens]:
        for k in d.keys():
            yield Item(item=k)

    @staticmethod
    def list_items(l: List) -> Iterable[Lens]:
        for i in range(len(l)):
            yield Item(item=i)

class Lens(abc.ABC, pydantic.BaseModel, Generic[T, R]):
    #def __repr__(self) -> str:
    #    return "Lens()"

    def __call__(self, *args, **kwargs) -> R:
        return self.get(*args, **kwargs)

    def _get_only_input(self, args, kwargs):
        if len(args) == 1 and len(kwargs) == 0:
            return args[0]

        if len(args) == 0 and len(kwargs) == 1:
            return next(iter(kwargs.values()))

        raise ValueError("Ambiguous object.")

    #def get(self, *args, **kwargs) -> R:
    #    return self._get_only_input(args, kwargs)

    def set(self, *args, val: R, **kwargs) -> R:
        return val

    def replace(self, *args, val: R, **kwargs) -> R:
        return val

    # https://docs.python.org/3/reference/datamodel.html#object.__lt__
    __ge__ = make_binop(lambda a, b: a >= b, ">=")
    __le__ = make_binop(lambda a, b: a <= b, "<=")
    __gt__ = make_binop(lambda a, b: a > b, ">")
    __lt__ = make_binop(lambda a, b: a < b, "<")
    __eq__ = make_binop(lambda a, b: a == b, "==")
    __ne__ = make_binop(lambda a, b: a != b, "!=")

    # https://docs.python.org/3/reference/datamodel.html#emulating-numeric-types
    __add__ = make_binop(lambda a, b: a + b, "+")
    __sub__ = make_binop(lambda a, b: a - b, "-")
    __mul__ = make_binop(lambda a, b: a * b, "*")
    __matmul__ = make_binop(lambda a, b: a * b, "@")
    __truediv__ = make_binop(lambda a, b: a / b, "/")
    __floordiv__ = make_binop(lambda a, b: a / b, "//")
    __mod__ = make_binop(lambda a, b: a % b, "%")
    __divmod__ = make_binop(lambda a, b: divmod(a, b), "divmod")
    __pow__ = make_binop(lambda a, b: a ** b, "**") # modulo?
    __lshift__ = make_binop(lambda a, b: a << b, "<<")
    __rshift__ = make_binop(lambda a, b: a >> b, ">>")
    __and__ = make_binop(lambda a, b: a & b, "&")
    __xor__ = make_binop(lambda a, b: a ^ b, "^")
    __or__ = make_binop(lambda a, b: a | b, "|")

    # https://docs.python.org/3/reference/datamodel.html#object.__neg__
    __neg__ = make_unop(lambda a: - a, "-")
    __pos__ = make_unop(lambda a: + a, "+")
    __abs__ = make_unop(lambda a: abs(a), "abs")
    __invert__ = make_unop(lambda a: ~ a, "~")

    def __getitem__(self: Lens[T, R], item: Union[str, int]) -> Lens[T, R]:
        outer = Item(item=item)
        if issubclass(Lens, type(self)):
            return outer
        else:
            return Comp(inner=self, outer=outer)

    def __getattr__(self: Lens[T, R], attr: str) -> Lens[T, R]:
        outer = Attr(attr=attr)
        if issubclass(Lens, type(self)):
            return outer
        else:
            return Comp(inner=self, outer=outer)

    #def __setattr__(self, attr: str, val: Any) ->

lens = Lens()

class Kwargs(Lens[T, Q]):
    def get(self, *args, **kwargs):
        return kwargs

class Args(Lens[T, Q]):
    def get(self, *args, **kwargs):
        return args

class Kwarg(Lens[T, Q]):
    kwarg: str

    def __init__(self, kwarg: str):
        super().__init__(kwarg=kwarg)

    def get(self, *args, **kwargs) -> Q:
        return kwargs[self.kwarg]

class Arg(Lens[T, Q]):
    arg: int

    def __init__(self, arg: int = 0):
        super().__init__(arg=arg)

    def get(self, *args, **kwargs) -> Q:
        return args[self.arg]

class Comp(Lens[T, Q], Generic[T, R, Q]):
    inner: Lens
    outer: Lens

    def get(self, *args, **kwargs) -> R:
        return self.outer.get(self.inner.get(*args, **kwargs))

    def set(self, obj: T, val: Q) -> T:
        return self.outer.set(
            obj=self.outer.get(obj),
            val=self.inner.set(obj, val)
        )
    def replace(self, obj: T, val: Q) -> T:
        return self.outer.replace(
            obj=self.outer.get(obj),
            val=self.inner.replace(obj, val)
        )

class Attr(Lens[T, R]):
    attr: str

    #def __repr__(self):
    #    return super().__repr__() + "." + self.attr

    def get(self, *args, **kwargs) -> R:
        obj = self._get_only_input(args, kwargs)
        if hasattr(obj, self.attr):
            return getattr(obj, self.attr)
        else:
            raise AttributeError(self.attr)

    def set(self, obj: T, val: R) -> T:
        setattr(obj, self.attr, val)
        return obj

    def replace(self, obj: T, val: R) -> T:
        obj_copy = copy.deepcopy(obj)
        setattr(obj_copy, self.attr, val)
        return obj_copy

class Item(Lens[T, R]):
    item: Union[str, int]

    #def __repr__(self):
    #    return super().__repr__() + f"[{self.item}]"

    def get(self, *args, **kwargs) -> R:
        obj = self._get_only_input(args, kwargs)
        return obj[self.item]

    def set(self, obj: T, val: R) -> T:
        obj[self.item] = val
        return obj

    def replace(self, obj: T, val: R) -> T:
        obj_copy = copy.deepcopy(obj)
        obj_copy[self.item] = val
        return obj_copy

class Literal(Lens[T, R]):
    val: R

    #def __repr__(self):
    #    return repr(self.val)

    def get(self, *args, **kwargs) -> R:
        return self.val

    def set(self, obj: T, val: R) -> T:
        raise ValueError("Literal cannot be set.")

    def replace(self, obj: T, val: R) -> T:
        raise ValueError("Literal cannot be replaced.")

class Expr(Lens[T, R]):
    def set(self, obj: T, val: R) -> T:
        raise ValueError("Expression cannot be set.")

    def replace(self, obj: T, val: R) -> T:
        raise ValueError("Expression cannot be replaced.")

class Binop(Expr[T, Q], Generic[T, Q, R]):
    lhs: Lens# [T, Q]
    rhs: Lens# [T, Q]
    binop: Callable# [[Q, Q], R]

    #def __repr__(self):
    #    return f"{repr(self.lhs)}{self.binop.__symbol__}{repr(self.rhs)}"

    def get(self, *args, **kwargs) -> R:
        lhs_val = self.lhs.get(*args, **kwargs)
        rhs_val = self.rhs.get(*args, **kwargs)
        return self.binop(lhs_val, rhs_val)

class Unop(Expr[T, Q], Generic[T, Q, R]):
    lhs: Lens# [T, Q]
    unop: Callable# [[Q], R]

    #def __repr__(self):
    #    return f"{repr(self.lhs)}{self.binop.__symbol__}{repr(self.rhs)}"

    def get(self, *args, **kwargs) -> R:
        lhs_val = self.lhs.get(*args, **kwargs)
        return self.unop(lhs_val)

"""
class Steps(Lens[T, R]):
    steps: Tuple[Lens[T, R]] = ()

    def get(self, obj: T) -> R:
        for step in self.steps:
            obj = step.get(obj)
        return obj

    def replace(self, obj: T, val: R) -> T:
        if len(self.steps) == 0:
            return val
        if len(self.steps) == 1:
            return self.steps[0].replace(obj, val)
        else:
            step = self.steps[0]
            rest = Steps(steps=self.steps[1:])

            return step.replace(rest.get(step.get(obj)), val)

    def set(self, obj: T, val: R) -> T:
        if len(self.steps) == 0:
            raise ValueError("Cannot set Lens with no steps.")
        elif len(self.steps) == 1:
            step = self.steps[0]
            return step.set(obj, val)
        else:
            step = self.steps[0]
            rest = Steps(self.steps[1:])
            return step.set(rest.get(obj), val)
"""

# Expr.update_forward_refs()
# Add.update_forward_refs()
Literal.update_forward_refs()
Lens.update_forward_refs()
# Id.update_forward_refs()
Attr.update_forward_refs()
Comp.update_forward_refs()

args = Args()
kwargs = Kwargs()
arg = args[0]
