from __future__ import annotations

import typing

import typeguard

from .lens import Ident
from .lens import Item
from .lens import Lens
from .lens import MappingKey
from .lens import MappingValue
from .lens import SequenceElement
from .lens import SequenceIndex

A = typing.TypeVar("A")
B = typing.TypeVar("B")
T = typing.TypeVar("T")
R = typing.TypeVar("R")
Q = typing.TypeVar("Q")

K = typing.TypeVar("K")
V = typing.TypeVar("V")

JSONBase = typing.Union[str, int, float, bool, type(None)]
JSONLike = typing.Union[
    typing.Dict[str, typing.Any],
    typing.List[typing.Any],
    str,
    int,
    float,
    bool,
    type(None),
]
JSON = typing.Dict[str, JSONLike]


def typ_isinstance(obj, typ):
    try:
        typeguard.check_type(obj, typ)
        return True
    except typeguard.TypeCheckError:
        return False


class ValidJSON:
    @staticmethod
    def of_type(obj: JSONLike, typ: T) -> typing.Iterable[Lens[JSONLike, T]]:
        try:
            typeguard.check_type(obj, JSONLike)
        except typeguard.TypeCheckError as e:
            raise TypeError(
                f"Expected JSON-like object, got {type(obj).__name__}."
            ) from e

        if typ_isinstance(obj, typ):
            yield Ident(obj_class=type(obj))

        if typ_isinstance(obj, JSONBase):
            pass

        elif typ_isinstance(obj, typing.Mapping):
            for k in obj.keys():
                for sublens in ValidJSON.of_type(obj[k], typ):
                    yield MappingValue(item=k)[sublens]

        elif typ_isinstance(obj, typing.Sequence):
            for i in range(len(obj)):
                for sublens in ValidJSON.of_type(obj[i], typ):
                    yield SequenceElement(item=i)[sublens]

        else:
            raise ValueError(
                f"Invalid JSON-like object of type {type(obj).__name__}."
            )

    @staticmethod
    def all_values(obj: JSONLike) -> typing.Iterable[Lens[JSONLike, JSONLike]]:
        return ValidJSON.of_type(obj, JSONLike)

    @staticmethod
    def base_values(obj: JSONLike) -> typing.Iterable[Lens[JSONLike, JSONBase]]:
        return ValidJSON.of_type(obj, JSONBase)


def make_validated_Mapping(obj_class: typing.Type[T]) -> type:
    """Create a class of validated lenses for mapping containers."""

    class _ValidatedMapping:
        @staticmethod
        def values(
            mapping: typing.Mapping[K, V],
        ) -> typing.Iterable[Lens[T[K, V], V]]:
            """Itarate over lenses for each value in a mapping."""

            try:
                typeguard.check_type(mapping, obj_class)
            except typeguard.TypeCheckError as e:
                raise TypeError(
                    f"Expected `{obj_class.__name__}`, got `{type(mapping).__name__}`."
                ) from e

            for k in mapping.keys():
                yield MappingValue(item=k, obj_class=obj_class, key_class=K)

        @staticmethod
        def keys(
            mapping: typing.Mapping[K, V],
        ) -> typing.Iterable[Lens[T[K, V], K]]:
            """Itarate over lenses for each key in a mapping."""

            try:
                typeguard.check_type(mapping, obj_class)
            except typeguard.TypeCheckError as e:
                raise TypeError(
                    f"Expected {obj_class.__name__}, got {type(mapping).__name__}."
                ) from e

            for k in mapping.keys():
                yield MappingKey(item=k, obj_class=obj_class, key_class=K)

    _ValidatedMapping.__name__ = "Valid" + obj_class.__name__.capitalize()

    return _ValidatedMapping


ValidDict = make_validated_Mapping(typing.Dict)
ValidMapping = make_validated_Mapping(typing.Mapping)


def make_validated_Sequence(obj_class: typing.Type[T]) -> type:
    """Validated lenses for sequence containers."""

    class _ValidatedSequence:
        @staticmethod
        def indices(
            seq: typing.Sequence[B],
        ) -> typing.Iterable[Lens[T[B], int]]:
            try:
                typeguard.check_type(seq, obj_class)
            except typeguard.TypeCheckError as e:
                raise TypeError(
                    f"Expected {obj_class.__name__}, got {type(seq).__name__}."
                ) from e

            for i in range(len(seq)):
                yield SequenceIndex(item=i, obj_class=obj_class, key_class=int)

        @staticmethod
        def elements(seq: typing.Sequence[B]) -> typing.Iterable[Lens[T[B], B]]:
            try:
                typeguard.check_type(seq, obj_class)
            except typeguard.TypeCheckError as e:
                raise TypeError(
                    f"Expected {obj_class.__name__}, got {type(seq).__name__}."
                ) from e

            for i in range(len(seq)):
                yield Item(item=i, obj_class=obj_class)

    _ValidatedSequence.__name__ = "Valid" + obj_class.__name__.capitalize()

    return _ValidatedSequence


ValidTuple = make_validated_Sequence(typing.Tuple)
ValidList = make_validated_Sequence(typing.List)
ValidSequence = make_validated_Sequence(typing.Sequence)
