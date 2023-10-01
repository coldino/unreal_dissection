from dataclasses import dataclass
from typing import Any

from ..discovery.function import UnparsableFunctionArtefact
from ..discovery.struct import StructArtefact
from ..discovery.system import DiscoverySystem
from ..lieftools import Image
from ..struct import get_struct_size_aligned
from ..ue.functions import StaticClassFnArtefact, ZConstructFnArtefact
from ..ue.native_structs import FClassParams, FEnumParams, FFunctionParams, FPackageParams, FStructParams


@dataclass(kw_only=True, frozen=True)
class ExportContext:
    discovery: DiscoverySystem
    image: Image


def export_array[T](count: int, ptr: int, ctx: ExportContext, struct: type[T]) -> tuple[T, ...]:
    if not ptr:
        return ()
    struct_size = get_struct_size_aligned(struct)
    ptrs = (ptr + struct_size * i for i in range(count))
    def checked_artefact(sub_ptr: int) -> T:
        artefact = ctx.discovery.found[sub_ptr]
        if not isinstance(artefact, StructArtefact):
            raise TypeError(f'Expected StructArtefact for {struct.__name__}, got {artefact.__class__.__name__}')
        target = artefact.struct # type: ignore
        if not isinstance(target, struct):
            raise TypeError(f'Expected {struct.__name__}, got {target.__class__.__name__}') # type: ignore
        return target
    return tuple(checked_artefact(sub_ptr) for sub_ptr in ptrs)

def export_ptr_array[T](count: int, ptr: int, ctx: ExportContext, struct: type[T]) -> tuple[T, ...]:
    if not ptr:
        return ()
    stream = ctx.image.get_stream(ptr)
    ptrs = stream.ptr_array(count)
    def checked_artefact(sub_ptr: int) -> T:
        artefact = ctx.discovery.found[sub_ptr]
        if not isinstance(artefact, struct):
            raise TypeError(f'Expected {struct.__name__}, got {artefact.__class__.__name__}')
        return artefact
    return tuple(checked_artefact(sub_ptr) for sub_ptr in ptrs)

def get_name(obj: Any, ctx: ExportContext) -> str:
    match obj:
        case ZConstructFnArtefact():
            params_artefact = ctx.discovery.found_structs[obj.params_struct_ptr]
            return get_name(params_artefact.struct, ctx)

        case StructArtefact():
            return get_name(obj.struct, ctx) # type: ignore

        case FClassParams():
            fn = ctx.discovery.found[obj.ClassNoRegisterFunc]
            return get_name(fn, ctx)

        case StaticClassFnArtefact():
            name = ctx.discovery.get_string(obj.name_ptr)
            return name

        case FPackageParams() | FStructParams() | FFunctionParams() | FEnumParams():
            name = ctx.discovery.get_string(obj.NameUTF8)
            return name

        case UnparsableFunctionArtefact():
            return '<unparsable>'

        case _:
            raise NotImplementedError(f'get_name for {obj.__class__.__name__}')

def get_blueprint_path(obj: Any, ctx: ExportContext) -> str:
    match obj:
        case ZConstructFnArtefact():
            return get_blueprint_path(ctx.discovery.found_structs[obj.params_struct_ptr].struct, ctx)

        case StaticClassFnArtefact():
            cls_name = ctx.discovery.get_string(obj.name_ptr)
            pkg_name = ctx.discovery.get_string(obj.package_name_ptr)
            return f'{pkg_name}.{cls_name}'

        case StructArtefact():
            return get_blueprint_path(obj.struct, ctx) # type: ignore

        case FPackageParams():
            pkg_name = ctx.discovery.get_string(obj.NameUTF8)
            return pkg_name

        case FClassParams():
            fn = ctx.discovery.found[obj.ClassNoRegisterFunc]
            return get_blueprint_path(fn, ctx)

        case FStructParams() | FEnumParams() | FFunctionParams():
            name = ctx.discovery.get_string(obj.NameUTF8)
            outer_fn = ctx.discovery.found[obj.OuterFunc]
            outer_name = get_blueprint_path(outer_fn, ctx)
            return f'{outer_name}.{name}'

        case UnparsableFunctionArtefact():
            return '<unparsable>'

        case _:
            raise NotImplementedError(f'get_blueprint_path for {obj.__class__.__name__}')

__all__ = (
    'ExportContext',
    'export_array',
    'export_ptr_array',
    'get_name',
    'get_blueprint_path',
)
