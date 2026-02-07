
# description of vector rotation emulation 
def rotate_left(elts: Node, rot_amount: Node, vl: Node) -> Node:
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

# description of vector rotation emulation 
def rotate_right(elts: Node, rot_amount: Node, vl: Node) -> Node:
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


for elt_type in [EltType.U8, EltType.U16, EltType.U32, EltType.U64]:
    uint_t = NodeFormatDescriptor(NodeFormatType.SCALAR, elt_type, lmul_type=None)
    for lmul in [LMULType.M1, LMULType.M2, LMULType.M4, LMULType.M8]:
        vuintm_t = NodeFormatDescriptor(NodeFormatType.VECTOR, elt_type, lmul)
        
        lhs = Input(vuintm_t, 0)
        rhs = Input(vuintm_t, 1)
        rhs_vx = Input(uint_t, 1)
        vl = Input(vl_type, 2, name="vl")

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

        print("// prototypes")
        for prototype in [vuintm_vror_vv_prototype, vuintm_vror_vx_prototype, vuintm_vrol_vv_prototype, vuintm_vrol_vx_prototype]:
            print(generate_intrinsic_prototype(prototype))
        print("\n// intrinsics")
        for prototype, emulation in [(vuintm_vror_vv_prototype, vuintm_vror_vv_emulation), (vuintm_vror_vx_prototype, vuintm_vror_vx_emulation), (vuintm_vrol_vv_prototype, vuintm_vrol_vv_emulation), (vuintm_vrol_vx_prototype, vuintm_vrol_vx_emulation) ]:
            print(generate_intrinsic_from_operation(prototype, emulation))