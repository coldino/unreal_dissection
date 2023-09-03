# ruff: noqa: F401
'''
This file exists to simply import all the explorer modules, so that they are registered.
'''
import unreal_dissection.explorer.struct  # type: ignore (PyLance doesn't know)
import unreal_dissection.ue.explorer.functions
import unreal_dissection.ue.explorer.params
import unreal_dissection.ue.explorer.property_params

done = True
