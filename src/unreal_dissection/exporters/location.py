from pathlib import PurePosixPath


def get_file_for_thing(typename: str, path: str) -> PurePosixPath:
    '''
    Convert a path and typename to a file path.

    >>> get_file_for_thing('package', '/Script/Engine')
    PurePosixPath('Script/Engine')
    >>> get_file_for_thing('class', '/Script/Engine.Actor')
    PurePosixPath('Script/Engine/Actor')
    >>> get_file_for_thing('function', '/Script/Engine.Actor.Tick')
    PurePosixPath('Script/Engine/Actor/Tick')
    '''
    if path[:1] != '/':
        raise ValueError(f'Path must be absolute: {path}')
    path = path[1:]

    if path.count('.') > 2:
        raise ValueError(f'Path contains too many dots: {path}')

    match typename:
        case 'package':
            return PurePosixPath(path)
        case 'class' | 'struct' | 'enum' | 'function':
            path = path.replace('.', '/')
            return PurePosixPath(path)
        case _:
            raise ValueError(f'Unknown typename: {typename}')
