# ruff: noqa: N802 - allow function names to include type names

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Any

from ..discovery.struct import StructArtefact
from ..discovery.system import get_explorer_for_type, register_explorer

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ..discovery.core import Discovery
    from ..lieftools import Image

log = getLogger(__name__)

@register_explorer(StructArtefact)
def explore_StructArtefact(subject: StructArtefact[Any], image: Image) -> Iterator[Discovery]:
    sub_explorer = get_explorer_for_type(subject.struct_type)
    if sub_explorer is not None:
        yield from sub_explorer(subject.struct, image)
    else:
        if subject.struct_type not in unhandled_struct_types:
            unhandled_struct_types.add(subject.struct_type)
            log.warning('Unhandled struct type: {subject.struct_type}', extra=dict(subject=subject))
        yield from ()

unhandled_struct_types: set[type] = set()
