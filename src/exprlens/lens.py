from __future__ import annotations

import abc
import ast
import copy
import inspect
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

import pydantic
import typeguard

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")

T = TypeVar("T")

K = TypeVar("K")
V = TypeVar("V")

TypeLike = Any
"""
# having trouble with this to catch Sequence, Mapping, etc.
typing.Union[
    Type,
    typing.TypeAlias,
    typing.GenericAlias
]
"""

LENS_SYMBOL = "@"

def _make_binop(imp, sym):
    imp.__symbol__ = sym

    def func(self, other):
        if isinstance(other, Lens):
            return Binop(lhs=self, rhs=other, binop=imp)
        else:
            return Binop(lhs=self, rhs=Literal(val=other), binop=imp)

    return func


def _make_unop(imp, sym):
    imp.__symbol__ = sym

    def func(self):
        return Unop(lhs=self, unop=imp)

    return func


class Model(pydantic.BaseModel):
    model_config: ClassVar[pydantic.ConfigDict] = pydantic.ConfigDict(
        arbitrary_types_allowed=True)


class Lens(abc.ABC, Model, Generic[A, B]):
    obj_class: Optional[TypeLike] = pydantic.Field(None)
    key_class: Optional[TypeLike] = pydantic.Field(None)

    def _assert_obj(self, obj: A) -> None:
        if self.obj_class is not None:
            try:
                typeguard.check_type(obj, self.obj_class)
            except typeguard.TypeCheckError as e:
                raise ValueError(
                    f"Expected `{self.obj_class.__name__}` at `{str(self)}`, got `{type(obj).__name__}`."
                ) from e

    def _assert_key(self, key: A) -> None:
        if self.key_class is not None:
            try:
                typeguard.check_type(key, self.key_class)
            except typeguard.TypeCheckError as e:
                raise ValueError(
                    f"Expected `{self.key_class.__name__}` for `{str(self)}` key, got `{type(key).__name__}`."
                ) from e
    
    def validated(self, obj_class: type) -> type:
        return type(self.__class__.__name__ + "Validated", (self.__class__, ),
                    {
                        "obj_class": obj_class,
                        **self.model_dump()
                    })

    @staticmethod
    def of_expr(expr: Union[str, ast.Expr]) -> Lens[A, B]:
        pass

    def each(self, *args, **kwargs) -> Iterable[B]:
        return iter([self.get(*args, **kwargs)])

    def __len__(self) -> int:
        return 1

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return self.__str_step__()

    def __str_step__(self) -> str:
        raise NotImplementedError(
            f"Step str not implemented for {self.__class__.__name__}.")

    def __call__(self, *args, **kwargs) -> B:
        return self.get(*args, **kwargs)

    def _get_only_input(self, args, kwargs) -> B:
        if len(args) == 1 and len(kwargs) == 0:
            return args[0]

        if len(args) == 0 and len(kwargs) == 1:
            return next(iter(kwargs.values()))

        raise ValueError("Ambiguous object.")

    def get(self, *args, **kwargs) -> B:
        raise NotImplementedError(
            f"Get not implemented for {self.__class__.__name__}.")

    def set(self, *args, val: B, **kwargs) -> A:
        raise NotImplementedError(
            f"Set not implemented for {self.__class__.__name__}.")

    def replace(self, *args, val: B, **kwargs) -> A:
        obj = self._get_only_input(args, kwargs)
        obj_copy = copy.deepcopy(obj)
        self.set(obj_copy, val)
        return obj_copy

    # https://docs.python.org/3/reference/datamodel.html#object.__lt__
    __ge__ = _make_binop(lambda a, b: a >= b, ">=")
    __le__ = _make_binop(lambda a, b: a <= b, "<=")
    __gt__ = _make_binop(lambda a, b: a > b, ">")
    __lt__ = _make_binop(lambda a, b: a < b, "<")
    __eq__ = _make_binop(lambda a, b: a == b, "==")
    __ne__ = _make_binop(lambda a, b: a != b, "!=")

    # https://docs.python.org/3/reference/datamodel.html#emulating-numeric-types
    __add__ = _make_binop(lambda a, b: a + b, "+")
    __sub__ = _make_binop(lambda a, b: a - b, "-")
    __mul__ = _make_binop(lambda a, b: a * b, "*")
    __matmul__ = _make_binop(lambda a, b: a * b, "@")
    __truediv__ = _make_binop(lambda a, b: a / b, "/")
    __floordiv__ = _make_binop(lambda a, b: a / b, "//")
    __mod__ = _make_binop(lambda a, b: a % b, "%")
    __divmod__ = _make_binop(lambda a, b: divmod(a, b), "divmod")
    __pow__ = _make_binop(lambda a, b: a**b, "**")  # modulo?
    __lshift__ = _make_binop(lambda a, b: a << b, "<<")
    __rshift__ = _make_binop(lambda a, b: a >> b, ">>")
    __and__ = _make_binop(lambda a, b: a & b, "&")
    __xor__ = _make_binop(lambda a, b: a ^ b, "^")
    __or__ = _make_binop(lambda a, b: a | b, "|")

    # https://docs.python.org/3/reference/datamodel.html#object.__neg__
    __neg__ = _make_unop(lambda a: -a, "-")
    __pos__ = _make_unop(lambda a: +a, "+")
    __abs__ = _make_unop(lambda a: abs(a), "abs")
    __invert__ = _make_unop(lambda a: ~a, "~")

    def __getitem__(self: Lens[A, B], item: Union[slice, str,
                                                  int]) -> Lens[A, C]:
        
        self._assert_key(item)
        
        if isinstance(item, slice):
            outer: Lens[B, C] = SequenceSlice(item=_Slice.of_slice(item))
        elif isinstance(item, int):
            outer: Lens[B, C] = SequenceIndex(item=item)
        elif isinstance(item, str):
            outer: Lens[B, C] = MappingValue(item=item)
        else:
            raise ValueError(f"Unsupported item type: {type(item)}")

        if isinstance(self, Ident):
            return outer

        if isinstance(self, Seq):
            return Seq(steps=self.steps + [outer])

        return Seq(steps=[self, outer])

    def __getattr__(self: Lens[A, B], attr: str) -> Lens[A, C]:
        outer = Attr(attr=attr)

        if isinstance(self, Ident):
            return outer

        if isinstance(self, Seq):
            return Seq(steps=self.steps + [outer])

        return Seq(steps=[self, outer])


class ArgsKwargs(Model):
    args: Tuple
    kwargs: Dict[str, Any]

    def bind_onto(
            self, sig: Union[Callable,
                             inspect.Signature]) -> inspect.BoundArguments:
        if not isinstance(sig, inspect.Signature):
            sig = inspect.signature(sig)

        return sig.bind(*self.args, **self.kwargs)


class Ident(Lens[A, ArgsKwargs]):
    def __str_step__(self) -> str:
        return ""

    def get(self, *args, **kwargs) -> ArgsKwargs:
        return ArgsKwargs(args=args, kwargs=kwargs)

    def set(self, obj: A, val: A) -> A:
        return val


class Kwargs(Lens[A, Dict[str, B]]):
    key_class: TypeLike = str

    def __str_step__(self) -> str:
        return "kwargs"

    def get(self, *args, **kwargs) -> Dict[str, B]:
        return kwargs


class Args(Lens[A, Tuple[B, ...]]):
    key_class: TypeLike = int

    def __str_step__(self) -> str:
        return "args"

    def get(self, *args, **kwargs) -> Tuple[B, ...]:
        return args


class Seq(Lens[A, B]):
    steps: List[Lens]  # A -> a -> b -> ... -> B

    @staticmethod
    def _each(steps: List[Lens], *args, **kwargs) -> Iterable[B]:
        if len(steps) == 0:
            yield Lens._get_only_input(args, kwargs)
        else:
            for val in steps[0].each(*args, **kwargs):
                yield from Seq._each(steps[1:], val)

    def each(self, *args, **kwargs) -> Iterable[B]:
        return Seq._each(self.steps, *args, **kwargs)

    def __len__(self) -> int:
        return sum(map(len, self.steps))

    def __str__(self) -> str:
        return "".join(
            map(lambda x: x.__str_step__(), self.steps))
    
    def __str_step__(self) -> str:
        return str(self)

    def get(self, *args, **kwargs) -> B:
        if len(self.steps) == 0:
            return Ident().get(*args, **kwargs)
        elif len(self.steps) == 1:
            return self.steps[0].get(*args, **kwargs)

        val = self.steps[0].get(*args, **kwargs)
        for step in self.steps[1:]:
            val = step.get(val)
        return val

    @staticmethod
    def _set(steps: List[Lens], obj: A, val: B) -> A:
        if len(steps) == 0:
            return val
        else:
            old_obj = steps[0].get(obj)
            new_obj = Seq._set(
                steps[1:],
                obj=old_obj,
                val=val
            )
            if id(old_obj) != id(new_obj):
                # Only set if a different object was returned. 
                return steps[0].set(
                    obj=obj,
                    val=new_obj
                )
            else:
                return obj
            
    def set(self, obj: A, val: B) -> A:
        return Seq._set(self.steps, obj, val)


class Attr(Lens[A, B]):
    attr: str

    def __str_step__(self) -> str:
        return f".{self.attr}"

    def get(self, *args, **kwargs) -> B:
        obj = self._get_only_input(args, kwargs)
        if hasattr(obj, self.attr):
            return getattr(obj, self.attr)
        else:
            raise AttributeError(self.attr)

    def set(self, obj: A, val: B) -> B:
        setattr(obj, self.attr, val)
        return obj


class Item(Lens[A, B], Generic[A, B, T]):
    item: T

    def __str_step__(self) -> str:
        return f"[{repr(self.item)}]"

    def get(self, *args, **kwargs) -> B:
        obj = self._get_only_input(args, kwargs)

        self._assert_obj(obj)

        return obj[self.item]

    def set(self, obj: A, val: B) -> A:
        self._assert_obj(obj)

        obj[self.item] = val

        return obj


class Kwarg(Item[Dict[str, B], B, str]):
    pass

class Arg(Item[Tuple[B, ...], B, int]):
    pass

class SequenceIndex(Item[Sequence[B], B, int]):
    obj_class: TypeLike = Sequence[B]


class _Slice(pydantic.BaseModel):
    start: Optional[int] = None
    stop: Optional[int] = None
    step: Optional[int] = None

    def __str__(self) -> str:
        return f"{self.start or ''}:{self.stop or ''}:{self.step or ''}"

    @staticmethod
    def of_slice(s: slice) -> _Slice:
        return _Slice(start=s.start, stop=s.stop, step=s.step)

    def to_slice(self) -> slice:
        return slice(self.start, self.stop, self.step)


class SequenceSlice(Item[Sequence[B], B, _Slice]):
    obj_class: TypeLike = Sequence[B]

    def get(self, *args, **kwargs) -> B:
        obj: Sequence[B] = self._get_only_input(args, kwargs)
        return obj[self.item.to_slice()]

    def set(self, obj: Sequence[B], val: B) -> T:
        obj[self.item.to_slice()] = val
        return obj


class MappingValue(Item[Mapping[A, B], B, B]):
    obj_class: TypeLike = Mapping[A, B]


class MappingKey(Item[Mapping[A, B], B, A]):
    obj_class: TypeLike = Mapping

    def get(self, *args, **kwargs) -> A:
        return self.item

    def set(self, obj: Mapping[A, B], val: A) -> Mapping[A, B]:
        obj[val] = obj.pop(self.item)
        return obj


class Expr(Lens[A, B]):

    def __str__(self) -> str:
        return self.__str_step__()

    def set(self, obj: A, val: B) -> A:
        raise ValueError(f"Expression {str(self)} cannot be set.")

    def replace(self, obj: A, val: B) -> B:
        raise ValueError(f"Expression {str(self)} cannot be replaced.")


class Literal(Expr[A, B]):
    val: B

    def __str_step__(self) -> str:
        return repr(self.val)

    def get(self, *args, **kwargs) -> B:
        return self.val

    def set(self, obj: A, val: B) -> A:
        raise ValueError("Literal cannot be set.")

    def replace(self, obj: A, val: B) -> A:
        raise ValueError("Literal cannot be replaced.")


class Binop(Expr[A, C], Generic[A, B, C]):
    lhs: Lens  # [A, B]
    rhs: Lens  # [A, B]
    binop: Callable  # [[B, B], C]

    def __str_step__(self) -> str:
        return f"({str(self.lhs)} {self.binop.__symbol__} {str(self.rhs)})"

    def get(self, *args, **kwargs) -> C:
        lhs_val = self.lhs.get(*args, **kwargs)
        rhs_val = self.rhs.get(*args, **kwargs)
        return self.binop(lhs_val, rhs_val)


class Unop(Expr[A, C], Generic[A, B, C]):
    lhs: Lens  # [A, B]
    unop: Callable  # [[B], C]

    def __str_step__(self) -> str:
        return f"{self.unop.__symbol__}({str(self.lhs)})"

    def get(self, *args, **kwargs) -> C:
        lhs_val = self.lhs.get(*args, **kwargs)
        return self.unop(lhs_val)


# Expr.update_forward_refs()
# Add.update_forward_refs()
# Literal.update_forward_refs()
# Lens.update_forward_refs()
# Id.update_forward_refs()
# Attr.update_forward_refs()
# Seq.update_forward_refs()

argskwargs = Ident()
lens = Ident()
args = Args()
kwargs = Kwargs()
arg = args[0]

__all__ = ["argskwargs", "args", "kwargs", "arg", "Lens", "lens"]
