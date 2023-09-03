from __future__ import annotations

from typing import Iterator

from ...discovery.core import Discovery
from ...discovery.function import FunctionDiscovery
from ...discovery.string import Utf8Discovery
from ...discovery.system import register_explorer
from ...lieftools import Image
from ..functions import ZConstructFnType, parse_ZConstruct_fn
from ..native_enums import EPropertyGenFlags
from ..native_structs import DynamicPropertyParams


@register_explorer(DynamicPropertyParams)
def explore_DynamicPropertyParams(subject: DynamicPropertyParams, image: Image) -> Iterator[Discovery]:
        yield Utf8Discovery(subject.NameUTF8_ptr)
        yield Utf8Discovery(subject.RepNotifyFuncUTF8_ptr)

        # Handle extra values on known types
        match subject.Flags.value:
            case EPropertyGenFlags.Byte | EPropertyGenFlags.Enum:
                yield FunctionDiscovery(subject.EnumFunc_ptr, parser_fn=parse_ZConstruct_fn, info=ZConstructFnType.Enum)
            case EPropertyGenFlags.Class:
                yield FunctionDiscovery(subject.MetaClassFunc_ptr, parser_fn=parse_ZConstruct_fn, info=ZConstructFnType.Class)
                yield FunctionDiscovery(subject.ClassFunc_ptr, parser_fn=parse_ZConstruct_fn, info=ZConstructFnType.Class)
            case EPropertyGenFlags.Delegate:
                # TODO: SignatureFunctionFunc_ptr
                # TODO: SetBitFunc_ptr
                pass
            case EPropertyGenFlags.FieldPath:
                # TODO: PropertyClassFunc_ptr
                pass
            case EPropertyGenFlags.Interface:
                # TODO: InterfaceClassFunc_ptr
                pass
            case EPropertyGenFlags.InlineMulticastDelegate | EPropertyGenFlags.SparseMulticastDelegate:
                # TODO: SignatureFunctionFunc_ptr
                pass
            case EPropertyGenFlags.Object | EPropertyGenFlags.WeakObject | EPropertyGenFlags.LazyObject | EPropertyGenFlags.SoftObject:
                # TODO: ClassFunc_ptr
                pass
            case EPropertyGenFlags.SoftClass:
                # TODO: MetaClassFunc_ptr
                pass
            case EPropertyGenFlags.Struct:
                # TODO: ScriptStructFunc_ptr
                pass
            case _:
                pass # TODO: Check which other cases need to be handled
