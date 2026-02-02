# RISC-V Zvbb vror* Instruction Emulation Library

A header-only C library that emulates RISC-V Zvbb (Vector Basic Bit-manipulation) vector rotate right (`vror*`) instructions using standard RISC-V vector intrinsics.

## Overview

The RISC-V Zvbb extension provides dedicated vector bit manipulation instructions, including `vror` (vector rotate right). This library emulates these instructions for systems that don't have native Zvbb support by using the standard RVV (RISC-V Vector) instructions: `vsrl`, `vsll`, and `vor`.

**Rotation Formula**: `rotate_right(x, n) = (x >> n) | (x << (width - n))`

## Features

- **Header-only**: Easy integration, just include `zvbb_emu.h`
- **Complete coverage**: All `vror` instruction variants
  - `vror.vv`: Vector-vector (per-element rotation amounts)
  - `vror.vx`: Vector-scalar (uniform rotation amount)
  - `vror.vi`: Vector-immediate (compile-time constant)
- **Multiple element widths**: 8, 16, 32, and 64-bit elements
- **LMUL support**: m1, m2, m4, m8 configurations
- **Comprehensive test suite**: 1000+ random test cases
- **Performance benchmarks**: Throughput and latency measurements

## Directory Structure

```
rvv-intrinsic-emulation/
├── include/
│   └── zvbb_emu.h          # Header-only library (API + implementation)
├── tests/
│   └── test_vror.c         # Comprehensive test suite
├── bench/
│   └── bench_vror.c        # Performance benchmarks
├── Makefile                # Build system
└── README.md               # This file
```

## Requirements

- **RISC-V GCC** with vector extension support
- Target architecture: `rv64gcv` (RISC-V 64-bit with vector extension)
- Optional: QEMU user-mode or RISC-V hardware for execution

### Compiler Installation

For cross-compilation:
```bash
# Ubuntu/Debian
sudo apt-get install gcc-riscv64-linux-gnu

# Or build from source
# https://github.com/riscv-collab/riscv-gnu-toolchain
```

## Building

```bash
# Build everything
make all

# Build and run tests only
make test

# Build and run benchmarks only
make bench

# Clean build artifacts
make clean

# Show help
make help
```

## Usage Example

```c
#include "zvbb_emu.h"
#include <stdio.h>

int main() {
    // Set vector length for 32-bit elements
    size_t vl = vsetvl_e32m1(4);
    
    // Prepare data
    uint32_t data[4] = {0x12345678, 0xABCDEF00, 0x00112233, 0xFFFFFFFF};
    uint32_t result[4];
    
    // Load data into vector register
    vuint32m1_t vec_data = vle32_v_u32m1(data, vl);
    
    // Rotate right by 8 bits (vror.vx)
    vuint32m1_t vec_result = vror_vx_u32m1_emu(vec_data, 8, vl);
    
    // Store result
    vse32_v_u32m1(result, vec_result, vl);
    
    // Print results
    for (int i = 0; i < 4; i++) {
        printf("0x%08x -> 0x%08x\n", data[i], result[i]);
    }
    
    return 0;
}
```

## API Reference

### Function Naming Convention

Format: `vror_{variant}_{type}{lmul}_emu`

- **variant**: `vv` (vector-vector), `vx` (vector-scalar), or `vi` (vector-immediate)
- **type**: `u8`, `u16`, `u32`, or `u64`
- **lmul**: `m1`, `m2`, `m4`, or `m8`

### Examples

```c
// Vector-scalar rotate (all elements rotated by same amount)
vuint32m1_t vror_vx_u32m1_emu(vuint32m1_t vs2, uint32_t rs1, size_t vl);

// Vector-vector rotate (per-element rotation amounts)
vuint32m1_t vror_vv_u32m1_emu(vuint32m1_t vs2, vuint32m1_t vs1, size_t vl);

// Vector-immediate rotate (compile-time constant)
vuint32m1_t vror_vi_u32m1_emu(vuint32m1_t vs2, size_t imm, size_t vl);
```

Note: `vror.vi` variants are implemented as macros to enable compiler optimizations for immediate values.

## Testing

The test suite includes:

1. **Basic correctness tests**: Verify rotation logic with known values
2. **Edge cases**: Rotate by 0, full width, all-ones patterns
3. **Multi-width tests**: All element sizes (8, 16, 32, 64 bits)
4. **Random testing**: 1000+ iterations with random data verified against scalar reference

```bash
make test
```

Expected output:
```
===============================================
RISC-V Zvbb vror* Emulation Test Suite
===============================================

--- Basic Correctness Tests ---
Testing vror.vx u32 basic... PASS
Testing vror.vi u32 basic... PASS
...

Test Summary:
  Passed: 12
  Failed: 0
  Total:  12

✓ All tests passed!
```

## Benchmarking

The benchmark suite measures:

- **Throughput**: Operations per second, cycles per operation
- **Latency**: Dependency chain measurements
- **Multi-width performance**: Different element sizes
- **CSV output**: For further analysis

```bash
make bench
```

## Performance Characteristics

The emulation uses 4 vector operations per `vror`:
1. `vrsub` or scalar subtraction (for computing `width - n`)
2. `vsrl` (shift right logical)
3. `vsll` (shift left logical)
4. `vor` (bitwise OR to combine results)

Expected overhead compared to native `vror`:
- **vror.vi**: ~3-4x (best case, immediate allows optimization)
- **vror.vx**: ~4x
- **vror.vv**: ~5x (worst case, requires `vrsub`)

## Implementation Details

The library uses the standard rotation formula:
```
rotate_right(x, n) = (x >> n) | (x << (width - n))
```

This is implemented using:
- **Right shift**: `vsrl` (vector shift right logical)
- **Left shift**: `vsll` (vector shift left logical)  
- **Combine**: `vor` (vector bitwise OR)

For `vror.vv`, we use `vrsub` to compute `width - n` per element.

## License

See [LICENSE](LICENSE) file for details.

## References

- [RISC-V Vector Extension Specification](https://github.com/riscv/riscv-v-spec)
- [RISC-V Cryptography Extensions (Zvbb)](https://github.com/riscv/riscv-crypto)
- [RISC-V Vector Intrinsics](https://github.com/riscv-non-isa/rvv-intrinsic-doc)

## Contributing

Contributions are welcome! Areas for improvement:

- Additional instruction emulations (vrol, other Zvbb instructions)
- Optimizations for specific microarchitectures
- Masked operation variants
- Native Zvbb comparison tests

## Author

Created for RISC-V vector development and testing.
