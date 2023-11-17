# ruff: noqa: E402,I001,F401,Q000,E501,INP001,F403,F405
# pyright: basic

#%%
import sys
from pathlib import Path
from logging import INFO, basicConfig

basicConfig(level=INFO)

from unreal_dissection import fully_discover, load_image
from unreal_dissection.cli import display_exe_info
from unreal_dissection.ue.functions import *
from unreal_dissection.exporters.core import *
from unreal_dissection.ue.native_structs import *
from unreal_dissection.exporters.export_types import exporters

#%%
filename = sys.argv[-1]
if not Path(filename).exists():
    print(f"File {filename} does not exist")
    sys.exit(1)

#%%
image = load_image(filename)
display_exe_info(image)
discovery = fully_discover(image)
discovery.print_summary()
ctx = ExportContext(image=image, discovery=discovery)

# %%
