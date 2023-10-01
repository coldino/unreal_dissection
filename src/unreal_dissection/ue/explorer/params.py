# ruff: noqa: N802 - allow function names to include type names

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from ...discovery.function import FunctionDiscovery
from ...discovery.string import Utf8Discovery
from ...discovery.struct import StructDiscovery
from ...discovery.system import register_explorer
from ...struct import get_struct_size_aligned
from ..functions import parse_ZConstructOrStaticClass
from ..native_structs import (
    FClassFunctionLinkInfo,
    FClassParams,
    FEnumeratorParams,
    FEnumParams,
    FFunctionParams,
    FImplementedInterfaceParams,
    FPackageParams,
    FStructParams,
    PropertyParams,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ...discovery.core import Discovery
    from ...lieftools import Image

log = getLogger(__name__)


@register_explorer(FPackageParams)
def explore_FPackageParams(subject: FPackageParams, image: Image) -> Iterator[Discovery]:
    yield Utf8Discovery(subject.NameUTF8)

    if subject.SingletonFuncArrayFn:
        for ptr in image.get_stream(subject.SingletonFuncArrayFn).ptr_array(subject.NumSingletons):
            yield FunctionDiscovery(ptr, parse_ZConstructOrStaticClass)


@register_explorer(FClassParams)
def explore_FClassParams(subject: FClassParams, image: Image) -> Iterator[Discovery]:
    yield FunctionDiscovery(subject.ClassNoRegisterFunc, parse_ZConstructOrStaticClass)
    yield Utf8Discovery(subject.ClassConfigNameUTF8)

    if subject.DependencySingletonFuncArray:
        for ptr in image.get_stream(subject.DependencySingletonFuncArray).ptr_array(subject.NumDependencySingletons):
            yield FunctionDiscovery(ptr, parse_ZConstructOrStaticClass)

    if subject.FunctionLinkArray:
        struct_size = get_struct_size_aligned(FClassFunctionLinkInfo)
        for i in range(subject.NumFunctions):
            yield StructDiscovery(subject.FunctionLinkArray + struct_size * i, FClassFunctionLinkInfo)

    if subject.PropertyArray:
        for ptr in image.get_stream(subject.PropertyArray).ptr_array(subject.NumProperties):
            yield StructDiscovery(ptr, PropertyParams)

    if subject.ImplementedInterfaceArray:
        struct_size = get_struct_size_aligned(FImplementedInterfaceParams)
        for i in range(subject.NumImplementedInterfaces):
            yield StructDiscovery(subject.ImplementedInterfaceArray + struct_size * i, FImplementedInterfaceParams)


@register_explorer(FStructParams)
def explore_FStructParams(subject: FStructParams, image: Image) -> Iterator[Discovery]:
    yield FunctionDiscovery(subject.OuterFunc, parse_ZConstructOrStaticClass)
    yield FunctionDiscovery(subject.SuperFunc, parse_ZConstructOrStaticClass)
    yield Utf8Discovery(subject.NameUTF8)

    if subject.PropertyArray:
        for ptr in image.get_stream(subject.PropertyArray).ptr_array(subject.NumProperties):
            yield StructDiscovery(ptr, PropertyParams)


@register_explorer(FEnumParams)
def explore_FEnumParams(subject: FEnumParams, _image: Image) -> Iterator[Discovery]:
    yield FunctionDiscovery(subject.OuterFunc, parse_ZConstructOrStaticClass)
    yield Utf8Discovery(subject.NameUTF8)
    yield Utf8Discovery(subject.CppTypeUTF8)

    if subject.EnumeratorParams:
        struct_size = get_struct_size_aligned(FEnumeratorParams)
        for i in range(subject.NumEnumerators):
            yield StructDiscovery(subject.EnumeratorParams + struct_size * i, FEnumeratorParams)


@register_explorer(FFunctionParams)
def explore_FFunctionParams(subject: FFunctionParams, image: Image) -> Iterator[Discovery]:
    yield FunctionDiscovery(subject.OuterFunc, parse_ZConstructOrStaticClass)
    yield FunctionDiscovery(subject.SuperFunc, parse_ZConstructOrStaticClass)
    yield Utf8Discovery(subject.NameUTF8)
    yield Utf8Discovery(subject.OwningClassName)
    yield Utf8Discovery(subject.DelegateName)

    if subject.PropertyArray:
        for ptr in image.get_stream(subject.PropertyArray).ptr_array(subject.NumProperties):
            yield StructDiscovery(ptr, PropertyParams)


@register_explorer(FEnumeratorParams)
def explore_FEnumeratorParams(subject: FEnumeratorParams, _image: Image) -> Iterator[Discovery]:
    yield Utf8Discovery(subject.NameUTF8)


@register_explorer(FImplementedInterfaceParams)
def explore_FImplementedInterfaceParams(subject: FImplementedInterfaceParams, _image: Image) -> Iterator[Discovery]:
    yield FunctionDiscovery(subject.ClassFunc, parse_ZConstructOrStaticClass)
    yield from ()


@register_explorer(FClassFunctionLinkInfo)
def explore_FClassFunctionLinkInfo(subject: FClassFunctionLinkInfo, _image: Image) -> Iterator[Discovery]:
    yield FunctionDiscovery(subject.CreateFuncPtr, parse_ZConstructOrStaticClass)
    yield Utf8Discovery(subject.FuncNameUTF8)
