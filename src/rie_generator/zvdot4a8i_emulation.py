"""
Zvdot4a8i (Vector 4-element Dot Product of packed 8-bit Integers)
instruction emulation generator.

This module generates C code for emulating RISC-V Zvdot4a8i vector
dot product instructions (vdota4, vdota4u, vdota4su, vdota4us) using
standard RVV 1.0 intrinsics.

Emulation strategy:
  For each 32-bit element, extract the four 8-bit sub-elements using
  vnsrl (narrowing shift right logical) for vectors or scalar
  shift+mask for scalars, then use vwmacc (widening
  multiply-accumulate) family to accumulate into the 32-bit result.
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
    TailPolicy,
    MaskPolicy,
)


def extract_byte_lane(src: Node, lane: int, narrow_lmul: LMULType, vl: Node) -> Node:
    """Extract 8-bit lane from a 32-bit source (vector or scalar).

    For vectors: uses vnsrl (narrowing shift right logical)
    For scalars: uses scalar shift + mask
    """
    if src.node_format.node_format_type == NodeFormatType.VECTOR:
        narrow_u8_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U8, narrow_lmul)
        shift = Immediate(get_scalar_format(src.node_format), lane * 8)
        return Operation(narrow_u8_fmt, OperationDesciptor(OperationType.NSRL), src, shift, vl)
    else:
        # scalar: shift right and mask to get byte
        scalar_u8_fmt = NodeFormatDescriptor(NodeFormatType.SCALAR, EltType.U8)
        if lane == 0:
            return Operation(
                scalar_u8_fmt, OperationDesciptor(OperationType.AND),
                src, Immediate(get_scalar_format(src.node_format), 0xFF)
            )
        else:
            shifted = Operation(
                src.node_format, OperationDesciptor(OperationType.SRL),
                src, Immediate(get_scalar_format(src.node_format), lane * 8)
            )
            return Operation(
                scalar_u8_fmt, OperationDesciptor(OperationType.AND),
                shifted, Immediate(get_scalar_format(src.node_format), 0xFF)
            )


def dot4_uu(vs2: Node, vs1: Node, vd: Node, vl: Node) -> Node:
    """Emulate vdota4u: unsigned-unsigned 4-element dot product.

    vd[i] += u8(vs2[i][0]) * u8(vs1[i][0])
           + u8(vs2[i][1]) * u8(vs1[i][1])
           + u8(vs2[i][2]) * u8(vs1[i][2])
           + u8(vs2[i][3]) * u8(vs1[i][3])
    """
    narrow_lmul = LMULType.divide(vs2.node_format.lmul_type, 4)

    acc = vd
    for lane in range(4):
        vs2_lane = extract_byte_lane(vs2, lane, narrow_lmul, vl)
        vs1_lane = extract_byte_lane(vs1, lane, narrow_lmul, vl)
        acc = Operation(
            vd.node_format, OperationDesciptor(OperationType.WMACCU),
            vs1_lane, vs2_lane, vl,
            dst=acc, tail_policy=TailPolicy.UNDISTURBED
        )
    return acc


def dot4_ss(vs2: Node, vs1: Node, vd: Node, vl: Node) -> Node:
    """Emulate vdota4: signed-signed 4-element dot product.

    vd[i] += s8(vs2[i][0]) * s8(vs1[i][0])
           + s8(vs2[i][1]) * s8(vs1[i][1])
           + s8(vs2[i][2]) * s8(vs1[i][2])
           + s8(vs2[i][3]) * s8(vs1[i][3])

    Uses vnsrl to extract raw bytes (unsigned), then vwmacc to
    interpret them as signed and perform widening multiply-accumulate.
    Note: vwmacc reinterprets the raw bytes as signed.
    """
    narrow_lmul = LMULType.divide(vs2.node_format.lmul_type, 4)

    acc = vd
    for lane in range(4):
        vs2_lane = extract_byte_lane(vs2, lane, narrow_lmul, vl)
        vs1_lane = extract_byte_lane(vs1, lane, narrow_lmul, vl)
        acc = Operation(
            vd.node_format, OperationDesciptor(OperationType.WMACC),
            vs1_lane, vs2_lane, vl,
            dst=acc, tail_policy=TailPolicy.UNDISTURBED
        )
    return acc


def dot4_su(vs2: Node, vs1: Node, vd: Node, vl: Node) -> Node:
    """Emulate vdota4su: signed(vs2)-unsigned(vs1) 4-element dot product.

    vd[i] += s8(vs2[i][0]) * u8(vs1[i][0])
           + s8(vs2[i][1]) * u8(vs1[i][1])
           + s8(vs2[i][2]) * u8(vs1[i][2])
           + s8(vs2[i][3]) * u8(vs1[i][3])

    Uses vwmaccsu: signed * unsigned widening multiply-accumulate.
    __riscv_vwmaccsu(vd, signed_op, unsigned_op, vl)
    -> vs2 lanes are the signed operand, vs1 lanes are unsigned.
    """
    narrow_lmul = LMULType.divide(vs2.node_format.lmul_type, 4)

    acc = vd
    for lane in range(4):
        # vs2 sub-elements are signed, vs1 sub-elements are unsigned
        vs2_lane = extract_byte_lane(vs2, lane, narrow_lmul, vl)
        vs1_lane = extract_byte_lane(vs1, lane, narrow_lmul, vl)
        # vwmaccsu(vd, signed, unsigned, vl)
        acc = Operation(
            vd.node_format, OperationDesciptor(OperationType.WMACCSU),
            vs2_lane, vs1_lane, vl,
            dst=acc, tail_policy=TailPolicy.UNDISTURBED
        )
    return acc


def dot4_us(vs2: Node, rs1: Node, vd: Node, vl: Node) -> Node:
    """Emulate vdota4us: unsigned(vs2)-signed(rs1) 4-element dot product (vx only).

    vd[i] += u8(vs2[i][0]) * s8(rs1[0])
           + u8(vs2[i][1]) * s8(rs1[1])
           + u8(vs2[i][2]) * s8(rs1[2])
           + u8(vs2[i][3]) * s8(rs1[3])

    Uses vwmaccus: unsigned * signed widening multiply-accumulate.
    __riscv_vwmaccus(vd, unsigned_scalar, signed_vector, vl)
    Note: vx-only, rs1 is a scalar holding 4 packed bytes.
    """
    narrow_lmul = LMULType.divide(vs2.node_format.lmul_type, 4)

    acc = vd
    for lane in range(4):
        vs2_lane = extract_byte_lane(vs2, lane, narrow_lmul, vl)
        rs1_lane = extract_byte_lane(rs1, lane, narrow_lmul, vl)
        # vwmaccus(vd, unsigned_scalar, signed_vector, vl)
        acc = Operation(
            vd.node_format, OperationDesciptor(OperationType.WMACCUS),
            rs1_lane, vs2_lane, vl,
            dst=acc, tail_policy=TailPolicy.UNDISTURBED
        )
    return acc


# LMUL values valid for 32-bit elements (SEW=32)
# M1 -> 8-bit uses MF4, M2 -> MF2, M4 -> M1, M8 -> M2
VALID_32BIT_LMULS = [LMULType.M1, LMULType.M2, LMULType.M4, LMULType.M8]


def generate_zvdot4a8i_emulation(attributes: list[str] = [], prototypes: bool = False, definitions: bool = True):
    """Generate all Zvdot4a8i instruction emulations.

    Generates emulation code for:
      - vdota4.vv / vdota4.vx   (signed-signed)
      - vdota4u.vv / vdota4u.vx (unsigned-unsigned)
      - vdota4su.vv / vdota4su.vx (signed-unsigned)
      - vdota4us.vx              (unsigned-signed, vx only)
    """
    output = []

    vl_type = NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None)
    vl = Input(vl_type, 3, name="vl")

    output.append("#include <stdint.h>\n")
    output.append("#include <riscv_vector.h>\n")
    output.append("#include <stddef.h>\n")

    for lmul in VALID_32BIT_LMULS:
        # Accumulator / result type: 32-bit signed or unsigned
        vint32_t = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.S32, lmul)
        vuint32_t = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U32, lmul)

        # Scalar operand type (32 bits, holding 4 packed 8-bit values)
        scalar_u32_t = NodeFormatDescriptor(NodeFormatType.SCALAR, EltType.U32, lmul_type=None)

        # Inputs
        vs2_u = Input(vuint32_t, 0, name="vs2")
        vs1_u = Input(vuint32_t, 1, name="vs1")
        vd_u  = Input(vuint32_t, 2, name="vd")
        rs1_u = Input(scalar_u32_t, 1, name="rs1")

        vs2_s = Input(vint32_t, 0, name="vs2")
        vs1_s = Input(vint32_t, 1, name="vs1")
        vd_s  = Input(vint32_t, 2, name="vd")
        rs1_s = Input(scalar_u32_t, 1, name="rs1")

        zvdot4a8i_insns = []

        # --- vdota4u: unsigned-unsigned ---
        # vv variant
        proto_dota4u_vv = Operation(
            vuint32_t, OperationDesciptor(OperationType.DOTA4U),
            vs2_u, vs1_u, vl,
            dst=vd_u, tail_policy=TailPolicy.UNDISTURBED
        )
        emul_dota4u_vv = dot4_uu(vs2_u, vs1_u, vd_u, vl)
        zvdot4a8i_insns.append((proto_dota4u_vv, emul_dota4u_vv))

        # vx variant
        proto_dota4u_vx = Operation(
            vuint32_t, OperationDesciptor(OperationType.DOTA4U),
            vs2_u, rs1_u, vl,
            dst=vd_u, tail_policy=TailPolicy.UNDISTURBED
        )
        emul_dota4u_vx = dot4_uu(vs2_u, rs1_u, vd_u, vl)
        zvdot4a8i_insns.append((proto_dota4u_vx, emul_dota4u_vx))

        # --- vdota4: signed-signed ---
        # vv variant
        proto_dota4_vv = Operation(
            vint32_t, OperationDesciptor(OperationType.DOTA4),
            vs2_s, vs1_s, vl,
            dst=vd_s, tail_policy=TailPolicy.UNDISTURBED
        )
        emul_dota4_vv = dot4_ss(vs2_s, vs1_s, vd_s, vl)
        zvdot4a8i_insns.append((proto_dota4_vv, emul_dota4_vv))

        # vx variant
        proto_dota4_vx = Operation(
            vint32_t, OperationDesciptor(OperationType.DOTA4),
            vs2_s, rs1_s, vl,
            dst=vd_s, tail_policy=TailPolicy.UNDISTURBED
        )
        emul_dota4_vx = dot4_ss(vs2_s, rs1_s, vd_s, vl)
        zvdot4a8i_insns.append((proto_dota4_vx, emul_dota4_vx))

        # --- vdota4su: signed(vs2)-unsigned(vs1) ---
        # vv variant: vs2 signed, vs1 unsigned
        proto_dota4su_vv = Operation(
            vint32_t, OperationDesciptor(OperationType.DOTA4SU),
            vs2_s, vs1_u, vl,
            dst=vd_s, tail_policy=TailPolicy.UNDISTURBED
        )
        emul_dota4su_vv = dot4_su(vs2_s, vs1_u, vd_s, vl)
        zvdot4a8i_insns.append((proto_dota4su_vv, emul_dota4su_vv))

        # vx variant
        proto_dota4su_vx = Operation(
            vint32_t, OperationDesciptor(OperationType.DOTA4SU),
            vs2_s, rs1_u, vl,
            dst=vd_s, tail_policy=TailPolicy.UNDISTURBED
        )
        emul_dota4su_vx = dot4_su(vs2_s, rs1_u, vd_s, vl)
        zvdot4a8i_insns.append((proto_dota4su_vx, emul_dota4su_vx))

        # --- vdota4us: unsigned(vs2)-signed(rs1), vx only ---
        proto_dota4us_vx = Operation(
            vint32_t, OperationDesciptor(OperationType.DOTA4US),
            vs2_u, rs1_s, vl,
            dst=vd_s, tail_policy=TailPolicy.UNDISTURBED
        )
        emul_dota4us_vx = dot4_us(vs2_u, rs1_s, vd_s, vl)
        zvdot4a8i_insns.append((proto_dota4us_vx, emul_dota4us_vx))

        if prototypes:
            output.append(f"// Zvdot4a8i prototypes (LMUL={LMULType.to_string(lmul)})")
            for proto, _ in zvdot4a8i_insns:
                output.append(generate_intrinsic_prototype(proto))

        if definitions:
            output.append(f"\n// Zvdot4a8i definitions (LMUL={LMULType.to_string(lmul)})")
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
    parser.add_argument("-p", "--prototype", default=False, action="store", type=bool, help="generate prototypes")
    parser.add_argument("-d", "--definition", default=True, action="store", type=bool, help="generate definitions")
    args = parser.parse_args()

    main(attributes=args.attributes, prototypes=args.prototype, definitions=args.definition)
