# RIE Generator — RISC-V Vector Intrinsic Emulation Generator

A Python code generator that produces C functions emulating RISC-V vector extension instructions (Zvkb, Zvdot4a8i) using only standard RVV 1.0 intrinsics.

## Overview

Some RISC-V vector extensions (e.g. Zvkb for vector crypto bit-manipulation) introduce new instructions that may not yet be available on all hardware. This tool automatically generates C emulation functions that implement the same semantics using base RVV 1.0 instructions (`vsrl`, `vsll`, `vor`, `vand`, `vnot`, …).

### Supported Extensions

| Extension | Instructions | Status |
|-----------|-------------|--------|
| **Zvkb** | `vror`, `vrol`, `vandn`, `vbrev8`, `vrev8` | ✅ Implemented |
| **Zvdot4a8i** | — | 🚧 Placeholder |

### Supported Intrinsic Variants

- **Operand types**: `vv` (vector-vector), `vx` (vector-scalar)
- **Element widths**: 8, 16, 32, 64-bit unsigned integers
- **LMUL**: m1, m2, m4, m8
- **Policies**: tail undisturbed/agnostic, mask undisturbed/agnostic

## Directory Structure

```
rvv-intrinsic-emulation/
├── src/rie_generator/          # Python package
│   ├── __init__.py             # Package exports
│   ├── core.py                 # Core IR types, enums, and C code generation
│   ├── zvkb_emulation.py       # Zvkb instruction emulation descriptions
│   └── zvdot4a8i_emulation.py  # Zvdot4a8i (placeholder)
├── scripts/
│   ├── generate_emulation.py   # Standalone CLI script
│   ├── rie_generator.py        # Legacy generator module
│   └── zvbb_emulation.py       # Legacy Zvbb script
├── pyproject.toml              # Python packaging configuration
├── LICENSE                     # MIT License
└── README.md
```

## Usage

### Standalone (no installation required)

```bash
# Generate Zvkb emulation to stdout
python3 scripts/generate_emulation.py -e zvkb

# Write to a file
python3 scripts/generate_emulation.py -e zvkb -o zvkb_emu.h

# Generate all extensions
python3 scripts/generate_emulation.py
```

### As an Installed Package

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .

# CLI entry points
rie-zvkb > zvkb_emu.h
rie-zvdot4a8i > zvdot4a8i_emu.h
```

### As a Library

```python
from rie_generator import (
    EltType, LMULType, OperationType,
    Operation, OperationDesciptor, Input,
    NodeFormatDescriptor, NodeFormatType,
    generate_intrinsic_from_operation,
)
from rie_generator.zvkb_emulation import rotate_right, and_not, brev8, rev8
```

## How It Works

The generator builds an intermediate representation (IR) of each emulated instruction as a tree of `Operation` nodes, then lowers that IR to C code using RVV 1.0 intrinsics.

**Example — `vror` (rotate right):**
```
rotate_right(x, n) = vor(vsrl(x, n), vsll(x, width - n))
```

**Example — `vandn` (and-not):**
```
vandn(x, y) = vand(x, vnot(y))
```

## Requirements

- Python ≥ 3.8 (no external dependencies for code generation)

## License

MIT — see [LICENSE](LICENSE).

## References

- [RISC-V Vector Extension Specification](https://github.com/riscv/riscv-v-spec)
- [RISC-V Cryptography Extensions (Zvkb)](https://github.com/riscv/riscv-crypto)
- [RISC-V Vector Intrinsics](https://github.com/riscv-non-isa/rvv-intrinsic-doc)
