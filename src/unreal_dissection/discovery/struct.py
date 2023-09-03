from collections.abc import Iterator
from dataclasses import dataclass

from ..lieftools import Image
from ..struct import struct_from_stream
from .core import Artefact, Discovery


@dataclass(frozen=True, unsafe_hash=True, eq=True, slots=True, repr=False)
class StructArtefact[T](Artefact):
    '''A struct discovered by the extractor.'''
    struct_type: type[T]
    struct: T

@dataclass(frozen=True, unsafe_hash=True, eq=True, slots=True, repr=False)
class StructDiscovery(Discovery):
    struct_type: type

    def perform(self, image: Image) -> Iterator[Artefact|Discovery]:
        start = self.ptr
        stream = image.get_stream(self.ptr)
        data = struct_from_stream(self.struct_type, stream)
        yield StructArtefact(start, stream.addr, self.struct_type, data)

