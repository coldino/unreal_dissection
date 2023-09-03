import re
import struct
from dataclasses import dataclass
from typing import Iterator

from ..lieftools import Image

# from ..pattern import compile_pattern
#
# Z_CONSTRUCT_PATTERN = compile_pattern(
#     ' [01001...] 83 ec ?'        # SUB RSP, ???
#     ' [01001...] 8b 05 ? ? ? ?'  # MOV RAX, [???]  ; RAX = cache address
#     ' [01001...] 85 c0'          # TEST RAX, RAX
#     ' 75 ?'                      # JNZ ???
#     ' [01001...] 8d 15 ? ? ? ?'  # LEA RDX, [???]
#     ' [01001...] 8d 0d ? ? ? ?'  # LEA RCX, [???]
#     ' e8 ? ? ? ?'                # CALL ???
#     ' [01001...] 8b 05 ? ? ? ?'  # MOV RAX, [???]
# )

Z_CONSTRUCT_RE = re.compile(
    rb"\x48\x83\xec \x28"  #         SUB RSP, 0x28
    rb"(?:"  #                       (
        rb"\x48\x8b\x05 ...."  #         MOV RAX, [???]  ; RAX = cache address
        rb"\x48\x85\xc0"  #              TEST RAX, RAX
    rb"|"  #                         |
        rb"\x48\x83\x3d\x04 ...."  #     CMP [???], 0x0
    rb")"  #                         )
    rb"\x75 (?:\x1a|\x13)"  #        JNZ to fn end
    rb"\x48\x8d\x15 (....)"  #       LEA RDX, [???]  ; RDX = struct address
    rb"\x48\x8d\x0d ...."  #         LEA RCX, [???]
    rb"\xe8 (....)"  #               CALL ???        ; registration fn
    rb"\x48\x8b\x05 ...."  #         MOV RAX, [???]
    ,
    re.DOTALL | re.VERBOSE)


@dataclass(frozen=True, slots=True)
class ZConstruct:
    fn_addr: int
    call_addr: int
    struct_addr: int


def find_z_constructs(image: Image) -> Iterator[ZConstruct]:
    """Finds all ZConstruct_XXX_XXX functions using a simple pattern-based search.

    Args:
        image: The image to search in.

    Returns:
        The ZConstructs within the memoryview.
    """
    base_address, memory = image.get_section_memory(".text")

    for match in Z_CONSTRUCT_RE.finditer(memory):
        fn_addr = base_address + match.start()
        struct_rel = struct.unpack('<i', match.group(1))[0]
        struct_addr = struct_rel + base_address + match.end(1)
        call_rel = struct.unpack('<i', match.group(2))[0]
        call_addr = call_rel + base_address + match.end(2)
        yield ZConstruct(fn_addr, call_addr, struct_addr)
