from collections.abc import Iterable
from typing import Any

from ..discovery.struct import StructArtefact
from ..ue.functions import StaticClassFnArtefact, ZConstructFnArtefact
from ..ue.native_enums import EPropertyGenFlags
from ..ue.native_structs import (
    FClassFunctionLinkInfo,
    FClassParams,
    FEnumeratorParams,
    FEnumParams,
    FFunctionParams,
    FPackageParams,
    FStructParams,
    PropertyParams,
)
from .core import ExportContext, export_array, export_ptr_array, get_blueprint_path


def _without_name(obj: dict[str, Any]) -> dict[str, Any]:
    del obj['name']
    return obj

def _parse_property_list(properties: list[PropertyParams], ctx: ExportContext) -> Iterable[dict[str, Any]]:
    # Properties should be parsed in reverse
    # Special cases like arrays and maps are followed by their element types

    output: list[dict[str, Any]] = []
    inputs = iter(reversed(properties))

    while True:
        prop = next(inputs, None)
        if prop is None:
            break

        match prop.Flags.value:
            case EPropertyGenFlags.Array:
                # Next property is the inner element type
                element_prop = next(inputs)
                export = export_PropertyParams(prop, ctx)
                export['type'] = prop.Flags.value.name
                export['array_element'] = _without_name(export_PropertyParams(element_prop, ctx))
                export['array_dim'] = prop.ArrayDim
                output.append(export)
            case EPropertyGenFlags.Map:
                # Next two properties are the key and value types
                key_prop = next(inputs)
                value_prop = next(inputs)
                export = export_PropertyParams(prop, ctx)
                export['type'] = prop.Flags.value.name
                export['map_key'] = _without_name(export_PropertyParams(key_prop, ctx))
                export['map_value'] = _without_name(export_PropertyParams(value_prop, ctx))
                output.append(export)
            case EPropertyGenFlags.Set:
                # Next property is the inner element type
                element_prop = next(inputs)
                export = export_PropertyParams(prop, ctx)
                export['type'] = prop.Flags.value.name
                export['set_element'] = _without_name(export_PropertyParams(element_prop, ctx))
                output.append(export)
            case EPropertyGenFlags.Enum:
                # Next property is the enum type
                enum_prop = next(inputs)
                export = export_PropertyParams(prop, ctx)
                export['type'] = prop.Flags.value.name
                export['enum_type'] = _without_name(export_PropertyParams(enum_prop, ctx))
                output.append(export)
            case _:
                export = export_PropertyParams(prop, ctx)
                output.append(export)

    return reversed(output)


def export_FPackageParams(struct: FPackageParams, ctx: ExportContext) -> dict[str, Any]:  # noqa: N802
    return {
        'name': ctx.discovery.get_string(struct.NameUTF8),
        'flags': struct.PackageFlags.value,

        # Skipped:

        # Singletons: export_array(artefact.NumSingletons, artefact.SingletonFuncArrayFn, discovery, ???),
        # BodyCRC: artefact.BodyCRC,
        # DeclarationsCRC: artefact.DeclarationsCRC,
    }

def export_FClassFunctionLinkInfo(struct: FClassFunctionLinkInfo, ctx: ExportContext) -> dict[str, Any]:  # noqa: N802
    return {
        'name': ctx.discovery.get_string(struct.FuncNameUTF8),
        'function': get_blueprint_path(ctx.discovery.found[struct.CreateFuncPtr], ctx),
    }

def export_FClassParams(struct: FClassParams, ctx: ExportContext) -> dict[str, Any]:  # noqa: N802
    reg_fn = ctx.discovery.found[struct.ClassNoRegisterFunc]
    if not isinstance(reg_fn, StaticClassFnArtefact):
        raise TypeError(f'Expected StaticClassFnArtefact, got {reg_fn.__class__.__name__}')

    deps = export_ptr_array(struct.NumDependencySingletons, struct.DependencySingletonFuncArray, ctx, ZConstructFnArtefact)
    deps = [ctx.discovery.found[dep.params_struct_ptr] for dep in deps]

    props = export_ptr_array(struct.NumProperties, struct.PropertyArray, ctx, StructArtefact) # type: ignore
    props: list[PropertyParams] = [prop.struct for prop in props] # type: ignore

    # Interfaces disabled currently due to a bug in the parser
    # interfaces = export_ptr_array(struct.NumImplementedInterfaces, struct.ImplementedInterfaceArray, ctx, StaticClassFnArtefact)

    functions = export_array(struct.NumFunctions, struct.FunctionLinkArray, ctx, FClassFunctionLinkInfo)

    return {
        'name': ctx.discovery.get_string(reg_fn.name_ptr),
        'ini_name': ctx.discovery.get_string(struct.ClassConfigNameUTF8, default=None),
        'class_info': struct.CppClassInfo,

        'dependencies': tuple(get_blueprint_path(dependency, ctx) for dependency in deps),
        'properties': tuple(_parse_property_list(props, ctx)),
        # 'interfaces': tuple(get_blueprint_path(interface_ptr, ctx) for interface_ptr in interfaces),
        'functions': tuple(export_FClassFunctionLinkInfo(fn, ctx) for fn in functions),
    }

def export_FEnumeratorParams(enum: FEnumeratorParams, ctx: ExportContext) -> dict[str, Any]:  # noqa: N802
    return {
        'value': enum.Value,
        'name': ctx.discovery.get_string(enum.NameUTF8),
    }

def export_FEnumParams(enum: FEnumParams, ctx: ExportContext) -> dict[str, Any]:  # noqa: N802
    params = export_array(enum.NumEnumerators, enum.EnumeratorParams, ctx, FEnumeratorParams)

    return {
        'name': ctx.discovery.get_string(enum.NameUTF8),
        'cpp_type_name': ctx.discovery.get_string(enum.CppTypeUTF8),
        'object_flags': enum.ObjectFlags.value,
        'enum_flags': enum.EnumFlags.value,
        'cpp_form': enum.CppForm,
        'params': tuple(export_FEnumeratorParams(param, ctx) for param in params),
    }

def export_PropertyParams(struct: PropertyParams, ctx: ExportContext) -> dict[str, Any]:  # noqa: N802
    output = {
        'name': ctx.discovery.get_string(struct.NameUTF8_ptr),
        'type': struct.Flags.value.name,
        'property_flags': struct.PropertyFlags.value,
        'object_flags': struct.ObjectFlags.value,
    }
    if struct.ArrayDim != 1:
        output['array_dim'] = struct.ArrayDim

    notify_func_name = ctx.discovery.get_string(struct.RepNotifyFuncUTF8_ptr, default=None)
    if notify_func_name:
        output['notify_func_name'] = notify_func_name

    match struct.Flags.value:
        case EPropertyGenFlags.Array:
            output['array_flags'] = struct.ArrayFlags.value
        case EPropertyGenFlags.Bool:
            output['bool_element_size'] = struct.ElementSize
            output['bool_size_of_outer'] = struct.SizeOfOuter
        case EPropertyGenFlags.Byte | EPropertyGenFlags.Enum:
            if struct.EnumFunc_ptr:
                output['enum_name'] = get_blueprint_path(ctx.discovery.found[struct.EnumFunc_ptr], ctx)
        case EPropertyGenFlags.Class:
            if struct.MetaClassFunc_ptr:
                output['class_meta'] = get_blueprint_path(ctx.discovery.found[struct.MetaClassFunc_ptr], ctx)
            if struct.ClassFunc_ptr:
                output['class'] = get_blueprint_path(ctx.discovery.found[struct.ClassFunc_ptr], ctx)
        case EPropertyGenFlags.Delegate:
            if struct.SignatureFunctionFunc_ptr:
                output['delegate_type'] = get_blueprint_path(ctx.discovery.found[struct.SignatureFunctionFunc_ptr], ctx)
        case EPropertyGenFlags.FieldPath:
            pass
        case EPropertyGenFlags.Interface:
            if struct.InterfaceClassFunc_ptr:
                output['interface_class'] = get_blueprint_path(ctx.discovery.found[struct.InterfaceClassFunc_ptr], ctx)
        case EPropertyGenFlags.Map:
            output['map_flags'] = struct.MapFlags.value
        case EPropertyGenFlags.InlineMulticastDelegate | EPropertyGenFlags.SparseMulticastDelegate:
            if struct.SignatureFunctionFunc_ptr:
                output['delegate_type'] = get_blueprint_path(ctx.discovery.found[struct.SignatureFunctionFunc_ptr], ctx)
        case EPropertyGenFlags.Object | EPropertyGenFlags.WeakObject | EPropertyGenFlags.LazyObject | EPropertyGenFlags.SoftObject:  # noqa: E501
            if struct.ClassFunc_ptr:
                output['object_ref'] = get_blueprint_path(ctx.discovery.found[struct.ClassFunc_ptr], ctx)
        case EPropertyGenFlags.SoftClass:
            if struct.MetaClassFunc_ptr:
                output['class_meta_class'] = get_blueprint_path(ctx.discovery.found[struct.MetaClassFunc_ptr], ctx)
        case EPropertyGenFlags.Struct:
            if struct.ScriptStructFunc_ptr:
                output['struct'] = get_blueprint_path(ctx.discovery.found[struct.ScriptStructFunc_ptr], ctx)
        case _:
            pass

    return output

def export_FStructParams(struct: FStructParams, ctx: ExportContext) -> dict[str, Any]:  # noqa: N802
    props = export_ptr_array(struct.NumProperties, struct.PropertyArray, ctx, StructArtefact) # type: ignore
    props: list[PropertyParams] = [prop.struct for prop in props] # type: ignore

    output: dict[str, Any] = {
        'name': ctx.discovery.get_string(struct.NameUTF8),
        'object_flags': struct.ObjectFlags.value,
        'struct_flags': struct.StructFlags.value,
        'native_size': struct.SizeOf,
        'native_align': struct.AlignOf,
        'properties': tuple(_parse_property_list(props, ctx)),
    }

    if struct.SuperFunc:
        output['super'] = get_blueprint_path(ctx.discovery.found[struct.SuperFunc], ctx)

    # Skipped:
    # OuterFunc

    return output

def export_FFunctionParams(struct: FFunctionParams, ctx: ExportContext) -> dict[str, Any]: # noqa: N802
    props = export_ptr_array(struct.NumProperties, struct.PropertyArray, ctx, StructArtefact) # type: ignore
    props: list[PropertyParams] = [prop.struct for prop in props] # type: ignore

    output: dict[str, Any] = {
        'name': ctx.discovery.get_string(struct.NameUTF8),
        'object_flags': struct.ObjectFlags.value,
        'function_flags': struct.FunctionFlags.value,
        'rpc_id': struct.RPCId,
        'rpc_response_id': struct.RPCResponseId,
        'properties': tuple(_parse_property_list(props, ctx)),
    }

    if struct.DelegateName:
        output['delegate_name'] = ctx.discovery.get_string(struct.DelegateName)
    if struct.SuperFunc:
        output['super'] = get_blueprint_path(ctx.discovery.found[struct.SuperFunc], ctx)

    # Skipped:
    # OuterFunc

    return output

exporters = {
    FPackageParams: export_FPackageParams,
    FStructParams: export_FStructParams,
    FClassParams: export_FClassParams,
    FEnumParams: export_FEnumParams,
    FFunctionParams: export_FFunctionParams,
    FEnumeratorParams: export_FEnumeratorParams,
    FClassFunctionLinkInfo: export_FClassFunctionLinkInfo,
    PropertyParams: export_PropertyParams,
}

__all__ = (
    'exporters',
)
