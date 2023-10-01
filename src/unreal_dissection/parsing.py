from dataclasses import dataclass


@dataclass(frozen=True, slots=True, repr=False, kw_only=True)
class ParsingContext:
    ue_version_tuple: tuple[int, ...]
    ue_version_string: str
