import re

"""
Zvdota family of dot-product extensions emulation generator.

This module generates C code for emulating RISC-V Zvdota vector
dot-product instructions using standard RVV 1.0 intrinsics.

The Zvdota family computes a dot product between two vector register groups
(vs2 and vs1), producing a scalar result accumulated into element 0 of vd.
Other elements of vd are tail and follow the tail agnostic/undisturbed policy.

Sub-extensions covered:

  Zvqwdota8i  — 8-bit integer dot product, 32-bit accumulation
    vqwdotau.vv vd, vs2, vs1, vm   # unsigned(vs2) · vs1 (altfmt selects vs1 sign)
    vqwdotas.vv vd, vs2, vs1, vm   # signed(vs2)   · vs1 (altfmt selects vs1 sign)
    SEW=8, vd EEW=4*SEW=32, depends on Zve32x

  Zvqwdota16i — 16-bit integer dot product, 64-bit accumulation
    Same encodings as Zvqwdota8i but at SEW=16.
    vd EEW=4*SEW=64, depends on Zve64x

  Zvfwdota16bf — BF16 dot product, FP32 accumulation
    vfwdota.vv vd, vs2, vs1, vm    # altfmt=1, SEW=16
    vd EEW=2*SEW=32, depends on Zve32f

  Zvfqwdota8f — OFP8 dot product, FP32 accumulation
    vfqwdota.vv     vd, vs2, vs1, vm   # E4M3(vs2) · vs1 (altfmt selects vs1 fmt)
    vfqwdota.alt.vv vd, vs2, vs1, vm   # E5M2(vs2) · vs1 (altfmt selects vs1 fmt)
    SEW=8, vd EEW=4*SEW=32, depends on Zve32f

Common properties:
  - vs2 and vs1 have EMUL=LMUL, EEW=SEW
  - vd always has EMUL=1
  - These instructions are maskable
  - vstart must be 0
  - vd cannot overlap vs2 or vs1
"""

from .core import (
    Operation,
    OperationDescriptor,
    NodeFormatDescriptor,
    NodeFormatType,
    Immediate,
    Input,
    Node,
    EltType,
    LMULType,
    OperationType,
    generate_intrinsic_name,
    generate_intrinsic_prototype,
    generate_intrinsic_from_operation,
    TailPolicy,
    MaskPolicy,
)

from .description_helper import emulate_with_split_lmul


# ---------------------------------------------------------------------------
# Emulation building blocks
# ---------------------------------------------------------------------------

def vqwdota_emulation(vs2: Node, vs1: Node, vd: Node, vl: Node,
                       tail_policy: TailPolicy = TailPolicy.AGNOSTIC,
                       mask_policy: MaskPolicy = MaskPolicy.UNMASKED,
                       vm: Node = None) -> Operation:
    """Emulate vqwdota.vv (signed or unsigned 8-bit vs2 dot product, 32-bit accumulation).

        Signs are determined from vs2 and vs1 formats.
        The intrinsics expose a single API which is mapped to either vqwdotau.vv or vqwdotas.vv based on the element types.
        For u8 vs u8 => vqwdotau.vv
        For u8 vs i8 => vqwdotau.vv
        For i8 vs u8 => vqwdotas.vv
        For i8 vs i8 => vqwdotas.vv

        vs1 signedness is encoded in vtype.atlfmt (0: unsigned, 1: signed)

    """
    lmul = vs2.node_format.lmul_type
    # M8 and M4 splitting: split into two M4 halves, process independently, reassemble
    if lmul in [LMULType.M4, LMULType.M8]:
        half_lmul = LMULType.divide(lmul, 2)

        # FIXME: the following helper functions have been copied from description_helper.emulate_with_split_lmul.
        # they should be factorized
        idx_fmt = NodeFormatDescriptor(NodeFormatType.IMMEDIATE, EltType.SIZE_T)
        # Derive M4/M8 formats from each input's own element type
        def make_half_lmul_format(node):
            return NodeFormatDescriptor(NodeFormatType.VECTOR, node.node_format.elt_type, half_lmul)
        def get_halves(node):
            half_lmul_format = make_half_lmul_format(node)
            lo = Operation(half_lmul_format, OperationDescriptor(OperationType.GET), node, Immediate(idx_fmt, 0))
            hi = Operation(half_lmul_format, OperationDescriptor(OperationType.GET), node, Immediate(idx_fmt, 1))
            return lo, hi

        vl_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None)
        vs2_split = get_halves(vs2)
        vs1_split = get_halves(vs1)

        half_lmul_result_fmt = NodeFormatDescriptor(NodeFormatType.PLACEHOLDER, vs2.node_format.elt_type, half_lmul)
        placeholder = Immediate(half_lmul_result_fmt, None)
        vlmax_half_lmul = Operation(vl_fmt, OperationDescriptor(OperationType.VSETVLMAX), placeholder)

        # vl_half = vl / 2
        vl_lo = Operation(vl_fmt, OperationDescriptor(OperationType.MIN),
                        vl, vlmax_half_lmul)
        vl_hi = Operation(vl_fmt, OperationDescriptor(OperationType.SUB),
                            vl, vl_lo)

        result_lo = vqwdota_emulation(vs2_split[0], vs1_split[0], vd, vl_lo, tail_policy=TailPolicy.AGNOSTIC, mask_policy=MaskPolicy.UNMASKED, vm=None)
        result_hi = vqwdota_emulation(vs2_split[1], vs1_split[1], result_lo, vl_hi, tail_policy=TailPolicy.AGNOSTIC, mask_policy=MaskPolicy.UNMASKED, vm=None)

        return result_hi

    prod_elt_format = EltType.widen(vs2.node_format.elt_type)
    prod_format = NodeFormatDescriptor(NodeFormatType.VECTOR, prod_elt_format, LMULType.multiply(vs2.node_format.lmul_type, 2))
    if EltType.is_signed(vs2.node_format.elt_type) and EltType.is_signed(vs1.node_format.elt_type):
        mul_op = OperationType.WMUL
        red_op = OperationType.WREDSUM
    elif EltType.is_unsigned(vs2.node_format.elt_type) and EltType.is_unsigned(vs1.node_format.elt_type):
        mul_op = OperationType.WMULU
        red_op = OperationType.WREDSUMU
    else:
        mul_op = OperationType.WMULSU
        red_op = OperationType.WREDSUM
    # widening product
    products = Operation(
        prod_format,
        OperationDescriptor(mul_op),
        # swapping operands to ensure the first operand is signed if at least one of vs2/vs1 are signed
        vs2 if EltType.is_signed(vs2.node_format.elt_type) else vs1,
        vs1 if EltType.is_signed(vs2.node_format.elt_type) else vs2,
        vl,
    )
    # Reduction intrinsincs do not care about the actual mask policy (agnostic/undisturbed),
    # only masked/unmasked is relevant.
    reduction_mask_policy = mask_policy
    if mask_policy != MaskPolicy.UNMASKED:
        reduction_mask_policy = MaskPolicy.AGNOSTIC
    # widening reduction
    red_format = vd.node_format
    reduced = Operation(
        red_format,
        OperationDescriptor(red_op),
        products,
        vd,
        vl,
        vm=vm,
        dst=vd,
        tail_policy=TailPolicy.AGNOSTIC,
        mask_policy=reduction_mask_policy,
    )

    return reduced
    
    
    


def vqwdotas_emulation(vs2: Node, vs1: Node, vd: Node, vl: Node,
                       vm: Node, tail_policy: TailPolicy,
                       mask_policy: MaskPolicy) -> Operation:
    """Emulate vqwdotas.vv (signed 8-bit vs2 dot product, 32-bit accumulation).

    TODO: implement emulation using base RVV 1.0 operations.
    """
    pass


def vfwdota_emulation(vs2: Node, vs1: Node, vd: Node, vl: Node,
                      vm: Node, tail_policy: TailPolicy,
                      mask_policy: MaskPolicy) -> Operation:
    """Emulate vfwdota.vv (BF16 dot product, FP32 accumulation).

    TODO: implement emulation using base RVV 1.0 operations.
    """
    pass


def vfqwdota_emulation(vs2: Node, vs1: Node, vd: Node, vl: Node,
                       vm: Node, tail_policy: TailPolicy,
                       mask_policy: MaskPolicy) -> Operation:
    """Emulate vfqwdota.vv (OFP8 E4M3 vs2 dot product, FP32 accumulation).

    TODO: implement emulation using base RVV 1.0 operations.
    """
    pass


def vfqwdota_alt_emulation(vs2: Node, vs1: Node, vd: Node, vl: Node,
                           vm: Node, tail_policy: TailPolicy,
                           mask_policy: MaskPolicy) -> Operation:
    """Emulate vfqwdota.alt.vv (OFP8 E5M2 vs2 dot product, FP32 accumulation).

    TODO: implement emulation using base RVV 1.0 operations.
    """
    pass


# ---------------------------------------------------------------------------
# Valid parameter spaces
# ---------------------------------------------------------------------------

# Zvqwdota8i: SEW=8 sources, 32-bit accumulator, LMUL ∈ {1,2,4,8}
ZVQWDOTA8I_VALID_LMULS = [LMULType.M1, LMULType.M2, LMULType.M4, LMULType.M8]

# Zvqwdota16i: SEW=16 sources, 64-bit accumulator, LMUL ∈ {1,2,4,8}
ZVQWDOTA16I_VALID_LMULS = [LMULType.M1, LMULType.M2, LMULType.M4, LMULType.M8]

# Zvfwdota16bf: SEW=16 BF16 sources, FP32 accumulator, LMUL ∈ {1,2,4,8}
ZVFWDOTA16BF_VALID_LMULS = [LMULType.M1, LMULType.M2, LMULType.M4, LMULType.M8]

# Zvfqwdota8f: SEW=8 OFP8 sources, FP32 accumulator, LMUL ∈ {1,2,4,8}
ZVFQWDOTA8F_VALID_LMULS = [LMULType.M1, LMULType.M2, LMULType.M4, LMULType.M8]


# ---------------------------------------------------------------------------
# Top-level generator
# ---------------------------------------------------------------------------

def generate_zvdota_emulation(
    attributes: list[str] = [],
    prototypes: bool = False,
    definitions: bool = True,
    lmul_filter: list = None,
    tail_policy_filter: list = None,
    mask_policy_filter: list = None,
    label_filter: str = None,
):
    """Generate all Zvdota family instruction emulations.

    Args:
        attributes: list of attributes to add to the generated code
        prototypes: if True, generate prototypes only
        definitions: if True, generate definitions only
        lmul_filter: if set, only generate for these LMULType values
        tail_policy_filter: if set, only generate for these TailPolicy values
        mask_policy_filter: if set, only generate for these MaskPolicy values
        label_filter: regex pattern to filter generated intrinsics by name

    Generates emulation code for:
      - vqwdotau.vv   (Zvqwdota8i:  unsigned 8-bit vs2 → 32-bit accumulator)
      - vqwdotas.vv   (Zvqwdota8i:  signed 8-bit vs2 → 32-bit accumulator)
      - vfwdota.vv    (Zvfwdota16bf: BF16 → FP32 accumulator)
      - vfqwdota.vv   (Zvfqwdota8f: OFP8 E4M3 vs2 → FP32 accumulator)
      - vfqwdota.alt.vv (Zvfqwdota8f: OFP8 E5M2 vs2 → FP32 accumulator)

    NOTE: Zvqwdota16i (SEW=16 → 64-bit) uses the same encodings as Zvqwdota8i
          but at SEW=16.  It is not yet generated here since it would require
          64-bit accumulator element types (S64/U64) which have limited
          toolchain support.
    """
    output = []

    vl_type = NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None)
    vl = Input(vl_type, 3, name="vl")

    output.append("#include <stdint.h>\n")
    output.append("#include <riscv_vector.h>\n")
    output.append("#include <stddef.h>\n")

    all_tail_policies = [TailPolicy.UNDISTURBED, TailPolicy.AGNOSTIC]
    all_mask_policies = [MaskPolicy.UNDISTURBED, MaskPolicy.AGNOSTIC, MaskPolicy.UNMASKED]

    tail_policies = [t for t in all_tail_policies if tail_policy_filter is None or t in tail_policy_filter]
    mask_policies = [m for m in all_mask_policies if mask_policy_filter is None or m in mask_policy_filter]

    # -----------------------------------------------------------------------
    # Zvqwdota8i: vqwdotau.vv / vqwdotas.vv
    #   SEW=8 inputs, 32-bit accumulator
    #   vs2, vs1: EMUL=LMUL, EEW=8
    #   vd: EMUL=1, EEW=32
    # -----------------------------------------------------------------------
    zvqwdota8i_lmuls = [l for l in ZVQWDOTA8I_VALID_LMULS if lmul_filter is None or l in lmul_filter]

    for lmul in zvqwdota8i_lmuls:
        for tail_policy in tail_policies:
            for mask_policy in mask_policies:
                # Source formats: unsigned and signed 8-bit at LMUL
                vuint8_t = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U8, lmul)
                vint8_t = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.S8, lmul)
                # Accumulator format: 32-bit at EMUL=1
                vuint32_m1_t = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U32, LMULType.M1)
                vint32_m1_t = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.S32, LMULType.M1)
                # Mask type is relative to vs1/vs2
                vbool_t = NodeFormatDescriptor(NodeFormatType.MASK, EltType.U8, lmul)

                # --- Inputs ---
                vs2_u = Input(vuint8_t, 0, name="vs2")
                vs1_u = Input(vuint8_t, 1, name="vs1")
                vs2_s = Input(vint8_t, 0, name="vs2")
                vs1_s = Input(vint8_t, 1, name="vs1")
                vd_u = Input(vuint32_m1_t, 2, name="vd")
                vd_s = Input(vint32_m1_t, 2, name="vd")
                vm = Input(vbool_t, -2, name="vm")

                zvqwdota8i_insns = []

                # --- vqwdotau.vv: unsigned vs2 ---
                proto_qwdotau = Operation(
                    vuint32_m1_t, OperationDescriptor(OperationType.QWDOTA),
                    vd_u, vs2_u, vs1_u, vl,
                    dst=vd_u, tail_policy=tail_policy, mask_policy=mask_policy, vm=vm
                )
                emul_qwdotau = vqwdota_emulation(vs2_u, vs1_u, vd_u, vl, tail_policy, mask_policy, vm)
                zvqwdota8i_insns.append((proto_qwdotau, emul_qwdotau))

                # --- vqwdotas.vv: signed vs2 ---
                proto_qwdotas = Operation(
                    vint32_m1_t, OperationDescriptor(OperationType.QWDOTA),
                    vd_s, vs2_s, vs1_s, vl,
                    dst=vd_s, tail_policy=tail_policy, mask_policy=mask_policy, vm=vm
                )
                emul_qwdotas = vqwdota_emulation(vs2_s, vs1_s, vd_s, vl, tail_policy, mask_policy, vm)
                zvqwdota8i_insns.append((proto_qwdotas, emul_qwdotas))

                lmul_str = LMULType.to_string(lmul)
                tail_policy_str = TailPolicy.to_string(tail_policy)
                mask_policy_str = MaskPolicy.to_string(mask_policy)

                if label_filter is not None:
                    zvqwdota8i_insns = [(p, e) for p, e in zvqwdota8i_insns if re.search(label_filter, generate_intrinsic_name(p))]
                if prototypes:
                    output.append(f"// Zvqwdota8i prototypes (LMUL={lmul_str}), tail_policy={tail_policy_str}, mask_policy={mask_policy_str}")
                    for proto, _ in zvqwdota8i_insns:
                        output.append(generate_intrinsic_prototype(proto))

                if definitions:
                    output.append(f"\n// Zvqwdota8i definitions (LMUL={lmul_str}), tail_policy={tail_policy_str}, mask_policy={mask_policy_str}")
                    for proto, emul in zvqwdota8i_insns:
                        if emul is not None:
                            output.append(generate_intrinsic_from_operation(proto, emul, attributes=attributes))
                        else:
                            output.append(f"// TODO: emulation not yet implemented for {generate_intrinsic_name(proto)}")

    # -----------------------------------------------------------------------
    # Zvfwdota16bf: vfwdota.vv
    #   SEW=16 BF16 inputs, FP32 accumulator
    #   vs2, vs1: EMUL=LMUL, EEW=16
    #   vd: EMUL=1, EEW=32
    #   Requires altfmt=1
    # -----------------------------------------------------------------------
    # NOTE: BF16 is not natively supported in the current RVV type system.
    #       The sources use EEW=16 (treated as BF16), and the accumulator is FP32.
    #       We use U16 as a placeholder for BF16 element type.
    zvfwdota16bf_lmuls = [l for l in ZVFWDOTA16BF_VALID_LMULS if lmul_filter is None or l in lmul_filter]

    for lmul in zvfwdota16bf_lmuls:
        for tail_policy in tail_policies:
            for mask_policy in mask_policies:
                # Source format: 16-bit (BF16 placeholder) at LMUL
                vuint16_t = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U16, lmul)
                # Accumulator format: 32-bit at EMUL=1
                vuint32_m1_t = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U32, LMULType.M1)
                # Mask type relative to vd (EMUL=1, EEW=32)
                vbool_t = NodeFormatDescriptor(NodeFormatType.MASK, EltType.U16, lmul)

                vs2 = Input(vuint16_t, 0, name="vs2")
                vs1 = Input(vuint16_t, 1, name="vs1")
                vd = Input(vuint32_m1_t, 2, name="vd")
                vm = Input(vbool_t, -2, name="vm")

                zvfwdota16bf_insns = []

                proto_fwdota = Operation(
                    vuint32_m1_t, OperationDescriptor(OperationType.FWDOTA),
                    vd, vs2, vs1, vl,
                    dst=vd, tail_policy=tail_policy, mask_policy=mask_policy, vm=vm
                )
                emul_fwdota = vfwdota_emulation(vs2, vs1, vd, vl, vm, tail_policy, mask_policy)
                zvfwdota16bf_insns.append((proto_fwdota, emul_fwdota))

                lmul_str = LMULType.to_string(lmul)
                tail_policy_str = TailPolicy.to_string(tail_policy)
                mask_policy_str = MaskPolicy.to_string(mask_policy)

                if label_filter is not None:
                    zvfwdota16bf_insns = [(p, e) for p, e in zvfwdota16bf_insns if re.search(label_filter, generate_intrinsic_name(p))]
                if prototypes:
                    output.append(f"// Zvfwdota16bf prototypes (LMUL={lmul_str}), tail_policy={tail_policy_str}, mask_policy={mask_policy_str}")
                    for proto, _ in zvfwdota16bf_insns:
                        output.append(generate_intrinsic_prototype(proto))

                if definitions:
                    output.append(f"\n// Zvfwdota16bf definitions (LMUL={lmul_str}), tail_policy={tail_policy_str}, mask_policy={mask_policy_str}")
                    for proto, emul in zvfwdota16bf_insns:
                        if emul is not None:
                            output.append(generate_intrinsic_from_operation(proto, emul, attributes=attributes))
                        else:
                            output.append(f"// TODO: emulation not yet implemented for {generate_intrinsic_name(proto)}")

    # -----------------------------------------------------------------------
    # Zvfqwdota8f: vfqwdota.vv / vfqwdota.alt.vv
    #   SEW=8 OFP8 inputs, FP32 accumulator
    #   vs2, vs1: EMUL=LMUL, EEW=8
    #   vd: EMUL=1, EEW=32
    #   vfqwdota.vv     — E4M3(vs2), altfmt selects vs1 format
    #   vfqwdota.alt.vv — E5M2(vs2), altfmt selects vs1 format
    # -----------------------------------------------------------------------
    # NOTE: OFP8 formats are not natively supported in the RVV type system.
    #       We use U8 as a placeholder for the OFP8 element types.
    zvfqwdota8f_lmuls = [l for l in ZVFQWDOTA8F_VALID_LMULS if lmul_filter is None or l in lmul_filter]

    for lmul in zvfqwdota8f_lmuls:
        for tail_policy in tail_policies:
            for mask_policy in mask_policies:
                # Source format: 8-bit (OFP8 placeholder) at LMUL
                vuint8_t = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U8, lmul)
                # Accumulator format: 32-bit at EMUL=1
                vuint32_m1_t = NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U32, LMULType.M1)
                # Mask type relative to vs1/vs2
                vbool_t = NodeFormatDescriptor(NodeFormatType.MASK, EltType.U8, lmul)

                vs2 = Input(vuint8_t, 0, name="vs2")
                vs1 = Input(vuint8_t, 1, name="vs1")
                vd = Input(vuint32_m1_t, 2, name="vd")
                vm = Input(vbool_t, -2, name="vm")

                zvfqwdota8f_insns = []

                # --- vfqwdota.vv: E4M3(vs2) ---
                proto_fqwdota = Operation(
                    vuint32_m1_t, OperationDescriptor(OperationType.FQWDOTA),
                    vd, vs2, vs1, vl,
                    dst=vd, tail_policy=tail_policy, mask_policy=mask_policy, vm=vm
                )
                emul_fqwdota = vfqwdota_emulation(vs2, vs1, vd, vl, vm, tail_policy, mask_policy)
                zvfqwdota8f_insns.append((proto_fqwdota, emul_fqwdota))

                # --- vfqwdota.alt.vv: E5M2(vs2) ---
                proto_fqwdota_alt = Operation(
                    vuint32_m1_t, OperationDescriptor(OperationType.FQWDOTA_ALT),
                    vd, vs2, vs1, vl,
                    dst=vd, tail_policy=tail_policy, mask_policy=mask_policy, vm=vm
                )
                emul_fqwdota_alt = vfqwdota_alt_emulation(vs2, vs1, vd, vl, vm, tail_policy, mask_policy)
                zvfqwdota8f_insns.append((proto_fqwdota_alt, emul_fqwdota_alt))

                lmul_str = LMULType.to_string(lmul)
                tail_policy_str = TailPolicy.to_string(tail_policy)
                mask_policy_str = MaskPolicy.to_string(mask_policy)

                if label_filter is not None:
                    zvfqwdota8f_insns = [(p, e) for p, e in zvfqwdota8f_insns if re.search(label_filter, generate_intrinsic_name(p))]
                if prototypes:
                    output.append(f"// Zvfqwdota8f prototypes (LMUL={lmul_str}), tail_policy={tail_policy_str}, mask_policy={mask_policy_str}")
                    for proto, _ in zvfqwdota8f_insns:
                        output.append(generate_intrinsic_prototype(proto))

                if definitions:
                    output.append(f"\n// Zvfqwdota8f definitions (LMUL={lmul_str}), tail_policy={tail_policy_str}, mask_policy={mask_policy_str}")
                    for proto, emul in zvfqwdota8f_insns:
                        if emul is not None:
                            output.append(generate_intrinsic_from_operation(proto, emul, attributes=attributes))
                        else:
                            output.append(f"// TODO: emulation not yet implemented for {generate_intrinsic_name(proto)}")

    return "\n".join(output)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(attributes: list[str] = [], prototypes: bool = False, definitions: bool = True):
    """CLI entry point for generating Zvdota emulation code."""
    print(generate_zvdota_emulation(attributes=attributes, prototypes=prototypes, definitions=definitions))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--attributes", nargs="+", default=[], help="Attributes to add to the generated code")
    parser.add_argument("-p", "--prototypes", default=False, action="store_true", help="generate prototypes")
    parser.add_argument("--no-definitions", default=True, action="store_false", help="do not generate definitions")
    args = parser.parse_args()

    main(attributes=args.attributes, prototypes=args.prototypes, definitions=not args.no_definitions)
