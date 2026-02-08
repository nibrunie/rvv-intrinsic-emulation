"""
Zvkb (Vector Bit-manipulation) instruction emulation generator.

This module generates C code for emulating RISC-V Zvkb vector rotate
instructions (vror, vrol) using standard RVV intrinsics.
"""

from .core import (
    Operation,
    OperationDesciptor,
    NodeFormatDescriptor,
    NodeFormatType,
    Immediate,
    Input,
    Node,
    get_scalar_format,
    element_size,
    EltType,
    LMULType,
    OperationType,
    generate_intrinsic_prototype,
    generate_intrinsic_from_operation,
)


def rotate_left(elts: Node, rot_amount: Node, vl: Node) -> Node:
    """Generate a rotate left operation using shifts and OR."""
    left_shift = Operation(
        elts.node_format,
        OperationDesciptor(OperationType.SLL),
        elts, rot_amount, vl
    )
    if rot_amount.node_format.node_format_type == NodeFormatType.SCALAR:
        rsub = Operation(
            rot_amount.node_format,
            OperationDesciptor(OperationType.RSUB),
            rot_amount,
            Immediate(get_scalar_format(rot_amount.node_format), element_size(elts.node_format.elt_type))
        )
    else:
        rsub = Operation(
            rot_amount.node_format,
            OperationDesciptor(OperationType.RSUB),
            rot_amount,
            Immediate(get_scalar_format(rot_amount.node_format), element_size(elts.node_format.elt_type)),
            vl
        )
    right_shift = Operation(
        elts.node_format,
        OperationDesciptor(OperationType.SRL),
        elts,
        rsub,
        vl   
    )
     
    or_desc = OperationDesciptor(OperationType.OR)
    return Operation(elts.node_format, or_desc, left_shift, right_shift, vl)


def rotate_right(elts: Node, rot_amount: Node, vl: Node) -> Node:
    """Generate a rotate right operation using shifts and OR."""
    right_shift = Operation(
        elts.node_format,
        OperationDesciptor(OperationType.SRL),
        elts, rot_amount, vl
    )
    if rot_amount.node_format.node_format_type == NodeFormatType.SCALAR:
        rsub = Operation(
            rot_amount.node_format,
            OperationDesciptor(OperationType.RSUB),
            rot_amount,
            Immediate(get_scalar_format(rot_amount.node_format), element_size(elts.node_format.elt_type))
        )
    else:
        rsub = Operation(
            rot_amount.node_format,
            OperationDesciptor(OperationType.RSUB),
            rot_amount,
            Immediate(get_scalar_format(rot_amount.node_format), element_size(elts.node_format.elt_type)),
            vl
        )
    left_shift = Operation(
        elts.node_format,
        OperationDesciptor(OperationType.SLL),
        elts,
        rsub,
        vl
    )
     
    or_desc = OperationDesciptor(OperationType.OR)
    return Operation(elts.node_format, or_desc, left_shift, right_shift, vl)


def and_not(op0: Node, op1: Node, vl: Node) -> Node:
    """Generate vector andn (and not) using operation RVV 1.0 operation only."""
    not_desc = OperationDesciptor(OperationType.NOT)
    not_op1 = Operation(op1.node_format, not_desc, op1, vl)
    and_desc = OperationDesciptor(OperationType.AND)
    return Operation(op0.node_format, and_desc, op0, not_op1, vl)


def brev8(op0: Node, vl: Node) -> Node:
    """Generate vector brev8 (bit reverse in bytes) using operation RVV 1.0 operation only."""
    elt_size = element_size(op0.node_format.elt_type)
    mask_elt_size = (1 << (elt_size)) - 1
    mask_4bits = Immediate(op0.node_format, 0x0F0F0F0F0F0F0F0F & mask_elt_size)
    # inversing nimbles in byte
    op0_lo = Operation(op0.node_format, OperationDesciptor(OperationType.AND), op0, mask_4bits, vl)
    op0_lo_shift = Operation(op0.node_format, OperationDesciptor(OperationType.SLL), op0_lo, Immediate(get_scalar_format(op0.node_format), 4), vl)
    op0_hi_shift = Operation(op0.node_format, OperationDesciptor(OperationType.SRL), op0, Immediate(get_scalar_format(op0.node_format), 4), vl)
    op0_hi_masked = Operation(op0.node_format, OperationDesciptor(OperationType.AND), op0_hi_shift, mask_4bits, vl)
    op0_inv_nimbles = Operation(op0.node_format, OperationDesciptor(OperationType.OR), op0_lo_shift, op0_hi_masked, vl)
    # inversing 2-bit in nimbles
    mask_2bits = Immediate(op0.node_format, 0x3333333333333333 & mask_elt_size)
    op0_2bits_lo = Operation(op0.node_format, OperationDesciptor(OperationType.AND), op0_inv_nimbles, mask_2bits, vl)
    op0_2bits_lo_shift = Operation(op0.node_format, OperationDesciptor(OperationType.SLL), op0_2bits_lo, Immediate(get_scalar_format(op0.node_format), 2), vl)
    op0_2bits_hi_shift = Operation(op0.node_format, OperationDesciptor(OperationType.SRL), op0_inv_nimbles, Immediate(get_scalar_format(op0.node_format), 2), vl)
    op0_2bits_hi_masked = Operation(op0.node_format, OperationDesciptor(OperationType.AND), op0_2bits_hi_shift, mask_2bits, vl)
    op0_inv_2bits = Operation(op0.node_format, OperationDesciptor(OperationType.OR), op0_2bits_lo_shift, op0_2bits_hi_masked, vl)
    # inversing 1-bit in nimbles
    mask_1bit = Immediate(op0.node_format, 0x5555555555555555 & mask_elt_size)
    op0_1bit_lo = Operation(op0.node_format, OperationDesciptor(OperationType.AND), op0_inv_2bits, mask_1bit, vl)
    op0_1bit_lo_shift = Operation(op0.node_format, OperationDesciptor(OperationType.SLL), op0_1bit_lo, Immediate(get_scalar_format(op0.node_format), 1), vl)
    op0_1bit_hi_shift = Operation(op0.node_format, OperationDesciptor(OperationType.SRL), op0_inv_2bits, Immediate(get_scalar_format(op0.node_format), 1), vl)
    op0_1bit_hi_masked = Operation(op0.node_format, OperationDesciptor(OperationType.AND), op0_1bit_hi_shift, mask_1bit, vl)
    op0_inv_1bit = Operation(op0.node_format, OperationDesciptor(OperationType.OR), op0_1bit_lo_shift, op0_1bit_hi_masked, vl)
    return op0_inv_1bit

def rev8(op0: Node, vl: Node) -> Node:
    """ Emulate byte reversal in element using only base operations """
    elt_size = element_size(op0.node_format.elt_type)
    mask_elt_size = (1 << (elt_size)) - 1
    # word swap
    if elt_size > 32:
        word_mask = Immediate(op0.node_format, 0xffffffff & mask_elt_size)
        op0_lo = Operation(op0.node_format, OperationDesciptor(OperationType.AND), op0, word_mask, vl)
        op0_hi = Operation(op0.node_format, OperationDesciptor(OperationType.SRL), op0, Immediate(get_scalar_format(op0.node_format), 32), vl)
        op0_lo_shift = Operation(op0.node_format, OperationDesciptor(OperationType.SLL), op0_lo, Immediate(get_scalar_format(op0.node_format), 32), vl)
        op0_hi_masked = Operation(op0.node_format, OperationDesciptor(OperationType.AND), op0_hi, word_mask, vl)
        op0 = Operation(op0.node_format, OperationDesciptor(OperationType.OR), op0_lo_shift, op0_hi_masked, vl)
    
    # half word swap
    if elt_size > 16:
        half_word_mask = Immediate(op0.node_format, 0xffff0000ffff & mask_elt_size)
        op0_lo = Operation(op0.node_format, OperationDesciptor(OperationType.AND), op0, half_word_mask, vl)
        op0_hi = Operation(op0.node_format, OperationDesciptor(OperationType.SRL), op0, Immediate(get_scalar_format(op0.node_format), 16), vl)
        op0_lo_shift = Operation(op0.node_format, OperationDesciptor(OperationType.SLL), op0_lo, Immediate(get_scalar_format(op0.node_format), 16), vl)
        op0_hi_masked = Operation(op0.node_format, OperationDesciptor(OperationType.AND), op0_hi, half_word_mask, vl)
        op0 = Operation(op0.node_format, OperationDesciptor(OperationType.OR), op0_lo_shift, op0_hi_masked, vl)

    # last byte swap
    if elt_size > 8:
        byte_mask = Immediate(op0.node_format, 0xff00ff00ff00ff & mask_elt_size)
        op0_lo = Operation(op0.node_format, OperationDesciptor(OperationType.AND), op0, byte_mask, vl)
        op0_hi = Operation(op0.node_format, OperationDesciptor(OperationType.SRL), op0, Immediate(get_scalar_format(op0.node_format), 8), vl)
        op0_lo_shift = Operation(op0.node_format, OperationDesciptor(OperationType.SLL), op0_lo, Immediate(get_scalar_format(op0.node_format), 8), vl)
        op0_hi_masked = Operation(op0.node_format, OperationDesciptor(OperationType.AND), op0_hi, byte_mask, vl)
        op0 = Operation(op0.node_format, OperationDesciptor(OperationType.OR), op0_lo_shift, op0_hi_masked, vl)
    return op0


def generate_zvkb_emulation():
    """Generate all Zvkb rotate instruction emulations."""
    output = []
    
    vl_type = NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None)
    vl = Input(vl_type, 2, name="vl")

    output.append("#include <stdint.h>\n")
    output.append("#include <riscv_vector.h>\n")
    output.append("#include <stddef.h>\n")

    for elt_type in [EltType.U8, EltType.U16, EltType.U32, EltType.U64]:
        uint_t = NodeFormatDescriptor(NodeFormatType.SCALAR, elt_type, lmul_type=None)
        rhs_vx = Input(uint_t, 1)
        for lmul in [LMULType.M1, LMULType.M2, LMULType.M4, LMULType.M8]:
            vuintm_t = NodeFormatDescriptor(NodeFormatType.VECTOR, elt_type, lmul)
            
            lhs = Input(vuintm_t, 0)
            rhs = Input(vuintm_t, 1)

            vuintm_vror_vv_prototype = Operation(
                vuintm_t,
                OperationDesciptor(OperationType.ROR),
                lhs,
                rhs,
                vl
            )
            vuintm_vror_vv_emulation = rotate_right(lhs, rhs, vl)

            vuintm_vror_vx_prototype = Operation(
                vuintm_t,
                OperationDesciptor(OperationType.ROR),
                lhs,
                rhs_vx,
                vl
            )
            vuintm_vror_vx_emulation = rotate_right(lhs, rhs_vx, vl)

            vuintm_vrol_vv_prototype = Operation(
                vuintm_t,
                OperationDesciptor(OperationType.ROL),
                lhs,
                rhs,
                vl
            )
            vuintm_vrol_vv_emulation = rotate_left(lhs, rhs, vl)

            vuintm_vrol_vx_prototype = Operation(
                vuintm_t,
                OperationDesciptor(OperationType.ROL),
                lhs,
                rhs_vx,
                vl
            )
            vuintm_vrol_vx_emulation = rotate_left(lhs, rhs_vx, vl)

            vuintm_vandn_vv_prototype = Operation(
                vuintm_t,
                OperationDesciptor(OperationType.ANDN),
                lhs,
                rhs,
                vl
            )
            vuintm_vandn_vv_emulation = and_not(lhs, rhs, vl)

            vuintm_vandn_vx_prototype = Operation(
                vuintm_t,
                OperationDesciptor(OperationType.ANDN),
                lhs,
                rhs_vx,
                vl
            )
            vuintm_vandn_vx_emulation = and_not(lhs, rhs_vx, vl)

            vuintm_brev8_v_prototype = Operation(
                vuintm_t,
                OperationDesciptor(OperationType.BREV8),
                lhs,
                vl
            )
            vuintm_brev8_v_emulation = brev8(lhs, vl)

            vuintm_rev8_v_prototype = Operation(
                vuintm_t,
                OperationDesciptor(OperationType.REV8),
                lhs,
                vl
            )
            vuintm_rev8_v_emulation = rev8(lhs, vl)

            zvkb_insns = [
                (vuintm_vror_vv_prototype, vuintm_vror_vv_emulation),
                (vuintm_vror_vx_prototype, vuintm_vror_vx_emulation),
                (vuintm_vrol_vv_prototype, vuintm_vrol_vv_emulation),
                (vuintm_vrol_vx_prototype, vuintm_vrol_vx_emulation),
                (vuintm_vandn_vv_prototype, vuintm_vandn_vv_emulation),
                (vuintm_vandn_vx_prototype, vuintm_vandn_vx_emulation),
                (vuintm_brev8_v_prototype, vuintm_brev8_v_emulation),
                (vuintm_rev8_v_prototype, vuintm_rev8_v_emulation)
            ]

            output.append("// prototypes")
            for prototype in [p for p, e in zvkb_insns]:
                output.append(generate_intrinsic_prototype(prototype))
            output.append("\n// intrinsics")
            for prototype, emulation in zvkb_insns:
                output.append(generate_intrinsic_from_operation(prototype, emulation))
    
    return "\n".join(output)


def main():
    """CLI entry point for generating Zvkb emulation code."""
    print(generate_zvkb_emulation())


if __name__ == "__main__":
    main()
