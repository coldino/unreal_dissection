# ruff: noqa: UP007 (Optional is required for typed_argparse to recognise optional arguments)
import importlib.util
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
from .exporters.output import OutputManager
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
    Json = 'json'
    # Ion = 'ion'
    # Yaml = 'yaml'

    def __str__(self) -> str:
        return str(self.value)

def format_type(value: str) -> FormatType:
    return FormatType(value)

all_elements = list(ExportElements)

class Args(tap.TypedArgs):
    exe: Path = tap.arg(positional=True, help='executable to analyse')
    output_dir: Optional[Path] = tap.arg('-o', help='output directory')
    output_archive: Optional[Path] = tap.arg('-a', help='output archive')
    allow_existing: bool = tap.arg(help='do not complain if output exists/not empty')
    format: FormatType = tap.arg('-f', '--format', default=FormatType.Json, help='select output format')
    filter: Optional[str] = tap.arg('-e', '--filter', help='simple text match filter to apply to artefacts')
    include: list[ExportElements] = tap.arg('-i',
                                            nargs='*',
                                            default=all_elements,
                                            help='types to export (multiple allowed; default: all)')
    exclude: list[ExportElements] = tap.arg('-x',
                                            nargs='*',
                                            default=cast(list[ExportElements], []),
                                            help='types to exclude from export (multiple allowed; default: none)')


def runner(args: Args):
    log.info('Beginning extraction of %s', args.exe)

    validate_args(args)

    log.info('Loading exe...')
    image = load_image(str(args.exe))
    display_exe_info(image)
    discovery = fully_discover(image)
    discovery.print_summary()

    if args.output_dir or args.output_archive:
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
    # Can only specify one of output directory or archive file
    if args.output_dir and args.output_archive:
        raise UserError('Cannot specify both output directory and archive')

    # If output directory is specified and exists, it must be empty
    if args.output_dir and args.output_dir.exists():
        # Check it's a directory
        if not args.output_dir.is_dir():
            raise UserError(f'Output path {args.output_dir} is not a directory')

        # Check it contains no non-hidden files, unless overridden
        if not args.allow_existing and any(not p.name.startswith('.') for p in args.output_dir.iterdir()):
            raise UserError(f'Output directory {args.output_dir} is not empty')

    # If output archive is specified, it must be a supported type
    if args.output_archive:
        ext = args.output_archive.suffix.lower()
        match ext:
            case '.zip':
                if not importlib.util.find_spec('zipfile'):
                    raise UserError("Zip format is unavailable because the 'zipfile' module is not installed")
            case '.7z':
                if not importlib.util.find_spec('py7zr'):
                    raise UserError("7zip format is unavailable because the 'py7zr' module is not installed")
            case _:
                raise UserError(f'Output file {args.output_archive} is not a supported archive type')

        # Check it doesn't exist, unless overridden
        if not args.allow_existing and args.output_archive.exists():
            raise UserError(f'Output file {args.output_archive} already exists')

    # Convert filter to lowercase
    if args.filter:
        args.filter = args.filter.lower()


class UserError(Exception):
    pass

def choose_output_manager(args: Args) -> OutputManager:
    if args.output_dir:
        from .exporters.out_dir import DirOutput
        return DirOutput(args.output_dir)

    if args.output_archive:
        ext = args.output_archive.suffix.lower()
        match ext:
            case '.zip':
                from .exporters.out_zip import ZipOutput
                return ZipOutput(args.output_archive)
            case '.7z':
                from .exporters.out_7z import SevenZipOutput
                return SevenZipOutput(args.output_archive)
            case _:
                pass

    raise ValueError('Unable to determine output system')

def perform_export(args: Args, image: Image, discovery: DiscoverySystem):
    ctx = ExportContext(image=image, discovery=discovery)

    selected_elements = set(args.include) - set(args.exclude)
    if not selected_elements:
        raise UserError('No elements selected for export')

    output_manager = choose_output_manager(args)
    with output_manager as output:
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
                path = path.with_suffix(f'.{args.format.value}')
                json_text = json.dumps(data, indent=2)
                output.write_file(json_text, path)

def main():
    try:
        tap.Parser(
            Args,
            prog='unreal_dissection',
            description='Extract type information from Unreal Engine executables.',
        ).bind(runner).run()
    except KeyboardInterrupt:
        print('Interrupted')
