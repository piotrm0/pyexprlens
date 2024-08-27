from __future__ import annotations

import typing

A = typing.TypeVar("A")
B = typing.TypeVar("B")
T = typing.TypeVar("T")
R = typing.TypeVar("R")
Q = typing.TypeVar("Q")

K = typing.TypeVar("K")
V = typing.TypeVar("V")

from .lens import Lens, MappingKey, MappingValue, Item


def make_validated_Mapping(obj_class: typing.Type[T]) -> type:
    """Create a class of validated lenses for mapping containers."""

    class _ValidatedMapping():

        @staticmethod
        def values(d: typing.Mapping[K, V]) -> typing.Iterable[Lens[T[K, V], V]]:
            """Itarate over lenses for each value in a mapping."""

            if not isinstance(d, obj_class):
                raise TypeError(f"Expected {obj_class.__name__}, got {type(d).__name__}.")

            for k in d.keys():
                yield MappingValue(item=k, obj_class=obj_class)

        @staticmethod
        def keys(d: typing.Mapping[K, V]) -> typing.Iterable[Lens[T[K, V], K]]:
            """Itarate over lenses for each key in a mapping."""

            if not isinstance(d, obj_class):
                raise TypeError(f"Expected {obj_class.__name__}, got {type(d).__name__}.")

            for k in d.keys():
                yield MappingKey(item=k, obj_class=obj_class)

    _ValidatedMapping.__name__ = "Valid" + obj_class.__name__.capitalize()

    return _ValidatedMapping



ValidDict = make_validated_Mapping(dict)
ValidMapping = make_validated_Mapping(typing.Mapping)


def make_validated_Sequence(obj_class: typing.Type[T]) -> type:
    """Validated lenses for sequence containers."""

    class _ValidatedSequence():

        @staticmethod
        def items(l: typing.Sequence[B]) -> typing.Iterable[Lens[T[B], B]]:

            if not isinstance(l, obj_class):
                raise TypeError(f"Expected {obj_class.__name__}, got {type(l).__name__}.")

            for i in range(len(l)):
                yield Item(item=i, obj_class=obj_class)

    _ValidatedSequence.__name__ = "Valid" + obj_class.__name__.capitalize()

    return _ValidatedSequence


ValidTuple = make_validated_Sequence(tuple)
ValidList = make_validated_Sequence(list)
ValidSequence = make_validated_Sequence(typing.Sequence)
