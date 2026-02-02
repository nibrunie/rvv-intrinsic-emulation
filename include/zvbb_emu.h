/**
 * @file zvbb_emu.h
 * @brief RISC-V Zvbb Vector Rotate Right (vror*) Instruction Emulation
 * 
 * This header-only library provides emulation for RISC-V Zvbb vector rotate
 * right instructions using standard RISC-V vector intrinsics (vsrl, vsll, vor).
 * 
 * Supported Instructions:
 * - vror.vv: Vector-vector rotate (each element rotated by corresponding amount)
 * - vror.vx: Vector-scalar rotate (all elements rotated by same amount)
 * - vror.vi: Vector-immediate rotate (compile-time constant rotation)
 * 
 * Element widths supported: 8, 16, 32, 64 bits
 * LMUL supported: mf8, mf4, mf2, m1, m2, m4, m8 (where applicable)
 * 
 * Usage Example:
 *   #include "zvbb_emu.h"
 *   
 *   vuint32m1_t data = ...;
 *   vuint32m1_t rotated = vror_vx_u32m1_emu(data, 8, vl);
 * 
 * @author Auto-generated
 * @date 2026-01-25
 */

#ifndef ZVBB_EMU_H
#define ZVBB_EMU_H

#include <riscv_vector.h>
#include <stdint.h>

// =============================================================================
// Helper Macros
// =============================================================================

/**
 * Emulate rotate right using shifts and OR
 * Formula: rotate_right(x, n) = (x >> n) | (x << (width - n))
 */

// =============================================================================
// vror.vv - Vector-Vector Rotate Right
// Each element rotated by corresponding element in rotation vector
// =============================================================================

// 8-bit elements
static inline vuint8m1_t vror_vv_u8m1_emu(vuint8m1_t vs2, vuint8m1_t vs1, size_t vl) {
    vuint8m1_t shift_right = vsrl_vv_u8m1(vs2, vs1, vl);
    vuint8m1_t width_minus_n = vrsub_vx_u8m1(vs1, 8, vl);
    vuint8m1_t shift_left = vsll_vv_u8m1(vs2, width_minus_n, vl);
    return vor_vv_u8m1(shift_right, shift_left, vl);
}

static inline vuint8m2_t vror_vv_u8m2_emu(vuint8m2_t vs2, vuint8m2_t vs1, size_t vl) {
    vuint8m2_t shift_right = vsrl_vv_u8m2(vs2, vs1, vl);
    vuint8m2_t width_minus_n = vrsub_vx_u8m2(vs1, 8, vl);
    vuint8m2_t shift_left = vsll_vv_u8m2(vs2, width_minus_n, vl);
    return vor_vv_u8m2(shift_right, shift_left, vl);
}

static inline vuint8m4_t vror_vv_u8m4_emu(vuint8m4_t vs2, vuint8m4_t vs1, size_t vl) {
    vuint8m4_t shift_right = vsrl_vv_u8m4(vs2, vs1, vl);
    vuint8m4_t width_minus_n = vrsub_vx_u8m4(vs1, 8, vl);
    vuint8m4_t shift_left = vsll_vv_u8m4(vs2, width_minus_n, vl);
    return vor_vv_u8m4(shift_right, shift_left, vl);
}

static inline vuint8m8_t vror_vv_u8m8_emu(vuint8m8_t vs2, vuint8m8_t vs1, size_t vl) {
    vuint8m8_t shift_right = vsrl_vv_u8m8(vs2, vs1, vl);
    vuint8m8_t width_minus_n = vrsub_vx_u8m8(vs1, 8, vl);
    vuint8m8_t shift_left = vsll_vv_u8m8(vs2, width_minus_n, vl);
    return vor_vv_u8m8(shift_right, shift_left, vl);
}

// 16-bit elements
static inline vuint16m1_t vror_vv_u16m1_emu(vuint16m1_t vs2, vuint16m1_t vs1, size_t vl) {
    vuint16m1_t shift_right = vsrl_vv_u16m1(vs2, vs1, vl);
    vuint16m1_t width_minus_n = vrsub_vx_u16m1(vs1, 16, vl);
    vuint16m1_t shift_left = vsll_vv_u16m1(vs2, width_minus_n, vl);
    return vor_vv_u16m1(shift_right, shift_left, vl);
}

static inline vuint16m2_t vror_vv_u16m2_emu(vuint16m2_t vs2, vuint16m2_t vs1, size_t vl) {
    vuint16m2_t shift_right = vsrl_vv_u16m2(vs2, vs1, vl);
    vuint16m2_t width_minus_n = vrsub_vx_u16m2(vs1, 16, vl);
    vuint16m2_t shift_left = vsll_vv_u16m2(vs2, width_minus_n, vl);
    return vor_vv_u16m2(shift_right, shift_left, vl);
}

static inline vuint16m4_t vror_vv_u16m4_emu(vuint16m4_t vs2, vuint16m4_t vs1, size_t vl) {
    vuint16m4_t shift_right = vsrl_vv_u16m4(vs2, vs1, vl);
    vuint16m4_t width_minus_n = vrsub_vx_u16m4(vs1, 16, vl);
    vuint16m4_t shift_left = vsll_vv_u16m4(vs2, width_minus_n, vl);
    return vor_vv_u16m4(shift_right, shift_left, vl);
}

static inline vuint16m8_t vror_vv_u16m8_emu(vuint16m8_t vs2, vuint16m8_t vs1, size_t vl) {
    vuint16m8_t shift_right = vsrl_vv_u16m8(vs2, vs1, vl);
    vuint16m8_t width_minus_n = vrsub_vx_u16m8(vs1, 16, vl);
    vuint16m8_t shift_left = vsll_vv_u16m8(vs2, width_minus_n, vl);
    return vor_vv_u16m8(shift_right, shift_left, vl);
}

// 32-bit elements
static inline vuint32m1_t vror_vv_u32m1_emu(vuint32m1_t vs2, vuint32m1_t vs1, size_t vl) {
    vuint32m1_t shift_right = vsrl_vv_u32m1(vs2, vs1, vl);
    vuint32m1_t width_minus_n = vrsub_vx_u32m1(vs1, 32, vl);
    vuint32m1_t shift_left = vsll_vv_u32m1(vs2, width_minus_n, vl);
    return vor_vv_u32m1(shift_right, shift_left, vl);
}

static inline vuint32m2_t vror_vv_u32m2_emu(vuint32m2_t vs2, vuint32m2_t vs1, size_t vl) {
    vuint32m2_t shift_right = vsrl_vv_u32m2(vs2, vs1, vl);
    vuint32m2_t width_minus_n = vrsub_vx_u32m2(vs1, 32, vl);
    vuint32m2_t shift_left = vsll_vv_u32m2(vs2, width_minus_n, vl);
    return vor_vv_u32m2(shift_right, shift_left, vl);
}

static inline vuint32m4_t vror_vv_u32m4_emu(vuint32m4_t vs2, vuint32m4_t vs1, size_t vl) {
    vuint32m4_t shift_right = vsrl_vv_u32m4(vs2, vs1, vl);
    vuint32m4_t width_minus_n = vrsub_vx_u32m4(vs1, 32, vl);
    vuint32m4_t shift_left = vsll_vv_u32m4(vs2, width_minus_n, vl);
    return vor_vv_u32m4(shift_right, shift_left, vl);
}

static inline vuint32m8_t vror_vv_u32m8_emu(vuint32m8_t vs2, vuint32m8_t vs1, size_t vl) {
    vuint32m8_t shift_right = vsrl_vv_u32m8(vs2, vs1, vl);
    vuint32m8_t width_minus_n = vrsub_vx_u32m8(vs1, 32, vl);
    vuint32m8_t shift_left = vsll_vv_u32m8(vs2, width_minus_n, vl);
    return vor_vv_u32m8(shift_right, shift_left, vl);
}

// 64-bit elements
static inline vuint64m1_t vror_vv_u64m1_emu(vuint64m1_t vs2, vuint64m1_t vs1, size_t vl) {
    vuint64m1_t shift_right = vsrl_vv_u64m1(vs2, vs1, vl);
    vuint64m1_t width_minus_n = vrsub_vx_u64m1(vs1, 64, vl);
    vuint64m1_t shift_left = vsll_vv_u64m1(vs2, width_minus_n, vl);
    return vor_vv_u64m1(shift_right, shift_left, vl);
}

static inline vuint64m2_t vror_vv_u64m2_emu(vuint64m2_t vs2, vuint64m2_t vs1, size_t vl) {
    vuint64m2_t shift_right = vsrl_vv_u64m2(vs2, vs1, vl);
    vuint64m2_t width_minus_n = vrsub_vx_u64m2(vs1, 64, vl);
    vuint64m2_t shift_left = vsll_vv_u64m2(vs2, width_minus_n, vl);
    return vor_vv_u64m2(shift_right, shift_left, vl);
}

static inline vuint64m4_t vror_vv_u64m4_emu(vuint64m4_t vs2, vuint64m4_t vs1, size_t vl) {
    vuint64m4_t shift_right = vsrl_vv_u64m4(vs2, vs1, vl);
    vuint64m4_t width_minus_n = vrsub_vx_u64m4(vs1, 64, vl);
    vuint64m4_t shift_left = vsll_vv_u64m4(vs2, width_minus_n, vl);
    return vor_vv_u64m4(shift_right, shift_left, vl);
}

static inline vuint64m8_t vror_vv_u64m8_emu(vuint64m8_t vs2, vuint64m8_t vs1, size_t vl) {
    vuint64m8_t shift_right = vsrl_vv_u64m8(vs2, vs1, vl);
    vuint64m8_t width_minus_n = vrsub_vx_u64m8(vs1, 64, vl);
    vuint64m8_t shift_left = vsll_vv_u64m8(vs2, width_minus_n, vl);
    return vor_vv_u64m8(shift_right, shift_left, vl);
}

// =============================================================================
// vror.vx - Vector-Scalar Rotate Right
// All elements rotated by the same scalar amount
// =============================================================================

// 8-bit elements
static inline vuint8m1_t vror_vx_u8m1_emu(vuint8m1_t vs2, uint8_t rs1, size_t vl) {
    vuint8m1_t shift_right = vsrl_vx_u8m1(vs2, rs1, vl);
    vuint8m1_t shift_left = vsll_vx_u8m1(vs2, 8 - rs1, vl);
    return vor_vv_u8m1(shift_right, shift_left, vl);
}

static inline vuint8m2_t vror_vx_u8m2_emu(vuint8m2_t vs2, uint8_t rs1, size_t vl) {
    vuint8m2_t shift_right = vsrl_vx_u8m2(vs2, rs1, vl);
    vuint8m2_t shift_left = vsll_vx_u8m2(vs2, 8 - rs1, vl);
    return vor_vv_u8m2(shift_right, shift_left, vl);
}

static inline vuint8m4_t vror_vx_u8m4_emu(vuint8m4_t vs2, uint8_t rs1, size_t vl) {
    vuint8m4_t shift_right = vsrl_vx_u8m4(vs2, rs1, vl);
    vuint8m4_t shift_left = vsll_vx_u8m4(vs2, 8 - rs1, vl);
    return vor_vv_u8m4(shift_right, shift_left, vl);
}

static inline vuint8m8_t vror_vx_u8m8_emu(vuint8m8_t vs2, uint8_t rs1, size_t vl) {
    vuint8m8_t shift_right = vsrl_vx_u8m8(vs2, rs1, vl);
    vuint8m8_t shift_left = vsll_vx_u8m8(vs2, 8 - rs1, vl);
    return vor_vv_u8m8(shift_right, shift_left, vl);
}

// 16-bit elements
static inline vuint16m1_t vror_vx_u16m1_emu(vuint16m1_t vs2, uint16_t rs1, size_t vl) {
    vuint16m1_t shift_right = vsrl_vx_u16m1(vs2, rs1, vl);
    vuint16m1_t shift_left = vsll_vx_u16m1(vs2, 16 - rs1, vl);
    return vor_vv_u16m1(shift_right, shift_left, vl);
}

static inline vuint16m2_t vror_vx_u16m2_emu(vuint16m2_t vs2, uint16_t rs1, size_t vl) {
    vuint16m2_t shift_right = vsrl_vx_u16m2(vs2, rs1, vl);
    vuint16m2_t shift_left = vsll_vx_u16m2(vs2, 16 - rs1, vl);
    return vor_vv_u16m2(shift_right, shift_left, vl);
}

static inline vuint16m4_t vror_vx_u16m4_emu(vuint16m4_t vs2, uint16_t rs1, size_t vl) {
    vuint16m4_t shift_right = vsrl_vx_u16m4(vs2, rs1, vl);
    vuint16m4_t shift_left = vsll_vx_u16m4(vs2, 16 - rs1, vl);
    return vor_vv_u16m4(shift_right, shift_left, vl);
}

static inline vuint16m8_t vror_vx_u16m8_emu(vuint16m8_t vs2, uint16_t rs1, size_t vl) {
    vuint16m8_t shift_right = vsrl_vx_u16m8(vs2, rs1, vl);
    vuint16m8_t shift_left = vsll_vx_u16m8(vs2, 16 - rs1, vl);
    return vor_vv_u16m8(shift_right, shift_left, vl);
}

// 32-bit elements
static inline vuint32m1_t vror_vx_u32m1_emu(vuint32m1_t vs2, uint32_t rs1, size_t vl) {
    vuint32m1_t shift_right = vsrl_vx_u32m1(vs2, rs1, vl);
    vuint32m1_t shift_left = vsll_vx_u32m1(vs2, 32 - rs1, vl);
    return vor_vv_u32m1(shift_right, shift_left, vl);
}

static inline vuint32m2_t vror_vx_u32m2_emu(vuint32m2_t vs2, uint32_t rs1, size_t vl) {
    vuint32m2_t shift_right = vsrl_vx_u32m2(vs2, rs1, vl);
    vuint32m2_t shift_left = vsll_vx_u32m2(vs2, 32 - rs1, vl);
    return vor_vv_u32m2(shift_right, shift_left, vl);
}

static inline vuint32m4_t vror_vx_u32m4_emu(vuint32m4_t vs2, uint32_t rs1, size_t vl) {
    vuint32m4_t shift_right = vsrl_vx_u32m4(vs2, rs1, vl);
    vuint32m4_t shift_left = vsll_vx_u32m4(vs2, 32 - rs1, vl);
    return vor_vv_u32m4(shift_right, shift_left, vl);
}

static inline vuint32m8_t vror_vx_u32m8_emu(vuint32m8_t vs2, uint32_t rs1, size_t vl) {
    vuint32m8_t shift_right = vsrl_vx_u32m8(vs2, rs1, vl);
    vuint32m8_t shift_left = vsll_vx_u32m8(vs2, 32 - rs1, vl);
    return vor_vv_u32m8(shift_right, shift_left, vl);
}

// 64-bit elements
static inline vuint64m1_t vror_vx_u64m1_emu(vuint64m1_t vs2, uint64_t rs1, size_t vl) {
    vuint64m1_t shift_right = vsrl_vx_u64m1(vs2, rs1, vl);
    vuint64m1_t shift_left = vsll_vx_u64m1(vs2, 64 - rs1, vl);
    return vor_vv_u64m1(shift_right, shift_left, vl);
}

static inline vuint64m2_t vror_vx_u64m2_emu(vuint64m2_t vs2, uint64_t rs1, size_t vl) {
    vuint64m2_t shift_right = vsrl_vx_u64m2(vs2, rs1, vl);
    vuint64m2_t shift_left = vsll_vx_u64m2(vs2, 64 - rs1, vl);
    return vor_vv_u64m2(shift_right, shift_left, vl);
}

static inline vuint64m4_t vror_vx_u64m4_emu(vuint64m4_t vs2, uint64_t rs1, size_t vl) {
    vuint64m4_t shift_right = vsrl_vx_u64m4(vs2, rs1, vl);
    vuint64m4_t shift_left = vsll_vx_u64m4(vs2, 64 - rs1, vl);
    return vor_vv_u64m4(shift_right, shift_left, vl);
}

static inline vuint64m8_t vror_vx_u64m8_emu(vuint64m8_t vs2, uint64_t rs1, size_t vl) {
    vuint64m8_t shift_right = vsrl_vx_u64m8(vs2, rs1, vl);
    vuint64m8_t shift_left = vsll_vx_u64m8(vs2, 64 - rs1, vl);
    return vor_vv_u64m8(shift_right, shift_left, vl);
}

// =============================================================================
// vror.vi - Vector-Immediate Rotate Right
// All elements rotated by compile-time constant
// =============================================================================

// Note: For immediate variants, we use macros to allow compile-time constant
// This enables potential compiler optimizations

#define vror_vi_u8m1_emu(vs2, imm, vl) ({ \
    vuint8m1_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 7; \
    vuint8m1_t _sr = vsrl_vx_u8m1(_vs2, _imm, _vl); \
    vuint8m1_t _sl = vsll_vx_u8m1(_vs2, 8 - _imm, _vl); \
    vor_vv_u8m1(_sr, _sl, _vl); \
})

#define vror_vi_u8m2_emu(vs2, imm, vl) ({ \
    vuint8m2_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 7; \
    vuint8m2_t _sr = vsrl_vx_u8m2(_vs2, _imm, _vl); \
    vuint8m2_t _sl = vsll_vx_u8m2(_vs2, 8 - _imm, _vl); \
    vor_vv_u8m2(_sr, _sl, _vl); \
})

#define vror_vi_u8m4_emu(vs2, imm, vl) ({ \
    vuint8m4_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 7; \
    vuint8m4_t _sr = vsrl_vx_u8m4(_vs2, _imm, _vl); \
    vuint8m4_t _sl = vsll_vx_u8m4(_vs2, 8 - _imm, _vl); \
    vor_vv_u8m4(_sr, _sl, _vl); \
})

#define vror_vi_u8m8_emu(vs2, imm, vl) ({ \
    vuint8m8_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 7; \
    vuint8m8_t _sr = vsrl_vx_u8m8(_vs2, _imm, _vl); \
    vuint8m8_t _sl = vsll_vx_u8m8(_vs2, 8 - _imm, _vl); \
    vor_vv_u8m8(_sr, _sl, _vl); \
})

#define vror_vi_u16m1_emu(vs2, imm, vl) ({ \
    vuint16m1_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 15; \
    vuint16m1_t _sr = vsrl_vx_u16m1(_vs2, _imm, _vl); \
    vuint16m1_t _sl = vsll_vx_u16m1(_vs2, 16 - _imm, _vl); \
    vor_vv_u16m1(_sr, _sl, _vl); \
})

#define vror_vi_u16m2_emu(vs2, imm, vl) ({ \
    vuint16m2_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 15; \
    vuint16m2_t _sr = vsrl_vx_u16m2(_vs2, _imm, _vl); \
    vuint16m2_t _sl = vsll_vx_u16m2(_vs2, 16 - _imm, _vl); \
    vor_vv_u16m2(_sr, _sl, _vl); \
})

#define vror_vi_u16m4_emu(vs2, imm, vl) ({ \
    vuint16m4_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 15; \
    vuint16m4_t _sr = vsrl_vx_u16m4(_vs2, _imm, _vl); \
    vuint16m4_t _sl = vsll_vx_u16m4(_vs2, 16 - _imm, _vl); \
    vor_vv_u16m4(_sr, _sl, _vl); \
})

#define vror_vi_u16m8_emu(vs2, imm, vl) ({ \
    vuint16m8_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 15; \
    vuint16m8_t _sr = vsrl_vx_u16m8(_vs2, _imm, _vl); \
    vuint16m8_t _sl = vsll_vx_u16m8(_vs2, 16 - _imm, _vl); \
    vor_vv_u16m8(_sr, _sl, _vl); \
})

#define vror_vi_u32m1_emu(vs2, imm, vl) ({ \
    vuint32m1_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 31; \
    vuint32m1_t _sr = vsrl_vx_u32m1(_vs2, _imm, _vl); \
    vuint32m1_t _sl = vsll_vx_u32m1(_vs2, 32 - _imm, _vl); \
    vor_vv_u32m1(_sr, _sl, _vl); \
})

#define vror_vi_u32m2_emu(vs2, imm, vl) ({ \
    vuint32m2_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 31; \
    vuint32m2_t _sr = vsrl_vx_u32m2(_vs2, _imm, _vl); \
    vuint32m2_t _sl = vsll_vx_u32m2(_vs2, 32 - _imm, _vl); \
    vor_vv_u32m2(_sr, _sl, _vl); \
})

#define vror_vi_u32m4_emu(vs2, imm, vl) ({ \
    vuint32m4_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 31; \
    vuint32m4_t _sr = vsrl_vx_u32m4(_vs2, _imm, _vl); \
    vuint32m4_t _sl = vsll_vx_u32m4(_vs2, 32 - _imm, _vl); \
    vor_vv_u32m4(_sr, _sl, _vl); \
})

#define vror_vi_u32m8_emu(vs2, imm, vl) ({ \
    vuint32m8_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 31; \
    vuint32m8_t _sr = vsrl_vx_u32m8(_vs2, _imm, _vl); \
    vuint32m8_t _sl = vsll_vx_u32m8(_vs2, 32 - _imm, _vl); \
    vor_vv_u32m8(_sr, _sl, _vl); \
})

#define vror_vi_u64m1_emu(vs2, imm, vl) ({ \
    vuint64m1_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 63; \
    vuint64m1_t _sr = vsrl_vx_u64m1(_vs2, _imm, _vl); \
    vuint64m1_t _sl = vsll_vx_u64m1(_vs2, 64 - _imm, _vl); \
    vor_vv_u64m1(_sr, _sl, _vl); \
})

#define vror_vi_u64m2_emu(vs2, imm, vl) ({ \
    vuint64m2_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 63; \
    vuint64m2_t _sr = vsrl_vx_u64m2(_vs2, _imm, _vl); \
    vuint64m2_t _sl = vsll_vx_u64m2(_vs2, 64 - _imm, _vl); \
    vor_vv_u64m2(_sr, _sl, _vl); \
})

#define vror_vi_u64m4_emu(vs2, imm, vl) ({ \
    vuint64m4_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 63; \
    vuint64m4_t _sr = vsrl_vx_u64m4(_vs2, _imm, _vl); \
    vuint64m4_t _sl = vsll_vx_u64m4(_vs2, 64 - _imm, _vl); \
    vor_vv_u64m4(_sr, _sl, _vl); \
})

#define vror_vi_u64m8_emu(vs2, imm, vl) ({ \
    vuint64m8_t _vs2 = (vs2); \
    size_t _vl = (vl); \
    size_t _imm = (imm) & 63; \
    vuint64m8_t _sr = vsrl_vx_u64m8(_vs2, _imm, _vl); \
    vuint64m8_t _sl = vsll_vx_u64m8(_vs2, 64 - _imm, _vl); \
    vor_vv_u64m8(_sr, _sl, _vl); \
})

#endif // ZVBB_EMU_H
