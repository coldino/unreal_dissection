from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator
from functools import singledispatch
from logging import getLogger
from typing import Any

from ..lieftools import Image
from ..parsing import ParsingContext
from .core import Artefact, Discoverable, Discovery, DiscoveryComparison
from .function import FunctionArtefact, FunctionParserFn, TrampolineArtefact, UnparsableFunctionArtefact
from .string import StringArtefact
from .struct import StructArtefact

pretty: Callable[[Any], str]
try:
    from IPython.lib.pretty import pretty  # type: ignore
except ImportError:
    from pprint import pformat as pretty

log = getLogger(__name__)

NO_DEFAULT = object()

class DiscoverySystem:
    '''A system for dynamic discovery within in a binary image.

    This system is responsible for managing the discovery queue and the set of discovered artefacts.

    Discoveries are queued for processing, while found artefacts are categorised and stored.

    '''
    image: Image
    pending: dict[int, Discovery]
    found: dict[int, Artefact]
    found_strings: dict[int, StringArtefact]
    found_structs: dict[int, StructArtefact[Any]]
    found_structs_by_type: dict[type, list[StructArtefact[Any]]]
    found_structs_by_type_and_ptr: dict[type, dict[int, StructArtefact[Any]]]
    found_functions: dict[int, FunctionArtefact]
    found_functions_by_type: dict[type, list[FunctionArtefact]]
    found_functions_by_type_and_ptr: dict[FunctionParserFn, dict[int, FunctionArtefact]]
    found_trampolines: dict[int, TrampolineArtefact]

    def __init__(self, image: Image):
        self.image = image
        self.pending = {}
        self.found = {}
        self.found_trampolines = {}
        self.found_strings = {}
        self.found_structs = {}
        self.found_structs_by_type = defaultdict(list)
        self.found_structs_by_type_and_ptr = defaultdict(dict)
        self.found_functions = {}
        self.found_functions_by_type = defaultdict(list)
        self.found_functions_by_type_and_ptr = defaultdict(dict)

        ue_version_string = image.version_string
        if not ue_version_string:
            raise ValueError('No version string found')
        ue_version_tuple = image.version_tuple
        if not ue_version_tuple:
            raise ValueError('No version tuple found')

        self.ctx = ParsingContext(
            ue_version_string=ue_version_string,
            ue_version_tuple=ue_version_tuple,
        )

    def queue(self, discovery: Discovery):
        '''Add a pending discovery to the queue.

        If the discovery is a duplicate, it will be ignored as long as it matches the existing discovery.
        Discoveries that are considered more specific than existing discoveries will replace them.
        '''
        if discovery.ptr == 0 or discovery.ptr == 0xFFFFFFFFFFFFFFFF:  # noqa: PLR1714
            return

        log.debug('Queuing %s', discovery)
        if discovery.ptr in self.found:
            log.debug('Skipping as a duplicate')
            return

        pending = self.pending.get(discovery.ptr, None)
        if pending is not None:
            log.debug('Checking matching pending discovery @ 0x%x', discovery.ptr)
            match discovery.compare(pending):
                case DiscoveryComparison.NoMatch:
                    log.exception('Conflicting discovery @ 0x%x: %r and %r', discovery.ptr, discovery, pending)
                    raise ValueError(
                        f'Conflicting discovery @ 0x{discovery.ptr:x}: {discovery!s} and {pending!s}',
                        discovery,
                        pending,
                    )
                case DiscoveryComparison.Replace:
                    log.debug('Replacing pending discovery')
                    self.pending[discovery.ptr] = discovery
                case DiscoveryComparison.Keep:
                    log.debug('Keeping pending discovery @ 0x%x', discovery.ptr)
                    pass
        else:
            self.pending[discovery.ptr] = discovery

    def process_one(self) -> bool:
        '''Process the next queued discovery.

        Discoveries may produce any number of other discoveries or artefacts. Discoveries are queued
        for future processing, while artefacts are registered as found.

        Returns:
            True if a discovery was processed, False if there are no discoveries to process.
        '''
        if not self.pending:
            return False

        # Step through pending discoveries looking for one that is ready to process
        for discovery in self.pending.values():
            if discovery.is_ready():
                break
        else:
            # No discoveries are ready to process
            log.warning('process_one called but no discoveries are ready')
            return False

        # Remove the discovery from the queue and process it
        del self.pending[discovery.ptr]
        log.debug('Processing discovery %s', discovery)
        try:
            for thing in discovery.perform(self.image, self.ctx):
                if isinstance(thing, Discovery):
                    self.queue(thing)
                else:
                    self._register_found(thing, discovery)

                    # Potentially recurse into the discovered thing
                    self._discover(thing)
        except Exception as e:
            log.exception('Error while processing %s', pretty(discovery), exc_info=e)
            raise

        return True

    def process_all(self):
        '''Process all queued discoveries.

        This will continue processing discoveries until the queue is empty.
        '''
        while self.pending:
            self.process_one()

    def find_container(self, rva: int) -> Artefact | None:
        '''Find the container for a given RVA.

        This will return the artefact that contains the given RVA, or None if no container is found.

        Note: this function is not efficient and should not be used in performance-critical code.
        '''
        for artefact in self.found.values():
            if artefact.start_addr <= rva < artefact.end_addr:
                return artefact
        return None

    def get_string_artefact(self, ptr: int) -> StringArtefact | None:
        '''Get the string artefact for a given pointer.

        This will return the string artefact for the given pointer, or None if no string is found.
        '''
        return self.found_strings.get(ptr, None)

    @singledispatch
    def get_string[T](self, ptr: int, *, default: T=NO_DEFAULT) -> str | T:
        '''Get the string for a given pointer.

        This will return the string for the given pointer, or None if no string is found.
        '''
        artefact = self.get_string_artefact(ptr)
        if artefact is None:
            if default is NO_DEFAULT:
                raise ValueError(f'No string found @ 0x{ptr:x}')
            return default
        return artefact.string

    @get_string.register
    def _(self, ptr: int) -> str:
        artefact = self.get_string_artefact(ptr)
        if artefact is None:
            raise ValueError(f'No string found @ 0x{ptr:x}')
        return artefact.string

    def get_struct[T](self, ptr: int, struct_type: type[T]) -> StructArtefact[T] | None:
        '''Get the struct artefact for a given pointer.

        This will return the struct artefact for the given pointer, or None if no struct is found.
        '''
        return self.found_structs_by_type_and_ptr[struct_type].get(ptr)

    def print_summary(self):
        print(f'Found {len(self.found)} artefacts:')
        print(f'  {len(self.found_strings)} strings')
        for struct_type,structs in self.found_structs_by_type.items():
            print(f'  {len(structs)} {struct_type.__name__} structs')
        for fn_type,fns in self.found_functions_by_type.items():
            if count := _count_parseable(fns):
                print(f'  {count} {_clean_fn_name(fn_type.__name__)} functions')
        print(f'  {_count_unparsable(self.found.values())} unparsable functions')


    def _discover(self, discoverable: Any):
        try:
            if isinstance(discoverable, Discoverable):
                for discovery in discoverable.register_discoveries(self.image):
                    self.queue(discovery)
            elif explorer := get_explorer_for_type(type(discoverable)):
                for discovery in explorer(discoverable, self.image):
                    self.queue(discovery)
        except Exception as e:
            log.exception('Error while discovering %s', pretty(discoverable), exc_info=e)
            raise


    def _register_found(self, thing: Artefact, for_discovery: Discovery):
        log.debug('Registering %s', pretty(thing))
        self.found[for_discovery.ptr] = thing  # type: ignore

        match thing:
            case StringArtefact():
                self.found_strings[for_discovery.ptr] = thing
            case StructArtefact():
                self.found_structs[for_discovery.ptr] = thing # type: ignore
                self.found_structs_by_type[thing.struct_type].append(thing)  # type: ignore
                self.found_structs_by_type_and_ptr[thing.struct_type][for_discovery.ptr] = thing  # type: ignore
            case FunctionArtefact():
                self.found_functions[for_discovery.ptr] = thing
                self.found_functions_by_type[thing.fn_type].append(thing)  # type: ignore
                self.found_functions_by_type_and_ptr[thing.fn_type][for_discovery.ptr] = thing
            case TrampolineArtefact():
                self.found_trampolines[for_discovery.ptr] = thing
            case _:
                log.warning('Unhandled discovery result %r for %r', thing, for_discovery)


type AnyExplorerFn = Callable[[Any, Image], Iterator[Discovery]]

_registered_explorers: dict[str, AnyExplorerFn] = {}


def register_explorer[T](for_type: type[T]) -> Callable[
    [Callable[[T, Image], Iterator[Discovery]]],
    Callable[[T, Image], Iterator[Discovery]]]:

    def decorator(fn: Callable[[T, Image], Iterator[Discovery]]) -> Callable[[T, Image], Iterator[Discovery]]:
        if for_type.__name__ in _registered_explorers:
            log.warning('Replacing already-registered explorer for {for_type}', extra=dict(for_type=for_type))
        _registered_explorers[for_type.__name__] = fn
        log.debug('Registered explorer for {for_type.__name__}: {fn.__name__}', extra=dict(for_type=for_type, fn=fn))
        return fn

    return decorator

def get_explorer_for_type(for_type: type) -> AnyExplorerFn | None:
    return _registered_explorers.get(for_type.__name__, None)

def _count_unparsable(artefacts: Iterable[Artefact]) -> int:
    return sum(1 for artefact in artefacts if isinstance(artefact, UnparsableFunctionArtefact))

def _count_parseable(artefacts: Iterable[Artefact]) -> int:
    return sum(1 for artefact in artefacts if not isinstance(artefact, UnparsableFunctionArtefact))

def _clean_fn_name(fn_name: str) -> str:
    return fn_name.removeprefix('parse_').removesuffix('_fn')

__all__ = [
    'DiscoverySystem',
    'register_explorer',
    'get_explorer_for_type',
]
