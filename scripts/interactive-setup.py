# ruff: noqa
from logging import INFO, basicConfig
basicConfig(level=INFO)

from unreal_dissection import fully_discover, load_image
image = load_image(r"E:\Data\purlovia\pre-asa-testing\2023_Sep06_Windows_Shipping_NoPAK_Unversioned\Purlovia_UE5\Binaries\Win64\Purlovia_UE5-Win64-Shipping.exe")
discovery = fully_discover(image)
