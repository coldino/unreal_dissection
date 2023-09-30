# Unreal Dissector

This project is a Python library that extracts metadata from Unreal Engine game executables without running them.

***Note:*** *This project is very new, will contain bugs, and will not support all games yet.*

It can find all the package/class/enum/struct/function definitions along with their properties. This is intended to assist with decoding assets, which for UE5+ are otherwise lacking the required metadata.

To achieve this various techniques are used from pattern matching to simplistic parsing of compiled code (x64 only). These methods will not be entirely safe from changes to UE's core mechanisms, but should be relatively easy to update when this happens.

To see it in action you can run it directly:
```sh
python -m unreal_dissection PATH_TO_EXE
```
Example output:
```txt
Found 140244 artefacts:
  40634 strings
  139 FPackageParams structs
  1287 FEnumParams structs
  2800 FClassParams structs
  3209 FStructParams structs
  9304 FFunctionParams structs
  7517 FEnumeratorParams structs
  46652 DynamicPropertyParams structs
  8819 FClassFunctionLinkInfo structs
  208 FImplementedInterfaceParams structs
  16867 ZConstruct functions
  2808 StaticClass functions
```

To access the data you'll need to access it from Python, for example:
```py
import logging
from unreal_dissection import load_image, fully_discover
from unreal_dissection.ue.native_structs import FPackageParams

logging.basicConfig(level=logging.INFO)
image = load_image('<path to exe>')
discovery = fully_discover(image)

for pkg_artefact in discovery.found_structs_by_type[FPackageParams]:
    pkg_struct = pkg_artefact.struct
    pkg_name = discovery.found_strings[pkg_struct.NameUTF8].string
    print(f'{pkg_name} @ 0x{pkg_artefact.start_addr:x}')
```

While in theory both Windows and Linux exe's are supported only Windows is tested currently.

Known limitations
* Games split into exe + DLL are not supported
* Only 64-bit builds are supported

Requirements
* Python 3.12, available as release candidate at the time of writing
* Poetry
* A development version of `lief` from their Nightly repository (see [their installation page](https://lief-project.github.io/doc/latest/installation.html) for more info)

## Installation

```txt
pip install git+https://github.com/coldino/unreal-dissection.git#egg=unreal_dissection
```
