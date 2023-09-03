import sys
from logging import INFO, basicConfig, getLogger

basicConfig(level=INFO)
log = getLogger("unreal_dissection")

import unreal_dissection.explorer.struct  # type: ignore
import unreal_dissection.ue.explorer.functions  # type: ignore
import unreal_dissection.ue.explorer.params  # type: ignore
import unreal_dissection.ue.explorer.property_params  # type: ignore

from .discovery.system import DiscoverySystem
from .lieftools import Image
from .ue.analyse import analyse_image
from .ue.discovery.function import ZConstructFunctionDiscovery


def fully_discover(image: Image) -> DiscoverySystem:
    discovery = DiscoverySystem(image)

    log.info("Beginning early analysis...")
    analysis = analyse_image(image)

    log.info("Performing discovery...")
    # Queue everything found
    for fn_type, pkg_struct in analysis.known_functions.items():
        for fn in pkg_struct.callers:
            discovery.queue(ZConstructFunctionDiscovery(fn.fn_addr, fn_type))

    # Process discoveries until we have none left
    discovery.process_all()

    # Show what was found
    discovery.print_summary()

    return discovery


if __name__ == "__main__":
    # Simply grab filename from commandline
    filename = sys.argv[1] if len(sys.argv) > 1 else "Purlovia.exe"
    log.info("Beginning extraction of %s", filename)

    log.info("Loading exe...")
    image = Image(filename)

    discovery = fully_discover(image)
