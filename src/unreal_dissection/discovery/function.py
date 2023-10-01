from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from logging import getLogger
from typing import TYPE_CHECKING, Any

from ..dissassembly import CodeGrabber
from ..parsing import ParsingContext
from .core import Artefact, Discovery, DiscoveryComparison

if TYPE_CHECKING:
    from ..lieftools import Image

log = getLogger(__name__)

@dataclass(frozen=True, unsafe_hash=True, eq=True, slots=True, repr=False)
class TrampolineArtefact(Artefact):
    '''A jump to a function discovered by the extractor.'''
    target: FunctionArtefact

@dataclass(frozen=True, unsafe_hash=True, eq=True, slots=True, repr=False)
class FunctionArtefact(Artefact):
    '''A parsed function discovered by the extractor.'''
    fn_type: FunctionParserFn

@dataclass(frozen=True, unsafe_hash=True, eq=True, slots=True, repr=False)
class UnparsableFunctionArtefact(FunctionArtefact):
    '''A function that could not be parsed.'''


@dataclass(frozen=True, unsafe_hash=True, eq=True, slots=True, repr=False)
class FunctionDiscovery(Discovery):
    parser_fn: FunctionParserFn
    info: Any|None = field(default=None, compare=False)

    def __str__(self):
        return f'{self.__class__.__name__}[{self.parser_fn.__name__.split(".")[-1]}] @ 0x{self.ptr:x}'

    def compare(self, previous: Discovery) -> DiscoveryComparison:
        # Must be the same type
        if not isinstance(previous, FunctionDiscovery):
            log.warning('FunctionDiscovery.compare: complete type mismatch: {self} != {previous}',
                        extra=dict(self=self, previous=previous))
            return DiscoveryComparison.NoMatch

        # Must be the same type of function
        if self.parser_fn != previous.parser_fn:
            log.warning('FunctionDiscovery.compare: function mismatch: 0x{self.parser_fn} != 0x{previous.parser_fn}',
                        extra=dict(self=self, previous=previous))
            return DiscoveryComparison.NoMatch

        # If we have info, but the other doesn't, replace it
        if self.info is not None and previous.info is None:
            return DiscoveryComparison.Replace

        # If we don't have info, keep the other one
        if self.info is None:
            return DiscoveryComparison.Keep

        # Otherwise the info must match
        if self.info != previous.info:
            log.warning('FunctionDiscovery.compare: info mismatch: {self.info} != {previous.info}',
                        extra=dict(self=self, previous=previous))
            return DiscoveryComparison.NoMatch

        # If we get here, the info matches
        return DiscoveryComparison.Keep

    def perform(self, image: Image, ctx: ParsingContext) -> Iterator[Artefact|Discovery]:
        code = CodeGrabber(image.get_stream(self.ptr), 2048)
        yield from self.parser_fn(code, ctx, self.info)


FunctionParserFn = Callable[[CodeGrabber, ParsingContext, Any|None], Iterator[Artefact|Discovery]]
