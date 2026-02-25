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


# ---------------------------------------------------------------------------
# Emulation building blocks
# ---------------------------------------------------------------------------

# TODO: add emulation functions here, e.g.:
#
# def my_operation(op0: Node, vl: Node, ...) -> Operation:
#     """Emulate <instruction> using base RVV 1.0 operations."""
#     ...

def vzip_emulation(vs1: Node, vs2: Node, vl: Node, vm: Node, vd: Node, tail_policy: TailPolicy, mask_policy: MaskPolicy) -> Operation:
    """Emulate vzip using base RVV 1.0 operations."""
    # if SEW < ELEN and Zvkb is supported, we could use widening shift operations
    # TODO: support LMUL=8 (by splitting)
    # TODO: support SEW = ELEN
    widened_elt_type = EltType.widen(vs1.format.elt_type)
    widened_lmul = LMULType.multiply(vs1.format.lmul, 2)
    widened_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, widened_elt_type, widened_lmul)
    vs2_widened = Operation(
        widened_fmt,
        OperationDescriptor(OperationType.ZEXT_VF2),
        vs2,
        vl,
        vm=vm,
        tail_policy=tail_policy,
        mask_policy=mask_policy,
    )
    vs1_widened = Operation(
        widened_fmt,
        OperationDescriptor(OperationType.ZEXT_VF2),
        vs1,
        vl,
        vm=vm,
        tail_policy=tail_policy,
        mask_policy=mask_policy,
    )
    # vs1 also need to be shifted to odd positions
    vs1_shifted = Operation(
        widened_fmt,
        OperationDescriptor(OperationType.SLL),
        vs1_widened,
        Immediate(element_size(vs1.format.elt_type), NodeFormatDescriptor(NodeFormatType.SCALAR, widened_elt_type, None)),
        vl,
        vm=vm,
        tail_policy=tail_policy,
        mask_policy=mask_policy,
    )
    result = Operation(
        widened_fmt,
        OperationDescriptor(OperationType.OR),
        vs2_widened,
        vs1_shifted,
        vl,
        vm=vm,
        tail_policy=tail_policy,
        mask_policy=mask_policy,
    )
    return result

def vunzip_emulation(extractEven: bool, vs2: Node, vl: Node, vm: Node, vd: Node, tail_policy: TailPolicy, mask_policy: MaskPolicy) -> Operation:
    """Emulate vunzip using base RVV 1.0 operations."""
    # if SEW < ELEN and Zvkb is supported, we could use widening shift operations
    # TODO: support SEW = ELEN
    widened_elt_type = EltType.widen(vs2.format.elt_type)
    widened_lmul = LMULType.divide(vs2.format.lmul, 2)
    # FIXME: we want the ceil(vl / 2)
    half_vl = Operation(
        NodeFormatDescriptor(NodeFormatType.SCALAR, EltType.SIZE_T, None),
        OperationDescriptor(OperationType.DIV),
        vl,
        Immediate(2, NodeFormatDescriptor(NodeFormatType.SCALAR, EltType.SIZE_T, None)),
    )
    widened_fmt = NodeFormatDescriptor(NodeFormatType.VECTOR, widened_elt_type, widened_lmul)
    vs2_cast = Operation(
        widened_fmt,
        OperationDescriptor(OperationType.REINTERPRET_CAST),
        vs2,
        half_vl,
    )
    shift_amount = Immediate(0 if extractEven else element_size(vs2.format.elt_type), NodeFormatDescriptor(NodeFormatType.SCALAR, widened_elt_type, None))
    vs2_shifted = Operation(
        vs2.node_format,
        OperationDescriptor(OperationType.SRL),
        vs2_cast,
        shift_amount,
        half_vl,
        vm=vm,
        tail_policy=tail_policy,
        mask_policy=mask_policy,
    )
    return vs2_shifted    

def vpair_emulation(pairEven: bool, vs1: Node, vs2: Node, vl: Node, vm: Node, vd: Node, tail_policy: TailPolicy, mask_policy: MaskPolicy) -> Operation:
    pass

# ---------------------------------------------------------------------------
# Valid parameter spaces
# ---------------------------------------------------------------------------

# TODO: adjust these to match the extension specification
VALID_ELT_TYPES = [EltType.U8, EltType.U16, EltType.U32, EltType.U64]
VALID_LMULS = [LMULType.M1, LMULType.M2, LMULType.M4, LMULType.M8]


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
            vuint_t = NodeFormatDescriptor(NodeFormatType.VECTOR, elt_type, lmul)
            vbool_t = NodeFormatDescriptor(NodeFormatType.MASK, elt_type, lmul)

            lhs = Input(vuint_t, 0)
            rhs = Input(vuint_t, 1)
            vm = Input(vbool_t, -2, name="vm")
            vd = Input(vuint_t, -1, name="vd")

            for tail_policy in tail_policies:
                for mask_policy in mask_policies:
                    dst = vd if tail_policy == TailPolicy.UNDISTURBED or mask_policy == MaskPolicy.UNDISTURBED else None
                    mask = vm if mask_policy not in (MaskPolicy.UNDEFINED, MaskPolicy.UNMASKED) else None

                    # TODO: build prototype + emulation Operation pairs here
                    # Example pattern:
                    #
                    # proto = Operation(
                    #     vuint_t,
                    #     OperationDescriptor(OperationType.XXX),
                    #     lhs, rhs, vl,
                    #     vm=mask, tail_policy=tail_policy,
                    #     mask_policy=mask_policy, dst=dst,
                    # )
                    # emul = my_operation(lhs, rhs, vl, vm=mask, dst=dst,
                    #                     tail_policy=tail_policy,
                    #                     mask_policy=mask_policy)
                    #
                    # if prototypes:
                    #     output.append(generate_intrinsic_prototype(proto))
                    # if definitions:
                    #     output.append(generate_intrinsic_from_operation(proto, emul, attributes))
                    pass

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
