/**
 * Functional test for Zvzip vpaire/vpairo: 4×4 matrix transpose.
 *
 * Matrix layout (row-major, uint32_t, one row per vector register):
 *   v1 = | a  b  c  d | A  B  C  D | ...   (row 0)
 *   v2 = | e  f  g  h | E  F  G  H | ...   (row 1)
 *   v3 = | i  j  k  l | I  J  K  L | ...   (row 2)
 *   v4 = | m  n  o  p | M  N  O  P | ...   (row 3)
 *
 * After transpose:
 *   v1 = | a  e  i  m | A  E  I  M | ...   (column 0)
 *   v2 = | b  f  j  n | B  F  J  N | ...   (column 1)
 *   v3 = | c  g  k  o | C  G  K  O | ...   (column 2)
 *   v4 = | d  h  l  p | D  H  L  P | ...   (column 3)
 *
 * Algorithm (two rounds of vpaire/vpairo at increasing SEW):
 *
 *   // Round 1 – e32, m1: pair adjacent elements
 *   v5 = vpaire(v1, v2)    v6 = vpairo(v1, v2)
 *   v7 = vpaire(v3, v4)    v8 = vpairo(v3, v4)
 *
 *   // Round 2 – e64, m1: pair adjacent 64-bit groups
 *   v1 = vpaire(v5, v7)    v2 = vpaire(v6, v8)
 *   v3 = vpairo(v5, v7)    v4 = vpairo(v6, v8)
 */

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include <riscv_vector.h>

/* Pull in the generated Zvzip emulation intrinsics */
#include "zvzip_emu.h"

/* ---------- helpers ---------- */

static void print_u32_vector(const char *label, const uint32_t *buf, size_t n) {
    printf("  %s:", label);
    for (size_t i = 0; i < n; i++)
        printf(" %2u", buf[i]);
    printf("\n");
}

static int check_u32_vector(const char *label, const uint32_t *got,
                            const uint32_t *expected, size_t n) {
    if (memcmp(got, expected, n * sizeof(uint32_t)) == 0)
        return 0;
    printf("MISMATCH in %s\n", label);
    print_u32_vector("expected", expected, n);
    print_u32_vector("     got", got, n);
    return 1;
}

/* ---------- transpose ---------- */

/**
 * Transpose N/4 consecutive 4×4 uint32_t matrices stored row-major
 * in four vectors (rows 0-3), writing the result back in-place.
 *
 * n must be a multiple of 4.
 */
static void transpose_4x4_u32(uint32_t *row0, uint32_t *row1,
                               uint32_t *row2, uint32_t *row3, size_t n) {
    /* Load rows */
    size_t vl32 = __riscv_vsetvl_e32m1(n);
    vuint32m1_t v1 = __riscv_vle32_v_u32m1(row0, vl32);
    vuint32m1_t v2 = __riscv_vle32_v_u32m1(row1, vl32);
    vuint32m1_t v3 = __riscv_vle32_v_u32m1(row2, vl32);
    vuint32m1_t v4 = __riscv_vle32_v_u32m1(row3, vl32);

    /* Round 1 – SEW=32: pair adjacent elements */
    vuint32m1_t v5 = __riscv_vpaire_vv_u32m1(v1, v2, vl32);
    vuint32m1_t v6 = __riscv_vpairo_vv_u32m1(v1, v2, vl32);
    vuint32m1_t v7 = __riscv_vpaire_vv_u32m1(v3, v4, vl32);
    vuint32m1_t v8 = __riscv_vpairo_vv_u32m1(v3, v4, vl32);

    /* Round 2 – SEW=64: pair adjacent 64-bit groups */
    size_t vl64 = __riscv_vsetvl_e64m1(n / 2);  /* half as many 64-bit elements */
    vuint64m1_t v5_64 = __riscv_vreinterpret_v_u32m1_u64m1(v5);
    vuint64m1_t v6_64 = __riscv_vreinterpret_v_u32m1_u64m1(v6);
    vuint64m1_t v7_64 = __riscv_vreinterpret_v_u32m1_u64m1(v7);
    vuint64m1_t v8_64 = __riscv_vreinterpret_v_u32m1_u64m1(v8);

    vuint64m1_t r1_64 = __riscv_vpaire_vv_u64m1(v5_64, v7_64, vl64);
    vuint64m1_t r2_64 = __riscv_vpaire_vv_u64m1(v6_64, v8_64, vl64);
    vuint64m1_t r3_64 = __riscv_vpairo_vv_u64m1(v5_64, v7_64, vl64);
    vuint64m1_t r4_64 = __riscv_vpairo_vv_u64m1(v6_64, v8_64, vl64);

    /* Store transposed rows */
    vl32 = __riscv_vsetvl_e32m1(n);
    __riscv_vse32_v_u32m1(row0, __riscv_vreinterpret_v_u64m1_u32m1(r1_64), vl32);
    __riscv_vse32_v_u32m1(row1, __riscv_vreinterpret_v_u64m1_u32m1(r2_64), vl32);
    __riscv_vse32_v_u32m1(row2, __riscv_vreinterpret_v_u64m1_u32m1(r3_64), vl32);
    __riscv_vse32_v_u32m1(row3, __riscv_vreinterpret_v_u64m1_u32m1(r4_64), vl32);
}

/* ---------- test driver ---------- */

int main(void) {
    int errors = 0;

    /*
     * Test: single 4×4 matrix
     *
     *   Input:                     Expected output:
     *   row0 =  1  2  3  4        row0 =  1  5  9 13
     *   row1 =  5  6  7  8        row1 =  2  6 10 14
     *   row2 =  9 10 11 12        row2 =  3  7 11 15
     *   row3 = 13 14 15 16        row3 =  4  8 12 16
     */
    {
        const size_t N = 4;
        uint32_t r0[] = { 1,  2,  3,  4};
        uint32_t r1[] = { 5,  6,  7,  8};
        uint32_t r2[] = { 9, 10, 11, 12};
        uint32_t r3[] = {13, 14, 15, 16};

        const uint32_t e0[] = { 1,  5,  9, 13};
        const uint32_t e1[] = { 2,  6, 10, 14};
        const uint32_t e2[] = { 3,  7, 11, 15};
        const uint32_t e3[] = { 4,  8, 12, 16};

        printf("Test 1: single 4x4 transpose\n");
        transpose_4x4_u32(r0, r1, r2, r3, N);

        errors += check_u32_vector("row0", r0, e0, N);
        errors += check_u32_vector("row1", r1, e1, N);
        errors += check_u32_vector("row2", r2, e2, N);
        errors += check_u32_vector("row3", r3, e3, N);
    }

    /*
     * Test: two consecutive 4×4 matrices (8 elements per row)
     *
     *  First matrix: values  1..16   (letters a..p in the diagram)
     *  Second matrix: values 17..32  (letters A..P in the diagram)
     */
    {
        const size_t N = 8;
        uint32_t r0[] = { 1,  2,  3,  4, 17, 18, 19, 20};
        uint32_t r1[] = { 5,  6,  7,  8, 21, 22, 23, 24};
        uint32_t r2[] = { 9, 10, 11, 12, 25, 26, 27, 28};
        uint32_t r3[] = {13, 14, 15, 16, 29, 30, 31, 32};

        const uint32_t e0[] = { 1,  5,  9, 13, 17, 21, 25, 29};
        const uint32_t e1[] = { 2,  6, 10, 14, 18, 22, 26, 30};
        const uint32_t e2[] = { 3,  7, 11, 15, 19, 23, 27, 31};
        const uint32_t e3[] = { 4,  8, 12, 16, 20, 24, 28, 32};

        printf("Test 2: two consecutive 4x4 transposes\n");
        transpose_4x4_u32(r0, r1, r2, r3, N);

        errors += check_u32_vector("row0", r0, e0, N);
        errors += check_u32_vector("row1", r1, e1, N);
        errors += check_u32_vector("row2", r2, e2, N);
        errors += check_u32_vector("row3", r3, e3, N);
    }

    /*
     * Test: double-transpose is identity
     */
    {
        const size_t N = 4;
        const uint32_t orig0[] = {10, 20, 30, 40};
        const uint32_t orig1[] = {50, 60, 70, 80};
        const uint32_t orig2[] = {11, 22, 33, 44};
        const uint32_t orig3[] = {55, 66, 77, 88};

        uint32_t r0[4], r1[4], r2[4], r3[4];
        memcpy(r0, orig0, sizeof(r0));
        memcpy(r1, orig1, sizeof(r1));
        memcpy(r2, orig2, sizeof(r2));
        memcpy(r3, orig3, sizeof(r3));

        printf("Test 3: double-transpose identity\n");
        transpose_4x4_u32(r0, r1, r2, r3, N);
        transpose_4x4_u32(r0, r1, r2, r3, N);

        errors += check_u32_vector("row0", r0, orig0, N);
        errors += check_u32_vector("row1", r1, orig1, N);
        errors += check_u32_vector("row2", r2, orig2, N);
        errors += check_u32_vector("row3", r3, orig3, N);
    }

    if (errors == 0)
        printf("ALL TESTS PASSED\n");
    else
        printf("%d ERRORS\n", errors);

    return errors != 0;
}
