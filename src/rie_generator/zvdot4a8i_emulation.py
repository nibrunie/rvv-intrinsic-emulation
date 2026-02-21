"""
Zvdot4a8i (Vector 4-element Dot Product of packed 8-bit Integers)
instruction emulation generator.

This module generates C code for emulating RISC-V Zvdot4a8i vector
dot product instructions (vdota4, vdota4u, vdota4su, vdota4us) using
standard RVV 1.0 intrinsics.

Emulation strategy (widening multiply + pairwise reduction):
  1. Widening multiply all 4 byte lanes at once (SEW=8, vl=4*orig_vl)
  2. Extract high/low product pairs via narrowing shift (SEW=64→32)
  3. Widening add high + low pairs (SEW=16→32)
  4. Extract high/low sums via narrowing shift (SEW=64→32)
  5. Add high + low sums (SEW=32)
  6. Add with accumulator vd (SEW=32)
"""

from .core import (
    Operation,
    OperationDesciptor,
    NodeFormatDescriptor,
    NodeFormatType,
    Immediate,
    Input,
    Node,
    EltType,
    expand_reinterpret_cast,
    LMULType,
    OperationType,
    generate_intrinsic_prototype,
    generate_intrinsic_from_operation,
    TailPolicy,
    MaskPolicy,
)


def dot4_pipeline(
        vs2: Node,
        vs1: Node,
        vd: Node,
        vl: Node,
        wmul_op: OperationType,
        wadd_op: OperationType,
        lmul: LMULType,
        tail_policy: TailPolicy,
        mask_policy: MaskPolicy,
        vm: Node = None
    ) -> Node:
    """Common dot product emulation pipeline.

    Args:
        vs2: first source operand (vector, 32-bit elements)
        vs1: second source operand (vector or scalar, 32-bit)
        vd: accumulator source (vector, 32-bit)
        vl: vector length
        wmul_op: widening multiply operation type (WMUL, WMULU, WMULSU)
        wadd_op: widening add operation type (WADD, WADDU)
        lmul: original LMUL for 32-bit elements
        tail_policy: tail policy
        mask_policy: mask policy
        vm: mask
    """
    # M8 splitting: split into two M4 halves, process independently, reassemble
    if lmul == LMULType.M8:
        half_lmul = LMULType.M4
        vl_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None)
        idx_fmt = NodeFormatDescriptor(NodeFormatType.IMMEDIATE, EltType.SIZE_T)

        # Derive M4/M8 formats from each input's own element type
        def make_m4(node):
            return NodeFormatDescriptor(NodeFormatType.VECTOR, node.node_format.elt_type, half_lmul)

        def get_halves(node):
            m4 = make_m4(node)
            lo = Operation(m4, OperationDesciptor(OperationType.GET), node, Immediate(idx_fmt, 0))
            hi = Operation(m4, OperationDesciptor(OperationType.GET), node, Immediate(idx_fmt, 1))
            return lo, hi

        # GET: extract low (index 0) and high (index 1) M4 chunks
        # For scalar operands, pass through directly (e.g. vdota4us swaps rs1 into vs2)
        if vs2.node_format.node_format_type == NodeFormatType.VECTOR:
            vs2_lo, vs2_hi = get_halves(vs2)
        else:
            vs2_lo = vs2
            vs2_hi = vs2
        vd_lo, vd_hi = get_halves(vd)

        # For vector vs1, split; for scalar vs1, pass through directly
        if vs1.node_format.node_format_type == NodeFormatType.VECTOR:
            vs1_lo, vs1_hi = get_halves(vs1)
        else:
            vs1_lo = vs1
            vs1_hi = vs1

        # vl_half = vl / 2
        vl_half = Operation(vl_fmt, OperationDesciptor(OperationType.DIV),
                            vl, Immediate(vl_fmt, 2))

        # Process each M4 half independently
        result_lo = dot4_pipeline(vs2_lo, vs1_lo, vd_lo, vl_half,
                                  wmul_op, wadd_op, half_lmul,
                                  tail_policy, mask_policy, vm=None)
        result_hi = dot4_pipeline(vs2_hi, vs1_hi, vd_hi, vl_half,
                                  wmul_op, wadd_op, half_lmul,
                                  tail_policy, mask_policy, vm=None)

        # CREATE: reassemble two M4 results into M8 (result type matches vd)
        result_elt = vd.node_format.elt_type
        m4_result_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, result_elt, half_lmul)
        m8_result_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, result_elt, LMULType.M8)
        result = Operation(m8_result_fmt, OperationDesciptor(OperationType.CREATE),
                           result_lo, result_hi)
        return result

    # --- Standard path (M1, M2, M4): requires 2*LMUL ≤ M8 ---
    # Derived formats
    lmul_x2 = LMULType.multiply(lmul, 2)
    # SEW=8 at original LMUL (same register group as 32-bit, 4x more elements)
    u8_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U8, lmul)
    s8_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.S8, lmul)
    # SEW=16 at 2*LMUL (widening multiply result)
    u16_x2_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U16, lmul_x2)
    s16_x2_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.S16, lmul_x2)
    # SEW=32 at original LMUL (narrowing result)
    u32_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U32, lmul)
    s32_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.S32, lmul)
    # SEW=16 at original LMUL (for widening add sources)
    u16_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U16, lmul)
    s16_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.S16, lmul)
    # SEW=32 at 2*LMUL (widening add result)
    u32_x2_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U32, lmul_x2)
    s32_x2_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.S32, lmul_x2)
    # SEW=64 at 2*LMUL (narrowing result)
    u64_x2_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U64, lmul_x2)
    s64_x2_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.S64, lmul_x2)

    # Choose signed/unsigned formats based on multiply type
    is_result_signed = wmul_op in (OperationType.WMUL, OperationType.WMULSU)
    prod_16_x2_fmt = s16_x2_fmt if is_result_signed else u16_x2_fmt
    prod_32_fmt = s32_fmt if is_result_signed else u32_fmt
    sum_16_fmt = s16_fmt if is_result_signed else u16_fmt
    sum_32_x2_fmt = s32_x2_fmt if is_result_signed else u32_x2_fmt
    result_32_fmt = vd.node_format

    result_64_x2_fmt = s64_x2_fmt if is_result_signed else u64_x2_fmt

    # Scalar formats for shift amounts and vl multiplier
    scalar_u32_fmt = NodeFormatDescriptor(NodeFormatType.SCALAR, EltType.U32)
    vl_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None)

    vs2_is_signed = wmul_op in (OperationType.WMUL, OperationType.WMULSU)
    vs1_is_signed = wmul_op in (OperationType.WMUL, OperationType.WMUL)
    vs1_fmt = s8_fmt if vs1_is_signed else u8_fmt
    vs2_fmt = s8_fmt if vs2_is_signed else u8_fmt

    if vs1.node_format.node_format_type is NodeFormatType.SCALAR:
        vs1 = Operation(u32_fmt, OperationDesciptor(OperationType.MV), vs1, vl)
    if vs2.node_format.node_format_type is NodeFormatType.SCALAR:
        vs2 = Operation(u32_fmt, OperationDesciptor(OperationType.MV), vs2, vl)


    assert vs2.node_format.node_format_type is NodeFormatType.VECTOR
    assert vs1.node_format.node_format_type is NodeFormatType.VECTOR

    # Step 0: Reinterpret vs1 as u8
    #vs1_u8 = Operation(u8_fmt, OperationDesciptor(OperationType.REINTERPRET), vs1)
    vs1_e8 = expand_reinterpret_cast(vs1, vs1_fmt)
    # Since vs2/vs1 might be swapped, we also need to check whether vs2/rs2 needs to
    # be reinterpreted
    #vs2_u8 = Operation(u8_fmt, OperationDesciptor(OperationType.REINTERPRET), vs2)
    vs2_e8 = expand_reinterpret_cast(vs2, vs2_fmt)

    # Step 1: vl_x4 = 4 * vl (for SEW=8 operations)
    vl_x4 = Operation(vl_fmt, OperationDesciptor(OperationType.MUL),
                       vl, Immediate(vl_fmt, 4))
    # Step 1 (cont.): vl_x2 = 2 * vl (for SEW=16 operations)
    vl_x2 = Operation(vl_fmt, OperationDesciptor(OperationType.MUL),
                       vl, Immediate(vl_fmt, 2))

    # Step 1: Widening multiply 8-bit to 16-bit
    # SEW=8, LMUL=original, vl=4*original_vl
    products = Operation(prod_16_x2_fmt, OperationDesciptor(wmul_op),
                         vs2_e8, vs1_e8, vl_x4)

    # reinterpret products as SEW=64  with 2x original LMUL (and original vl, since 64 is twice the original 32-bit SEW)
    products = Operation(result_64_x2_fmt, OperationDesciptor(OperationType.REINTERPRET), products)

    # narrowing shift only operates on unsigned element, so casting might be required here
    products = expand_reinterpret_cast(products, u64_x2_fmt)

    # Step 2: Extract high products via narrow right shift by 32
    # Source: products viewed as SEW=64 at 2*LMUL, result: SEW=32 at LMUL
    shift_32 = Immediate(scalar_u32_fmt, 32)
    high_products = Operation(u32_fmt, OperationDesciptor(OperationType.NSRL),
                              products, shift_32, vl)

    # Step 3: Extract low products via narrow right shift by 0
    shift_0 = Immediate(scalar_u32_fmt, 0)
    low_products = Operation(u32_fmt, OperationDesciptor(OperationType.NSRL),
                             products, shift_0, vl)

    high_products = expand_reinterpret_cast(high_products, prod_32_fmt)
    low_products = expand_reinterpret_cast(low_products, prod_32_fmt)

    high_products = Operation(sum_16_fmt, OperationDesciptor(OperationType.REINTERPRET),
                              high_products)
    low_products = Operation(sum_16_fmt, OperationDesciptor(OperationType.REINTERPRET),
                              low_products)

    # Step 4: Widening addition of high and low products
    # Source: SEW=16 at LMUL, vl=2*original_vl, result: SEW=32 at 2*LMUL
    sums = Operation(sum_32_x2_fmt, OperationDesciptor(wadd_op),
                     high_products, low_products, vl_x2)

    # Reinterpret sums as SEW=64 at 2*LMUL
    sums = Operation(result_64_x2_fmt, OperationDesciptor(OperationType.REINTERPRET), sums)

    sums = expand_reinterpret_cast(sums, u64_x2_fmt)

    # Step 5: Extract high sums via narrow right shift by 32
    # Source: sums viewed as SEW=64 at 2*LMUL, result: SEW=32 at LMUL
    high_sums = Operation(u32_fmt, OperationDesciptor(OperationType.NSRL),
                          sums, shift_32, vl)

    # Step 6: Extract low sums via narrow right shift by 0
    low_sums = Operation(u32_fmt, OperationDesciptor(OperationType.NSRL),
                         sums, shift_0, vl)

    high_sums = expand_reinterpret_cast(high_sums, result_32_fmt)
    low_sums = expand_reinterpret_cast(low_sums, result_32_fmt)

    # Step 7: Single-width addition of high and low sums (SEW=32)
    partial_sum = Operation(result_32_fmt, OperationDesciptor(OperationType.ADD),
                            high_sums, low_sums, vl)

    # Step 8: Final single-width addition with accumulator (vd)
    result = Operation(result_32_fmt, OperationDesciptor(OperationType.ADD),
                       partial_sum, vd, vl, tail_policy=tail_policy, mask_policy=mask_policy, dst=vd, vm=vm)

    return result


# LMUL values valid for 32-bit elements (SEW=32)
# M1-M4 use the standard widening pipeline; M8 uses the CREATE/GET split path
VALID_32BIT_LMULS = [LMULType.M1, LMULType.M2, LMULType.M4, LMULType.M8]


def generate_zvdot4a8i_emulation(attributes: list[str] = [], prototypes: bool = False, definitions: bool = True,
                                  lmul_filter: list = None, tail_policy_filter: list = None, mask_policy_filter: list = None):
    """Generate all Zvdot4a8i instruction emulations.

    Args:
        attributes: list of attributes to add to the generated code
        prototypes: if True, generate prototypes only
        definitions: if True, generate definitions only
        lmul_filter: if set, only generate for these LMULType values
        tail_policy_filter: if set, only generate for these TailPolicy values
        mask_policy_filter: if set, only generate for these MaskPolicy values

    Generates emulation code for:
      - vdota4.vv / vdota4.vx   (signed-signed)
      - vdota4u.vv / vdota4u.vx (unsigned-unsigned)
      - vdota4su.vv / vdota4su.vx (signed-unsigned)
      - vdota4us.vx              (unsigned-signed, vx only)
    """
    output = []

    vl_type = NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None)
    vl = Input(vl_type, 3, name="vl")
    all_tail_policies = [TailPolicy.UNDISTURBED, TailPolicy.AGNOSTIC]
    all_mask_policies = [MaskPolicy.UNDISTURBED, MaskPolicy.AGNOSTIC, MaskPolicy.UNMASKED]

    output.append("#include <stdint.h>\n")
    output.append("#include <riscv_vector.h>\n")
    output.append("#include <stddef.h>\n")

    lmuls = [l for l in VALID_32BIT_LMULS if lmul_filter is None or l in lmul_filter]
    tail_policies = [t for t in all_tail_policies if tail_policy_filter is None or t in tail_policy_filter]
    mask_policies = [m for m in all_mask_policies if mask_policy_filter is None or m in mask_policy_filter]

    for lmul in lmuls:
        for tail_policy in tail_policies:
            for mask_policy in mask_policies:
                vint32_t = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.S32, lmul)
                vuint32_t = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U32, lmul)
                scalar_u32_t = NodeFormatDescriptor(NodeFormatType.SCALAR, EltType.U32, lmul_type=None)
                vbooln_t = NodeFormatDescriptor(NodeFormatType.MASK, EltType.U32, lmul)

                # --- Inputs ---
                vs2_u = Input(vuint32_t, 0, name="vs2")
                vs1_u = Input(vuint32_t, 1, name="vs1")
                vd_u  = Input(vuint32_t, 2, name="vd")
                rs1_u = Input(scalar_u32_t, 1, name="rs1")

                vs2_s = Input(vint32_t, 0, name="vs2")
                vs1_s = Input(vint32_t, 1, name="vs1")
                vd_s  = Input(vint32_t, 2, name="vd")
                rs1_s = Input(scalar_u32_t, 1, name="rs1")

                # vd_dst = Input(vint32_t, -1, name="vd")
                vm = Input(vbooln_t, -2, name="vm")
                
                # dst = vd_dst if tail_policy == TailPolicy.UNDISTURBED or mask_policy == MaskPolicy.UNDISTURBED else None

                zvdot4a8i_insns = []

                # --- vdota4u: unsigned-unsigned ---
                # vv
                proto_dota4u_vv = Operation(
                    vuint32_t, OperationDesciptor(OperationType.DOT4AU),
                    vd_u, vs2_u, vs1_u, vl,
                    dst=vd_u, tail_policy=tail_policy, mask_policy=mask_policy, vm=vm
                )
                emul_dota4u_vv = dot4_pipeline(vs2_u, vs1_u, vd_u, vl, OperationType.WMULU, OperationType.WADDU, lmul, tail_policy, mask_policy, vm)
                zvdot4a8i_insns.append((proto_dota4u_vv, emul_dota4u_vv))

                # vx: use vector-scalar widening multiply directly
                proto_dota4u_vx = Operation(
                    vuint32_t, OperationDesciptor(OperationType.DOT4AU),
                    vd_u, vs2_u, rs1_u, vl,
                    dst=vd_u, tail_policy=tail_policy, mask_policy=mask_policy, vm=vm
                )
                emul_dota4u_vx = dot4_pipeline(vs2_u, rs1_u, vd_u, vl, OperationType.WMULU, OperationType.WADDU, lmul, tail_policy, mask_policy, vm)
                zvdot4a8i_insns.append((proto_dota4u_vx, emul_dota4u_vx))

                # --- vdota4: signed-signed ---
                # vv
                proto_dota4_vv = Operation(
                    vint32_t, OperationDesciptor(OperationType.DOT4A),
                    vd_s, vs2_s, vs1_s, vl,
                    dst=vd_s, tail_policy=tail_policy, mask_policy=mask_policy, vm=vm
                )
                emul_dota4_vv = dot4_pipeline(vs2_s, vs1_s, vd_s, vl, OperationType.WMUL, OperationType.WADD, lmul, tail_policy, mask_policy, vm)
                zvdot4a8i_insns.append((proto_dota4_vv, emul_dota4_vv))

                # vx
                proto_dota4_vx = Operation(
                    vint32_t, OperationDesciptor(OperationType.DOT4A),
                    vd_s, vs2_s, rs1_s, vl,
                    dst=vd_s, tail_policy=tail_policy, mask_policy=mask_policy, vm=vm
                )
                emul_dota4_vx = dot4_pipeline(vs2_s, rs1_s, vd_s, vl, OperationType.WMUL, OperationType.WADD, lmul, tail_policy, mask_policy, vm)
                zvdot4a8i_insns.append((proto_dota4_vx, emul_dota4_vx))

                # --- vdota4su: signed(vs2)-unsigned(vs1) ---
                # vv
                proto_dota4su_vv = Operation(
                    vint32_t, OperationDesciptor(OperationType.DOT4ASU),
                    vd_s, vs2_s, vs1_u, vl,
                    dst=vd_s, tail_policy=tail_policy, mask_policy=mask_policy, vm=vm
                )
                emul_dota4su_vv = dot4_pipeline(vs2_s, vs1_u, vd_s, vl, OperationType.WMULSU, OperationType.WADD, lmul, tail_policy, mask_policy, vm)
                zvdot4a8i_insns.append((proto_dota4su_vv, emul_dota4su_vv))

                # vx
                proto_dota4su_vx = Operation(
                    vint32_t, OperationDesciptor(OperationType.DOT4ASU),
                    vd_s, vs2_s, rs1_u, vl,
                    dst=vd_s, tail_policy=tail_policy, mask_policy=mask_policy, vm=vm
                )
                emul_dota4su_vx = dot4_pipeline(vs2_s, rs1_u, vd_s, vl, OperationType.WMULSU, OperationType.WADD, lmul, tail_policy, mask_policy, vm)
                zvdot4a8i_insns.append((proto_dota4su_vx, emul_dota4su_vx))

                # --- vdota4us: unsigned(vs2)-signed(rs1), vx only ---
                # vwmulsu_vx(vs2, rs1) treats vs2 as signed and rs1 as unsigned.
                # We need unsigned(vs2) * signed(rs1), so we use swapped operand order.
                proto_dota4us_vx = Operation(
                    vint32_t, OperationDesciptor(OperationType.DOT4AUS),
                    vd_s, vs2_u, rs1_s, vl,
                    dst=vd_s, tail_policy=tail_policy, mask_policy=mask_policy, vm=vm
                )
                # Pass rs1 first (signed) and vs2 second (unsigned) for vwmulsu
                emul_dota4us_vx = dot4_pipeline(rs1_s, vs2_u, vd_s, vl, OperationType.WMULSU, OperationType.WADD, lmul, tail_policy, mask_policy, vm)
                zvdot4a8i_insns.append((proto_dota4us_vx, emul_dota4us_vx))

                lmul_str = LMULType.to_string(lmul)
                tail_policy_str = TailPolicy.to_string(tail_policy)
                mask_policy_str = MaskPolicy.to_string(mask_policy)

                if prototypes:
                    output.append(f"// Zvdot4a8i prototypes (LMUL={lmul_str}), tail_policy={tail_policy_str}, mask_policy={mask_policy_str}")
                    for proto, _ in zvdot4a8i_insns:
                        output.append(generate_intrinsic_prototype(proto))

                if definitions:
                    output.append(f"\n// Zvdot4a8i definitions (LMUL={lmul_str}), tail_policy={tail_policy_str}, mask_policy={mask_policy_str}")
                    for proto, emul in zvdot4a8i_insns:
                        output.append(generate_intrinsic_from_operation(proto, emul, attributes=attributes))

    return "\n".join(output)


def main(attributes: list[str] = [], prototypes: bool = False, definitions: bool = True):
    """CLI entry point for generating Zvdot4a8i emulation code."""
    print(generate_zvdot4a8i_emulation(attributes, prototypes, definitions))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--attributes", nargs="+", default=[], help="Attributes to add to the generated code")
    parser.add_argument("-p", "--prototypes", default=False, action="store", type=bool, help="generate prototypes")
    parser.add_argument("-d", "--definitions", default=True, action="store", type=bool, help="generate definitions")
    args = parser.parse_args()

    main(attributes=args.attributes, prototypes=args.prototypes, definitions=args.definitions)
