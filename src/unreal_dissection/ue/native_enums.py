
from enum import CONTINUOUS, STRICT, UNIQUE, Enum, IntFlag, verify


@verify(CONTINUOUS, UNIQUE)
class EPropertyGenFlags(Enum, boundary=STRICT):
    Byte = 0x00 # FBytePropertyParams
    Int8 = 0x01
    Int16 = 0x02
    Int = 0x03
    Int64 = 0x04
    UInt16 = 0x05
    UInt32 = 0x06
    UInt64 = 0x07
    UnsizedInt = 0x08 # ?
    UnsizedUInt = 0x09 # ?
    Float = 0x0a
    Double = 0x0b
    Bool = 0x0c
    SoftClass = 0x0d
    WeakObject = 0x0e
    LazyObject = 0x0f
    SoftObject = 0x10
    Class = 0x11
    Object = 0x12
    Interface = 0x13
    Name = 0x14
    Str = 0x15
    Array = 0x16 # FArrayPropertyParams
    Map = 0x17
    Set = 0x18
    Struct = 0x19 # FStructPropertyParams
    Delegate = 0x1a
    InlineMulticastDelegate = 0x1b
    SparseMulticastDelegate = 0x1c
    Text = 0x1d
    Enum = 0x1e # FEnumPropertyParams
    FieldPath = 0x1f
    LargeWorldCoordinatesReal = 0x20

class EPropertyTypeFlags(IntFlag):
    ObjectPtr = 0x40 # duplicated in symbols
    NativeBool = 0x40 # duplicated in symbols

class PropertyTypeFull:
    def __init__(self, value: int):
        self.value = EPropertyGenFlags(value & 0x3f)
        self.flags = EPropertyTypeFlags(value & ~0x3f)

    def __str__(self):
        if self.flags > 0:
            return f'{self.value} | {self.flags.name}'
        return f'{self.value}'

    def __repr__(self):
        if self.flags > 0:
            return f'{self.value} | {self.flags!s}'
        return str(self.value)

@verify(UNIQUE)
class EPropertyFlags(IntFlag, boundary=STRICT):
    NoFlags = 0
    Edit = (1 << 0)
    ConstParm = (1 << 1)
    BlueprintVisible = (1 << 2)
    ExportObject = (1 << 3)
    BlueprintReadOnly = (1 << 4)
    Net = (1 << 5)
    EditFixedSize = (1 << 6)
    Parm = (1 << 7)
    OutParm = (1 << 8)
    ZeroConstructor = (1 << 9)
    ReturnParm = (1 << 10)
    DisableEditOnTemplate = (1 << 11)
    Transient = (1 << 13)
    Config = (1 << 14)
    DisableEditOnInstance = (1 << 16)
    EditConst = (1 << 17)
    GlobalConfig = (1 << 18)
    InstancedReference = (1 << 19)
    DuplicateTransient = (1 << 21)
    SaveGame = (1 << 24)
    NoClear = (1 << 25)
    ReferenceParm = (1 << 27)
    BlueprintAssignable = (1 << 28)
    Deprecated = (1 << 29)
    IsPlainOldData = (1 << 30)
    RepSkip = (1 << 31)
    RepNotify = (1 << 32)
    Interp = (1 << 33)
    NonTransactional = (1 << 34)
    EditorOnly = (1 << 35)
    NoDestructor = (1 << 36)
    AutoWeak = (1 << 38)
    ContainsInstancedReference = (1 << 39)
    AssetRegistrySearchable = (1 << 40)
    SimpleDisplay = (1 << 41)
    AdvancedDisplay = (1 << 42)
    Protected = (1 << 43)
    BlueprintCallable = (1 << 44)
    BlueprintAuthorityOnly = (1 << 45)
    TextExportTransient = (1 << 46)
    NonPIEDuplicateTransient = (1 << 47)
    ExposeOnSpawn = (1 << 48)
    PersistentInstance = (1 << 49)
    UObjectWrapper = (1 << 50)
    HasGetValueTypeHash = (1 << 51)
    NativeAccessSpecifierPublic = (1 << 52)
    NativeAccessSpecifierProtected = (1 << 53)
    NativeAccessSpecifierPrivate = (1 << 54)
    SkipSerialization = (1 << 55)

@verify(CONTINUOUS, UNIQUE)
class EObjectFlags(IntFlag, boundary=STRICT):
    NoFlags = 0
    Public = (1 << 0)
    Standalone = (1 << 1)
    MarkAsNative = (1 << 2)
    Transactional = (1 << 3)
    ClassDefaultObject = (1 << 4)
    ArchetypeObject = (1 << 5)
    Transient = (1 << 6)
    MarkAsRootSet = (1 << 7)
    TagGarbageTemp = (1 << 8)
    NeedInitialization = (1 << 9)
    NeedLoad = (1 << 10)
    KeepForCooker = (1 << 11)
    NeedPostLoad = (1 << 12)
    NeedPostLoadSubobjects = (1 << 13)
    NewerVersionExists = (1 << 14)
    BeginDestroyed = (1 << 15)
    FinishDestroyed = (1 << 16)
    BeingRegenerated = (1 << 17)
    DefaultSubObject = (1 << 18)
    WasLoaded = (1 << 19)
    TextExportTransient = (1 << 20)
    LoadCompleted = (1 << 21)
    InheritableComponentTemplate = (1 << 22)
    DuplicateTransient = (1 << 23)
    StrongRefOnFrame = (1 << 24)
    NonPIEDuplicateTransient = (1 << 25)
    Dynamic = (1 << 26)
    WillBeLoaded = (1 << 27)
    HasExternalPackage = (1 << 28)
    PendingKill = (1 << 29)
    Garbage = (1 << 30)
    AllocatedInSharedPage = (1 << 31)


@verify(UNIQUE)
class EPackageFlags(IntFlag, boundary=STRICT):
    none						= 0x00000000
    NewlyCreated				= 0x00000001
    ClientOptional				= 0x00000002
    ServerSideOnly				= 0x00000004
    CompiledIn					= 0x00000010
    ForDiffing					= 0x00000020
    EditorOnly					= 0x00000040
    Developer					= 0x00000080
    UncookedOnly				= 0x00000100
    Cooked						= 0x00000200
    ContainsNoAsset				= 0x00000400
    NotExternallyReferenceable  = 0x00000800
    UnversionedProperties		= 0x00002000
    ContainsMapData				= 0x00004000
    IsSaving					= 0x00008000
    Compiling					= 0x00010000
    ContainsMap					= 0x00020000
    RequiresLocalizationGather	= 0x00040000
    PlayInEditor				= 0x00100000
    ContainsScript				= 0x00200000
    DisallowExport				= 0x00400000
    CookGenerated				= 0x08000000
    DynamicImports				= 0x10000000
    RuntimeGenerated			= 0x20000000
    ReloadingForCooker			= 0x40000000
    FilterEditorOnly			= 0x80000000
    """
    TransientFlags				= NewlyCreated | IsSaving | ReloadingForCooker,
    """


@verify(CONTINUOUS, UNIQUE)
class EClassFlags(IntFlag, boundary=STRICT):
    NoFlags = 0
    Abstract = (1 << 0)
    DefaultConfig = (1 << 1)
    Config = (1 << 2)
    Transient = (1 << 3)
    Optional = (1 << 4)
    MatchedSerializers = (1 << 5)
    ProjectUserConfig = (1 << 6)
    Native = (1 << 7)
    NoExport = (1 << 8)
    NotPlaceable = (1 << 9)
    PerObjectConfig = (1 << 10)
    ReplicationDataIsSetUp = (1 << 11)
    EditInlineNew = (1 << 12)
    CollapseCategories = (1 << 13)
    Interface = (1 << 14)
    CustomConstructor = (1 << 15)
    Const = (1 << 16)
    NeedsDeferredDependencyLoading = (1 << 17)
    CompiledFromBlueprint = (1 << 18)
    MinimalAPI = (1 << 19)
    RequiredAPI = (1 << 20)
    DefaultToInstanced = (1 << 21)
    TokenStreamAssembled = (1 << 22)
    HasInstancedReference = (1 << 23)
    Hidden = (1 << 24)
    Deprecated = (1 << 25)
    HideDropDown = (1 << 26)
    GlobalUserConfig = (1 << 27)
    Intrinsic = (1 << 28)
    Constructed = (1 << 29)
    ConfigDoNotCheckDefaults = (1 << 30)
    NewerVersionExists = (1 << 31)


@verify(UNIQUE)
class EStructFlags(IntFlag, boundary=STRICT):
    NoFlags = 0x00000000
    Native = 0x00000001
    IdenticalNative = 0x00000002
    HasInstancedReference = 0x00000004
    NoExport = 0x00000008
    Atomic = 0x00000010
    Immutable = 0x00000020
    AddStructReferencedObjects = 0x00000040
    RequiredAPI = 0x00000200
    NetSerializeNative = 0x00000400
    SerializeNative = 0x00000800
    CopyNative = 0x00001000
    IsPlainOldData = 0x00002000
    NoDestructor = 0x00004000
    ZeroConstructor = 0x00008000
    ExportTextItemNative = 0x00010000
    ImportTextItemNative = 0x00020000
    PostSerializeNative = 0x00040000
    SerializeFromMismatchedTag = 0x00080000
    NetDeltaSerializeNative = 0x00100000
    PostScriptConstruct = 0x00200000
    NetSharedSerialization = 0x00400000
    Trashed = 0x00800000
    NewerVersionExists = 0x01000000
    CanEditChange = 0x02000000

    """
    Inherit			    = HasInstancedReference + Atomic,
    ComputedFlags		= NetDeltaSerializeNative + NetSerializeNative + SerializeNative + PostSerializeNative + CopyNative +
                        IsPlainOldData + NoDestructor + ZeroConstructor + IdenticalNative + AddStructReferencedObjects +
                        ExportTextItemNative + ImportTextItemNative + SerializeFromMismatchedTag + PostScriptConstruct +
                        NetSharedSerialization
    """


@verify(CONTINUOUS, UNIQUE)
class EClassCastFlags(IntFlag, boundary=STRICT):
    NoFlags = 0
    UField = 0x1
    FInt8Property = 0x2
    UEnum = 0x4
    UStruct = 0x8
    UScriptStruct = 0x10
    UClass = 0x20
    FByteProperty = 0x40
    FIntProperty = 0x80
    FFloatProperty = 0x100
    FUInt64Property = 0x200
    FClassProperty = 0x400
    FUInt32Property = 0x800
    FInterfaceProperty = 0x1000
    FNameProperty = 0x2000
    FStrProperty = 0x4000
    FProperty = 0x8000
    FObjectProperty = 0x10000
    FBoolProperty = 0x20000
    FUInt16Property = 0x40000
    UFunction = 0x80000
    FStructProperty = 0x100000
    FArrayProperty = 0x200000
    FInt64Property = 0x400000
    FDelegateProperty = 0x800000
    FNumericProperty = 0x1000000
    FMulticastDelegateProperty = 0x2000000
    FObjectPropertyBase = 0x4000000
    FWeakObjectProperty = 0x8000000
    FLazyObjectProperty = 0x10000000
    FSoftObjectProperty = 0x20000000
    FTextProperty = 0x40000000
    FInt16Property = 0x80000000
    FDoubleProperty = 0x100000000
    FSoftClassProperty = 0x200000000
    UPackage = 0x400000000
    ULevel = 0x800000000
    AActor = 0x1000000000
    APlayerController = 0x2000000000
    APawn = 0x4000000000
    USceneComponent = 0x8000000000
    UPrimitiveComponent = 0x10000000000
    USkinnedMeshComponent = 0x20000000000
    USkeletalMeshComponent = 0x40000000000
    UBlueprint = 0x80000000000
    UDelegateFunction = 0x100000000000
    UStaticMeshComponent = 0x200000000000
    FMapProperty = 0x400000000000
    FSetProperty = 0x800000000000
    FEnumProperty = 0x1000000000000
    USparseDelegateFunction = 0x2000000000000
    FMulticastInlineDelegateProperty = 0x4000000000000
    FMulticastSparseDelegateProperty = 0x8000000000000
    FFieldPathProperty = 0x10000000000000
    FObjectPtrProperty = 0x20000000000000
    FClassPtrProperty = 0x40000000000000
    FLargeWorldCoordinatesRealProperty = 0x80000000000000

@verify(CONTINUOUS, UNIQUE)
class EArrayPropertyFlags(IntFlag, boundary=STRICT):
    none = 0
    UsesMemoryImageAllocator = 0x1

@verify(CONTINUOUS, UNIQUE)
class EMapPropertyFlags(IntFlag, boundary=STRICT):
    none = 0
    UsesMemoryImageAllocator = 0x1

@verify(CONTINUOUS, UNIQUE)
class EEnumFlags(IntFlag, boundary=STRICT):
    none = 0
    Flags = 0x1
    NewerVersionExists = 0x2

@verify(UNIQUE)
class EFunctionFlags(IntFlag, boundary=STRICT):
    none = 0
    Final = 0x1
    RequiredAPI = 0x2
    BlueprintAuthorityOnly = 0x4
    BlueprintCosmetic = 0x8
    Net = 0x40
    NetReliable = 0x80
    NetRequest = 0x100
    Exec = 0x200
    Native = 0x400
    Event = 0x800
    NetResponse = 0x1000
    Static = 0x2000
    NetMulticast = 0x4000
    UbergraphFunction = 0x8000
    MulticastDelegate = 0x10000
    Public = 0x20000
    Private = 0x40000
    Protected = 0x80000
    Delegate = 0x100000
    NetServer = 0x200000
    HasOutParms = 0x400000
    HasDefaults = 0x800000
    NetClient = 0x1000000
    DLLImport = 0x2000000
    BlueprintCallable = 0x4000000
    BlueprintEvent = 0x8000000
    BlueprintPure = 0x10000000
    EditorOnly = 0x20000000
    Const = 0x40000000
    NetValidate = 0x80000000
    AllFlags = 0xFFFFFFFF
