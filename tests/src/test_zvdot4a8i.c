#include "zvdot4a8i_emu.h"
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>


#define TEST_SIZE_N 128
#define TEST_SIZE_M 64
#define TEST_SIZE_K 32

// implement a 8-bit integer matrix multipliy n x k x m

void matrix_multiply(uint32_t* out, uint32_t* acc, uint8_t* lhs, uint8_t* rhs) {
    for (int i = 0; i < TEST_SIZE_M; i++) {
        for (int j = 0; j < TEST_SIZE_N; j++) {
            out[i * TEST_SIZE_N + j] = acc[i * TEST_SIZE_N + j];
            for (int k = 0; k < TEST_SIZE_K; k++) {
                out[i * TEST_SIZE_N + j] += (uint32_t) lhs[i * TEST_SIZE_K + k] * (uint32_t) rhs[k * TEST_SIZE_N + j];
            }
        }
    }
}

void matrix_multiply_baseline(uint32_t* out, uint32_t* acc, uint8_t* lhs, uint8_t* rhs) {
    for (int i = 0; i < TEST_SIZE_M; i++) {
        for (int j = 0; j < TEST_SIZE_N; j++) {
            out[i * TEST_SIZE_N + j] = acc[i * TEST_SIZE_N + j];
            for (int k = 0; k < TEST_SIZE_K; k += 4) {
                out[i * TEST_SIZE_N + j] += (uint32_t) lhs[i * TEST_SIZE_K + k] * (uint32_t) rhs[k * TEST_SIZE_N + j];
                out[i * TEST_SIZE_N + j] += (uint32_t) lhs[i * TEST_SIZE_K + k + 1] * (uint32_t) rhs[(k + 1) * TEST_SIZE_N + j];
                out[i * TEST_SIZE_N + j] += (uint32_t) lhs[i * TEST_SIZE_K + k + 2] * (uint32_t) rhs[(k + 2) * TEST_SIZE_N + j];
                out[i * TEST_SIZE_N + j] += (uint32_t) lhs[i * TEST_SIZE_K + k + 3] * (uint32_t) rhs[(k + 3) * TEST_SIZE_N + j];
            }
        }
    }
}

#ifdef __riscv_vector
void matrix_multiply_intrinsics(uint32_t* out, uint32_t* acc, uint8_t* lhs, uint8_t* rhs) {
    for (int j = 0; j < TEST_SIZE_N; j++) {
        size_t avl = TEST_SIZE_M;
        size_t vl = -1;
        for (int i = 0; avl > 0; i += vl) {
            // out[i * TEST_SIZE_M + j] = acc[i * TEST_SIZE_M + j];
            vl = __riscv_vsetvl_e32m1(avl);
	    avl -= vl;

            vuint32m1_t vout = __riscv_vlse32_v_u32m1(acc + i * TEST_SIZE_N + j, TEST_SIZE_N * sizeof(uint32_t), vl);
            // for (int k = 0; k < TEST_SIZE_K; k += 4) {
            //    out[i * TEST_SIZE_M + j] += (uint32_t) lhs[i * TEST_SIZE_K + k] * (uint32_t) rhs[k * TEST_SIZE_M + j];
            //    out[i * TEST_SIZE_M + j] += (uint32_t) lhs[i * TEST_SIZE_K + k + 1] * (uint32_t) rhs[(k + 1) * TEST_SIZE_M + j];
            //    out[i * TEST_SIZE_M + j] += (uint32_t) lhs[i * TEST_SIZE_K + k + 2] * (uint32_t) rhs[(k + 2) * TEST_SIZE_M + j];
            //    out[i * TEST_SIZE_M + j] += (uint32_t) lhs[i * TEST_SIZE_K + k + 3] * (uint32_t) rhs[(k + 3) * TEST_SIZE_M + j];
            //}
            for (int k = 0; k < TEST_SIZE_K; k += 4) {
                vuint32m1_t vlhs = __riscv_vlse32_v_u32m1((uint32_t*)(lhs + i * TEST_SIZE_K + k), TEST_SIZE_K, vl);
                // building right hand side operand
                uint32_t rhs_4elts = 0;
                for (int l = 0; l < 4; l++) {
                    rhs_4elts += (uint32_t) (rhs[(k + l) * TEST_SIZE_N + j]) << (l * 8);
                }
                vout = __riscv_vdot4au_vx_u32m1(vout, vlhs, rhs_4elts, vl);
            }
            __riscv_vsse32_v_u32m1(out + i * TEST_SIZE_N + j, TEST_SIZE_N * sizeof(uint32_t), vout, vl);
        }
    }
}
#endif
    


int main() {
    uint8_t* lhs = malloc(TEST_SIZE_N * TEST_SIZE_K * sizeof(uint8_t));
    uint8_t* rhs = malloc(TEST_SIZE_K * TEST_SIZE_M * sizeof(uint8_t));
    uint32_t* acc = malloc(TEST_SIZE_N * TEST_SIZE_M * sizeof(uint32_t));
    uint32_t* out_ref = malloc(TEST_SIZE_N * TEST_SIZE_M * sizeof(uint32_t));
    uint32_t* out_emu = malloc(TEST_SIZE_N * TEST_SIZE_M * sizeof(uint32_t));

    // randomizing input    
    for (int i = 0; i < TEST_SIZE_N; i++) {
        for (int j = 0; j < TEST_SIZE_K; j++) {
            lhs[i * TEST_SIZE_K + j] = rand() % 256;
        }
    }
    for (int i = 0; i < TEST_SIZE_K; i++) {
        for (int j = 0; j < TEST_SIZE_M; j++) {
            rhs[i * TEST_SIZE_M + j] = rand() % 256;
        }
    }
    for (int i = 0; i < TEST_SIZE_N; i++) {
        for (int j = 0; j < TEST_SIZE_M; j++) {
            acc[i * TEST_SIZE_M + j] = rand();
        }
    }

    // testing
    matrix_multiply(out_ref, acc, lhs, rhs);
#   ifdef __riscv_vector
        matrix_multiply_intrinsics(out_emu, acc, lhs, rhs);
#   else
        matrix_multiply_baseline(out_emu, acc, lhs, rhs);
#   endif

    // comparing
    for (int i = 0; i < TEST_SIZE_N; i++) {
        for (int j = 0; j < TEST_SIZE_M; j++) {
            if (out_ref[i * TEST_SIZE_M + j] != out_emu[i * TEST_SIZE_M + j]) {
                printf("Mismatch at (%d, %d): expected %d, got %d\n", i, j, out_ref[i * TEST_SIZE_M + j], out_emu[i * TEST_SIZE_M + j]);
                return 1;
            }
        }
    }

    printf("All tests passed!\n");
    return 0;
}
