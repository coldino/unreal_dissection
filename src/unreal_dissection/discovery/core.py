from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ..lieftools import Image
    from ..parsing import ParsingContext


@runtime_checkable
class Discoverable(Protocol):
    def register_discoveries(self, image: Image) -> Iterator[Discovery]: ...


class DiscoveryComparison(Enum):
    NoMatch = auto()
    Keep = auto()
    Replace = auto()


@dataclass(frozen=True, slots=True)
class Artefact:
    '''Base class for all artefacts discovered by the extractor.'''
    start_addr: int
    end_addr: int

    def _repr_pretty_(self, p: Any, cycle: bool):  # noqa: FBT001 - implementing external protocol
        '''Pretty-printing repr for IPython.'''
        header = f'{self.__class__.__name__} @ 0x{self.start_addr:x}-0x{self.end_addr:x} ('
        p.text(header)
        if cycle:
            p.text('...)')
            return
        with p.indent(2):
            p.breakable('')
            names = (field.name for field in fields(self) if not (field.name.startswith('_') or field.name == 'ptr'))
            for i, name in enumerate(names):
                if i > 0:
                    p.text(',')
                    p.breakable()
                p.text(f'{name}=')
                p.pretty(getattr(self, name))
        p.text(')')


@dataclass(frozen=True, unsafe_hash=True, eq=True, slots=True, repr=False)
class Discovery(metaclass=ABCMeta):
    '''Base class for all pending discoveries made by the extractor.'''
    ptr: int

    def is_ready(self) -> bool:
        '''Return True if this discovery is ready to be processed.'''
        return True

    @abstractmethod
    def perform(self, image: Image, ctx: ParsingContext) -> Iterator[Artefact|Discovery]:
        '''Perform this discovery, yielding any artefacts or further discoveries.'''
        raise NotImplementedError

    def compare(self, previous: Discovery) -> DiscoveryComparison:
        ''''''
        # Must be the same type, or a subclass of it
        if not issubclass(type(self), type(previous)):
            return DiscoveryComparison.NoMatch

        # By default assume any differences mean no match
        if self != previous:
            return DiscoveryComparison.NoMatch

        return DiscoveryComparison.Keep

    def __str__(self):
        return f'{self.__class__.__name__} @ 0x{self.ptr:x}'

    def _repr_pretty_(self, p: Any, cycle: bool):  # noqa: FBT001 - implementing external protocol
        '''Pretty-printing repr for IPython.'''
        header = f'{self.__class__.__name__} @ 0x{self.ptr:x} ('
        p.text(header)
        if cycle:
            p.text('...)')
            return
        with p.indent(2):
            p.breakable('')
            names = (field.name for field in fields(self) if not (field.name.startswith('_') or field.name == 'ptr'))
            for i, name in enumerate(names):
                if i > 0:
                    p.text(',')
                    p.breakable()
                p.text(f'{name}=')
                p.pretty(getattr(self, name))
        p.text(')')
