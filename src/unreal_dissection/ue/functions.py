# ruff: noqa: N802 - allow function names to include type names

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING, Any

from ..discovery.function import FunctionArtefact, TrampolineArtefact, UnparsableFunctionArtefact
from ..dissassembly import CachedCallResult, CodeGrabber, UnexpectedInstructionError, parse_cached_call, parse_trampolines
from .z_construct import ZConstructFnType, lookup_construct_fn_type, lookup_struct_type_by_fn_addr

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ..discovery.core import Artefact, Discovery
    from ..parsing import ParsingContext
    from .native_enums import EClassCastFlags, EClassFlags

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


def parse_StaticClass(code: CodeGrabber, _ctx: ParsingContext, _info: Any|None) -> Iterator[Artefact|Discovery]:
    '''Parse a ::StaticClass function that calls GetPrivateStaticClassBody.'''
    # Record any trampolines
    jumps = list(parse_trampolines(code))

    # Parse the function, gathering the arguments passed to GetPrivateStaticClassBody
    start_addr = code.addr
    parsed = parse_cached_call(code)
    end_addr = code.addr

    # Create the main artefact
    artefact = StaticClassFnArtefact(start_addr, end_addr, parse_StaticClass, *parsed.parameters) # type: ignore

    # Return any tramplines and the main artefact
    yield from (TrampolineArtefact(jmp, jmp+5, artefact) for jmp in jumps)
    yield artefact


@dataclass(frozen=True, slots=True, repr=False)
class ZConstructFnArtefact(FunctionArtefact):
    called_method_type: ZConstructFnType
    called_method_ptr: int
    cache_ptr: int
    params_struct_ptr: int


def parse_ZConstruct(code: CodeGrabber, _ctx: ParsingContext, info: ZConstructFnType|None) -> Iterator[Artefact|Discovery]:
    '''Parse a Z_Construct_XXX_XXX function that calls a UCodeGen_Private::ConstructXXX.'''
    # Record any trampolines
    jumps = list(parse_trampolines(code))

    # Parse the function, gathering the arguments passed to the UCodeGen_Private::ConstructXXX function
    start_addr = code.addr
    try:
        parsed = parse_cached_call(code)
    except AssertionError:
        # This is not a typical Z_Construct function, so we can't parse it
        parsed = None
    except UnexpectedInstructionError:
        # This is not a typical Z_Construct function, so we can't parse it
        parsed = None
    end_addr = code.addr

    known_type: ZConstructFnType|None = None
    called_fn_type: ZConstructFnType|None = None

    if parsed:
        # Look up the type from previously categorised functions
        known_type = lookup_struct_type_by_fn_addr(start_addr)
        if known_type is None:
            # This is not a typical Z_Construct function, so we can't parse it
            parsed = None

    if parsed:
        # Ensure the called function matches
        called_fn_type = lookup_construct_fn_type(parsed.called_fn_addr)
        if called_fn_type is None:
            # This function does not call a UCodeGen_Private::ConstructXXX function, so we can't parse it
            parsed = None

    if parsed:
        # Bail if we have mismatched types
        if known_type != called_fn_type:
            raise ValueError(f'Expected {known_type} but got {called_fn_type} for Z_Construct function at 0x{start_addr:x}')
        if known_type != info:
            raise ValueError(f'Expected {known_type} but got {info} for Z_Construct function at 0x{start_addr:x}')

        # Create the main artefact
        artefact = ZConstructFnArtefact(
            start_addr, end_addr,
            parse_ZConstruct, known_type, # type: ignore
            parsed.called_fn_addr, *parsed.parameters)
    else:
        # Record the function as unparsable
        artefact = UnparsableFunctionArtefact(start_addr, end_addr, parse_ZConstruct)

    # Return any tramplines and the main artefact
    yield from (TrampolineArtefact(jmp, jmp+5, artefact) for jmp in jumps)
    yield artefact


def parse_ZConstructOrStaticClass(code: CodeGrabber, _ctx: ParsingContext, _info: None) -> Iterator[Artefact|Discovery]:
    # Record any trampolines
    jumps = list(parse_trampolines(code))

    # Parse the function, gathering the arguments passed to the function
    start_addr = code.addr
    try:
        parsed = parse_cached_call(code)
    except (AssertionError, UnexpectedInstructionError):
        # This is not a typical function, so we can't parse it
        parsed = None
    end_addr = code.addr

    # Start with the assumption we can't parse the function
    artefact = UnparsableFunctionArtefact(start_addr, end_addr, parse_ZConstructOrStaticClass)

    if parsed:
        # Decide what to do by the number of arguments and the function called
        if len(parsed.parameters) == 2:
            # This is a Z_Construct function
            artefact = _generate_artefact_for_ZConstruct(parsed, start_addr, end_addr) or artefact
        elif len(parsed.parameters) == 14:
            # This is a StaticClass function
            artefact = _generate_artefact_for_StaticClass(parsed, start_addr, end_addr) or artefact

    # Return any tramplines and the artefact we found
    yield from (TrampolineArtefact(jmp, jmp+5, artefact) for jmp in jumps)
    yield artefact


def _generate_artefact_for_StaticClass(parsed: CachedCallResult, start_addr: int, end_addr: int) -> FunctionArtefact|None:
    # Create the main artefact
    artefact = StaticClassFnArtefact(
        start_addr, end_addr,
        parse_StaticClass,
        *parsed.parameters,  # type: ignore
    )

    return artefact


def _generate_artefact_for_ZConstruct(parsed: CachedCallResult, start_addr: int, end_addr: int) -> FunctionArtefact|None:
    # Ensure the type is one of the known ones
    struct_type = lookup_struct_type_by_fn_addr(start_addr)
    if struct_type is None:
        # This is not a typical Z_Construct function, so we can't parse it
        return None

    # Ensure the called function matches
    called_fn_type = lookup_construct_fn_type(parsed.called_fn_addr)
    if called_fn_type is None:
        # This function does not call a UCodeGen_Private::ConstructXXX function, so we can't parse it
        return None

    # Bail if we have mismatched types
    if struct_type != called_fn_type:
        raise ValueError(f'Expected {struct_type} but got {called_fn_type} for Z_Construct function at 0x{start_addr:x}')

    # Create the main artefact
    artefact = ZConstructFnArtefact(
        start_addr, end_addr,
        parse_ZConstruct,
        struct_type, # type: ignore
        parsed.called_fn_addr,
        *parsed.parameters,
    )

    return artefact

__all__ = (
    'StaticClassFnArtefact',
    'ZConstructFnArtefact',
    'parse_StaticClass',
    'parse_ZConstruct',
    'parse_ZConstructOrStaticClass',
)
