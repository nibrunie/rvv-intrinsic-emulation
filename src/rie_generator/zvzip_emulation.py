"""
Zvzip instruction emulation generator.

This module generates C code for emulating RISC-V Zvzip vector
instructions using standard RVV 1.0 intrinsics.
"""

from .core import (
    Operation,
    OperationDescriptor,
    NodeFormatDescriptor,
    NodeFormatType,
    Immediate,
    Input,
    Node,
    element_size,
    EltType,
    LMULType,
    OperationType,
    generate_intrinsic_prototype,
    generate_intrinsic_from_operation,
    TailPolicy,
    MaskPolicy,
)

from .description_helper import get_vlenb


# ---------------------------------------------------------------------------
# Emulation building blocks
# ---------------------------------------------------------------------------

def vzip_emulation(vs1: Node, vs2: Node, vl: Node, vm: Node, vd: Node, tail_policy: TailPolicy, mask_policy: MaskPolicy) -> Operation:
    # if SEW < ELEN and Zvkb is supported, we could use widening shift operations
    # No need to support LMUL=8 inputs (since vzip does not support it, as destination EMUL would exceed 8)
    # TODO: support SEW = ELEN
    elen = 64
    if element_size(vs1.node_format.elt_type) == elen:
        return vzip_emulation_elen(vs1, vs2, vl, vm, vd, tail_policy, mask_policy)
    else:
        return vzip_emulation_non_elen(vs1, vs2, vl, vm, vd, tail_policy, mask_policy)

def vzip_emulation_elen(vs1: Node, vs2: Node, vl: Node, vm: Node, vd: Node, tail_policy: TailPolicy, mask_policy: MaskPolicy) -> Operation:
    """Emulate vzip when SEW = ELEN using base RVV 1.0 operations."""
    narrowed_elt_type = EltType.narrow(vs1.node_format.elt_type)
    widened_lmul = LMULType.multiply(vs1.node_format.lmul_type, 2)
    fmt_narrow_elt = NodeFormatDescriptor(NodeFormatType.VECTOR, narrowed_elt_type, vs1.node_format.lmul_type)
    widened_fmt_narrow_elt = NodeFormatDescriptor(NodeFormatType.VECTOR, narrowed_elt_type, widened_lmul)
    widened_fmt_std_elt = NodeFormatDescriptor(NodeFormatType.VECTOR, vs1.node_format.elt_type, widened_lmul)
    # destination format (EMUL=2*LMUL, EEW=SEW)
    vd_fmt = widened_fmt_std_elt
    twice_vl = Operation(
        NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None),
        OperationDescriptor(OperationType.MUL),
        vl,
        Immediate(NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None), 2),
    )
    four_vl = Operation(
        NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None),
        OperationDescriptor(OperationType.MUL),
        vl,
        Immediate(NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None), 4),
    )
    vs2_narrow_casted = Operation(
        fmt_narrow_elt,
        OperationDescriptor(OperationType.REINTERPRET),
        vs2,
    )
    vs1_narrow_casted = Operation(
        fmt_narrow_elt,
        OperationDescriptor(OperationType.REINTERPRET),
        vs1,
    )

    vs2_extended = Operation(
        widened_fmt_std_elt,
        OperationDescriptor(OperationType.ZEXT_VF2),
        vs2_narrow_casted,
        twice_vl,
    )
    vs2_casted_std_elt = Operation(
        widened_fmt_narrow_elt,
        OperationDescriptor(OperationType.REINTERPRET),
        vs2_extended,
    )
    # build mask/
    vlenb = get_vlenb()

    vm_vs2_slide = Operation(
        NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U8, LMULType.M1),
        OperationDescriptor(OperationType.MV),
        Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, EltType.U8, None), 0x66),
        vlenb,
    )
    vs2_slided = Operation(
        widened_fmt_narrow_elt,
        OperationDescriptor(OperationType.SLIDEDOWN),
        vs2_casted_std_elt,
        Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, narrowed_elt_type, None), 1),
        four_vl,
        vm=vm_vs2_slide,
        mask_policy=MaskPolicy.UNDISTURBED,
        tail_policy=TailPolicy.AGNOSTIC,
        dst=vs2_casted_std_elt
    )
    vs2_result_casted = Operation(
        vd_fmt,
        OperationDescriptor(OperationType.REINTERPRET),
        vs2_slided,
    )

    vs1_extended = Operation(
        widened_fmt_std_elt,
        OperationDescriptor(OperationType.ZEXT_VF2),
        vs1_narrow_casted,
        twice_vl,
    )
    vs1_casted_std_elt = Operation(
        widened_fmt_std_elt,
        OperationDescriptor(OperationType.REINTERPRET),
        vs1_extended,
    )
    vm_vs1_hi_slide = Operation(
        NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U8, LMULType.M1),
        OperationDescriptor(OperationType.MV),
        Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, EltType.U8, None), 0x88),
        vlenb,
    )
    vm_vs1_lo_slide = Operation(
        NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U8, LMULType.M1),
        OperationDescriptor(OperationType.MV),
        Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, EltType.U8, None), 0x44),
        vlenb,
    )
    vs1_hi_slided = Operation(
        widened_fmt_narrow_elt,
        OperationDescriptor(OperationType.SLIDEUP),
        vs1_casted_std_elt,
        Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, narrowed_elt_type, None), 1),
        four_vl,
        vm=vm_vs1_hi_slide,
        mask_policy=MaskPolicy.UNDISTURBED,
        tail_policy=TailPolicy.AGNOSTIC,
        dst=vs1_casted_std_elt
    )
    vs1_lo_slided = Operation(
        widened_fmt_narrow_elt,
        OperationDescriptor(OperationType.SLIDEUP),
        vs1_casted_std_elt,
        Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, narrowed_elt_type, None), 2),
        four_vl,
        vm=vm_vs1_lo_slide,
        mask_policy=MaskPolicy.UNDISTURBED,
        tail_policy=TailPolicy.AGNOSTIC,
        dst=vs1_hi_slided
    )
    vs1_result_casted = Operation(
        vd_fmt,
        OperationDescriptor(OperationType.REINTERPRET),
        vs1_lo_slided,
    )
    # combining vs2 and vs1_lo_slided
    result = Operation(
        vd_fmt,
        OperationDescriptor(OperationType.OR),
        vs2_result_casted,
        vs1_result_casted,
        twice_vl,
        vm=vm,
        dst=vd,
        tail_policy=tail_policy,
        mask_policy=mask_policy,
    )
    return result

    

def vzip_emulation_non_elen(vs1: Node, vs2: Node, vl: Node, vm: Node, vd: Node, tail_policy: TailPolicy, mask_policy: MaskPolicy) -> Operation:
    """Emulate vzip when SEW < ELEN using base RVV 1.0 operations."""
    widened_elt_type = EltType.widen(vs1.node_format.elt_type)
    widened_lmul = LMULType.multiply(vs1.node_format.lmul_type, 2)
    widened_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, widened_elt_type, widened_lmul)
    vd_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, vs1.node_format.elt_type, widened_lmul)
    twice_vl = Operation(
        NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None),
        OperationDescriptor(OperationType.MUL),
        vl,
        Immediate(NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None), 2),
    )
    vs2_widened = Operation(
        widened_fmt,
        OperationDescriptor(OperationType.ZEXT_VF2),
        vs2,
        twice_vl,
    )
    vs1_widened = Operation(
        widened_fmt,
        OperationDescriptor(OperationType.ZEXT_VF2),
        vs1,
        vl,
    )
    # vs1 also need to be shifted to odd positions
    vs1_shifted = Operation(
        widened_fmt,
        OperationDescriptor(OperationType.SLL),
        vs1_widened,
        Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, widened_elt_type, None), element_size(vs1.node_format.elt_type)),
        vl,
    )
    vs2_casted = Operation(
        vd_fmt,
        OperationDescriptor(OperationType.REINTERPRET),
        vs2_widened,
    )
    vs1_casted = Operation(
        vd_fmt,
        OperationDescriptor(OperationType.REINTERPRET),
        vs1_shifted,
    )
    result = Operation(
        vd_fmt,
        OperationDescriptor(OperationType.OR),
        vs2_casted,
        vs1_casted,
        twice_vl,
        vm=vm,
        dst=vd,
        tail_policy=tail_policy,
        mask_policy=mask_policy,
    )
    return result

def vunzip_emulation(extractEven: bool, vs2: Node, vl: Node, vm: Node, vd: Node, tail_policy: TailPolicy, mask_policy: MaskPolicy) -> Operation:
    elen = 64 # FIXME: should be derived from target
    if element_size(vs2.node_format.elt_type) < elen:
        return vunzip_emulation_non_elen(extractEven, vs2, vl, vm, vd, tail_policy, mask_policy)
    else:
        return vunzip_emulation_elen(extractEven, vs2, vl, vm, vd, tail_policy, mask_policy)

def vunzip_emulation_non_elen(extractEven: bool, vs2: Node, vl: Node, vm: Node, vd: Node, tail_policy: TailPolicy, mask_policy: MaskPolicy) -> Operation:
    """Emulate vunzip (when SEW < ELEN) using base RVV 1.0 operations."""
    # as SEW < ELEN, if Zvkb is supported, we could use widening shift operations
    widened_elt_type = EltType.widen(vs2.node_format.elt_type)
    widened_lmul = LMULType.divide(vs2.node_format.lmul_type, 2)
    # FIXME: we want the ceil(vl / 2)
    half_vl = Operation(
        NodeFormatDescriptor(NodeFormatType.SCALAR, EltType.SIZE_T, None),
        OperationDescriptor(OperationType.DIV),
        vl,
        Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, EltType.SIZE_T, None), 2),
    )
    widened_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, widened_elt_type, widened_lmul)
    vs2_cast = Operation(
        widened_fmt,
        OperationDescriptor(OperationType.REINTERPRET),
        vs2,
        half_vl,
    )
    shift_amount = Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, widened_elt_type, None), 0 if extractEven else element_size(vs2.node_format.elt_type))
    vs2_shifted = Operation(
        vs2.node_format,
        OperationDescriptor(OperationType.SRL),
        vs2_cast,
        shift_amount,
        half_vl,
        vm=vm,
        dst=vd,
        tail_policy=tail_policy,
        mask_policy=mask_policy,
    )
    return vs2_shifted    

def vunzip_emulation_elen(extractEven: bool, vs2: Node, vl: Node, vm: Node, vd: Node, tail_policy: TailPolicy, mask_policy: MaskPolicy) -> Operation:
    """Emulate vunzip (when SEW = ELEN) using base RVV 1.0 operations."""
    narrowed_lmul = LMULType.divide(vs2.node_format.lmul_type, 2)
    vd_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, vs2.node_format.elt_type, narrowed_lmul)
    # even if the destination format as half the LMUL value of the sources (a), we need to keep the source LMUL when
    # emulating with a vcompress since 2*VL elements might be accessed from the source.
    #
    # Note (a): actually destination has EMUL=LMUL, and source has EMUL=2*LMUL
    vlenb = get_vlenb()
    # building mask for vcompress
    vm_extract = Operation(
        NodeFormatDescriptor(NodeFormatType.VECTOR, EltType.U8, LMULType.M1),
        OperationDescriptor(OperationType.MV),
        Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, EltType.U8, None), 0x55 if extractEven else 0xAA),
        vlenb,
    )
    vd_raw = Operation(
        vs2.node_format,
        OperationDescriptor(OperationType.COMPRESS),
        vs2,
        vm_extract,
        vl,
        dst=vd,
        tail_policy=tail_policy,
        mask_policy=MaskPolicy.UNMASKED,
    )
    idx_fmt = NodeFormatDescriptor(NodeFormatType.SCALAR, EltType.SIZE_T, None)
    result_unmasked = Operation(vd_fmt, OperationDescriptor(OperationType.GET), vd_raw, Immediate(idx_fmt, 0))
    # implementing masking
    if mask_policy == MaskPolicy.UNMASKED:
        return result_unmasked
    else:
        return Operation(
            vd_fmt,
            OperationDescriptor(OperationType.MV),
            result_unmasked,
            vl,
            vm=vm,
            dst=vd,
            tail_policy=tail_policy,
            mask_policy=mask_policy,
        )


def vpair_emulation(pairEven: bool, vs1: Node, vs2: Node, vl: Node, vm: Node, vd: Node, tail_policy: TailPolicy, mask_policy: MaskPolicy) -> Operation:
    pass

# ---------------------------------------------------------------------------
# Valid parameter spaces
# ---------------------------------------------------------------------------

# TODO: adjust these to match the extension specification
VALID_ELT_TYPES = [EltType.U8, EltType.U16, EltType.U32, EltType.U64] # Unsupported by emulation: EltType.U64
VALID_LMULS = [LMULType.M1, LMULType.M2, LMULType.M4]    # Unsupported by emulation: LMULType.M8


# ---------------------------------------------------------------------------
# Top-level generator
# ---------------------------------------------------------------------------

def generate_zvzip_emulation(
    attributes: list[str] = [],
    prototypes: bool = False,
    definitions: bool = True,
    lmul_filter: list = None,
    elt_filter: list = None,
    tail_policy_filter: list = None,
    mask_policy_filter: list = None,
):
    """Generate all Zvzip instruction emulations.

    Args:
        attributes: list of attributes to add to the generated code
        prototypes: if True, generate prototypes only
        definitions: if True, generate definitions only
        lmul_filter: if set, only generate for these LMULType values
        elt_filter: if set, only generate for these EltType values
        tail_policy_filter: if set, only generate for these TailPolicy values
        mask_policy_filter: if set, only generate for these MaskPolicy values
    """
    output = []

    vl_type = NodeFormatDescriptor(NodeFormatType.VECTOR_LENGTH, EltType.SIZE_T, None)
    vl = Input(vl_type, 2, name="vl")

    output.append("#include <stdint.h>\n")
    output.append("#include <riscv_vector.h>\n")
    output.append("#include <stddef.h>\n")

    all_elt_types = VALID_ELT_TYPES
    all_lmuls = VALID_LMULS
    all_tail_policies = [TailPolicy.UNDISTURBED, TailPolicy.AGNOSTIC]
    all_mask_policies = [MaskPolicy.UNDISTURBED, MaskPolicy.AGNOSTIC, MaskPolicy.UNMASKED]

    elt_types = [e for e in all_elt_types if elt_filter is None or e in elt_filter]
    lmuls = [l for l in all_lmuls if lmul_filter is None or l in lmul_filter]
    tail_policies = [t for t in all_tail_policies if tail_policy_filter is None or t in tail_policy_filter]
    mask_policies = [m for m in all_mask_policies if mask_policy_filter is None or m in mask_policy_filter]

    for elt_type in elt_types:
        for lmul in lmuls:
            print(f"Generating zvzip for {elt_type} {lmul}")
            vuint_t = NodeFormatDescriptor(NodeFormatType.VECTOR, elt_type, lmul)
            vbool_t = NodeFormatDescriptor(NodeFormatType.MASK, elt_type, LMULType.multiply(lmul, 2))
            vd_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, elt_type, LMULType.multiply(lmul, 2))

            vs2 = Input(vuint_t, 0, name="vs2")
            vs1 = Input(vuint_t, 1, name="vs1")
            vm = Input(vbool_t, -2, name="vm")
            vd = Input(vuint_t, -1, name="vd")

            for tail_policy in tail_policies:
                for mask_policy in mask_policies:
                    dst = vd if tail_policy == TailPolicy.UNDISTURBED or mask_policy == MaskPolicy.UNDISTURBED else None
                    mask = vm if mask_policy not in (MaskPolicy.UNDEFINED, MaskPolicy.UNMASKED) else None

                    # --- vzip: interleave two base vectors into a widened result ---
                    # vzip only valid when widened elt_type and widened lmul exist

                    vzip_vv_prototype = Operation(
                        vd_fmt,
                        OperationDescriptor(OperationType.ZIP),
                        vs2,
                        vs1,
                        vl,
                        vm=mask,
                        tail_policy=tail_policy,
                        mask_policy=mask_policy,
                        dst=dst,
                    )
                    vzip_vv_emulation = vzip_emulation(vs2, vs1, vl, mask, dst, tail_policy, mask_policy)

                    # --- vunzip.even / vunzip.odd: deinterleave widened vector ---
                    # input is the widened (interleaved) vector, output is base format
                    widened_input = Input(vd_fmt, 0)

                    vunzip_even_prototype = Operation(
                        vuint_t,
                        OperationDescriptor(OperationType.UNZIP_EVEN),
                        widened_input,
                        vl,
                        vm=mask,
                        tail_policy=tail_policy,
                        mask_policy=mask_policy,
                        dst=dst,
                    )
                    vunzip_even_emulation = vunzip_emulation(True, widened_input, vl, mask, dst, tail_policy, mask_policy)

                    vunzip_odd_prototype = Operation(
                        vuint_t,
                        OperationDescriptor(OperationType.UNZIP_ODD),
                        widened_input,
                        vl,
                        vm=mask,
                        tail_policy=tail_policy,
                        mask_policy=mask_policy,
                        dst=dst,
                    )
                    vunzip_odd_emulation = vunzip_emulation(False, widened_input, vl, mask, dst, tail_policy, mask_policy)

                    zvzip_insns = [
                        (vzip_vv_prototype, vzip_vv_emulation),
                        (vunzip_even_prototype, vunzip_even_emulation),
                        (vunzip_odd_prototype, vunzip_odd_emulation),
                    ]

                    if prototypes:
                        output.append("// prototypes")
                        for proto, _ in zvzip_insns:
                            output.append(generate_intrinsic_prototype(proto))
                    if definitions:
                        output.append("\n// intrinsics")
                        for proto, emul in zvzip_insns:
                            output.append(generate_intrinsic_from_operation(proto, emul, attributes=attributes))



    return "\n".join(output)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(attributes: list[str] = [], prototypes: bool = False, definitions: bool = True):
    """CLI entry point for generating Zvzip emulation code."""
    print(generate_zvzip_emulation(attributes=attributes, prototypes=prototypes, definitions=definitions))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--attributes", nargs="+", default=[], help="Attributes to add to the generated code")
    parser.add_argument("-p", "--prototypes", default=False, action="store", type=bool, help="generate prototypes")
    parser.add_argument("-d", "--definitions", default=True, action="store", type=bool, help="generate definitions")
    args = parser.parse_args()

    main(attributes=args.attributes, prototypes=args.prototypes, definitions=args.definitions)
