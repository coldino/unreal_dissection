from __future__ import annotations

from ...discovery.function import FunctionDiscovery
from ..functions import ZConstructFnType, parse_ZConstruct_fn


class ZConstructFunctionDiscovery(FunctionDiscovery):
    def __init__(self, ptr: int, info: ZConstructFnType|None):
        super().__init__(ptr, parse_ZConstruct_fn, info)

    # No longer needed now we know all the z_construct function types up-front
    # def is_ready(self) -> bool:
    #     return self.info is not None




# GetStaticClassBodyFunctionDiscovery...
