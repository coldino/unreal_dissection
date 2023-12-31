# ruff: noqa: ERA001
from dataclasses import dataclass

from ..lieftools import Image
from ..parsing import ParsingContext
from .functions import ZConstructFnType
from .z_construct import ZConstructInfo, discover_z_constructs
from .z_construct_search import ZConstruct


@dataclass(frozen=True)
class AnalysisResult:
    # all_calls: dict[int, list[int]]
    z_constructs: list[ZConstruct]
    known_functions: dict[ZConstructFnType, ZConstructInfo]


def analyse_image(image: Image, ctx: ParsingContext):
    # # Grab useful sections - NOT CURRENTLY NEEDED
    # text_base, text_memory = image.get_section_memory(SECTION_TEXT)

    # # Record all calls within the .text section
    # all_calls = analyse_all_calls(text_memory,
    #                               text_base,
    #                               allow_min=text_base,
    #                               allow_max=text_base + len(text_memory),
    #                               min_count=None)
    # print(f'Found {len(all_calls)} potential functions from {sum(len(v) for v in all_calls.values())} sites')

    # Discover and categorize Z_Construct functions
    z_constructs, known_functions = discover_z_constructs(image, ctx)

    # Return the results
    return AnalysisResult(z_constructs, known_functions) # all_calls,
