from __future__ import annotations

import struct

DEFAULT_ALLOW_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.=-+*()/\\:,;#'

# Pre-compile the structs for better performance
U8_STRUCT = struct.Struct('<B')
S8_STRUCT = struct.Struct('<b')
U16_STRUCT = struct.Struct('<H')
S16_STRUCT = struct.Struct('<h')
U32_STRUCT = struct.Struct('<I')
S32_STRUCT = struct.Struct('<i')
U64_STRUCT = struct.Struct('<Q')
S64_STRUCT = struct.Struct('<q')


class MemoryStream:

    def __init__(self, memory: memoryview, base: int, offset: int | None = None, rva: int | None = None):
        '''Creates a new memory stream for easy deserialization.

        Only one of offset or RVA can be specified. If neither are specified, the stream will start at offset 0.

        Args:
            memory: The memory to read from.
            base: The base RVA of the memory.
            offset: The offset to start reading from.
            rva: The RVA to start reading from.
        '''
        if offset is not None and rva is not None:
            raise ValueError('Cannot specify both offset and RVA')

        self._memory = memory
        self._base = base

        if offset is not None:
            self.set_offset(offset)
        elif rva is not None:
            self.set_addr(rva)
        else:
            self.set_offset(0)

    def __repr__(self) -> str:
        return f'MemoryStream(base=0x{self._base:x}, offset={self._pos}, rva=0x{self.addr:x})'

    def clone(self) -> MemoryStream:
        return MemoryStream(self._memory, self._base, offset=self._pos)

    def clone_offset(self, offset: int) -> MemoryStream:
        return MemoryStream(self._memory, self._base, offset=self._pos + offset)

    def clone_at(self, rva: int) -> MemoryStream:
        return MemoryStream(self._memory, self._base, rva=rva)

    @property
    def offset(self) -> int:
        return self._pos

    @property
    def addr(self) -> int:
        return self._pos + self._base

    @property
    def base(self) -> int:
        return self._base

    def set_offset(self, offset: int):
        self._pos = offset

    def set_addr(self, addr: int):
        if addr < self._base or addr >= self._base + len(self._memory):
            raise ValueError('Position is outside of stream')
        self._pos = addr - self._base

    def bytes(self, length: int, *, peek:bool=False) -> memoryview:
        data = self._memory[self._pos:self._pos + length]
        if not peek:
            self._pos += length
        return data

    def u8(self, *, peek:bool=False) -> int:
        val = U8_STRUCT.unpack_from(self._memory, self._pos)[0]
        if not peek:
            self._pos += U8_STRUCT.size
        return val

    def u16(self, *, peek:bool=False) -> int:
        val = U16_STRUCT.unpack_from(self._memory, self._pos)[0]
        if not peek:
            self._pos += U16_STRUCT.size
        return val

    def u32(self, *, peek:bool=False) -> int:
        val = U32_STRUCT.unpack_from(self._memory, self._pos)[0]
        if not peek:
            self._pos += U32_STRUCT.size
        return val

    def u64(self, *, peek:bool=False) -> int:
        val = U64_STRUCT.unpack_from(self._memory, self._pos)[0]
        if not peek:
            self._pos += U64_STRUCT.size
        return val

    def s8(self, *, peek:bool=False) -> int:
        val = S8_STRUCT.unpack_from(self._memory, self._pos)[0]
        if not peek:
            self._pos += S8_STRUCT.size
        return val

    def s16(self, *, peek:bool=False) -> int:
        val = S16_STRUCT.unpack_from(self._memory, self._pos)[0]
        if not peek:
            self._pos += S16_STRUCT.size
        return val

    def s32(self, *, peek:bool=False) -> int:
        val = S32_STRUCT.unpack_from(self._memory, self._pos)[0]
        if not peek:
            self._pos += S32_STRUCT.size
        return val

    def s64(self, *, peek:bool=False) -> int:
        val = S64_STRUCT.unpack_from(self._memory, self._pos)[0]
        if not peek:
            self._pos += S64_STRUCT.size
        return val

    def ptr_array(self, count: int, *, peek:bool=False) -> list[int]:
        if count == 0:
            return []
        stream = self.clone() if peek else self
        return [stream.u64() for _ in range(count)]

    def utf8zt(self, allow_chars:str|None=DEFAULT_ALLOW_CHARS, limit:int=256) -> str:
        start = self._pos
        end = start + limit
        memory_slice = self._memory[start:end]
        size = len(memory_slice)

        for i in range(len(memory_slice)):
            self._pos += 1
            if memory_slice[i] == 0:
                size = i
                break
        else:
            raise ValueError('String too long')

        text = memory_slice[:size].tobytes().decode('utf-8')

        if allow_chars is not None:
            for c in text:
                if c not in allow_chars:
                    raise ValueError(f'Invalid char 0x{c:02x} ("{c}") in string')

        return text

    def utf8zt_safe(self, allow_chars:str|None=DEFAULT_ALLOW_CHARS, limit:int=256) -> str|None:
        start = self._pos
        end = start + limit
        memory_slice = self._memory[start:end]
        size = len(memory_slice)
        for i in range(len(memory_slice)):
            self._pos += 1
            if memory_slice[i] == 0:
                size = i
                break

        try:
            text = memory_slice[:size].tobytes().decode('utf-8')
        except UnicodeDecodeError:
            return None

        if allow_chars is not None:
            for c in text:
                if c not in allow_chars:
                    return None

        return text

    def utf16zt(self, allow_chars:str|None=DEFAULT_ALLOW_CHARS, limit:int=256) -> str:
        """
        Doctests:
        >>> MemoryStream(b'\x00', 0).utf16zt()
        ''
        """
        start = self._pos
        end = start + limit*2
        memory_slice = self._memory[start:end]

        # Find the length by looking for the null terminator
        words = memory_slice.cast('H')
        size = len(words)
        for i in range(len(words)):
            self._pos += 2
            if words[i] == 0:
                size = i
                break
        else:
            raise ValueError('String too long')

        # Decode the string as UTF16
        text = memory_slice[:size*2].tobytes().decode('utf-16')

        # Check for disallowed characters
        if allow_chars is not None:
            for c in text:
                if c not in allow_chars:
                    raise ValueError(f'Invalid char 0x{ord(c):02x} ("{c}") in string')

        return text

    def utf16zt_safe(self, allow_chars:str|None=DEFAULT_ALLOW_CHARS, limit:int=256) -> str|None:
        start = self._pos
        end = start + limit*2
        memory_slice = self._memory[start:end]

        # Find the length by looking for the null terminator
        words = memory_slice.cast('H')
        size = len(words)
        for i in range(len(words)):
            self._pos += 2
            if words[i] == 0:
                size = i
                break

        # Decode the string as UTF16
        try:
            text = memory_slice[:size*2].tobytes().decode('utf-16')
        except UnicodeDecodeError:
            return None

        # Check for disallowed characters
        if allow_chars is not None:
            for c in text:
                if c not in allow_chars:
                    return None

        return text
