import struct
from collections.abc import Iterator


def find_calls(target: int, memory: memoryview, base_address: int) -> Iterator[int]:
    '''Finds calls to a target address in a memoryview.

    Args:
        target: The target address to search for.
        memory: The memory to search in.
        base_address: The base address of the memoryview.

    Returns:
        The offsets of the calls within the memoryview.
    '''
    for offset in range(len(memory) - 5):
        if memory[offset] == 0xe8:
            delta = struct.unpack('<i', memory[offset + 1:offset + 5])[0]
            call_target = base_address + offset + 5 + delta
            if call_target == target:
                yield offset + base_address


def analyse_all_calls(memory: memoryview,
                      base_address: int,
                      allow_min: int | None = None,
                      allow_max: int | None = None,
                      min_count: int | None = 1000) -> dict[int, list[int]]:
    '''Finds all calls in a memoryview.

    Args:
        memory: The memory to search in.
        base_address: The base address of the memoryview.

    Returns:
        A dictionary of target addresses to lists of offsets of calls to that address.
    '''

    # Gather all the (valid) calls first
    calls: dict[int, list[int]] = {}
    for offset in range(len(memory) - 5):
        if memory[offset] == 0xe8:
            delta = struct.unpack('<i', memory[offset + 1:offset + 5])[0]
            call_target = base_address + offset + 5 + delta
            if (allow_min is None or call_target >= allow_min) and (allow_max is None or call_target <= allow_max):
                calls.setdefault(call_target, []).append(offset + base_address)

    # Filter out the ones that don't have enough calls
    if min_count is not None:
        calls = {target: offsets for target, offsets in calls.items() if len(offsets) >= min_count}

    # Sort by the most called
    calls = dict(sorted(calls.items(), key=lambda item: len(item[1]), reverse=True))

    return calls
