
from pathlib import Path, PurePosixPath
from types import TracebackType

from .output import OutputManager


class DirOutput(OutputManager):
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self) -> 'DirOutput':
        return self

    def write_file(self, data: str, path: PurePosixPath) -> None:
        file = self.path / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(data)

    def __exit__(self, exc_type: type[BaseException] | None,
                 exc_value: BaseException | None,
                 traceback: TracebackType | None) -> bool:
        return False
