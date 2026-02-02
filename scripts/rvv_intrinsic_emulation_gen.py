from enum import Enum, auto


# Enum class of integer types
class IntType(Enum):
    U8 = auto()
    U16 = auto()
    U32 = auto()
    U64 = auto()
    S8 = auto()
    S16 = auto()
    S32 = auto()
    S64 = auto()
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
    ROTL = auto()
    ROXR = auto()
    ROXL = auto()
    SLL = auto()
    SRL = auto()
    SRA = auto()
    NSRL = auto() 
    RSUB = auto()
    ADD = auto()
    SUB = auto()
    OR = auto()
    AND = auto()
    XOR = auto()

    INPUT = auto()
    IMMEDIATE = auto()

    @staticmethod
    def to_string(op_type: 'OperationType') -> str:
        if op_type == OperationType.ROR:
            return "ror"
        elif op_type == OperationType.ROTL:
            return "rotl"
        elif op_type == OperationType.ROXR:
            return "roxr"
        elif op_type == OperationType.ROXL:
            return "roxl"
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
    def __init__(self, op_type, dst_type):
        self.op_type = op_type
        self.dst_type = dst_type

class Node:
    def __init__(self):
        self.node_type = NodeType.UNDEFINED

class Immediate(Node):
    def __init__(self, node_descriptor: NodeDescriptor, value: int):
        self.node_descriptor = node_descriptor
        self.value = value
        self.node_type = NodeType.IMMEDIATE

class Input(Node):
    def __init__(self, node_descriptor: NodeDescriptor, index: int):
        self.node_descriptor = node_descriptor
        self.index = index
        self.node_type = NodeType.INPUT

class Operation(Node):
    def __init__(self, op_desc: OperationDesciptor, *args):
        self.op_desc = op_desc
        self.args = args
        self.node_type = NodeType.OPERATION

class OperandType(Enum):
    VECTOR = auto()
    SCALAR = auto()
    IMMEDIATE = auto()

class NodeType(Enum):
    INPUT = auto()
    IMMEDIATE = auto()
    OPERATION = auto()
    UNDEFINED = auto()

class NodeDescriptor:
    def __init__(self, operand_type, int_type, lmul_type, node_type = NodeType.UNDEFINED):
        self.operand_type = operand_type
        self.int_type = int_type
        self.lmul_type = lmul_type
        self.node_type = node_type

class OperationDescriptor(NodeDescriptor):
    def __init__(self, op_type, dst_type):
        super().__init__(OperandType.VECTOR, dst_type, LMULType.M1, NodeType.OPERATION)
        self.op_type = op_type

class InputDescriptor(NodeDescriptor):
    def __init__(self, node_descriptor: NodeDescriptor):
        super().__init__(node_descriptor.operand_type, node_descriptor.int_type, node_descriptor.lmul_type)
        self.node_type = NodeType.INPUT

class OperandDescriptor(NodeDescriptor):
    def __init__(self, node_descriptor: NodeDescriptor, index: int):
        super().__init__(node_descriptor.operand_type, node_descriptor.int_type, node_descriptor.lmul_type)
        self.index = index
        self.node_type = NodeType.INPUT

    @property
    def node_descriptor(self) -> NodeDescriptor:
        return NodeDescriptor(self.operand_type, self.int_type, self.lmul_type)

class ImmediateDescriptor(NodeDescriptor):
    def __init__(self, node_descriptor: NodeDescriptor, value: int):
        super().__init__(node_descriptor.operand_type, node_descriptor.int_type, node_descriptor.lmul_type)
        self.value = value
        self.node_type = NodeType.IMMEDIATE


def element_size(int_type: IntType) -> int:
    if int_type == IntType.U8 or int_type == IntType.S8:
        return 8
    elif int_type == IntType.U16 or int_type == IntType.S16:
        return 16
    elif int_type == IntType.U32 or int_type == IntType.S32:
        return 32
    elif int_type == IntType.U64 or int_type == IntType.S64:
        return 64
    else:
        raise ValueError("Invalid integer type")


# description of vector rotation emulation 
def rotate_left(elts: OperandDescriptor, rot_amount: OperandDescriptor) -> vtype_t:
    left_shift = Operation(
        OperationDesciptor(OperationType.SLL, elts.node_descriptor),
        elts, rot_amount
    )
    right_shift = Operation(
        OperationDesciptor(OperationType.SRL, elts.node_descriptor),
        elts,
        Operation(
            OperationDesciptor(OperationType.RSUB, elts.node_descriptor),
            rot_amount,
            ImmediateDescriptor(NodeDescriptor(OperandType.IMMEDIATE, elts.int_type, elts.lmul_type), element_size(elts.int_type))
        )
    )
     
    or_desc = OperationDesciptor(OperationType.OR, elts.node_descriptor)
    return Operation(or_desc, left_shift, right_shift)

def int_type_to_scalar_type(int_type: IntType) -> str:
    if int_type == IntType.U8:
        return "uint8_t"
    elif int_type == IntType.S8:
        return "int8_t"
    elif int_type == IntType.U16:
        return "uint16_t"
    elif int_type == IntType.S16:
        return "int16_t"
    elif int_type == IntType.U32:
        return "uint32_t"
    elif int_type == IntType.S32:
        return "int32_t"
    elif int_type == IntType.U64:
        return "uint64_t"
    else:
        raise ValueError("Invalid integer type")

def int_type_to_vector_type(int_type: IntType, lmul_type: LMULType) -> str:
    if int_type == IntType.U8:
        return f"vuint8{LMULType.to_string(lmul_type)}_t"
    elif int_type == IntType.S8:
        return f"vint8{LMULType.to_string(lmul_type)}_t"
    elif int_type == IntType.U16:
        return f"vuint16{LMULType.to_string(lmul_type)}_t"
    elif int_type == IntType.S16:
        return f"vint16{LMULType.to_string(lmul_type)}_t"
    elif int_type == IntType.U32:
        return f"vuint32{LMULType.to_string(lmul_type)}_t"
    elif int_type == IntType.S32:
        return f"vint32{LMULType.to_string(lmul_type)}_t"
    elif int_type == IntType.U64:
        return f"vuint64{LMULType.to_string(lmul_type)}_t"
    else:
        raise ValueError("Invalid integer type")

def generate_operand_type(op_descriptor: OperandDescriptor) -> str:
    if op_descriptor.operand_type == OperandType.VECTOR:
        return int_type_to_vector_type(op_descriptor.int_type, op_descriptor.lmul_type)
    elif op_descriptor.operand_type == OperandType.SCALAR:
        return int_type_to_scalar_type(op_descriptor.int_type)
    elif op_descriptor.operand_type == OperandType.IMMEDIATE:
        return int_type_to_scalar_type(op_descriptor.int_type)
    else:
        raise ValueError("Invalid operand type")

def generate_intrinsic_type_tag(op_descriptor: OperandDescriptor) -> str:
    type_tag = {
        IntType.U8: "u8",
        IntType.S8: "i8",
        IntType.U16: "u16",
        IntType.S16: "i16",
        IntType.U32: "u32",
        IntType.S32: "i32",
        IntType.U64: "u64",
        IntType.S64: "i64",
    }
    return f"{type_tag[op_descriptor.int_type]}{LMULType.to_string(op_descriptor.lmul_type)}"


def generate_intrinsic_name(prototype: Operation) -> str:
    intrinsic_type_tag = generate_intrinsic_type_tag(prototype.op_desc.dst_type)
    intrinsic_name = f"__riscv_v{OperationType.to_string(prototype.op_desc.op_type)}_vv_{intrinsic_type_tag}"
    return intrinsic_name

def generate_intrinsic_prototype(prototype: Operation) -> str:
    # generate intrinsic name
    intrinsic_name = generate_intrinsic_name(prototype)
    # generate prototype
    dst_type = generate_operand_type(prototype.op_desc.dst_type)
    src_types = [generate_operand_type(arg) for arg in prototype.args]
    prototype = f"{dst_type} {intrinsic_name}({', '.join(src_types)})"
    return f"{prototype};"

def generate_operation(op: Operation, memoization_map: dict[str]) -> str:
    if op.op_desc.node_type == NodeType.INPUT:
        return memoization_map[op]
    elif op.op_desc.node_type == NodeType.IMMEDIATE:
        return op.args[0].value
    else:
        # generate all sources
        pre_body = "".join([generate_operation(arg, memoization_map) for arg in op.args])
        call_op = f"{generate_intrinsic_name(op)}({', '.join([f'op{i}' for i, arg in enumerate(op.args)])})"
        memoization_map[op] = call_op
        return pre_body + call_op

def generate_intrinsic_from_operation(prototype: Operation, emulation: Operation) -> str:
    intrinsic_name = generate_intrinsic_name(prototype)
    # generate body
    dst_type = generate_operand_type(prototype.op_desc.dst_type)
    src_types = [generate_operand_type(arg) for arg in prototype.args]
    src_list = [f"{src_type} op{i}" for i, src_type in enumerate(src_types)]
    memoisation_map = {src: f"op{i}" for i, src in enumerate(prototype.args)}
    header = f"{dst_type} {intrinsic_name}({', '.join(src_list)}) {{\n"
    body = generate_operation(emulation, memoisation_map)
    footer = "}"
    return header + body + footer

    
    
    

lhs = OperandDescriptor(NodeDescriptor(OperandType.VECTOR, IntType.U64, LMULType.M1), 0)
rhs = OperandDescriptor(NodeDescriptor(OperandType.VECTOR, IntType.U64, LMULType.M1), 1)

vuint64m1_vror_vv_prototype = Operation(
    OperationDesciptor(OperationType.ROR, NodeDescriptor(OperandType.VECTOR, IntType.U64, LMULType.M1)),
    lhs,
    rhs
)
vuint64m1_vror_vv_emulation = rotate_left(lhs, rhs)

print("prototype")
print(generate_intrinsic_prototype(vuint64m1_vror_vv_prototype))
print("intrinsic")
print(generate_intrinsic_from_operation(vuint64m1_vror_vv_prototype, vuint64m1_vror_vv_emulation))
