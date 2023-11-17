from dataclasses import dataclass
from typing import Any

from ..discovery.function import UnparsableFunctionArtefact
from ..discovery.struct import StructArtefact
from ..discovery.system import DiscoverySystem
from ..lieftools import Image
from ..struct import get_struct_size_aligned
from ..ue.functions import CachedRedirectFnArtefact, StaticClassFnArtefact, ZConstructFnArtefact
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
    return tuple(artefact for artefact in (checked_artefact(sub_ptr) for sub_ptr in ptrs) if artefact is not None)

def export_ptr_array[T](count: int, ptr: int, ctx: ExportContext, struct: type[T]) -> tuple[T, ...]:
    if not ptr:
        return ()
    stream = ctx.image.get_stream(ptr)
    ptrs = stream.ptr_array(count)
    def checked_artefact(sub_ptr: int) -> T | None:
        artefact = ctx.discovery.found[sub_ptr]
        if isinstance(artefact, CachedRedirectFnArtefact):
            artefact = ctx.discovery.found[artefact.called_method_ptr]
        if isinstance(artefact, UnparsableFunctionArtefact):
            return None
        if not isinstance(artefact, struct):
            raise TypeError(f'Expected {struct.__name__}, got {artefact.__class__.__name__}')
        return artefact
    return tuple(artefact for artefact in (checked_artefact(sub_ptr) for sub_ptr in ptrs) if artefact is not None)

def get_name(obj: Any, ctx: ExportContext) -> str:  # noqa: PLR0911
    match obj:
        case ZConstructFnArtefact():
            params_artefact = ctx.discovery.found_structs[obj.params_struct_ptr]
            return get_name(params_artefact.struct, ctx)

        case StructArtefact():
            return get_name(obj.struct, ctx) # type: ignore

        case CachedRedirectFnArtefact():
            return get_name(ctx.discovery.found[obj.called_method_ptr], ctx)

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
    return get_ref(obj, ctx)[1]

def get_ref(obj: Any, ctx: ExportContext) -> tuple[str, str]:  # noqa: PLR0911
    match obj:
        case ZConstructFnArtefact():
            return get_ref(ctx.discovery.found_structs[obj.params_struct_ptr].struct, ctx)

        case StaticClassFnArtefact():
            cls_name = ctx.discovery.get_string(obj.name_ptr)
            pkg_name = ctx.discovery.get_string(obj.package_name_ptr)
            return 'class', f'{pkg_name}.{cls_name}'

        case CachedRedirectFnArtefact():
            return get_ref(ctx.discovery.found[obj.called_method_ptr], ctx)

        case StructArtefact():
            return get_ref(obj.struct, ctx) # type: ignore

        case FPackageParams():
            pkg_name = ctx.discovery.get_string(obj.NameUTF8)
            return 'package', pkg_name

        case FClassParams():
            # Class details are only discovered from the associated registration function
            fn = ctx.discovery.found[obj.ClassNoRegisterFunc]
            return get_ref(fn, ctx)

        case FStructParams() | FEnumParams() | FFunctionParams():
            name = ctx.discovery.get_string(obj.NameUTF8)
            outer_fn = ctx.discovery.found[obj.OuterFunc]
            outer_name = get_blueprint_path(outer_fn, ctx)
            type_name = obj.__class__.__name__[1:-6].lower()
            return type_name, f'{outer_name}.{name}'

        case UnparsableFunctionArtefact():
            return '<unknown>', '<unparsable>'

        case _:
            raise NotImplementedError(f'get_blueprint_path for {obj.__class__.__name__}')

__all__ = (
    'ExportContext',
    'export_array',
    'export_ptr_array',
    'get_ref',
    'get_name',
    'get_blueprint_path',
)
