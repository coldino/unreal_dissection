from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum

from ..lieftools import Image
from .core import Artefact, Discovery


class StringEncoding(Enum):
    Utf8 = 'utf-8'
    Utf16 = 'utf-16'

@dataclass(frozen=True, unsafe_hash=True, eq=True, slots=True, repr=False)
class StringArtefact(Artefact):
    '''A string discovered by the extractor.'''
    encoding: StringEncoding
    string: str

    def __repr__(self) -> str:
        size_chr = 'w' if self.encoding == StringEncoding.Utf16 else ' '
        return f'{self.__class__.__name__} @ 0x{self.start_addr:x}-0x{self.end_addr:x} {size_chr}{self.string!r}'


@dataclass(frozen=True, unsafe_hash=True, eq=True, slots=True, repr=False)
class Utf8Discovery(Discovery):
    def perform(self, image: Image) -> Iterator[Artefact|Discovery]:
        start = self.ptr
        stream = image.get_stream(self.ptr)
        string = stream.utf8zt()
        yield StringArtefact(start, stream.addr, StringEncoding.Utf8, string)


@dataclass(frozen=True, unsafe_hash=True, eq=True, slots=True, repr=False)
class Utf16Discovery(Discovery):
    def perform(self, image: Image) -> Iterator[Artefact|Discovery]:
        start = self.ptr
        stream = image.get_stream(self.ptr)
        string = stream.utf16zt()
        yield StringArtefact(start, stream.addr, StringEncoding.Utf16, string)
