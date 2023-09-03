from collections.abc import Iterator
from dataclasses import dataclass
from typing import NamedTuple


class ByteMatch(NamedTuple):
    mask: int
    value: int

    def matches(self, value: int) -> bool:
        '''
        Checks if a value matches the byte match.

        Args:
            value: The value to check.

        Returns:
            True if the value matches the byte match, False otherwise.

        Doctests:
        >>> ByteMatch(mask=255, value=0xad).matches(0xad)
        True
        >>> ByteMatch(mask=255, value=0xad).matches(0xbe)
        False
        >>> ByteMatch(mask=0, value=0xad).matches(0xbe)
        False
        >>> ByteMatch(mask=0b11110000, value=0xa0).matches(0xa3)
        True
        >>> ByteMatch(mask=0b11110000, value=0x0d).matches(0x3d)
        False
        >>> ByteMatch(mask=0b00001111, value=0x0d).matches(0x3d)
        True
        '''
        return (value & self.mask) == self.value


@dataclass(frozen=True, slots=True, eq=True)
class Pattern:
    entries: tuple[ByteMatch, ...]

    def search(self, memory: memoryview) -> Iterator[int]:
        """
        Searches for the pattern in a memoryview.

        Args:
            memory: The memoryview to search in.

        Returns:
            The offsets of the pattern in the memoryview.

        Doctests:
        >>> list(Pattern((ByteMatch(mask=255, value=0xad), )).search(memoryview(b'\\xde\\xad\\xbe\\xef')))
        [1]
        >>> list(Pattern((ByteMatch(mask=255, value=0xad), ByteMatch(mask=255, value=0xbe)))
                .search(memoryview(b'\\xde\\xad\\xbe\\xef')))
        [1]
        >>> list(Pattern((ByteMatch(mask=255, value=0xff), )).search(memoryview(b'\\xff\\xde\\xad\\xbe\\xef\\xff')))
        [0, 5]
        >>> list(Pattern((ByteMatch(mask=255, value=0xff), )).search(memoryview(b'\\xde\\xad\\xbe\\xef')))
        []
        """
        for offset in range(len(memory) - len(self.entries) + 1):
            for i, match in enumerate(self.entries):
                if not match.matches(memory[offset + i]):
                    break
            else:
                yield offset


def compile_pattern(pattern: str) -> Pattern:
    """Compiles a pattern string into a tuple of byte matches.

    Args:
        pattern: The pattern to compile.

    Returns:
        A tuple of byte matches.

    Doctests:
    >>> compile_pattern('00 01 02 03')  # doctest: +NORMALIZE_WHITESPACE
    Pattern(entries=(ByteMatch(mask=255, value=0),
        ByteMatch(mask=255, value=1),
        ByteMatch(mask=255, value=2),
        ByteMatch(mask=255, value=3)))
    >>> compile_pattern('01 x 02')
    Pattern(entries=(ByteMatch(mask=255, value=1), ByteMatch(mask=0, value=0), ByteMatch(mask=255, value=2)))
    >>> compile_pattern('[01001...]') == Pattern(entries=(ByteMatch(mask=0b11111000, value=0b01001000),))
    True
    """
    result: list[ByteMatch] = []

    for byte in pattern.split(' '):
        if byte.startswith('['):  # Bit pattern
            result.append(_parse_bit_pattern(byte))
        elif byte in ('?', '??', 'x', 'xx'):
            result.append(ByteMatch(0, 0))  # Wildcard
        elif not byte:
            pass
        else:  # Hex byte
            result.append(ByteMatch(0xFF, int(byte, 16)))

    return Pattern(tuple(result))


def _parse_bit_pattern(pattern: str) -> ByteMatch:
    """Parses a bit pattern into a tuple of a mask and a value. Example: '[01001...]' -> ByteMatch(0b11111000, 0b01001000)

    Args:
        pattern: The bit pattern to parse.

    Returns:
        A tuple of a mask and a value.

    Doctests:
    >>> _parse_bit_pattern('[01001...]') == ByteMatch(0b11111000, 0b01001000)
    True
    >>> _parse_bit_pattern('[01001]')
    Traceback (most recent call last):
    ValueError: Invalid bit pattern '01001': must be 8 characters long
    >>> _parse_bit_pattern('[0100100101010]')
    Traceback (most recent call last):
    ValueError: Invalid bit pattern '0100100101010': must be 8 characters long
    >>> _parse_bit_pattern('[0101010a]')
    Traceback (most recent call last):
    ValueError: Unexpected character in bit pattern '0101010a'
    """
    if not pattern.startswith('[') or not pattern.endswith(']'):
        raise ValueError(f"Invalid bit pattern '{pattern}': must start and end with square brackets")
    pattern = pattern[1:-1]
    if len(pattern) != 8:
        raise ValueError(f"Invalid bit pattern '{pattern}': must be 8 characters long")

    mask = 0
    value = 0
    for char in pattern:
        mask <<= 1
        value <<= 1
        if char == '0':
            mask |= 1
        elif char == '1':
            mask |= 1
            value |= 1
        elif char in ('.', '?', 'x'):
            pass
        else:
            raise ValueError(f"Unexpected character in bit pattern '{pattern}'")

    return ByteMatch(mask, value)
