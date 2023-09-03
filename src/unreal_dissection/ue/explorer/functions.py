from __future__ import annotations

from logging import getLogger
from typing import Iterator

from ...discovery.core import Discovery
from ...discovery.function import FunctionDiscovery
from ...discovery.string import Utf16Discovery
from ...discovery.struct import StructDiscovery
from ...discovery.system import register_explorer
from ...lieftools import Image
from ..functions import StaticClassFnArtefact, ZConstructFnArtefact, ZConstructFnType, parse_StaticClass_fn
from ..native_structs import FClassParams, FEnumParams, FFunctionParams, FPackageParams, FStructParams

log = getLogger(__name__)


@register_explorer(ZConstructFnArtefact)
def explore_ZConstructFnArtefact(subject: ZConstructFnArtefact, image: Image) -> Iterator[Discovery]:
    log.debug('Exploring ZConstructFnArtefact %r', subject)
    yield StructDiscovery(subject.params_struct_ptr, ENUM_TO_STRUCT[subject.called_method_type])


@register_explorer(StaticClassFnArtefact)
def explore_StaticClassFnArtefact(subject: StaticClassFnArtefact, image: Image) -> Iterator[Discovery]:
    log.debug('Exploring StaticClassFnArtefact %r', subject)

    yield Utf16Discovery(subject.package_name_ptr)
    yield Utf16Discovery(subject.name_ptr)
    # yield FunctionDiscovery(subject.register_fn_ptr, parse_ClassNoReg_fn) # TODO: check one of these
    yield Utf16Discovery(subject.config_name_ptr)
    yield FunctionDiscovery(subject.super_class_fn_ptr, parse_StaticClass_fn)
    yield FunctionDiscovery(subject.within_class_fn_ptr, parse_StaticClass_fn)

ENUM_TO_STRUCT = {
    ZConstructFnType.Package: FPackageParams,
    ZConstructFnType.Class: FClassParams,
    ZConstructFnType.Struct: FStructParams,
    ZConstructFnType.Enum: FEnumParams,
    ZConstructFnType.Function: FFunctionParams,
}
