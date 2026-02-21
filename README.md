# RIE Generator — RISC-V Vector Intrinsic Emulation Generator

A Python code generator that produces C functions emulating RISC-V vector extension instructions (Zvkb, Zvdot4a8i) using only standard RVV 1.0 intrinsics.

## Overview

Some RISC-V vector extensions (e.g. Zvkb for vector crypto bit-manipulation, Zvdot4a8i for packed 8-bit integer dot products) introduce new instructions that may not yet be available on all hardware. This tool automatically generates C emulation functions that implement the same semantics using base RVV 1.0 instructions.

### Supported Extensions

| Extension | Instructions | Emulation Strategy |
|-----------|-------------|-------------------|
| **Zvkb** | `vror`, `vrol`, `vandn`, `vbrev8`, `vrev8` | Shift/OR decomposition |
| **Zvdot4a8i** | `vdota4`, `vdota4u`, `vdota4su`, `vdota4us` | Widening multiply + pairwise reduction |

### Zvdot4a8i Emulation Details

The dot product instructions (`vdota4*`) operate on packed 8-bit integer sub-elements within 32-bit vector elements. The emulation uses a single-pass widening multiply pipeline:

1. `vreinterpret` — view 32-bit elements as 8-bit
2. `vwmul*` — widening multiply 8→16-bit (vl = 4× original)
3. `vnsrl` × 2 — extract high/low product pairs (64→32-bit)
4. `vwadd*` — widening add pairs (16→32-bit, vl = 2× original)
5. `vnsrl` × 2 — extract high/low sums (64→32-bit)
6. `vadd` × 2 — sum pairs + accumulate into `vd`

### Supported Intrinsic Variants

- **Operand types**: `vv` (vector-vector), `vx` (vector-scalar)
- **Element widths**: 8, 16, 32, 64-bit unsigned integers (Zvkb); 32-bit signed/unsigned (Zvdot4a8i)
- **LMUL**: m1, m2, m4, m8 (Zvkb); m1, m2, m4 (Zvdot4a8i — limited by widening)
- **Policies**: tail undisturbed/agnostic, mask undisturbed/agnostic (Zvkb); tail undisturbed (Zvdot4a8i)

## Directory Structure

```
rvv-intrinsic-emulation/
├── src/rie_generator/          # Python package
│   ├── __init__.py             # Package exports
│   ├── core.py                 # Core IR types, enums, and C code generation
│   ├── zvkb_emulation.py       # Zvkb instruction emulation descriptions
│   └── zvdot4a8i_emulation.py  # Zvdot4a8i dot product emulation
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
# Generate all extensions to stdout
python3 scripts/generate_emulation.py

# Generate a single extension
python3 scripts/generate_emulation.py -e zvkb
python3 scripts/generate_emulation.py -e zvdot4a8i

# Write to a file with inline attributes
python3 scripts/generate_emulation.py -e zvkb -o zvkb_emu.h -a static inline
```

### Filtering Generated Output

The generator supports filtering on LMUL, element width, and tail/mask policies to produce only the variants you need:

```bash
# Only M1 LMUL
python3 scripts/generate_emulation.py -e zvdot4a8i --lmul m1

# Multiple LMUL values
python3 scripts/generate_emulation.py -e zvkb --lmul m1 m2

# Specific element width (Zvkb)
python3 scripts/generate_emulation.py -e zvkb --elt-width 32

# Specific tail/mask policies (Zvkb)
python3 scripts/generate_emulation.py -e zvkb --tail-policy ta --mask-policy ma

# Combine multiple filters
python3 scripts/generate_emulation.py -e zvkb --lmul m1 --elt-width 32 --tail-policy tu --mask-policy mu
```

| Argument | Values | Default | Applies To |
|----------|--------|---------|------------|
| `--lmul` | `mf8 mf4 mf2 m1 m2 m4 m8` | all valid | Zvkb, Zvdot4a8i |
| `--elt-width` | `8 16 32 64` | all valid | Zvkb |
| `--tail-policy` | `tu` (undisturbed), `ta` (agnostic) | all | Zvkb |
| `--mask-policy` | `mu` (undisturbed), `ma` (agnostic) | all | Zvkb |

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
    Operation, OperationDescriptor, Input,
    NodeFormatDescriptor, NodeFormatType,
    generate_intrinsic_from_operation,
)
from rie_generator.zvkb_emulation import rotate_right, and_not, brev8, rev8
from rie_generator.zvdot4a8i_emulation import dot4_pipeline
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

**Example — `vdota4u` (unsigned dot product):**
```
vdota4u(vs2, vs1, vd) =
  products = vwmulu(reinterpret_u8(vs2), reinterpret_u8(vs1), vl*4)
  high_p, low_p = vnsrl(products, 32), vnsrl(products, 0)
  sums = vwaddu(high_p, low_p, vl*2)
  high_s, low_s = vnsrl(sums, 32), vnsrl(sums, 0)
  vadd(vadd(high_s, low_s), vd)
```

## Requirements

- Python ≥ 3.8 (no external dependencies for code generation)

## License

MIT — see [LICENSE](LICENSE).

## References

- [RISC-V Vector Extension Specification](https://github.com/riscv/riscv-v-spec)
- [RISC-V Cryptography Extensions (Zvkb)](https://github.com/riscv/riscv-crypto)
- [RISC-V Vector Intrinsics](https://github.com/riscv-non-isa/rvv-intrinsic-doc)
- [RISC-V Vector Intrinsics Specification](https://github.com/riscv-non-isa/rvv-intrinsic-doc/blob/main/doc/rvv-intrinsic-spec.adoc)
