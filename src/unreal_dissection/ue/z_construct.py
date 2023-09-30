from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from itertools import groupby
from logging import getLogger
from typing import Any

from ..dissassembly import CodeGrabber, get_fn_stack_size
from ..lieftools import SECTION_RDATA, SECTION_TEXT, Image
from ..struct import struct_from_stream
from .native_structs import FClassParams, FEnumParams, FFunctionParams, FPackageParams, FStructParams
from .z_construct_search import ZConstruct, find_z_constructs

log = getLogger(__name__)


class ZConstructFnType(Enum):
    Package = auto()
    Function = auto()
    Enum = auto()
    Struct = auto()
    Class = auto()


@dataclass(frozen=True, slots=True)
class ZConstructInfo:
    fn_addr: int
    stack_size: int
    amount: int
    callers: tuple[ZConstruct, ...]

cache_by_fn_addr: dict[int, ZConstructFnType] = {}
cache_by_struct_addr: dict[int, ZConstructFnType] = {}
cache_by_called_fn_addr: dict[int, ZConstructFnType] = {}

def discover_z_constructs(image: Image):
    # Find all Z_Construct functions by pattern matching
    z_constructs = list(find_z_constructs(image))
    print(f'Found {len(z_constructs)} Z_Construct functions and structs')

    # Find the five UECodeGen_Private::ConstructXXX functions that these Z_Construct functions call
    codegen_construct_fns = _group_construct_fns(image, z_constructs)
    assert len(codegen_construct_fns) == 5

    # Make some guesses about which ConstructXXX functions are which
    known_functions: dict[ZConstructFnType, ZConstructInfo] = _categorize_z_construct_calls(image, codegen_construct_fns)
    assert len(known_functions) == 5

    print(f'Found and identified {len(known_functions)} UECodeGen_Private::Construct functions')
    for fn_type,fn in known_functions.items():
        print(f'  {fn.amount} calls to ConstructU{fn_type.name} @ 0x{fn.fn_addr:x} (stack size {fn.stack_size})')

    # Populate the cache
    cache_by_fn_addr.clear()
    for fn_type,fn in known_functions.items():
        cache_by_called_fn_addr[fn.fn_addr] = fn_type
        for caller in fn.callers:
            cache_by_fn_addr[caller.fn_addr] = fn_type
            cache_by_struct_addr[caller.struct_addr] = fn_type

    return (z_constructs, known_functions)

def lookup_struct_type_by_fn_addr(addr: int) -> ZConstructFnType|None:
    '''Look up the ZConstructFnType for a Z_Construct_XXX_XXX function.'''
    return cache_by_fn_addr.get(addr)

def lookup_struct_type_by_struct_addr(addr: int) -> ZConstructFnType|None:
    '''Look up the ZConstructFnType for a struct that is passed to a Z_Construct_XXX_XXX function.'''
    return cache_by_struct_addr.get(addr)

def lookup_construct_fn_type(addr: int) -> ZConstructFnType|None:
    '''Look up the ZConstructFnType for a ConstructXXX function.'''
    return cache_by_called_fn_addr.get(addr)

def _group_construct_fns(image: Image, z_constructs: list[ZConstruct]) -> list[ZConstructInfo]:
    '''Groups ZConstructs by the function they call.

    Args:
        z_constructs: The ZConstructs to group.

    Returns:
        The grouped ZConstructs, sorted least-called first.
    '''
    def get_call_addr(zc: ZConstruct) -> int:
        return zc.call_addr

    results: list[ZConstructInfo] = []
    for call_addr, callers in groupby(sorted(z_constructs, key=get_call_addr), key=get_call_addr):
        callers = tuple(callers)  # noqa: PLW2901
        code = CodeGrabber(image.get_stream(call_addr))
        try:
            stack_size = get_fn_stack_size(code)
        except AssertionError:
            log.warning('Failed to get stack size for ZConstruct function @ 0x{call_addr:x} (failed at 0x{code.addr:x}))',
                        extra=dict(call_addr=call_addr, code=code))
            continue
        results.append(ZConstructInfo(call_addr, stack_size, len(callers), callers))

    return sorted(results, key=lambda fu: fu.amount)



def _categorize_z_construct_calls(image: Image, z_constructs: list[ZConstructInfo]):
    # Analyse structs from each Z_Construct call target to work out which ConstructXXX function it is
    known_functions: dict[ZConstructFnType, ZConstructInfo] = {}
    for info in z_constructs:
        for caller in info.callers:
            # See if we can uniquely guess the struct type
            struct_types = list(_guess_possible_struct_types(image, caller.struct_addr))
            if len(struct_types) == 1:
                # We can, so record this as a known function
                struct_type = struct_types[0]
                enum_type = STRUCT_TO_ENUM[struct_type]
                known_functions[enum_type] = info
                break
        else:
            # Unable to guess the struct type, so skip it
            print(f'Unable to guess struct type for ConstructU... @ 0x{info.fn_addr:x}')

    return known_functions


def _guess_possible_struct_types(image: Image, addr: int):
    original_stream = image.get_stream(addr)

    for struct_type, validator in VALIDATION_FNS.items():
        stream = original_stream.clone()
        try:
            struct = struct_from_stream(struct_type, stream)
        except Exception:
            struct = None

        if not struct:
            continue

        try:
            validator(struct, image)
            yield struct_type
        except Exception:  # noqa: S112 - we WANT silent failure here
            continue


# The maximum number of entries in any struct array we allow for validation
MAX_ENTRIES = 0x2000

def _validate_package_params(struct: Any, image: Image):
    assert isinstance(struct, FPackageParams)
    assert image.get_section_name_from_rva(struct.NameUTF8) == SECTION_RDATA
    assert struct.NumSingletons >= 0
    assert struct.NumSingletons <= MAX_ENTRIES
    if struct.NumSingletons > 0:
        assert image.get_section_name_from_rva(struct.SingletonFuncArrayFn) == SECTION_RDATA

def _validate_class_params(struct: Any, image: Image):
    assert isinstance(struct, FClassParams)
    assert image.get_section_name_from_rva(struct.ClassNoRegisterFunc) == SECTION_TEXT
    assert image.get_section_name_from_rva(struct.CppClassInfo) == SECTION_RDATA
    if struct.ClassConfigNameUTF8:
        assert image.get_section_name_from_rva(struct.ClassConfigNameUTF8) == SECTION_RDATA

    assert struct.NumFunctions >= 0
    assert struct.NumFunctions <= MAX_ENTRIES
    assert struct.NumProperties >= 0
    assert struct.NumProperties <= MAX_ENTRIES
    assert struct.NumDependencySingletons >= 0
    assert struct.NumDependencySingletons <= MAX_ENTRIES

    if struct.NumFunctions > 0:
        assert image.get_section_name_from_rva(struct.FunctionLinkArray) == SECTION_RDATA
    if struct.NumProperties > 0:
        assert image.get_section_name_from_rva(struct.PropertyArray) == SECTION_RDATA
    if struct.NumDependencySingletons > 0:
        assert image.get_section_name_from_rva(struct.DependencySingletonFuncArray) == SECTION_RDATA

def _validate_struct_params(struct: Any, image: Image):
    assert isinstance(struct, FStructParams)
    if struct.OuterFunc:
        assert image.get_section_name_from_rva(struct.OuterFunc) == SECTION_TEXT
    if struct.SuperFunc:
        assert image.get_section_name_from_rva(struct.SuperFunc) == SECTION_TEXT
    if struct.StructOpsFunc:
        assert image.get_section_name_from_rva(struct.StructOpsFunc) == SECTION_TEXT
    assert image.get_section_name_from_rva(struct.NameUTF8) == SECTION_RDATA
    assert struct.NumProperties >= 0
    assert struct.NumProperties <= MAX_ENTRIES
    if struct.NumProperties > 0:
        assert image.get_section_name_from_rva(struct.PropertyArray) == SECTION_RDATA
    assert struct.SizeOf <= 0x1000000
    assert struct.AlignOf <= 4096

def _validate_enum_params(struct: Any, image: Image):
    assert isinstance(struct, FEnumParams)
    if struct.OuterFunc:
        assert image.get_section_name_from_rva(struct.OuterFunc) == SECTION_TEXT
    if struct.DisplayNameFn:
        assert image.get_section_name_from_rva(struct.DisplayNameFn) == SECTION_TEXT
    assert image.get_section_name_from_rva(struct.NameUTF8) == SECTION_RDATA
    assert image.get_section_name_from_rva(struct.CppTypeUTF8) == SECTION_RDATA
    assert struct.NumEnumerators >= 0
    assert struct.NumEnumerators <= MAX_ENTRIES
    if struct.NumEnumerators > 0:
        assert image.get_section_name_from_rva(struct.EnumeratorParams) == SECTION_RDATA

def _validate_function_params(struct: Any, image: Image):
    assert isinstance(struct, FFunctionParams)
    if struct.OuterFunc:
        assert image.get_section_name_from_rva(struct.OuterFunc) == SECTION_TEXT
    if struct.SuperFunc:
        assert image.get_section_name_from_rva(struct.SuperFunc) == SECTION_TEXT
    assert image.get_section_name_from_rva(struct.NameUTF8) == SECTION_RDATA
    if struct.OwningClassName:
        assert image.get_section_name_from_rva(struct.OwningClassName) == SECTION_RDATA
    if struct.DelegateName:
        assert image.get_section_name_from_rva(struct.DelegateName) == SECTION_RDATA
    assert struct.StructureSize <= 0x1000000
    assert struct.NumProperties >= 0
    assert struct.NumProperties <= MAX_ENTRIES
    if struct.NumProperties > 0:
        assert image.get_section_name_from_rva(struct.PropertyArray) == SECTION_RDATA

VALIDATION_FNS: dict[type, Callable[[object, Image], None]] = {
    FPackageParams: _validate_package_params,
    FClassParams: _validate_class_params,
    FStructParams: _validate_struct_params,
    FEnumParams: _validate_enum_params,
    FFunctionParams: _validate_function_params,
}

STRUCT_TO_ENUM = {
    FPackageParams: ZConstructFnType.Package,
    FClassParams: ZConstructFnType.Class,
    FStructParams: ZConstructFnType.Struct,
    FEnumParams: ZConstructFnType.Enum,
    FFunctionParams: ZConstructFnType.Function,
}

ENUM_TO_STRUCT = {
    ZConstructFnType.Package: FPackageParams,
    ZConstructFnType.Class: FClassParams,
    ZConstructFnType.Struct: FStructParams,
    ZConstructFnType.Enum: FEnumParams,
    ZConstructFnType.Function: FFunctionParams,
}
