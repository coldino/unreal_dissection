
from pathlib import Path, PurePosixPath
from types import TracebackType

import py7zr

from .output import OutputManager


class SevenZipOutput(OutputManager):
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self) -> 'SevenZipOutput':
        self.archive = py7zr.SevenZipFile(self.path, 'w')
        return self

    def write_file(self, data: str, path: PurePosixPath) -> None:
        self.archive.writestr(data, str(path))

    def __exit__(self, exc_type: type[BaseException] | None,
                 exc_value: BaseException | None,
                 traceback: TracebackType | None) -> bool:
        self.archive.close()
        return False
