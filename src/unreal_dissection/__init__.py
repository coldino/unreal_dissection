from logging import getLogger

from .discovery.system import DiscoverySystem
from .explorers import done  # type: ignore  # noqa: F401 - required to register explorers
from .lieftools import Image
from .ue.analyse import analyse_image
from .ue.discovery.function import ZConstructFunctionDiscovery

log = getLogger('unreal_dissection')

def load_image(path: str) -> Image:
    return Image(path)

def fully_discover(image: Image) -> DiscoverySystem:
    discovery = DiscoverySystem(image)

    log.info('Beginning early analysis...')
    analysis = analyse_image(image, discovery.ctx)

    log.info('Performing discovery...')
    # Queue everything found
    for fn_type, pkg_struct in analysis.known_functions.items():
        for fn in pkg_struct.callers:
            discovery.queue(ZConstructFunctionDiscovery(fn.fn_addr, fn_type))

    # Process discoveries until we have none left
    discovery.process_all()

    return discovery
