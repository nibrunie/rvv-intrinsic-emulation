from typing import Callable
from .core import TailPolicy, MaskPolicy, Operation, OperationDescriptor, NodeFormatDescriptor, NodeFormatType, EltType, LMULType, Immediate, OperationType, Node

def emulate_with_split_lmul(result_fmt: NodeFormatDescriptor, operands: list, vl: Node, generator: Callable, generator_extra_args: list, tail_policy: TailPolicy, mask_policy: MaskPolicy, vm: Node, generator_extra_kwargs: dict) -> Operation:
    """ generator is expected to follow the Generator API """
    # check that LMUL can actually be split
    # 1. LMUL value must be large enough that half LMUL is still valid for EEW  
    half_lmul = LMULType.divide(result_fmt.lmul_type, 2)
    assert LMULType.is_valid_for_eew(result_fmt.elt_type, half_lmul) 

    vl_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None)
    idx_fmt = NodeFormatDescriptor(NodeFormatType.IMMEDIATE, EltType.SIZE_T)

    # Derive M4/M8 formats from each input's own element type
    def make_half_lmul_format(node):
        return NodeFormatDescriptor(NodeFormatType.VECTOR, node.node_format.elt_type, half_lmul)

    def get_halves(node):
        half_lmul_format = make_half_lmul_format(node)
        lo = Operation(half_lmul_format, OperationDescriptor(OperationType.GET), node, Immediate(idx_fmt, 0))
        hi = Operation(half_lmul_format, OperationDescriptor(OperationType.GET), node, Immediate(idx_fmt, 1))
        return lo, hi

    split_operands = []
    for operand in operands:
        if operand.node_format.node_format_type == NodeFormatType.VECTOR:
            split_operands.append(get_halves(operand))
        else:
            split_operands.append((operand, operand))

    half_lmul_result_fmt = NodeFormatDescriptor(NodeFormatType.PLACEHOLDER, result_fmt.elt_type, half_lmul)
    placeholder = Immediate(half_lmul_result_fmt, None)
    vlmax_half_lmul = Operation(vl_fmt, OperationDescriptor(OperationType.VSETVLMAX), placeholder)

    # vl_half = vl / 2
    vl_lo = Operation(vl_fmt, OperationDescriptor(OperationType.MIN),
                      vl, vlmax_half_lmul)
    vl_hi = Operation(vl_fmt, OperationDescriptor(OperationType.SUB),
                        vl, vl_lo)
    
    # FIXME: implement mask support (through either mask splitting or masked merged with LMUL=8)


    args_lo, args_hi = zip(*split_operands)
    # Process each half-LMUL half independently
    # no masking, nor tail policy are applied
    result_lo = generator(*args_lo, *generator_extra_args, vl=vl_lo, vm=None, tail_policy=TailPolicy.AGNOSTIC, mask_policy=MaskPolicy.UNMASKED, **generator_extra_kwargs)
    result_hi = generator(*args_hi, *generator_extra_args, vl=vl_hi, vm=None, tail_policy=TailPolicy.AGNOSTIC, mask_policy=MaskPolicy.UNMASKED, **generator_extra_kwargs)

    # CREATE: reassemble two half original LMUL results into full LMUL
    result_elt = result_fmt.elt_type
    full_result_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, result_elt, result_fmt.lmul_type)
    result = Operation(full_result_fmt, OperationDescriptor(OperationType.CREATE),
                       result_lo, result_hi)
    return result
    
    
    