from __future__ import annotations

import typing

import typeguard

from .lens import Item
from .lens import Lens
from .lens import MappingKey
from .lens import MappingValue

A = typing.TypeVar("A")
B = typing.TypeVar("B")
T = typing.TypeVar("T")
R = typing.TypeVar("R")
Q = typing.TypeVar("Q")

K = typing.TypeVar("K")
V = typing.TypeVar("V")

def make_validated_Mapping(obj_class: typing.Type[T]) -> type:
    """Create a class of validated lenses for mapping containers."""

    class _ValidatedMapping():

        @staticmethod
        def values(mapping: typing.Mapping[K, V]) -> typing.Iterable[Lens[T[K, V], V]]:
            """Itarate over lenses for each value in a mapping."""

            try:
                typeguard.check_type(mapping, obj_class)
            except typeguard.TypeCheckError as e:
                raise TypeError(f"Expected `{obj_class.__name__}`, got `{type(mapping).__name__}`.") from e

            for k in mapping.keys():
                yield MappingValue(item=k, obj_class=obj_class)

        @staticmethod
        def keys(mapping: typing.Mapping[K, V]) -> typing.Iterable[Lens[T[K, V], K]]:
            """Itarate over lenses for each key in a mapping."""

            try:
                typeguard.check_type(mapping, obj_class)
            except typeguard.TypeCheckError as e:
                raise TypeError(f"Expected {obj_class.__name__}, got {type(mapping).__name__}.") from e

            for k in mapping.keys():
                yield MappingKey(item=k, obj_class=obj_class)

    _ValidatedMapping.__name__ = "Valid" + obj_class.__name__.capitalize()

    return _ValidatedMapping


ValidDict = make_validated_Mapping(typing.Dict)
ValidMapping = make_validated_Mapping(typing.Mapping)


def make_validated_Sequence(obj_class: typing.Type[T]) -> type:
    """Validated lenses for sequence containers."""

    class _ValidatedSequence():

        @staticmethod
        def items(seq: typing.Sequence[B]) -> typing.Iterable[Lens[T[B], B]]:

            try:
                typeguard.check_type(seq, obj_class)
            except typeguard.TypeCheckError as e:
                raise TypeError(f"Expected {obj_class.__name__}, got {type(seq).__name__}.") from e

            for i in range(len(seq)):
                yield Item(item=i, obj_class=obj_class)

    _ValidatedSequence.__name__ = "Valid" + obj_class.__name__.capitalize()

    return _ValidatedSequence


ValidTuple = make_validated_Sequence(typing.Tuple)
ValidList = make_validated_Sequence(typing.List)
ValidSequence = make_validated_Sequence(typing.Sequence)
