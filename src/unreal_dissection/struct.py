from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Self, cast

import dataclasses_struct as dcs
from dataclasses_struct import get_struct_size

if TYPE_CHECKING:
    from .parsing import ParsingContext
    from .stream import MemoryStream


class DynamicStruct(metaclass=ABCMeta):
    '''Base class for structs that can include logic while being deserialized from a MemoryStream.'''
    _deserialized = False
    _base_addr: int

    @abstractmethod
    def deserialize(self, stream: MemoryStream, ctx: ParsingContext) -> None: ...

    @classmethod
    def from_stream(cls, stream: MemoryStream, ctx: ParsingContext) -> Self:
        '''Create an instance of this dynamic struct type by deserializing it from a MemoryStream.'''
        obj = cls()
        obj._base_addr = stream.addr  # noqa: SLF001 - actually our own field
        obj.deserialize(stream, ctx)
        obj._deserialized = True  # noqa: SLF001 - actually our own field

        return obj

    def _repr_pretty_(self, p: Any, cycle: bool):  # noqa: FBT001 - implementing external protocol
        '''Pretty-printing repr for IPython.'''
        p.text(f'{self.__class__.__name__} @ 0x{self._base_addr:x}(')
        if cycle:
            p.text('...)')
            return
        with p.indent(2):
            p.breakable('')
            fields = ((k,v) for k,v in self.__dict__.items() if not k.startswith('_'))
            for i, (k, v) in enumerate(fields):
                if i > 0:
                    p.text(',')
                    p.breakable()
                p.text(f'{k}=')
                p.pretty(v)
        p.text(')')


def struct_from_stream[T](cls: type[T], stream: MemoryStream, ctx: ParsingContext) -> T:
    '''Create an instance of a struct by deserializing it from a MemoryStream.'''
    if dcs.is_dataclass_struct(cls):
        size = dcs.get_struct_size(cls)
        data = stream.bytes(size)
        return cast(T, cls.from_packed(data)) # type: ignore - Python isn't good with bytes/memoryview typing

    if issubclass(cls, DynamicStruct):
        return cls.from_stream(stream, ctx)

    raise TypeError(f'{cls} cannot be read directly from a stream')


def structclass[T](cls: type[T]) -> type[T]:
    return dcs.dataclass(dcs.LITTLE_ENDIAN)(cls) # type: ignore


def get_struct_size_aligned(cls: type, align: int = 8) -> int:
    '''Get the size of a struct, aligned to the supplied word size.'''
    struct_size = get_struct_size(cls)
    mask = align - 1
    return (struct_size + mask) & ~mask

__all__ = (
    'dcs',
    'structclass',
    'DynamicStruct',
    'struct_from_stream',
    'get_struct_size',
)
