from dataclasses import dataclass
from typing import Iterator

from ..lieftools import Image
from ..struct import struct_from_stream
from .core import Artefact, Discovery


@dataclass(frozen=True, unsafe_hash=True, eq=True, slots=True, repr=False)
class StructArtefact[T](Artefact):
    """A struct discovered by the extractor."""
    struct_type: type[T]
    struct: T

    # def register_discoveries(self, image: Image) -> Iterator[Discovery]:
    #     # Recurse into the discovered struct

    #     # ...which can either be a Discoverable
    #     if isinstance(self.struct, Discoverable):
    #         yield from self.struct.register_discoveries(image)
    #     else:
    #         # ...or might have a registered explorer
    #         explorer = get_explorer_for_type(self.struct_type)
    #         if explorer is not None:
    #             yield from explorer(self.struct, image)

@dataclass(frozen=True, unsafe_hash=True, eq=True, slots=True, repr=False)
class StructDiscovery(Discovery):
    struct_type: type

    def perform(self, image: Image) -> Iterator[Artefact|Discovery]:
        start = self.ptr
        stream = image.get_stream(self.ptr)
        data = struct_from_stream(self.struct_type, stream)
        yield StructArtefact(start, stream.addr, self.struct_type, data)


# import extractor.explorer.struct  # type: ignore
