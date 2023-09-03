# ruff: noqa: N802 - allow function names to include type names

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from ...discovery.function import FunctionDiscovery
from ...discovery.string import Utf8Discovery
from ...discovery.struct import StructDiscovery
from ...discovery.system import register_explorer
from ...struct import get_struct_size_aligned
from ..discovery.function import ZConstructFunctionDiscovery
from ..functions import parse_StaticClass
from ..native_structs import (
    DynamicPropertyParams,
    FClassFunctionLinkInfo,
    FClassParams,
    FEnumeratorParams,
    FEnumParams,
    FFunctionParams,
    FImplementedInterfaceParams,
    FPackageParams,
    FStructParams,
)
from ..z_construct import ZConstructFnType

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
            yield ZConstructFunctionDiscovery(ptr, ZConstructFnType.Function)


@register_explorer(FClassParams)
def explore_FClassParams(subject: FClassParams, image: Image) -> Iterator[Discovery]:
    yield FunctionDiscovery(subject.ClassNoRegisterFunc, parse_StaticClass)
    yield Utf8Discovery(subject.ClassConfigNameUTF8)

    if subject.DependencySingletonFuncArray:
        for ptr in image.get_stream(subject.DependencySingletonFuncArray).ptr_array(subject.NumDependencySingletons):
            yield ZConstructFunctionDiscovery(ptr, None)

    if subject.FunctionLinkArray:
        struct_size = get_struct_size_aligned(FClassFunctionLinkInfo)
        for i in range(subject.NumFunctions):
            yield StructDiscovery(subject.FunctionLinkArray + struct_size * i, FClassFunctionLinkInfo)

    if subject.PropertyArray:
        for ptr in image.get_stream(subject.PropertyArray).ptr_array(subject.NumProperties):
            yield StructDiscovery(ptr, DynamicPropertyParams)

    if subject.ImplementedInterfaceArray:
        struct_size = get_struct_size_aligned(FImplementedInterfaceParams)
        for i in range(subject.NumImplementedInterfaces):
            yield StructDiscovery(subject.ImplementedInterfaceArray + struct_size * i, FImplementedInterfaceParams)


@register_explorer(FStructParams)
def explore_FStructParams(subject: FStructParams, image: Image) -> Iterator[Discovery]:
    yield ZConstructFunctionDiscovery(subject.OuterFunc, None)
    yield ZConstructFunctionDiscovery(subject.SuperFunc, None)
    yield Utf8Discovery(subject.NameUTF8)

    if subject.PropertyArray:
        for ptr in image.get_stream(subject.PropertyArray).ptr_array(subject.NumProperties):
            yield StructDiscovery(ptr, DynamicPropertyParams)


@register_explorer(FEnumParams)
def explore_FEnumParams(subject: FEnumParams, _image: Image) -> Iterator[Discovery]:
    yield ZConstructFunctionDiscovery(subject.OuterFunc, None)
    yield Utf8Discovery(subject.NameUTF8)
    yield Utf8Discovery(subject.CppTypeUTF8)

    if subject.EnumeratorParams:
        struct_size = get_struct_size_aligned(FEnumeratorParams)
        for i in range(subject.NumEnumerators):
            yield StructDiscovery(subject.EnumeratorParams + struct_size * i, FEnumeratorParams)


@register_explorer(FFunctionParams)
def explore_FFunctionParams(subject: FFunctionParams, image: Image) -> Iterator[Discovery]:
    yield ZConstructFunctionDiscovery(subject.OuterFunc, None)
    yield ZConstructFunctionDiscovery(subject.SuperFunc, None)
    yield Utf8Discovery(subject.NameUTF8)
    yield Utf8Discovery(subject.OwningClassName)
    yield Utf8Discovery(subject.DelegateName)

    if subject.PropertyArray:
        for ptr in image.get_stream(subject.PropertyArray).ptr_array(subject.NumProperties):
            yield StructDiscovery(ptr, DynamicPropertyParams)


@register_explorer(FEnumeratorParams)
def explore_FEnumeratorParams(subject: FEnumeratorParams, _image: Image) -> Iterator[Discovery]:
    yield Utf8Discovery(subject.NameUTF8)


@register_explorer(FImplementedInterfaceParams)
def explore_FImplementedInterfaceParams(subject: FImplementedInterfaceParams, _image: Image) -> Iterator[Discovery]:
    yield ZConstructFunctionDiscovery(subject.ClassFunc, None)


@register_explorer(FClassFunctionLinkInfo)
def explore_FClassFunctionLinkInfo(subject: FClassFunctionLinkInfo, _image: Image) -> Iterator[Discovery]:
    yield ZConstructFunctionDiscovery(subject.CreateFuncPtr, ZConstructFnType.Function)
    yield Utf8Discovery(subject.FuncNameUTF8)
