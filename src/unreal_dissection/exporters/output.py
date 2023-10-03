from contextlib import AbstractContextManager
from pathlib import PurePosixPath


class OutputManager(AbstractContextManager['OutputManager']):
    def write_file(self, data: str, path: PurePosixPath) -> None:
        ...
