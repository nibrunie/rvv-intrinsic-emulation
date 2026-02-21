"""
Core module for RIE Generator - RISC-V Vector Intrinsic Emulation Generator

This module provides the fundamental types, classes, and functions for
generating C code that emulates RISC-V vector instructions.
"""

from enum import Enum, auto


# Enum class of integer types
class EltType(Enum):
    U8 = auto()
    U16 = auto()
    U32 = auto()
    U64 = auto()
    S8 = auto()
    S16 = auto()
    S32 = auto()
    S64 = auto()
    SIZE_T = auto()
    PLACEHOLDER = auto()


    @staticmethod
    def is_signed(elt_type: 'EltType') -> bool:
        return elt_type in [EltType.S8, EltType.S16, EltType.S32, EltType.S64]

    @staticmethod
    def inverse_sign(elt_type: 'EltType') -> 'EltType':
        if elt_type == EltType.U8:
            return EltType.S8
        elif elt_type == EltType.U16:
            return EltType.S16
        elif elt_type == EltType.U32:
            return EltType.S32
        elif elt_type == EltType.U64:
            return EltType.S64
        elif elt_type == EltType.S8:
            return EltType.U8
        elif elt_type == EltType.S16:
            return EltType.U16
        elif elt_type == EltType.S32:
            return EltType.U32
        elif elt_type == EltType.S64:
            return EltType.U64
        else:
            raise ValueError(f"Invalid element type: {elt_type}")

class LMULType(Enum):
    MF8 = auto()
    MF4 = auto()
    MF2 = auto()
    M1 = auto()
    M2 = auto()
    M4 = auto()
    M8 = auto()
    PLACEHOLDER = auto()

    @staticmethod
    def to_string(lmul_type: 'LMULType') -> str:
        if lmul_type == LMULType.MF8:
            return "mf8"
        elif lmul_type == LMULType.MF4:
            return "mf4"
        elif lmul_type == LMULType.MF2:
            return "mf2"
        elif lmul_type == LMULType.M1:
            return "m1"
        elif lmul_type == LMULType.M2:
            return "m2"
        elif lmul_type == LMULType.M4:
            return "m4"
        elif lmul_type == LMULType.M8:
            return "m8"
        elif lmul_type is None:
            return "undefined(None)"
        else:
            raise ValueError(f"Invalid LMUL type: {lmul_type}")

    @staticmethod
    def to_value(lmul_type: 'LMULType') -> float:
        if lmul_type == LMULType.MF8:
            return 0.125
        elif lmul_type == LMULType.MF4:
            return 0.25
        elif lmul_type == LMULType.MF2:
            return 0.5
        elif lmul_type == LMULType.M1:
            return 1
        elif lmul_type == LMULType.M2:
            return 2
        elif lmul_type == LMULType.M4:
            return 4
        elif lmul_type == LMULType.M8:
            return 8
        else:
            raise ValueError("Invalid LMUL type")

    @staticmethod
    def from_value(value: float) -> 'LMULType':
        VALUE_MAP = {
            0.125: LMULType.MF8,
            0.25: LMULType.MF4,
            0.5: LMULType.MF2,
            1: LMULType.M1,
            2: LMULType.M2,
            4: LMULType.M4,
            8: LMULType.M8,
        }
        if value not in VALUE_MAP:
            raise ValueError(f"Invalid LMUL value: {value}")
        return VALUE_MAP[value]

    @staticmethod
    def divide(lmul_type: 'LMULType', divisor: int) -> 'LMULType':
        """Divide an LMUL type by a power-of-two divisor."""
        return LMULType.from_value(LMULType.to_value(lmul_type) / divisor)

    @staticmethod
    def multiply(lmul_type: 'LMULType', factor: int) -> 'LMULType':
        """Multiply an LMUL type by a power-of-two factor."""
        return LMULType.from_value(LMULType.to_value(lmul_type) * factor)

class OperationType(Enum):
    ROR = auto()
    ROL = auto()
    SLL = auto()
    SRL = auto()
    SRA = auto()
    NSRL = auto() 
    ADD = auto()
    SUB = auto()
    RSUB = auto()
    OR = auto()
    AND = auto()
    ANDN = auto()
    XOR = auto()
    MUL = auto()
    DIV = auto()
    REM = auto()
    NOT = auto()
    EQ = auto()
    NE = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    BREV8 = auto()
    REV8 = auto()
    WMACC = auto()
    WMACCU = auto()
    WMACCSU = auto()
    WMACCUS = auto()
    DOT4A = auto()
    DOT4AU = auto()
    DOT4ASU = auto()
    DOT4AUS = auto()
    WMUL = auto()
    WMULU = auto()
    WMULSU = auto()
    WADD = auto()
    WADDU = auto()
    MV = auto()

    # misc
    REINTERPRET = auto()
    CREATE = auto()
    GET = auto()

    MIN = auto()
    MAX = auto()
    MINU = auto()
    MAXU = auto()

    VSETVLMAX = auto()

    INPUT = auto()
    IMMEDIATE = auto()

    @staticmethod
    def to_string(op_type: 'OperationType') -> str:
        if op_type == OperationType.ROR:
            return "ror"
        elif op_type == OperationType.ROL:
            return "rol"
        elif op_type == OperationType.SLL:
            return "sll"
        elif op_type == OperationType.SRL:
            return "srl"
        elif op_type == OperationType.SRA:
            return "sra"
        elif op_type == OperationType.NSRL:
            return "nsrl"
        elif op_type == OperationType.RSUB:
            return "rsub"
        elif op_type == OperationType.ADD:
            return "add"
        elif op_type == OperationType.SUB:
            return "sub"
        elif op_type == OperationType.OR:
            return "or"
        elif op_type == OperationType.AND:
            return "and"
        elif op_type == OperationType.ANDN:
            return "andn"
        elif op_type == OperationType.NOT:
            return "not"
        elif op_type == OperationType.XOR:
            return "xor"
        elif op_type == OperationType.BREV8:
            return "brev8"
        elif op_type == OperationType.REV8:
            return "rev8"
        elif op_type == OperationType.WMACC:
            return "wmacc"
        elif op_type == OperationType.WMACCU:
            return "wmaccu"
        elif op_type == OperationType.WMACCSU:
            return "wmaccsu"
        elif op_type == OperationType.WMACCUS:
            return "wmaccus"
        elif op_type == OperationType.DOT4A:
            return "dot4a"
        elif op_type == OperationType.DOT4AU:
            return "dot4au"
        elif op_type == OperationType.DOT4ASU:
            return "dot4asu"
        elif op_type == OperationType.DOT4AUS:
            return "dot4aus"
        elif op_type == OperationType.WMUL:
            return "wmul"
        elif op_type == OperationType.WMULU:
            return "wmulu"
        elif op_type == OperationType.WMULSU:
            return "wmulsu"
        elif op_type == OperationType.WADD:
            return "wadd"
        elif op_type == OperationType.WADDU:
            return "waddu"
        elif op_type == OperationType.MV:
            return "mv"
        elif op_type == OperationType.REINTERPRET:
            return "reinterpret"
        elif op_type == OperationType.CREATE:
            return "create"
        elif op_type == OperationType.GET:
            return "get"
        elif op_type == OperationType.MIN:
            return "min"
        elif op_type == OperationType.MAX:
            return "max"
        elif op_type == OperationType.MINU:
            return "minu"
        elif op_type == OperationType.MAXU:
            return "maxu"
        elif op_type == OperationType.VSETVLMAX:
            return "vsetvlmax"
        else:
            raise ValueError(f"Invalid operation type: {op_type}")

class OperationDesciptor:
    def __init__(self, op_type):
        self.op_type = op_type

class Node:
    def __init__(self):
        self.node_type = NodeType.UNDEFINED
        self.node_format = None


class NodeFormatType(Enum):
    VECTOR = auto()
    SCALAR = auto()
    IMMEDIATE = auto()
    VECTOR_LENGTH = auto()
    MASK = auto()
    PLACEHOLDER = auto()

class NodeType(Enum):
    INPUT = auto()
    IMMEDIATE = auto()
    OPERATION = auto()
    UNDEFINED = auto()

class NodeFormatDescriptor:
    def __init__(self, node_format_type: NodeFormatType, elt_type: EltType, lmul_type: LMULType=None):
        self.node_format_type = node_format_type
        self.elt_type = elt_type
        self.lmul_type = lmul_type

    def __str__(self):
        return f"{self.node_format_type.name}_{self.elt_type.name}_{LMULType.to_string(self.lmul_type)}"


class Immediate(Node):
    def __init__(self, node_format: NodeFormatDescriptor, value: int):
        self.node_format = node_format
        self.value = value
        self.node_type = NodeType.IMMEDIATE

class Input(Node):
    def __init__(self, node_format: NodeFormatDescriptor, index: int, name: str = None  ):
        self.node_format = node_format
        self.index = index
        self.name = name
        self.node_type = NodeType.INPUT

class TailPolicy(Enum):
    AGNOSTIC = auto()
    UNDISTURBED = auto()
    UNDEFINED = auto()

    def to_string(self):
        return self.name.lower()

class MaskPolicy(Enum):
    AGNOSTIC = auto()
    UNDISTURBED = auto()
    UNMASKED = auto()
    UNDEFINED = auto()

    def to_string(self):
        return self.name.lower()
    

class Operation(Node):
    def __init__(self, node_format: NodeFormatDescriptor, op_desc: OperationDesciptor, *args, vm: Input=None, dst: Input=None, tail_policy: TailPolicy=TailPolicy.UNDEFINED, mask_policy: MaskPolicy=MaskPolicy.UNDEFINED):
        self.node_format = node_format
        self.op_desc = op_desc
        self.args = args
        self.node_type = NodeType.OPERATION
        self.vm = vm
        self.dst = dst
        self.tail_policy = tail_policy
        self.mask_policy = mask_policy

def element_size(elt_type: EltType) -> int:
    if elt_type == EltType.U8 or elt_type == EltType.S8:
        return 8
    elif elt_type == EltType.U16 or elt_type == EltType.S16:
        return 16
    elif elt_type == EltType.U32 or elt_type == EltType.S32:
        return 32
    elif elt_type == EltType.U64 or elt_type == EltType.S64:
        return 64
    else:
        raise ValueError("Invalid integer type")

def get_scalar_format(node_format: NodeFormatDescriptor) -> NodeFormatDescriptor:
    return NodeFormatDescriptor(NodeFormatType.SCALAR, node_format.elt_type, None)

def get_mask_format(node_format: NodeFormatDescriptor) -> NodeFormatDescriptor:
    return NodeFormatDescriptor(NodeFormatType.MASK, node_format.elt_type, node_format.lmul_type)


def int_type_to_scalar_type(int_type: EltType) -> str:
    if int_type == EltType.U8:
        return "uint8_t"
    elif int_type == EltType.S8:
        return "int8_t"
    elif int_type == EltType.U16:
        return "uint16_t"
    elif int_type == EltType.S16:
        return "int16_t"
    elif int_type == EltType.U32:
        return "uint32_t"
    elif int_type == EltType.S32:
        return "int32_t"
    elif int_type == EltType.U64:
        return "uint64_t"
    else:
        raise ValueError("Invalid integer type")

def int_type_to_vector_type(int_type: EltType, lmul_type: LMULType) -> str:
    if int_type == EltType.U8:
        return f"vuint8{LMULType.to_string(lmul_type)}_t"
    elif int_type == EltType.S8:
        return f"vint8{LMULType.to_string(lmul_type)}_t"
    elif int_type == EltType.U16:
        return f"vuint16{LMULType.to_string(lmul_type)}_t"
    elif int_type == EltType.S16:
        return f"vint16{LMULType.to_string(lmul_type)}_t"
    elif int_type == EltType.U32:
        return f"vuint32{LMULType.to_string(lmul_type)}_t"
    elif int_type == EltType.S32:
        return f"vint32{LMULType.to_string(lmul_type)}_t"
    elif int_type == EltType.U64:
        return f"vuint64{LMULType.to_string(lmul_type)}_t"
    elif int_type == EltType.S64:
        return f"vint64{LMULType.to_string(lmul_type)}_t"
    else:
        raise ValueError(f"Invalid integer type: {int_type}")

def vector_type_to_mask_type(node_format: NodeFormatDescriptor) -> str:
    elt_size = element_size(node_format.elt_type)
    lmul_value = LMULType.to_value(node_format.lmul_type)
    n = int(elt_size / lmul_value)
    return f"vbool{n}_t"

def generate_node_format_type_string(node_format: NodeFormatDescriptor) -> str:
    if node_format.node_format_type == NodeFormatType.VECTOR:
        return int_type_to_vector_type(node_format.elt_type, node_format.lmul_type)
    elif node_format.node_format_type == NodeFormatType.SCALAR:
        return int_type_to_scalar_type(node_format.elt_type)
    elif node_format.node_format_type == NodeFormatType.IMMEDIATE:
        return int_type_to_scalar_type(node_format.elt_type)
    elif node_format.node_format_type == NodeFormatType.VECTOR_LENGTH:
        return "size_t"
    elif node_format.node_format_type == NodeFormatType.MASK:
        return vector_type_to_mask_type(node_format)
    else:
        raise ValueError("Invalid operand type")

def generate_intrinsic_type_tag(node_format: NodeFormatDescriptor) -> str:
    type_tag = {
        EltType.U8: "u8",
        EltType.S8: "i8",
        EltType.U16: "u16",
        EltType.S16: "i16",
        EltType.U32: "u32",
        EltType.S32: "i32",
        EltType.U64: "u64",
        EltType.S64: "i64",
    }
    return f"{type_tag[node_format.elt_type]}{LMULType.to_string(node_format.lmul_type)}"


def generate_intrinsic_name(prototype: Operation) -> str:
    intrinsic_type_tag = generate_intrinsic_type_tag(prototype.node_format)
    # building operand type descriptor (vv, vx, vi)
    operand_type_descriptor = ""
    for (index, arg) in enumerate(prototype.args):
        if len(prototype.args) > 3 and index == 0:
            # for 3-operand instructions (e.g. vfmadd or vwmacc), the first operand is never
            # described in the name suffix
            # Note: 3-operand instructions have actually 4 operands when vl is taken into account
            continue
        if arg.node_format.node_format_type == NodeFormatType.VECTOR:
            # w for wide, v for vector
            # w is not used for some single operand operations (e.g. reinterpret)
            if len(prototype.args) > 1 and element_size(arg.node_format.elt_type) > element_size(prototype.node_format.elt_type):
                operand_type_descriptor += "w"
            else: # element_size(args.node_format.elt_type) == element_size(prototype.node_format.elt_type):
                operand_type_descriptor += "v"
                
        elif arg.node_format.node_format_type == NodeFormatType.SCALAR:
            operand_type_descriptor += "x"
        elif arg.node_format.node_format_type == NodeFormatType.IMMEDIATE:
            operand_type_descriptor += "i"
    # Some intrinsics (e.g. reinterpret, create, get) require the source type
    # to be displayed in the name suffix, and use 'v' as operand descriptor
    if prototype.op_desc.op_type in [OperationType.REINTERPRET, OperationType.CREATE, OperationType.GET]:
        source_type_tag = generate_intrinsic_type_tag(prototype.args[0].node_format)
        intrinsic_type_tag = f"{source_type_tag}_{intrinsic_type_tag}"
        operand_type_descriptor = "v"
    suffix = ""
    # in rvv-intrinsics-doc, tail policy always come before mask policy
    # TODO: handle tail and mask AGNOSTIC policies
    if prototype.tail_policy == TailPolicy.UNDISTURBED:
        suffix += "tu"
    if prototype.mask_policy == MaskPolicy.AGNOSTIC:
        suffix += "m"
    elif prototype.mask_policy == MaskPolicy.UNDISTURBED:
        suffix += "mu"
    suffix = f"_{suffix}" if suffix != "" else ""
    # vmv uses special naming: __riscv_vmv_v_x_<type> (v_ prefix for destination)
    if prototype.op_desc.op_type == OperationType.MV:
        operand_type_descriptor = f"v_{operand_type_descriptor}"
    intrinsic_name = f"__riscv_v{OperationType.to_string(prototype.op_desc.op_type)}_{operand_type_descriptor}_{intrinsic_type_tag}{suffix}"
    return intrinsic_name

def generate_intrinsic_prototype(prototype: Operation) -> str:
    # generate intrinsic name
    intrinsic_name = generate_intrinsic_name(prototype)
    # generate prototype
    dst_type = generate_node_format_type_string(prototype.node_format)
    src_types = [generate_node_format_type_string(arg.node_format) for arg in prototype.args]
    if (prototype.tail_policy == TailPolicy.UNDISTURBED or prototype.mask_policy == MaskPolicy.UNDISTURBED) and prototype.dst not in prototype.args:
        assert prototype.dst is not None
        src_types = [generate_node_format_type_string(prototype.dst.node_format)] + src_types
    # in rvv-intrinsics-doc, vm come before tail (arguments order)
    if prototype.mask_policy not in (MaskPolicy.UNDEFINED, MaskPolicy.UNMASKED):
        src_types = [generate_node_format_type_string(prototype.vm.node_format)] + src_types
    prototype = f"{dst_type} {intrinsic_name}({', '.join(src_types)})"
    return f"{prototype};"

class CodeObject:
    def __init__(self, code: str):
        self.code = code
        self.free_var_idx = 0

    def append(self, code: str):
        self.code += code

    def allocate_new_free_var(self) -> str:
        var = f"tmp{self.free_var_idx}"
        self.free_var_idx += 1
        return var


def generate_operation(code: CodeObject, op: Node, memoization_map: dict[str]) -> str:
    if op.node_type == NodeType.INPUT:
        return memoization_map[op]
    elif op.node_type == NodeType.IMMEDIATE:
        return f"{op.value}"
    else:
        assert op.node_type == NodeType.OPERATION
        if op in memoization_map:
            return memoization_map[op]
        elif op.node_format.node_format_type == NodeFormatType.VECTOR or any(arg.node_format.node_format_type == NodeFormatType.VECTOR for arg in op.args):
            # generate intrinsic call
            intrinsic_arg_list = [generate_operation(code, arg, memoization_map) for arg in op.args]
            # CREATE and GET are pure register manipulation — no vl/tail/mask
            if op.op_desc.op_type not in (OperationType.CREATE, OperationType.GET):
                if (op.tail_policy == TailPolicy.UNDISTURBED or op.mask_policy == MaskPolicy.UNDISTURBED):
                    assert op.dst is not None
                    intrinsic_arg_list.insert(0, generate_operation(code, op.dst, memoization_map))
                if op.mask_policy not in (MaskPolicy.UNDEFINED, MaskPolicy.UNMASKED):
                    assert op.vm is not None
                    intrinsic_arg_list.insert(0, generate_operation(code, op.vm, memoization_map))
            
            call_op = f"{generate_intrinsic_name(op)}({', '.join(intrinsic_arg_list)})"
            # generate temp variable
            temp_var = code.allocate_new_free_var()
            memoization_map[op] = temp_var
            code.append(f"  {generate_node_format_type_string(op.node_format)} {temp_var} = {call_op};\n")
            return temp_var
        else:
            # scalar operation
            return generate_scalar_operation(code, op, memoization_map)

def generate_scalar_operation(code: CodeObject, op: Node, memoization_map: dict[str]) -> str:
    # some operations use argument as placeholder to carry metadata
    # Those arguments should not be evaluated
    if op.op_desc.op_type == OperationType.VSETVLMAX:
        vsetvlmax_fmt = op.args[0].node_format
        lmul = LMULType.to_value(vsetvlmax_fmt.lmul_type)
        elt_size = element_size(vsetvlmax_fmt.elt_type)
        return f"__riscv_vsetvlmax_e{elt_size}m{lmul}()"

    arg_list = [generate_operation(code, arg, memoization_map) for arg in op.args]
    if op.op_desc.op_type == OperationType.ADD:
        expression = f"{arg_list[0]} + {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.SUB:
        expression = f"{arg_list[0]} - {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.RSUB:
        expression = f"{arg_list[1]} - {arg_list[0]}"
    elif op.op_desc.op_type == OperationType.MUL:
        expression = f"{arg_list[0]} * {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.DIV:
        expression = f"{arg_list[0]} / {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.REM:
        expression = f"{arg_list[0]} % {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.AND:
        expression = f"{arg_list[0]} & {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.OR:
        expression = f"{arg_list[0]} | {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.XOR:
        expression = f"{arg_list[0]} ^ {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.NOT:
        expression = f"~{arg_list[0]}"
    elif op.op_desc.op_type == OperationType.SLL:
        expression = f"{arg_list[0]} << {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.SRL:
        expression = f"{arg_list[0]} >> {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.SRA:
        expression = f"{arg_list[0]} >> {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.ROL:
        expression = f"{arg_list[0]} << {arg_list[1]} | {arg_list[0]} >> (64 - {arg_list[1]})"
    elif op.op_desc.op_type == OperationType.ROR:
        expression = f"{arg_list[0]} >> {arg_list[1]} | {arg_list[0]} << (64 - {arg_list[1]})"
    elif op.op_desc.op_type == OperationType.EQ:
        expression = f"{arg_list[0]} == {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.NE:
        expression = f"{arg_list[0]} != {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.LT:
        expression = f"{arg_list[0]} < {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.LE:
        expression = f"{arg_list[0]} <= {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.GT:
        expression = f"{arg_list[0]} > {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.GE:
        expression = f"{arg_list[0]} >= {arg_list[1]}"
    elif op.op_desc.op_type == OperationType.MIN:
        lhs = arg_list[0]
        rhs = arg_list[1]
        expression = f"{lhs} < {rhs} ? {lhs} : {rhs}"
    elif op.op_desc.op_type == OperationType.MAX:
        lhs = arg_list[0]
        rhs = arg_list[1]
        expression = f"{lhs} > {rhs} ? {lhs} : {rhs}"
    elif op.op_desc.op_type == OperationType.MINU:
        lhs = arg_list[0]
        rhs = arg_list[1]
        expression = f"{lhs} < {rhs} ? {lhs} : {rhs}"
    elif op.op_desc.op_type == OperationType.MAXU:
        lhs = arg_list[0]
        rhs = arg_list[1]
        expression = f"{lhs} > {rhs} ? {lhs} : {rhs}"
    else:
        raise ValueError(f"Invalid operation type: {op.op_desc.op_type}")
    
    temp_var = code.allocate_new_free_var()
    memoization_map[op] = temp_var
    code.append(f"  {generate_node_format_type_string(op.node_format)} {temp_var} = {expression};\n")
    return temp_var
    

def generate_intrinsic_from_operation(prototype: Operation, emulation: Operation, attributes: list[str]) -> str:
    intrinsic_name = generate_intrinsic_name(prototype)
    # generate body
    dst_type = generate_node_format_type_string(prototype.node_format)
    src_types = [generate_node_format_type_string(arg.node_format) for arg in prototype.args]
    def get_src_name(src: Node) -> str:
        assert src.node_type == NodeType.INPUT
        if src.name is not None:
            return src.name
        else:
            return f"op{src.index}"
    src_list = [f"{src_type} {get_src_name(src)}" for src, src_type in zip(prototype.args, src_types)]
    memoisation_map = {src: get_src_name(src) for src in prototype.args}
    # if any tail/mask policy is set to undisturbed and the destination is not already an argument
    # (e.g. destructive MAC operations) then it needs to be added before all arguments
    if (prototype.tail_policy == TailPolicy.UNDISTURBED or prototype.mask_policy == MaskPolicy.UNDISTURBED) and not prototype.dst in prototype.args:
        assert prototype.dst is not None
        src_list.insert(0, f"{dst_type} {get_src_name(prototype.dst)}")
        memoisation_map[prototype.dst] = get_src_name(prototype.dst)
    if prototype.mask_policy not in [MaskPolicy.UNDEFINED, MaskPolicy.UNMASKED]:
        src_list.insert(0, f"{generate_node_format_type_string(prototype.vm.node_format)} {get_src_name(prototype.vm)}")
        memoisation_map[prototype.vm] = get_src_name(prototype.vm)
    attributes_str = " ".join(attributes)
    header = f"{attributes_str} {dst_type} {intrinsic_name}({', '.join(src_list)}) {{\n"
    code = CodeObject("")
    result = generate_operation(code, emulation, memoisation_map)
    footer = f"  return {result};\n}}"
    return header + code.code + footer

def expand_reinterpret_cast(source: Operation, cast_to_type: NodeFormatDescriptor) -> Operation:
    if source.node_format == cast_to_type or source.node_format.node_format_type != NodeFormatType.VECTOR:
        return source

    # Reinterpret cast does not support change of both signedness and element width at once
    # so we need to split them into two operations
    if EltType.is_signed(source.node_format.elt_type) != EltType.is_signed(cast_to_type.elt_type):
        inversed_sign_format = NodeFormatDescriptor(source.node_format.node_format_type, EltType.inverse_sign(source.node_format.elt_type), source.node_format.lmul_type)
        source = Operation(inversed_sign_format, OperationDesciptor(OperationType.REINTERPRET), source)

    assert EltType.is_signed(source.node_format.elt_type) == EltType.is_signed(cast_to_type.elt_type)
    if element_size(source.node_format.elt_type) != element_size(cast_to_type.elt_type):
        source = Operation(cast_to_type, OperationDesciptor(OperationType.REINTERPRET), source)

    return source
