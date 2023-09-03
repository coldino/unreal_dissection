from dataclasses import dataclass

from ..lieftools import SECTION_TEXT, Image
from ..search import analyse_all_calls
from .functions import ZConstructFnType
from .z_construct import ZConstructInfo, discover_z_constructs
from .z_construct_search import ZConstruct


@dataclass(frozen=True)
class AnalysisResult:
    all_calls: dict[int, list[int]]
    z_constructs: list[ZConstruct]
    known_functions: dict[ZConstructFnType, ZConstructInfo]


def analyse_image(image: Image):
    # Grab useful sections
    text_base, text_memory = image.get_section_memory(SECTION_TEXT)
    # rdata_base, rdata_memory = image.get_section_memory(SECTION_RDATA)

    # Record all calls within the .text section
    all_calls = analyse_all_calls(text_memory,
                                  text_base,
                                  allow_min=text_base,
                                  allow_max=text_base + len(text_memory),
                                  min_count=None)
    print(f"Found {len(all_calls)} potential functions from {sum(len(v) for v in all_calls.values())} sites")

    # Discover and categorize Z_Construct functions
    z_constructs, known_functions = discover_z_constructs(image)

    # # Find all Z_Construct functions by pattern matching
    # z_constructs = list(find_z_constructs(image))
    # print(f"Found {len(z_constructs)} Z_Construct functions and structs")

    # # Find the five UECodeGen_Private::ConstructXXX functions that these Z_Construct functions call
    # codegen_construct_fns = group_construct_fns(image, z_constructs)
    # assert len(codegen_construct_fns) == 5

    # # Make some guesses about which ConstructXXX functions are which
    # known_functions: dict[ZConstructFnType, ZConstructInfo] = categorize_z_construct_calls(image, codegen_construct_fns)
    # assert len(known_functions) == 5

    # print(f"Found and identified {len(known_functions)} UECodeGen_Private::Construct functions")
    # for fn_type,fn in known_functions.items():
    #     print(f"  {fn.amount} calls to ConstructU{fn_type.name} @ 0x{fn.fn_addr:x} (stack size {fn.stack_size})")

    # Return the results
    return AnalysisResult(all_calls, z_constructs, known_functions)
