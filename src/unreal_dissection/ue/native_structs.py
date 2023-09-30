from typing import Annotated

from dataclasses_struct import field

from ..stream import MemoryStream
from ..struct import DynamicStruct, dcs, structclass
from .native_enums import (
    EArrayPropertyFlags,
    EEnumFlags,
    EFunctionFlags,
    EMapPropertyFlags,
    EObjectFlags,
    EPackageFlags,
    EPropertyFlags,
    EPropertyGenFlags,
    EStructFlags,
    PropertyTypeFull,
)


@structclass
class FPackageParams:
    NameUTF8: dcs.U64 # ptr to utf8 string
    SingletonFuncArrayFn: dcs.U64 # ptr to unknown function
    NumSingletons: dcs.I32
    PackageFlags: Annotated[EPackageFlags, field.UnsignedIntField(4)] # dcs.U32
    BodyCRC: dcs.U32
    DeclarationsCRC: dcs.U32

@structclass
class FClassParams:
    ClassNoRegisterFunc: dcs.U64 # ptr to <cls>::StaticClass function
    ClassConfigNameUTF8: dcs.U64 # ptr to utf8 string
    CppClassInfo: dcs.U64 # ptr to FCppClassInfo
    DependencySingletonFuncArray: dcs.U64 # ptr to ptr array
    FunctionLinkArray: dcs.U64 # ptr to ptr array
    PropertyArray: dcs.U64 # ptr to ptr array (::PropPointers)
    ImplementedInterfaceArray: dcs.U64 # ptr to ptr array of FImplementedInterfaceParams
    NumDependencySingletons: dcs.I32
    NumFunctions: dcs.I32
    NumProperties: dcs.I32
    NumImplementedInterfaces: dcs.I32
    ClassFlags: dcs.U32

@structclass
class FStructParams:
    OuterFunc: dcs.U64 # ptr to Z_Construct_XXX function?
    SuperFunc: dcs.U64 # ptr to Z_Construct_XXX function?
    StructOpsFunc: dcs.U64 # ptr to another function
    NameUTF8: dcs.U64 # ptr to name
    SizeOf: dcs.U64
    AlignOf: dcs.U64
    PropertyArray: dcs.U64 # ptr to ptr array
    NumProperties: dcs.I32
    ObjectFlags: Annotated[EObjectFlags, field.UnsignedIntField(4)] # dcs.U32
    StructFlags: Annotated[EStructFlags, field.UnsignedIntField(4)] # dcs.U32

@structclass
class FEnumParams:
    OuterFunc: dcs.U64 # ptr to Z_Construct_XXX function
    DisplayNameFn: dcs.U64 # ptr to function that gets a display name
    NameUTF8: dcs.U64 # ptr to name
    CppTypeUTF8: dcs.U64 # ptr to cpp type name
    EnumeratorParams: dcs.U64 # ptr to ptr array
    NumEnumerators: dcs.I32
    ObjectFlags: Annotated[EObjectFlags, field.UnsignedIntField(4)] # dcs.U64
    EnumFlags: Annotated[EEnumFlags, field.UnsignedIntField(4)] # dcs.U64
    CppForm: dcs.U8

@structclass
class FFunctionParams:
    OuterFunc: dcs.U64 # ptr to Z_Construct_XXX function
    SuperFunc: dcs.U64 # ptr to Z_Construct_XXX function
    NameUTF8: dcs.U64 # ptr to name
    OwningClassName: dcs.U64 # ptr to utf8 name
    DelegateName: dcs.U64 # ptr to utf8 name
    StructureSize: dcs.U64
    PropertyArray: dcs.U64 # ptr to ptr array
    NumProperties: dcs.I32
    ObjectFlags: Annotated[EObjectFlags, field.UnsignedIntField(4)] # dcs.U32
    FunctionFlags: Annotated[EFunctionFlags, field.UnsignedIntField(4)] # dcs.U32
    RPCId: dcs.U16
    RPCResponseId: dcs.U16

@structclass
class FEnumeratorParams:
    NameUTF8: dcs.U64
    Value: dcs.I64

@structclass
class FImplementedInterfaceParams:
    ClassFunc: dcs.U64 # ptr to Z_Construct_UClass_XXX_NoRegister function
    Offset: dcs.I32
    bImplementedByK2: dcs.Bool  # noqa: N815

@structclass
class FClassFunctionLinkInfo:
    CreateFuncPtr: dcs.U64 # ptr to Z_Construct_UFunction_XXX function
    FuncNameUTF8: dcs.U64 # ptr to name


class PropertyParams(DynamicStruct):
    def deserialize(self, stream: MemoryStream) -> None:
        self.NameUTF8_ptr = stream.u64()
        self.RepNotifyFuncUTF8_ptr = stream.u64()
        self.PropertyFlags = EPropertyFlags(stream.u64())
        self.Flags = PropertyTypeFull(stream.u32())
        self.ObjectFlags = EObjectFlags(stream.u32())
        self.ArrayDim = stream.s32()

        # For some reason a couple of types don't have an offset
        if self.Flags.value != EPropertyGenFlags.Bool:
            self.Offset = stream.u32()

        # Handle extra values on known types
        match self.Flags.value:
            case EPropertyGenFlags.Array:
                self.ArrayFlags = EArrayPropertyFlags(stream.u32())
            case EPropertyGenFlags.Bool:
                self.ElementSize = stream.u32()
                self.SizeOfOuter = stream.u64()
                self.SetBitFunc_ptr = stream.u64()
            case EPropertyGenFlags.Byte | EPropertyGenFlags.Enum:
                self.EnumFunc_ptr = stream.u64()
            case EPropertyGenFlags.Class:
                self.MetaClassFunc_ptr = stream.u64()
                self.ClassFunc_ptr = stream.u64()
            case EPropertyGenFlags.Delegate:
                self.SignatureFunctionFunc_ptr = stream.u64()
            case EPropertyGenFlags.FieldPath:
                self.PropertyClassFunc_ptr = stream.u64()
            case EPropertyGenFlags.Interface:
                self.InterfaceClassFunc_ptr = stream.u64()
            case EPropertyGenFlags.Map:
                self.MapFlags = EMapPropertyFlags(stream.u32())
            case EPropertyGenFlags.InlineMulticastDelegate | EPropertyGenFlags.SparseMulticastDelegate:
                self.SignatureFunctionFunc_ptr = stream.u64()
            case EPropertyGenFlags.Object | EPropertyGenFlags.WeakObject | EPropertyGenFlags.LazyObject | EPropertyGenFlags.SoftObject:  # noqa: E501
                self.ClassFunc_ptr = stream.u64()
            case EPropertyGenFlags.SoftClass:
                self.MetaClassFunc_ptr = stream.u64()
            case EPropertyGenFlags.Struct:
                self.ScriptStructFunc_ptr = stream.u64()
            case _:
                pass # TODO: Check which other cases need to be handled

