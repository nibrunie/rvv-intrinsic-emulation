import re

"""
Zvabd instruction emulation generator.

This module generates C code for emulating RISC-V Zvabd vector
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
    generate_intrinsic_name,
    generate_intrinsic_prototype,
    generate_intrinsic_from_operation,
    TailPolicy,
    MaskPolicy,
)

from .description_helper import get_vlenb


# ---------------------------------------------------------------------------
# Emulation building blocks
# ---------------------------------------------------------------------------

def vabs_emulation(vs2: Node, vl: Node, vm: Node, vd: Node, tail_policy: TailPolicy, mask_policy: MaskPolicy) -> Operation:
    elt_type = vs2.node_format.elt_type
    mask_type = NodeFormatDescriptor(NodeFormatType.MASK, elt_type, vs2.node_format.lmul_type)
    comp = Operation(
        mask_type,
        OperationDescriptor(OperationType.LT),
        vs2,
        Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, elt_type, None), 0),
        vl,
    )
    neg = Operation(
        vs2.node_format,
        OperationDescriptor(OperationType.RSUB),
        vs2,
        Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, elt_type, None), 0),
        vl,
    )
    select = Operation(
        vs2.node_format,
        OperationDescriptor(OperationType.MERGE),
        neg,
        vs2,
        comp,
        vl,
        vm=None, # vmerge does not support masking
        tail_policy=tail_policy,
        mask_policy=MaskPolicy.UNMASKED,
        dst=vd,
    )
    if mask_policy in [MaskPolicy.UNDISTURBED, MaskPolicy.AGNOSTIC]:
        select = Operation(
            vs2.node_format,
            OperationDescriptor(OperationType.OR),
            select,
            Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, elt_type, None), 0),
            vl,
            vm=vm,
            tail_policy=tail_policy,
            mask_policy=mask_policy,
            dst=vd,
        )
    return select

def vabd_emulation(signed: bool, vs2: Node, vs1: Node, vl: Node, vm: Node, vd: Node, tail_policy: TailPolicy, mask_policy: MaskPolicy) -> Operation:
    elt_type = vs2.node_format.elt_type
    # Performing the subtraction twice (vs2 - vs1) and (vs1 - vs2)
    # Selecting the first result if vs2 >= vs1, else the second result
    mask_type = NodeFormatDescriptor(NodeFormatType.MASK, elt_type, vs2.node_format.lmul_type)
    comp = Operation(
        mask_type,
        OperationDescriptor(OperationType.GE if signed else OperationType.GEU),
        vs2,
        vs1,
        vl,
    )
    vs2_minus_vs1 = Operation(
        vs2.node_format,
        OperationDescriptor(OperationType.SUB),
        vs2,
        vs1,
        vl,
    )
    vs1_minus_vs2 = Operation(
        vs2.node_format,
        OperationDescriptor(OperationType.SUB),
        vs1,
        vs2,
        vl,
    )
    select = Operation(
        vs2.node_format,
        OperationDescriptor(OperationType.MERGE),
        vs2_minus_vs1,
        vs1_minus_vs2,
        comp,
        vl,
        vm=None, # vmerge does not support masking
        tail_policy=tail_policy,
        mask_policy=MaskPolicy.UNMASKED,
        dst=vd,
    )
    if mask_policy in [MaskPolicy.UNDISTURBED, MaskPolicy.AGNOSTIC]:
        select = Operation(
            vs2.node_format,
            OperationDescriptor(OperationType.OR),
            select,
            Immediate(NodeFormatDescriptor(NodeFormatType.SCALAR, elt_type, None), 0),
            vl,
            vm=vm,
            tail_policy=tail_policy,
            mask_policy=mask_policy,
            dst=vd,
        )
    return select


def vwabda_emulation(signed: bool, vd: Node, vs2: Node, vs1: Node, vl: Node, vm: Node, tail_policy: TailPolicy, mask_policy: MaskPolicy) -> Operation:
    vabd_result = vabd_emulation(signed, vs2, vs1, vl, vm, None, TailPolicy.UNDEFINED, MaskPolicy.UNMASKED)
    accumulation = Operation(
        vd.node_format,
        OperationDescriptor(OperationType.WADDU),
        vd,
        vabd_result,
        vl,
        vm=vm,
        tail_policy=tail_policy,
        mask_policy=mask_policy,
        dst=vd,
    )
    return accumulation
    
    

# ---------------------------------------------------------------------------
# Valid parameter spaces
# ---------------------------------------------------------------------------

# TODO: adjust these to match the extension specification
VALID_ELT_SIZES = [8, 16, 32, 64]
VALID_LMULS = [LMULType.M1, LMULType.M2, LMULType.M4, LMULType.M8]


# ---------------------------------------------------------------------------
# Top-level generator
# ---------------------------------------------------------------------------

def generate_zvabd_emulation(
    attributes: list[str] = [],
    prototypes: bool = False,
    definitions: bool = True,
    lmul_filter: list = None,
    elt_filter: list = None,
    tail_policy_filter: list = None,
    mask_policy_filter: list = None,
    label_filter: str = None,
):
    """Generate all Zvabd instruction emulations.

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

    elen = 64 # FIXME: get from config

    output.append("#include <stdint.h>\n")
    output.append("#include <riscv_vector.h>\n")
    output.append("#include <stddef.h>\n")

    all_elt_sizes = VALID_ELT_SIZES
    all_lmuls = VALID_LMULS
    all_tail_policies = [TailPolicy.UNDISTURBED, TailPolicy.AGNOSTIC]
    all_mask_policies = [MaskPolicy.UNDISTURBED, MaskPolicy.AGNOSTIC, MaskPolicy.UNMASKED]

    elt_sizes = [e for e in all_elt_sizes if elt_filter is None or e in elt_filter]
    lmuls = [l for l in all_lmuls if lmul_filter is None or l in lmul_filter]
    tail_policies = [t for t in all_tail_policies if tail_policy_filter is None or t in tail_policy_filter]
    mask_policies = [m for m in all_mask_policies if mask_policy_filter is None or m in mask_policy_filter]

    for elt_size in elt_sizes:
        for lmul in lmuls:
            elt_type_unsigned = EltType.from_size(False, elt_size)
            elt_type_signed = EltType.from_size(True, elt_size)
            wide_elt_type_unsigned = EltType.widen(elt_type_unsigned) if elt_size < elen else None
            vint_t = NodeFormatDescriptor(NodeFormatType.VECTOR, elt_type_signed, lmul)
            vuint_t = NodeFormatDescriptor(NodeFormatType.VECTOR, elt_type_unsigned, lmul)
            vbool_t = NodeFormatDescriptor(NodeFormatType.MASK, elt_type_unsigned, lmul)
            vdu_fmt = vuint_t
            vds_fmt = vint_t

            vs2_signed = Input(vint_t, 0, name="vs2")
            vs1_signed = Input(vint_t, 1, name="vs1")
            vs2_unsigned = Input(vuint_t, 0, name="vs2")
            vs1_unsigned = Input(vuint_t, 1, name="vs1")
            vm = Input(vbool_t, -2, name="vm")
            vdu = Input(vdu_fmt, -1, name="vd")
            vds = Input(vds_fmt, -1, name="vd")
            

            for tail_policy in tail_policies:
                for mask_policy in mask_policies:
                    dst_signed = vds if tail_policy == TailPolicy.UNDISTURBED or mask_policy == MaskPolicy.UNDISTURBED else None
                    dst_unsigned = vdu if tail_policy == TailPolicy.UNDISTURBED or mask_policy == MaskPolicy.UNDISTURBED else None
                    mask = vm if mask_policy not in (MaskPolicy.UNDEFINED, MaskPolicy.UNMASKED) else None

                    vabs_v_prototype = Operation(
                        vds_fmt,
                        OperationDescriptor(OperationType.ABS),
                        vs2_signed,
                        vl,
                        vm=mask,
                        tail_policy=tail_policy,
                        mask_policy=mask_policy,
                        dst=dst_signed,
                    )
                    vabs_v_emulation = vabs_emulation(vs2_signed, vl, mask, dst_signed, tail_policy, mask_policy)
                    
                    # partial list before conditionally adding vwabda[u] if SEW < ELEN
                    zvabd_insns = [
                        (vabs_v_prototype, vabs_v_emulation),
                    ]

                    if elt_size in [8, 16]: # vabd[u] is reserved when SEW != 8 or 16
                        vabd_vv_prototype = Operation(
                            vds_fmt,
                            OperationDescriptor(OperationType.ABD),
                            vs2_signed,
                            vs1_signed,
                            vl,
                            vm=mask,
                            tail_policy=tail_policy,
                            mask_policy=mask_policy,
                            dst=dst_signed,
                        )
                        vabd_vv_emulation = vabd_emulation(True, vs2_signed, vs1_signed, vl, mask, dst_signed, tail_policy, mask_policy)

                        vabdu_vv_prototype = Operation(
                            vdu_fmt,
                            OperationDescriptor(OperationType.ABDU),
                            vs2_unsigned,
                            vs1_unsigned,
                            vl,
                            vm=mask,
                            tail_policy=tail_policy,
                            mask_policy=mask_policy,
                            dst=dst_unsigned,
                        )
                        vabdu_vv_emulation = vabd_emulation(False, vs2_unsigned, vs1_unsigned, vl, mask, dst_unsigned, tail_policy, mask_policy)
                        zvabd_insns.append((vabd_vv_prototype, vabd_vv_emulation))
                        zvabd_insns.append((vabdu_vv_prototype, vabdu_vv_emulation))


                    if wide_elt_type_unsigned is not None and lmul != LMULType.M8 and element_size in [8, 16]: 
                        wide_lmul = LMULType.multiply(lmul, 2)
                        wide_vuint_t = NodeFormatDescriptor(NodeFormatType.VECTOR, wide_elt_type_unsigned, wide_lmul)
                        wide_vdu = Input(wide_vuint_t, -1, name="vd")

                        vwabda_vv_prototype = Operation(
                            wide_vuint_t,
                            OperationDescriptor(OperationType.WABDA),
                            wide_vdu,
                            vs2_signed,
                            vs1_signed,
                            vl,
                            vm=mask,
                            tail_policy=tail_policy,
                            mask_policy=mask_policy,
                            dst=wide_vdu,
                        )
                        vwabda_vv_emulation = vwabda_emulation(True, wide_vdu, vs2_signed, vs1_signed, vl, mask, tail_policy, mask_policy)

                        vwabdau_vv_prototype = Operation(
                            wide_vuint_t,
                            OperationDescriptor(OperationType.WABDAU),
                            wide_vdu,
                            vs2_unsigned,
                            vs1_unsigned,
                            vl,
                            vm=mask,
                            tail_policy=tail_policy,
                            mask_policy=mask_policy,
                            dst=wide_vdu,
                        )
                        vwabdau_vv_emulation = vwabda_emulation(False, wide_vdu, vs2_unsigned, vs1_unsigned, vl, mask, tail_policy, mask_policy)

                        zvabd_insns.append((vwabda_vv_prototype, vwabda_vv_emulation))
                        zvabd_insns.append((vwabdau_vv_prototype, vwabdau_vv_emulation))

                    if label_filter is not None:
                        zvabd_insns = [(p, e) for p, e in zvabd_insns if re.search(label_filter, generate_intrinsic_name(p))]
                    if prototypes:
                        output.append("// prototypes")
                        for proto, _ in zvabd_insns:
                            output.append(generate_intrinsic_prototype(proto))
                    if definitions:
                        output.append("\n// intrinsics")
                        for proto, emul in zvabd_insns:
                            output.append(generate_intrinsic_from_operation(proto, emul, attributes=attributes))



    return "\n".join(output)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(attributes: list[str] = [], prototypes: bool = False, definitions: bool = True):
    """CLI entry point for generating Zvabd emulation code."""
    print(generate_zvabd_emulation(attributes=attributes, prototypes=prototypes, definitions=definitions))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--attributes", nargs="+", default=[], help="Attributes to add to the generated code")
    parser.add_argument("-p", "--prototypes", default=False, action="store_true", help="generate prototypes")
    parser.add_argument("--no-definitions", default=True, action="store_false", help="do not generate definitions")
    args = parser.parse_args()

    main(attributes=args.attributes, prototypes=args.prototypes, definitions=not args.no_definitions)
