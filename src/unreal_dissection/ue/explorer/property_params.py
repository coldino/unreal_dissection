# ruff: noqa: N802 - allow function names to include type names

from __future__ import annotations

from typing import TYPE_CHECKING

from ...discovery.function import FunctionDiscovery
from ...discovery.string import Utf8Discovery
from ...discovery.system import register_explorer
from ..discovery.function import ZConstructFunctionDiscovery
from ..functions import ZConstructFnType, parse_StaticClass
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
                yield ZConstructFunctionDiscovery(subject.EnumFunc_ptr, ZConstructFnType.Enum)
            case EPropertyGenFlags.Bool:
                if subject.SetBitFunc_ptr:
                    pass
                # yield ZConstructFunctionDiscovery(subject.SetBitFunc_ptr, ZConstructFnType.Function) ???
            case EPropertyGenFlags.Class:
                yield ZConstructFunctionDiscovery(subject.MetaClassFunc_ptr, ZConstructFnType.Class)
                yield ZConstructFunctionDiscovery(subject.ClassFunc_ptr, ZConstructFnType.Class)
            case EPropertyGenFlags.Delegate:
                yield ZConstructFunctionDiscovery(subject.SignatureFunctionFunc_ptr, ZConstructFnType.Function)
            case EPropertyGenFlags.FieldPath:
                if subject.PropertyClassFunc_ptr:
                    pass # TODO: PropertyClassFunc_ptr
            case EPropertyGenFlags.Interface:
                yield FunctionDiscovery(subject.InterfaceClassFunc_ptr, parse_StaticClass)
            case EPropertyGenFlags.InlineMulticastDelegate | EPropertyGenFlags.SparseMulticastDelegate:
                yield ZConstructFunctionDiscovery(subject.SignatureFunctionFunc_ptr, ZConstructFnType.Function)
            case EPropertyGenFlags.SoftClass:
                yield ZConstructFunctionDiscovery(subject.MetaClassFunc_ptr, ZConstructFnType.Class)
            case EPropertyGenFlags.Object | EPropertyGenFlags.WeakObject | EPropertyGenFlags.LazyObject | EPropertyGenFlags.SoftObject:  # noqa: E501
                # Don't know what subject.ClassFunc_ptr is
                pass
            case EPropertyGenFlags.Struct:
                # Don't know what ScriptStructFunc_ptr is
                pass
            case _:
                pass # TODO: Check which other cases need to be handled
