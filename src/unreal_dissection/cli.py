# ruff: noqa: UP007 (Optional is required for typed_argparse to recognise optional arguments)
import json
import sys
from enum import Enum
from logging import getLogger
from pathlib import Path
from typing import Optional, cast

import typed_argparse as tap
from tqdm import tqdm

from . import fully_discover, load_image
from .discovery.system import DiscoverySystem
from .exporters.core import ExportContext, get_ref
from .exporters.export_types import exporters
from .exporters.location import get_file_for_thing
from .lieftools import Image
from .ue import native_structs

log = getLogger('unreal_dissection')

class ExportElements(Enum):
    FPackageParams = 'package'
    FClassParams = 'class'
    FStructParams = 'struct'
    FEnumParams = 'enum'
    FFunctionParams = 'function'

    def __str__(self) -> str:
        return str(self.value)

class FormatType(Enum):
    Ion = 'ion'
    Json = 'json'
    Yaml = 'yaml'

    def __str__(self) -> str:
        return str(self.value)

def format_type(value: str) -> FormatType:
    return FormatType(value)

all_elements = list(ExportElements)

class Args(tap.TypedArgs):
    exe: Path = tap.arg(positional=True, help='executable to analyse')
    output: Optional[Path] = tap.arg('-o', help='output directory (should be empty)')
    allow_existing: bool = tap.arg(help='do not complain if output directory is not empty')
    format: FormatType = tap.arg('-f', '--format', default=FormatType.Json, help='select output format')
    filter: Optional[str] = tap.arg('-e', '--filter', help='simple text match filter to apply to artefacts')
    include: list[ExportElements] = tap.arg('-i',
                                            nargs='*',
                                            default=all_elements,
                                            help='types to export (can be repeated; default: all)')
    exclude: list[ExportElements] = tap.arg('-x',
                                            nargs='*',
                                            default=cast(list[ExportElements], []),
                                            help='types to exclude from export (can be repeated; default: none)')


def runner(args: Args):
    log.info('Beginning extraction of %s', args.exe)

    validate_args(args)
    print(args)

    log.info('Loading exe...')
    image = load_image(str(args.exe))
    display_exe_info(image)
    discovery = fully_discover(image)
    discovery.print_summary()

    if args.output:
        perform_export(args, image, discovery)


def display_exe_info(image: Image):
    print('Executable info:')
    keys = ('CompanyName', 'InternalName', 'ProductName', 'ProductVersion')
    longest_key = max(len(key) for key in keys)
    for key in keys:
        display_key = key + ' ' * (longest_key - len(key))
        print(f'  {display_key} : {image.file_properties.get(key)}')
    print(f'UE version: {image.version_string}')


def validate_args(args: Args):
    # Ensure if the output directory exists that it is empty
    if args.output and not args.allow_existing and args.output.exists():
        # Check there are no non-hidden files
        if any(not p.name.startswith('.') for p in args.output.iterdir()):
            raise ValueError(f'Output directory {args.output} is not empty')

        # Prepare the output directory
        args.output.mkdir(parents=True, exist_ok=True)

    if args.filter:
        args.filter = args.filter.lower()


class UserError(Exception):
    pass


def perform_export(args: Args, image: Image, discovery: DiscoverySystem):
    if not args.output:
        raise UserError('Output directory not specified')

    ctx = ExportContext(image=image, discovery=discovery)

    selected_elements = set(args.include) - set(args.exclude)
    if not selected_elements:
        raise ValueError('No elements selected for export')

    print('Exporting:')
    for element_type in selected_elements:
        element_class = getattr(native_structs, element_type.name)
        element_exporter = exporters[element_class]

        structs = discovery.found_structs_by_type[element_class]

        source = tqdm(
            structs,
            desc=element_type.value.capitalize().ljust(10),
            disable=None,
            file=sys.stdout,
            unit='',
            dynamic_ncols=True,
        )
        if source.disable:
            print(f'  {element_type.value.capitalize()}...')

        for artefact in source:
            struct = artefact.struct
            typename, name = get_ref(struct, ctx)
            if typename != element_type.value:
                raise ValueError(f'Expected {element_type.name}, got {typename}')

            if args.filter and args.filter not in name.lower():
                continue

            data = element_exporter(struct, ctx) # type: ignore

            path = get_file_for_thing(typename, name)
            path = (args.output / path).with_suffix(f'.{args.format.value}')
            path.parent.mkdir(parents=True, exist_ok=True)
            json_text = json.dumps(data, indent=2)
            path.write_text(json_text)

def main():
    try:
        tap.Parser(
            Args,
            prog='unreal_dissection',
            description='Extract type information from Unreal Engine executables.',
        ).bind(runner).run()
    except KeyboardInterrupt:
        print('Interrupted')
