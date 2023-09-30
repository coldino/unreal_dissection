from enum import Enum
from logging import getLogger
from pathlib import Path

import typed_argparse as tap

from unreal_dissection import fully_discover, load_image

log = getLogger('unreal_dissection')

class FormatType(Enum):
    Ion = 'ion'
    Json = 'json'
    Yaml = 'yaml'

    def __str__(self) -> str:
        return str(self.value)

def format_type(value: str) -> FormatType:
    return FormatType(value)

class Args(tap.TypedArgs):
    exe: Path = tap.arg(positional=True, help='The executable to analyse')
    output: Path = tap.arg('-o', help='The output directory (wiped before starting)')
    no_wipe: bool = tap.arg('--no-wipe', help='Do not wipe the output directory before starting')
    format: FormatType = tap.arg('-f', '--format', default=FormatType.Json, help='The output format')

def runner(args: Args):
    log.info('Beginning extraction of %s', args.exe)

    log.info('Loading exe...')
    image = load_image(str(args.exe))
    _discovery = fully_discover(image)

    if False:
        match args.format:
            case FormatType.Json:
                from .exporters.json_format import JsonExporter
                JsonExporter(args.output)
            case _:
                raise NotImplementedError

def main():
    tap.Parser(Args).bind(runner).run()
