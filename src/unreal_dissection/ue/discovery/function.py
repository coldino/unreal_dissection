from __future__ import annotations

from ...discovery.function import FunctionDiscovery
from ..functions import ZConstructFnType, parse_ZConstruct


class ZConstructFunctionDiscovery(FunctionDiscovery):
    def __init__(self, ptr: int, info: ZConstructFnType|None):
        super().__init__(ptr, parse_ZConstruct, info)




# GetStaticClassBodyFunctionDiscovery...
