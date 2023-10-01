# ruff: noqa: N802 - allow function names to include type names

from __future__ import annotations

from typing import TYPE_CHECKING

from ...discovery.function import FunctionDiscovery
from ...discovery.string import Utf8Discovery
from ...discovery.system import register_explorer
from ..functions import parse_ZConstructOrStaticClass
from ..native_enums import EPropertyGenFlags
from ..native_structs import PropertyParams

if TYPE_CHECKING:
        from collections.abc import Iterator

        from ...discovery.core import Discovery
        from ...lieftools import Image


@register_explorer(PropertyParams)
def explore_PropertyParams(subject: PropertyParams, _image: Image) -> Iterator[Discovery]:
        yield Utf8Discovery(subject.NameUTF8_ptr)
        yield Utf8Discovery(subject.RepNotifyFuncUTF8_ptr)

        # Handle extra values on known types
        match subject.Flags.value:
            case EPropertyGenFlags.Byte | EPropertyGenFlags.Enum:
                yield FunctionDiscovery(subject.EnumFunc_ptr, parse_ZConstructOrStaticClass)
            case EPropertyGenFlags.Bool:
                # SetBitFunc_ptr is unparsable
                pass
            case EPropertyGenFlags.Class:
                yield FunctionDiscovery(subject.MetaClassFunc_ptr, parse_ZConstructOrStaticClass)
                yield FunctionDiscovery(subject.ClassFunc_ptr, parse_ZConstructOrStaticClass)
            case EPropertyGenFlags.Delegate:
                yield FunctionDiscovery(subject.SignatureFunctionFunc_ptr, parse_ZConstructOrStaticClass)
            case EPropertyGenFlags.FieldPath:
                if subject.PropertyClassFunc_ptr:
                    pass # TODO: PropertyClassFunc_ptr
            case EPropertyGenFlags.Interface:
                yield FunctionDiscovery(subject.InterfaceClassFunc_ptr, parse_ZConstructOrStaticClass)
            case EPropertyGenFlags.InlineMulticastDelegate | EPropertyGenFlags.SparseMulticastDelegate:
                yield FunctionDiscovery(subject.SignatureFunctionFunc_ptr, parse_ZConstructOrStaticClass)
            case EPropertyGenFlags.SoftClass:
                yield FunctionDiscovery(subject.MetaClassFunc_ptr, parse_ZConstructOrStaticClass)
            case EPropertyGenFlags.Object | EPropertyGenFlags.WeakObject | EPropertyGenFlags.LazyObject | EPropertyGenFlags.SoftObject:  # noqa: E501
                yield FunctionDiscovery(subject.ClassFunc_ptr, parse_ZConstructOrStaticClass)
            case EPropertyGenFlags.Struct:
                yield FunctionDiscovery(subject.ScriptStructFunc_ptr, parse_ZConstructOrStaticClass)
            case _:
                pass # TODO: Check which other cases need to be handled
