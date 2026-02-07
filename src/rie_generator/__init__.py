"""
RIE Generator - RISC-V Vector Intrinsic Emulation Generator

A Python library for generating C code that emulates RISC-V vector
instructions using standard RVV intrinsics.
"""

from .core import (
    # Enums
    EltType,
    LMULType,
    OperationType,
    NodeFormatType,
    NodeType,
    # Classes
    OperationDesciptor,
    Node,
    Immediate,
    Input,
    Operation,
    NodeFormatDescriptor,
    CodeObject,
    # Functions
    element_size,
    get_scalar_format,
    int_type_to_scalar_type,
    int_type_to_vector_type,
    generate_node_format_type_string,
    generate_intrinsic_type_tag,
    generate_intrinsic_name,
    generate_intrinsic_prototype,
    generate_operation,
    generate_intrinsic_from_operation,
)

__version__ = "0.1.0"
__all__ = [
    # Enums
    "EltType",
    "LMULType",
    "OperationType",
    "NodeFormatType",
    "NodeType",
    # Classes
    "OperationDesciptor",
    "Node",
    "Immediate",
    "Input",
    "Operation",
    "NodeFormatDescriptor",
    "CodeObject",
    # Functions
    "element_size",
    "get_scalar_format",
    "int_type_to_scalar_type",
    "int_type_to_vector_type",
    "generate_node_format_type_string",
    "generate_intrinsic_type_tag",
    "generate_intrinsic_name",
    "generate_intrinsic_prototype",
    "generate_operation",
    "generate_intrinsic_from_operation",
]
