from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import Any, Iterator

from ..discovery.core import Artefact, Discovery
from ..discovery.function import FunctionArtefact, TrampolineArtefact
from ..dissassembly import CodeGrabber, UnexpectedInstruction, parse_cached_call, parse_trampolines
from .native_enums import EClassCastFlags, EClassFlags
from .z_construct import ZConstructFnType, lookup_struct_type_by_fn_addr

log = getLogger(__name__)

@dataclass(frozen=True, slots=True, repr=False)
class StaticClassFnArtefact(FunctionArtefact):
    package_name_ptr: int  # ptr to package name
    name_ptr: int  # ptr to class name
    return_cache_ptr: int  # ptr to cache returned value
    register_fn_ptr: int  # ptr to class natives registration function
    size: int
    alignment: int
    class_flags: EClassFlags
    class_cast_flags: EClassCastFlags
    config_name_ptr: int  # ptr to config name (generally "Engine")
    class_constructor_ptr: int
    class_vtable_helper_ptr: int
    class_static_fns_ptr: int # ptr to array of static class functions???
    super_class_fn_ptr: int
    within_class_fn_ptr: int


def parse_StaticClass_fn(code: CodeGrabber, _info: Any|None) -> Iterator[Artefact|Discovery]:
    """Parse a ::StaticClass function that calls GetPrivateStaticClassBody."""
    # Record any trampolines
    jumps = list(parse_trampolines(code))

    # Parse the function, gathering the arguments passed to GetPrivateStaticClassBody
    start_addr = code.addr
    parsed = parse_cached_call(code)
    end_addr = code.addr

    # Create the main artefact
    artefact = StaticClassFnArtefact(start_addr, end_addr, parse_StaticClass_fn, *parsed.parameters) # type: ignore

    # Return any tramplines and the main artefact
    yield from (TrampolineArtefact(jmp, jmp+5, artefact) for jmp in jumps)
    yield artefact


@dataclass(frozen=True, slots=True, repr=False)
class ZConstructFnArtefact(FunctionArtefact):
    called_method_type: ZConstructFnType
    called_method_ptr: int
    cache_ptr: int
    params_struct_ptr: int


def parse_ZConstruct_fn(code: CodeGrabber, info: ZConstructFnType|None) -> Iterator[Artefact|Discovery]:
    """Parse a Z_Construct_XXX_XXX function that calls a UCodeGen_Private::ConstructXXX."""
    # assert info is not None

    # Record any trampolines
    jumps = list(parse_trampolines(code))

    # Parse the function, gathering the arguments passed to the UCodeGen_Private::ConstructXXX function
    start_addr = code.addr
    try:
        parsed = parse_cached_call(code)
    except AssertionError:
        # This is not a typical Z_Construct function, so we can't parse it
        log.warn('Failed to parse Z_Construct function at 0x%x', start_addr)
        return
    except UnexpectedInstruction:
        # This is not a typical Z_Construct function, so we can't parse it
        log.warn('Failed to parse Z_Construct function at 0x%x', start_addr)
        return
    end_addr = code.addr

    # Look up the struct type from the called function
    info = lookup_struct_type_by_fn_addr(start_addr)
    if info is None:
        # This is not a typical Z_Construct function, so we can't parse it
        return

    # Create the main artefact
    artefact = ZConstructFnArtefact(start_addr, end_addr, parse_ZConstruct_fn, info, parsed.called_fn_addr, *parsed.parameters)

    # Return any tramplines and the main artefact
    yield from (TrampolineArtefact(jmp, jmp+5, artefact) for jmp in jumps)
    yield artefact
