# Unreal Dissector

This project is a Python library and CLI utility that extracts metadata from Unreal Engine 5 game executables without running them.

***Note:*** *This project is very new, will contain bugs, and will not support all games yet.*

It can find all the package/class/enum/struct/function definitions along with their properties. This is intended to assist with decoding assets, which for UE5+ are otherwise lacking the required metadata.

To achieve this various techniques are used from pattern matching to simplistic parsing of compiled code (x64 only). These methods will not be entirely safe from changes to UE's core mechanisms and varying compiler flags, but should be relatively easy to update.

## Extraction

To extract everything from a game executable:
```sh
python -m unreal_dissection -a output.zip PATH_TO_EXE
```
Example output:
```txt
Found 135178 artefacts:
  38378 strings
  150 FPackageParams structs
  1224 FEnumParams structs
  2741 FClassParams structs
  3109 FStructParams structs
  8420 FFunctionParams structs
  6483 FEnumeratorParams structs
  8147 FClassFunctionLinkInfo structs
  44312 PropertyParams structs
  208 FImplementedInterfaceParams structs
  15644 ZConstruct functions
  4340 StaticClass functions
  2022 unparsable functions
Exporting:
Class     : 100%|███████████████████████████████████████████████| 2741/2741 [00:01<00:00, 1851.71/s]
Function  : 100%|███████████████████████████████████████████████| 8420/8420 [00:02<00:00, 3742.77/s]
Enum      : 100%|███████████████████████████████████████████████| 1224/1224 [00:00<00:00, 2672.49/s]
Package   : 100%|█████████████████████████████████████████████████| 150/150 [00:00<00:00, 6818.08/s]
Struct    : 100%|███████████████████████████████████████████████| 3109/3109 [00:01<00:00, 2905.85/s]
```

Note you can get full help on the commandline arguments using:
```sh
python -m unreal_dissection --help
```

To access the data programmatically you can do something like this:
```py
import logging
from unreal_dissection import load_image, fully_discover
from unreal_dissection.ue.native_structs import FPackageParams

logging.basicConfig(level=logging.INFO)
image = load_image('<path to exe>')
discovery = fully_discover(image)

for pkg_artefact in discovery.found_structs_by_type[FPackageParams]:
    pkg_struct = pkg_artefact.struct
    pkg_name = discovery.get_string(pkg_struct.NameUTF8)
    print(f'{pkg_name} @ 0x{pkg_artefact.start_addr:x}')
```

While in theory both Windows and Linux exe's are supported only Windows is tested currently.

Known limitations
* Games split into exe + DLL are not supported
* Only x64 builds are supported

Requirements
* Python 3.12
* Poetry

Note that a development version of `lief` 0.14 is used from their Nightly repository (see [their installation page](https://lief-project.github.io/doc/latest/installation.html) for more info).

## Installation

```txt
pip install git+https://github.com/coldino/unreal_dissection.git#egg=unreal_dissection
```

## Collaboration

This project is setup to use Ruff quite heavily so integration with an editor such as VSCode is recommended.

Get setup:
```sh
poetry install
```

Experimentation via iPython is very handy:
```sh
ipython -i scripts/interactive-setup.py <ue5 exe path>
```

```py
Executable info:
  CompanyName    : Epic Games, Inc.
  InternalName   : Purlovia_UE5
  ProductName    : UnrealGame
  ProductVersion : ++UE5+Release-5.2-CL-26001984
UE version: 5.2.1
INFO:unreal_dissection:Beginning early analysis...
Found 15055 Z_Construct functions and structs
Found and identified 5 UECodeGen_Private::Construct functions
  112 calls to ConstructUPackage @ 0x1419e23b0 (stack size 4296)
  1162 calls to ConstructUEnum @ 0x1419e1ce0 (stack size 1240)
  2587 calls to ConstructUClass @ 0x1419e19e0 (stack size 408)
  3210 calls to ConstructUStruct @ 0x1419e2590 (stack size 968)
  7984 calls to ConstructUFunction @ 0x1419e2080 (stack size 1728)
INFO:unreal_dissection:Performing discovery...
Found 127573 artefacts:
  36617 strings
  112 FPackageParams structs
  1162 FEnumParams structs
  2587 FClassParams structs
  3210 FStructParams structs
  7984 FFunctionParams structs
  6236 FEnumeratorParams structs
  7753 FClassFunctionLinkInfo structs
  42585 PropertyParams structs
  218 FImplementedInterfaceParams structs
  15055 ZConstruct functions
  4041 StaticClass functions
  13 unparsable functions

In [1]: discovery.found_structs_by_type[FStructParams][1045].struct
Out[1]: FStructParams(OuterFunc=5394382128, SuperFunc=0, StructOpsFunc=0, NameUTF8=5443559468, SizeOf=4, AlignOf=4, PropertyArray=5446092680, NumProperties=4, ObjectFlags=<EObjectFlags.Public|MarkAsNative|Transient: 69>, StructFlags=<EStructFlags.NoExport|Atomic|Immutable: 56>)

In [2]: discovery.get_string(_1.NameUTF8)
Out[2]: 'Color'
```

For a better example of how to traverse and pull data from the discovery system see `src/unreal_dissection/exporters/core.py` and `src/unreal_dissection/exporters/export_types.py`.
