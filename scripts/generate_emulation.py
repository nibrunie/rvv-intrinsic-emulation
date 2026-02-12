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
    args = parser.parse_args()
    
    output = []
    
    if args.extension in ('zvkb', 'all'):
        output.append("/* ===== Zvkb Emulation ===== */")
        output.append(generate_zvkb_emulation(attributes=args.attributes, prototypes=args.prototypes, definitions=args.definitions))
    
    if args.extension in ('zvdot4a8i', 'all'):
        output.append("\n/* ===== ZVDOT4A8I Emulation ===== */")
        output.append(generate_zvdot4a8i_emulation(attributes=args.attributes, prototypes=args.prototypes, definitions=args.definitions))
    
    result = "\n".join(output)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
        print(f"Generated emulation code written to: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
