from collections.abc import Iterator
from typing import cast

import lief

from .pattern import Pattern
from .search import find_calls
from .stream import MemoryStream

SECTION_TEXT = '.text'
SECTION_RDATA = '.rdata'


class Image:

    def __init__(self, src: lief.Binary | str | bytes):
        if not isinstance(src, lief.Binary):
            src = lief.parse(src)  # type: ignore

        binary: lief.Binary = src if isinstance(src, lief.Binary) else cast(lief.Binary, lief.parse(src))
        self.binary = binary
        self.base = binary.imagebase

        # Extract version information
        self._extract_version()

        # Create a map of section names to section objects
        self._sections = {
            cast(str, cast(lief.Section, section).name): cast(lief.Section, section)
            for section in binary.sections
        }

    def get_stream(self, rva: int) -> MemoryStream:
        '''Gets a memory stream from an RVA.

        Args:
            rva: The RVA to get the stream from.

        Returns:
            The memory stream.
        '''
        base, memory = self.get_section_memory_from_rva(rva)
        return MemoryStream(memory, base, rva=rva, verify_alignment=True)

    def get_section_name_from_rva(self, rva: int) -> str|None:
        '''Gets the section from an RVA.

        Args:
            rva: The RVA to get the section memory from.

        Returns:
            The section name or None is the RVA is not in any section.
        '''
        if rva < self.binary.imagebase:
            return None
        va = rva - self.binary.imagebase
        section: lief.Section
        for section in self.binary.sections:
            if section.virtual_address <= va < section.virtual_address + section.size:
                return cast(str, section.name)

        raise ValueError(f'RVA {rva:#x} is not in any section')

    def get_section_memory_from_rva(self, rva: int) -> tuple[int, memoryview]:
        '''Gets the memory of a section from an RVA.

        Args:
            rva: The RVA to get the section memory from.

        Returns:
            The base RVA and memory of the section as a memoryview.
        '''
        va = rva - self.binary.imagebase
        section: lief.Section
        for section in self.binary.sections:
            if section.virtual_address <= va < section.virtual_address + section.size:
                section_base = self.binary.imagebase + section.virtual_address
                return section_base, section.content

        raise ValueError(f'RVA {rva:#x} is not in any section')

    def get_section_memory(self, name: str) -> tuple[int, memoryview]:
        '''Gets the memory of a section.

        Args:
            name: The name of the section.

        Returns:
            The base address and memory of the section as a memoryview.
        '''
        section = self._sections[name]
        section_base = self.binary.imagebase + section.virtual_address
        return section_base, self.binary.get_content_from_virtual_address(section_base, section.size).toreadonly()

    def find_pattern(self, pattern: Pattern, section_name: str) -> Iterator[int]:
        '''Finds a pattern in the binary.

        Args:
            pattern: The pattern to search for.
            section: The name of the section to search in.

        Returns:
            The RVA of the pattern in the binary.
        '''
        base, memory = self.get_section_memory(section_name)
        for offset in pattern.search(memory):
            yield offset + base

    def find_calls(self, target: int, section_name: str = '.text') -> Iterator[int]:
        '''Finds calls to a target address in a section.

        Args:
            target: The target address to search for.
            section: The name of the section to search in.

        Returns:
            The RVAs of the calls within the section.
        '''
        base, memory = self.get_section_memory(section_name)
        for offset in find_calls(target, memory, base):
            yield offset + base

    def find_aligned_pointers(self, target: int, section_name: str = '.rdata') -> Iterator[int]:
        '''Finds 64-bit aligned locations within a section that point to a target RVA.

        Args:
            target: The target RVA to search for.
            section: The name of the section to search in.

        Returns:
            The RVAs of the aligned pointers within the section.
        '''
        base, memory = self.get_section_memory(section_name)

        # Cast memoryview to a u64 array
        qwords = memory[:memory.nbytes - (memory.nbytes % 8)].cast('Q')
        for i,value in enumerate(qwords):
            if value == target:
                yield i * 8 + base


    def _extract_version(self) -> None:
        self.version_tuple: tuple[int, ...]|None = None
        self.version_string: str|None = None

        binary = self.binary
        if not isinstance(binary, lief.PE.Binary) or not binary.has_resources:
            return
        resource_manager = binary.resources_manager
        if not resource_manager or not resource_manager.has_version:
            return
        version_entry: lief.PE.ResourceVersion = resource_manager.version # type: ignore
        if not version_entry:
            return

        # Extract fixed version info from the resource section
        self._extract_fixed_version_info(version_entry.fixed_file_info)

        # Extract remaining property data
        self._extract_string_version_info(version_entry.string_file_info)

    def _extract_fixed_version_info(self, fixed_file_info: lief.PE.ResourceFixedFileInfo):
        # Version info is four 16-bit integers split across two 32-bit integers
        version_ms = fixed_file_info.product_version_MS
        version_ls = fixed_file_info.product_version_LS
        version = (
            version_ms >> 16, version_ms & 0xFFFF,
            version_ls >> 16, version_ls & 0xFFFF,
        )

        # Remove trailing zeros
        while version and version[-1] == 0:
            version = version[:-1]

        self.version_tuple = version
        self.version_string = '.'.join(str(v) for v in version) if version else None

    def _extract_string_version_info(self, string_file_info: lief.PE.ResourceStringFileInfo):
        first_lang = string_file_info.langcode_items[0]
        items: dict[str, bytes] = first_lang.items # type: ignore
        self.file_properties = {key: value.decode('utf-8') for key, value in items.items()}
