from logging import getLogger
from typing import cast

from .discovery.function import FunctionDiscovery
from .discovery.system import DiscoverySystem
from .explorers import done  # type: ignore  # noqa: F401 - required to register explorers
from .lieftools import Image
from .pattern import compile_pattern
from .search import find_calls
from .ue.analyse import analyse_image
from .ue.discovery.function import ZConstructFunctionDiscovery
from .ue.functions import StaticClassFnArtefact, parse_StaticClass

log = getLogger('unreal_dissection')


STATICCLASS_PREQUEL = compile_pattern(
    '4C 8B DC '   # MOV R11, RSP
    '48 83 EC ')  # SUB RSP, #?

LOOKBACK_OFFSET = 0x140


def load_image(path: str) -> Image:
    return Image(path)

def fully_discover(image: Image) -> DiscoverySystem:
    discovery = DiscoverySystem(image)

    log.info('Beginning early analysis...')
    analysis = analyse_image(image, discovery.ctx)

    log.info('Performing discovery...')
    # Queue everything found
    for fn_type, pkg_struct in analysis.known_functions.items():
        for caller in pkg_struct.callers:
            discovery.queue(ZConstructFunctionDiscovery(caller.fn_addr, fn_type))

    # Process outstanding discoveries, continuing until we have none left
    discovery.process_all()

    # Look for all functions that call GetPrivateStaticClassBody
    first_fn: StaticClassFnArtefact = discovery.found_functions_by_type[parse_StaticClass][0] # type: ignore
    addr_GetPrivateStaticClassBody = first_fn.called_fn_addr  # noqa: N806
    if any(cast(StaticClassFnArtefact, fn).called_fn_addr != addr_GetPrivateStaticClassBody for
            fn in discovery.found_functions_by_type[parse_StaticClass]): # type: ignore
        raise ValueError('Not all StaticClass functions call GetPrivateStaticClassBody')

    # At this point we're confident in the address of the GetPrivateStaticClassBody function
    text_base, text_memory = image.get_section_memory('.text')
    calls_to_GetPrivateStaticClassBody = find_calls(addr_GetPrivateStaticClassBody, text_memory, text_base)  # noqa: N806
    for call in calls_to_GetPrivateStaticClassBody:
        # Walk backwards to find the start of the function
        area = text_memory[call - text_base - LOOKBACK_OFFSET:call - text_base]
        for offset in STATICCLASS_PREQUEL.search_reverse(area):
            fn_start = call - LOOKBACK_OFFSET + offset
            discovery.queue(FunctionDiscovery(fn_start, parse_StaticClass))
            break

    # Process outstanding discoveries, continuing until we have none left
    discovery.process_all()

    return discovery
