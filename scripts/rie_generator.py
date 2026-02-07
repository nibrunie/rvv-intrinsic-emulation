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
        else:
            raise ValueError("Invalid LMUL type")

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
        elif op_type == OperationType.XOR:
            return "xor"
        else:
            raise ValueError("Invalid operation type")

class OperationDesciptor:
    def __init__(self, op_type):
        self.op_type = op_type

class Node:
    def __init__(self):
        self.node_type = NodeType.UNDEFINED
        self.node_format = None

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

class Operation(Node):
    def __init__(self, node_format: NodeFormatDescriptor, op_desc: OperationDesciptor, *args):
        self.node_format = node_format
        self.op_desc = op_desc
        self.args = args
        self.node_type = NodeType.OPERATION

class NodeFormatType(Enum):
    VECTOR = auto()
    SCALAR = auto()
    IMMEDIATE = auto()
    VECTOR_LENGTH = auto()

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
    else:
        raise ValueError("Invalid integer type")

def generate_node_format_type_string(node_format: NodeFormatDescriptor) -> str:
    if node_format.node_format_type == NodeFormatType.VECTOR:
        return int_type_to_vector_type(node_format.elt_type, node_format.lmul_type)
    elif node_format.node_format_type == NodeFormatType.SCALAR:
        return int_type_to_scalar_type(node_format.elt_type)
    elif node_format.node_format_type == NodeFormatType.IMMEDIATE:
        return int_type_to_scalar_type(node_format.elt_type)
    elif node_format.node_format_type == NodeFormatType.VECTOR_LENGTH:
        return "size_t"
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
    for arg in prototype.args:
        if arg.node_format.node_format_type == NodeFormatType.VECTOR:
            operand_type_descriptor += "v"
        elif arg.node_format.node_format_type == NodeFormatType.SCALAR:
            operand_type_descriptor += "x"
        elif arg.node_format.node_format_type == NodeFormatType.IMMEDIATE:
            operand_type_descriptor += "i"
    intrinsic_name = f"__riscv_v{OperationType.to_string(prototype.op_desc.op_type)}_{operand_type_descriptor}_{intrinsic_type_tag}"
    return intrinsic_name

def generate_intrinsic_prototype(prototype: Operation) -> str:
    # generate intrinsic name
    intrinsic_name = generate_intrinsic_name(prototype)
    # generate prototype
    dst_type = generate_node_format_type_string(prototype.node_format)
    src_types = [generate_node_format_type_string(arg.node_format) for arg in prototype.args]
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
        # generate temp variable
        if op.node_format.node_format_type == NodeFormatType.VECTOR or any(arg.node_format.node_format_type == NodeFormatType.VECTOR for arg in op.args):
            call_op = f"{generate_intrinsic_name(op)}({', '.join([generate_operation(code, arg, memoization_map) for arg in op.args])})"
            temp_var = code.allocate_new_free_var()
            memoization_map[op] = temp_var
            code.append(f"  {generate_node_format_type_string(op.node_format)} {temp_var} = {call_op};\n")
            return temp_var
        else:
            # scalar operation
            return generate_scalar_operation(code, op, memoization_map)

def generate_scalar_operation(code: CodeObject, op: Node, memoization_map: dict[str]) -> str:
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
    else:
        raise ValueError(f"Invalid operation type: {op.op_desc.op_type}")
    
    temp_var = code.allocate_new_free_var()
    memoization_map[op] = temp_var
    code.append(f"  {generate_node_format_type_string(op.node_format)} {temp_var} = {expression};\n")
    return temp_var
    

def generate_intrinsic_from_operation(prototype: Operation, emulation: Operation) -> str:
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
    header = f"{dst_type} {intrinsic_name}({', '.join(src_list)}) {{\n"
    code = CodeObject("")
    result = generate_operation(code, emulation, memoisation_map)
    footer = f"  return {result};\n}}"
    return header + code.code + footer
    