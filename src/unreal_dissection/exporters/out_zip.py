
import zipfile
from pathlib import Path, PurePosixPath
from types import TracebackType

from .output import OutputManager


class ZipOutput(OutputManager):
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self) -> 'ZipOutput':
        self.archive = zipfile.ZipFile(self.path, 'w', compression=zipfile.ZIP_DEFLATED)
        return self

    def write_file(self, data: str, path: PurePosixPath) -> None:
        self.archive.writestr(str(path), data)

    def __exit__(self, exc_type: type[BaseException] | None,
                 exc_value: BaseException | None,
                 traceback: TracebackType | None) -> bool:
        self.archive.close()
        return False
