#!/usr/bin/env python3
"""
Standalone script for generating RVV intrinsic emulation code.

This script can be used without installing the package by running
it directly from the scripts directory.
"""

import sys
import os

# Add the src directory to the path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rie_generator.zvkb_emulation import generate_zvkb_emulation
from rie_generator.zvdot4a8i_emulation import generate_zvdot4a8i_emulation
from rie_generator.core import LMULType, EltType, TailPolicy, MaskPolicy

# Maps CLI string values to enum values
LMUL_MAP = {
    "mf8": LMULType.MF8, "mf4": LMULType.MF4, "mf2": LMULType.MF2,
    "m1": LMULType.M1, "m2": LMULType.M2, "m4": LMULType.M4, "m8": LMULType.M8,
}

ELT_WIDTH_MAP = {
    "8": [EltType.U8, EltType.S8],
    "16": [EltType.U16, EltType.S16],
    "32": [EltType.U32, EltType.S32],
    "64": [EltType.U64, EltType.S64],
}

TAIL_POLICY_MAP = {
    "tu": TailPolicy.UNDISTURBED,
    "ta": TailPolicy.AGNOSTIC,
}

MASK_POLICY_MAP = {
    "mu": MaskPolicy.UNDISTURBED,
    "ma": MaskPolicy.AGNOSTIC,
}


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate RISC-V Vector Intrinsic Emulation code'
    )
    parser.add_argument(
        '--extension', '-e',
        choices=['zvkb', 'zvdot4a8i', 'all'],
        default='all',
        help='Which extension to generate emulation for (default: all)'
    )
    parser.add_argument(
        '--attributes', '-a',
        nargs='+',
        default=[],
        help='Attributes to add to the generated code'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output file (default: stdout)'
    )
    parser.add_argument(
        '--prototypes', '-p',
        type=bool,
        default=False,
        help='Generate prototypes (default: False)'
    )
    parser.add_argument(
        '--definitions', '-d',
        type=bool,
        default=True,
        help='Generate definitions (default: True)'
    )
    parser.add_argument(
        '--lmul',
        nargs='+',
        choices=list(LMUL_MAP.keys()),
        default=None,
        help='LMUL values to generate (default: all valid for extension)'
    )
    parser.add_argument(
        '--elt-width',
        nargs='+',
        choices=list(ELT_WIDTH_MAP.keys()),
        default=None,
        help='Element widths in bits to generate (default: all valid for extension)'
    )
    parser.add_argument(
        '--tail-policy',
        nargs='+',
        choices=list(TAIL_POLICY_MAP.keys()),
        default=None,
        help='Tail policies to generate (default: all). Values: tu (undisturbed), ta (agnostic)'
    )
    parser.add_argument(
        '--mask-policy',
        nargs='+',
        choices=list(MASK_POLICY_MAP.keys()),
        default=None,
        help='Mask policies to generate (default: all). Values: mu (undisturbed), ma (agnostic)'
    )
    args = parser.parse_args()
    
    # Convert CLI strings to enum values (None means "all")
    lmul_filter = [LMUL_MAP[l] for l in args.lmul] if args.lmul else None
    elt_width_filter = []
    if args.elt_width:
        for w in args.elt_width:
            elt_width_filter.extend(ELT_WIDTH_MAP[w])
    else:
        elt_width_filter = None
    tail_policy_filter = [TAIL_POLICY_MAP[t] for t in args.tail_policy] if args.tail_policy else None
    mask_policy_filter = [MASK_POLICY_MAP[m] for m in args.mask_policy] if args.mask_policy else None

    output = []
    
    if args.extension in ('zvkb', 'all'):
        output.append("/* ===== Zvkb Emulation ===== */")
        output.append(generate_zvkb_emulation(
            attributes=args.attributes,
            prototypes=args.prototypes,
            definitions=args.definitions,
            lmul_filter=lmul_filter,
            elt_filter=elt_width_filter,
            tail_policy_filter=tail_policy_filter,
            mask_policy_filter=mask_policy_filter,
        ))
    
    if args.extension in ('zvdot4a8i', 'all'):
        output.append("\n/* ===== ZVDOT4A8I Emulation ===== */")
        output.append(generate_zvdot4a8i_emulation(
            attributes=args.attributes,
            prototypes=args.prototypes,
            definitions=args.definitions,
            lmul_filter=lmul_filter,
        ))
    
    result = "\n".join(output)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
        print(f"Generated emulation code written to: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
