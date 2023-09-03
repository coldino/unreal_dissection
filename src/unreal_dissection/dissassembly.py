from collections import defaultdict
from dataclasses import dataclass
from logging import getLogger
from typing import Generator

from iced_x86 import Code, Decoder, DecoderOptions, Formatter, FormatterSyntax, \
    Instruction, InstructionInfo, InstructionInfoFactory, Register, Register_

from .stream import MemoryStream

log = getLogger(__name__)

DBG = False
# DBG = True

info_factory = InstructionInfoFactory()
formatter = Formatter(FormatterSyntax.INTEL)
formatter.digit_separator = "_"
formatter.first_operand_char_index = 10


def print_instruction(instr: Instruction):
    # code = code_to_string(instr.code)
    # regs = [used_reg_to_string(r) for r in info_factory.info(instr).used_registers()]
    print(f'{instr.ip:010x} {formatter.format(instr)}')  #  ({code}) , uses={regs}


class CodeGrabber:
    def __init__(self, stream: MemoryStream, size:int=0x1000):
        self.size = size
        self.stream = stream
        start = self.stream.addr

        if DBG: print(f'CodeGrabber: {start:010x} (+{size})')
        self.decoder = self._init_decoder()

    @property
    def addr(self) -> int:
        return self.decoder.ip

    def next_info(self) -> tuple[Instruction, InstructionInfo]:
        inst: Instruction = next(self.decoder)  # type: ignore
        info = info_factory.info(inst)
        if DBG: print_instruction(inst)
        return inst, info

    def next_inst(self) -> Instruction:
        inst: Instruction = next(self.decoder)  # type: ignore
        if DBG: print_instruction(inst)
        return inst

    def backup(self, inst: Instruction):
        self.decoder.position -= inst.len

    def jump(self, addr: int):
        self.stream.set_addr(addr)
        self.decoder = self._init_decoder()

    def _init_decoder(self):
        data = self.stream.bytes(self.size, peek=True)
        return Decoder(64, bytes(data), DecoderOptions.NONE, self.stream.addr)


@dataclass
class CachedCallResult:
    cache_addr: int
    called_fn_addr: int
    parameters: list[int]


def parse_cached_call(code: CodeGrabber) -> CachedCallResult:
    stack_size, stack_save_reg = parse_fn_prelude(code)

    # Look for cache apparatus first
    inst = code.next_inst()
    if inst.code == Code.CALL_REL32_64:
        # Not a cached call at all - hopefully a redirect to one!
        code.jump(inst.memory_displacement)
        return parse_cached_call(code)
    elif inst.code == Code.MOV_R64_RM64:
        # MOV RAX, [ptr] (cache variable)
        cache_var = inst.memory_displacement
        cache_form = 1

        # TEST RAX, RAX (test if cached)
        inst = code.next_inst()
        assert inst.code == Code.TEST_RM64_R64

        # JNE #? (skip call if already cached)
        inst = code.next_inst()
        assert inst.code in (Code.JNE_REL8_64, Code.JNE_REL32_64)
        ret_label = inst.memory_displacement
        # print(f"ret_label: {ret_label:010x}")
    elif inst.code == Code.CMP_RM64_IMM8:
        # CMP [cache_ptr], #0
        cache_var = inst.memory_displacement
        cache_form = 2

        # JNZ #? (skip call if already cached)
        inst = code.next_inst()
        assert inst.code in (Code.JNE_REL8_64, Code.JNE_REL32_64)
        ret_label = inst.memory_displacement
    else:
        raise AssertionError(f"Unexpected instruction when parsing cached call: {inst.code} @ 0x{inst.ip:x}")

    # Parse the setup and call of the function
    fn_addr, parameters = gather_call_params(code, stack_size, stack_save_reg)

    # MOV RAX, [?] (should be cache_var)
    inst = code.next_inst()
    if inst.code == Code.MOV_R64_RM64:
        if cache_form == 2: assert inst.ip == ret_label
        assert inst.memory_displacement == cache_var

        # ADD RSP, #? (0x28)
        inst = code.next_inst()
        if cache_form == 1: assert inst.ip == ret_label
        assert inst.code == Code.ADD_RM64_IMM8
        assert inst.immediate8 == stack_size

        # RET
        inst = code.next_inst()
        assert inst.code == Code.RETNQ
    else:
        # We have to assume there's some other processing here that we don't care about
        log.warning(f"Unexpected instruction after cached call: {inst.code} @ 0x{inst.ip:x}")

    return CachedCallResult(
        cache_addr=cache_var,
        called_fn_addr=fn_addr,
        parameters=parameters
    )


# Registers that are used for function arguments (others are transferred via stack)
ARG_REGS = [Register.RCX, Register.RDX, Register.R8, Register.R9]


def gather_call_params(code: CodeGrabber,
                       stack_size: int,
                       stack_save_reg: Register_ | None = None,
                       known_regs: dict[Register_, int] | None = None) -> tuple[int, list[int]]:
    '''Dissassemble a function call, returning the parameters and the call address'''

    # Track the state of each register in this section
    # This is needed because optimisers will reuse registers and reorder instructions
    regs: dict[Register_, int] = defaultdict(lambda: 0)
    if known_regs is not None:
        regs.update(known_regs)
    regs[Register.RSP] = 0x1000_0000_0000_0000  # Fake stack bottom
    if stack_save_reg is not None:
        regs[stack_save_reg] = 0x1000_0000_0000_0000 + stack_size  # Fake stack top

    # Collect all of the parameters to the call so we can order them later
    parameters: list[tuple[int, int, int]] = []  # (value, size, offset)
    while True:
        # Read the next call parameter
        inst, info = code.next_info()

        # Terminate on CALL
        if inst.code == Code.CALL_REL32_64:
            break

        # Look for LEA Rx, [#]
        if inst.code == Code.LEA_R64_M:
            value = inst.memory_displacement
            size = inst.memory_displ_size
            reg: Register_ = info.used_registers()[0].register
            regs[reg] = value

            # Is this a stack entry or a direct argument register?
            if reg in ARG_REGS:
                offset = 0xFFFF - ARG_REGS.index(reg)
                if DBG:
                    print(
                        f' -> offset1: 0x{offset:02x} ({formatter.format_register(reg)}) = 0x{value:010x}'
                    )
                parameters.append((value, size, offset))
            else:
                # Should be using RAX
                assert reg == Register.RAX

                # Must be followed by MOV [R11 + #], RAX
                inst, info = code.next_info()
                assert inst.code == Code.MOV_RM64_R64
                assert info.used_memory()[0].base == Register.R11
                assert info.used_registers()[1].register == Register.RAX
                offset = -info.used_memory()[0].displacement_i64
                if DBG: print(f' -> offset2: 0x{offset:02x} = 0x{value:x}')
                parameters.append((value, size, offset))

        # Or MOV qword [R11 + #], #?
        elif inst.code == Code.MOV_RM64_IMM32:
            assert info.used_memory()[0].base == Register.R11
            offset = -info.used_memory()[0].displacement_i64
            value = inst.immediate(1)
            if DBG: print(f' -> offset3: 0x{offset:02x} = qword ptr [R11 + 0x{offset:02x}]')
            parameters.append((value, 8, offset))

        # Or MOV dword [R11 + #], #?
        elif inst.code == Code.MOV_RM32_IMM32:
            if info.used_memory()[0].base == Register.R11:
                offset = -info.used_memory()[0].displacement
                if DBG: print(f' -> offset4: 0x{offset:02x} = dword ptr [R11 - 0x{offset:02x}]')
            elif info.used_memory()[0].base == Register.RSP:
                offset = stack_size - info.used_memory()[0].displacement
                if DBG: print(f' -> offset5: 0x{offset:02x} = dword ptr [RSP + 0x{info.used_memory()[0].displacement:02x}]')
            else:
                raise AssertionError("Unknown MOV when parameter push")
            value = inst.immediate32
            parameters.append((value, 4, offset))

        # Or MOV [Rx + #], Rx (reuse of previous register)
        elif inst.code == Code.MOV_RM64_R64:
            if info.used_memory()[0].base == Register.R11:
                offset = -info.used_memory()[0].displacement_i64
                if DBG: print(f' -> offset6: 0x{offset:02x} = dword ptr [R11 - 0x{offset:02x}]')
            elif info.used_memory()[0].base == Register.RSP:
                offset = stack_size - info.used_memory()[0].displacement_i64
                if DBG: print(f' -> offset7: 0x{offset:02x} = dword ptr [RSP + 0x{info.used_memory()[0].displacement:02x}]')
            else:
                raise AssertionError("Unknown MOV when parameter push")
            value = regs[info.used_registers()[1].register]
            parameters.append((value, 8, offset))

        # Or MOV Rx, #? (simply set a register)
        elif inst.code == Code.MOV_R64_IMM64:
            reg: Register_ = info.used_registers()[0].register
            value = inst.immediate(1)

            # Is this a stack entry or a direct argument register?
            if reg in ARG_REGS:
                offset = 0xFFFF - ARG_REGS.index(reg)
                if DBG:
                    print(
                        f' -> offset8: 0x{offset:02x} ({formatter.format_register(reg)}) = 0x{value:010x}'
                    )
                parameters.append((value, 8, offset))
            else:
                regs[reg] = value

        else:
            raise AssertionError(f"Unknown instruction when parameter push: {inst.code} @ 0x{inst.ip:010x}")

    # We're at the CALL
    fn = inst.memory_displacement

    # Sort the stack/register parameters into call argument order
    parameters.sort(key=lambda x: x[2], reverse=True)
    # for p in parameters:
    #     print(f"    {p[0]:010x} {p[1]:x} {p[2]:x} = {str16_at(code.stream, p[0])}")

    return fn, [param[0] for param in parameters if param[2] >= 0]


def get_fn_stack_size(code: CodeGrabber) -> int:
    inst, info = code.next_info()

    # Optionally skip MOV R11, RSP
    if inst.code == Code.MOV_R64_RM64:
        assert info.used_registers()[1].register == Register.RSP
        inst, info = code.next_info()

    # Skip over PUSHes
    while inst.code == Code.PUSH_R64:
        inst, info = code.next_info()

    # Skip reordered LEA's
    while inst.code == Code.LEA_R64_M:
        inst, info = code.next_info()

    # Handle the form that needs _chkstk: MOV EAX, #?
    if inst.code == Code.MOV_R32_IMM32:
        assert info.used_registers()[0].register == Register.RAX
        stack_size = inst.immediate32

        inst, info = code.next_info()
        # Expect CALL _chkstk
        assert inst.code == Code.CALL_REL32_64

        inst, info = code.next_info()
        # Expect SUB RSP,RAX
        assert inst.code == Code.SUB_R64_RM64
        assert info.used_registers()[0].register == Register.RSP
        assert info.used_registers()[1].register == Register.RAX
        return stack_size

    # Expect SUB RSP, #?
    assert inst.code == Code.SUB_RM64_IMM32
    assert info.used_registers()[0].register == Register.RSP
    return inst.immediate(1)

class UnexpectedInstruction(Exception):
    pass

def parse_fn_prelude(code: CodeGrabber) -> tuple[int, Register_ | None]:
    """Parse a typical function prelude.

    The prelude consists of zero to many jump instructions, followed by a stack setup.

    Returns:
        A CodeGrabber object for the function body, the stack size, and the register used to save the stack ptr.

    """
    stack_size = 0
    stack_save_reg: Register_ | None = None

    # Handle stack setup
    inst, info = code.next_info()

    # MOV R11, RSP (save stack ptr, optional)
    if inst.code == Code.MOV_R64_RM64:
        assert info.used_registers()[1].register == Register.RSP
        stack_save_reg = info.used_registers()[0].register
        inst, info = code.next_info()

    # SUB RSP, #? (local stack size)
    if inst.code == Code.SUB_RM64_IMM8:
        assert info.used_registers()[0].register == Register.RSP
        stack_size = inst.immediate8
    elif inst.code == Code.SUB_RM64_IMM32:
        assert info.used_registers()[0].register == Register.RSP
        stack_size = inst.immediate32
    else:
        raise UnexpectedInstruction(f"Unexpected function prelude at 0x{inst.ip:x}: {formatter.format(inst)}")

    return stack_size, stack_save_reg


def parse_trampolines(code: CodeGrabber) -> Generator[int, None, None]:
    """Parse any trampolines leading to a function."""
    while True:
        inst = code.next_inst()

        if inst.code == Code.JMP_REL32_64:
            code.jump(inst.memory_displacement)
            yield inst.ip
            continue

        # Anything else ends the search
        code.jump(inst.ip)
        break
