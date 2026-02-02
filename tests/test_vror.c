/**
 * @file test_vror.c
 * @brief Test suite for RISC-V Zvbb vror* emulation library
 * 
 * Tests include:
 * - Basic correctness tests with known values
 * - Edge cases (rotate by 0, full width, etc.)
 * - Random testing against scalar reference implementation
 * - All element widths (8, 16, 32, 64 bits)
 * - All instruction variants (vv, vx, vi)
 */

#include "../include/zvbb_emu.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

// =============================================================================
// Scalar Reference Implementation
// =============================================================================

static inline uint8_t ror_u8_ref(uint8_t x, uint8_t n) {
    n &= 7;
    return (x >> n) | (x << (8 - n));
}

static inline uint16_t ror_u16_ref(uint16_t x, uint16_t n) {
    n &= 15;
    return (x >> n) | (x << (16 - n));
}

static inline uint32_t ror_u32_ref(uint32_t x, uint32_t n) {
    n &= 31;
    return (x >> n) | (x << (32 - n));
}

static inline uint64_t ror_u64_ref(uint64_t x, uint64_t n) {
    n &= 63;
    return (x >> n) | (x << (64 - n));
}

// =============================================================================
// Test Statistics
// =============================================================================

static int tests_passed = 0;
static int tests_failed = 0;

#define TEST_ASSERT(cond, fmt, ...) do { \
    if (!(cond)) { \
        printf("FAIL: " fmt "\n", ##__VA_ARGS__); \
        tests_failed++; \
        return 0; \
    } \
} while(0)

#define TEST_PASS() do { \
    tests_passed++; \
    return 1; \
} while(0)

// =============================================================================
// Basic Correctness Tests - 32-bit
// =============================================================================

static int test_vror_vx_u32_basic() {
    printf("Testing vror.vx u32 basic... ");
    
    size_t vl = vsetvl_e32m1(4);
    uint32_t data[4] = {0x12345678, 0xABCDEF00, 0x00112233, 0xFFFFFFFF};
    uint32_t expected[4];
    uint32_t result[4];
    
    // Rotate right by 8 bits
    for (int i = 0; i < 4; i++) {
        expected[i] = ror_u32_ref(data[i], 8);
    }
    
    vuint32m1_t vec_data = vle32_v_u32m1(data, vl);
    vuint32m1_t vec_result = vror_vx_u32m1_emu(vec_data, 8, vl);
    vse32_v_u32m1(result, vec_result, vl);
    
    for (int i = 0; i < 4; i++) {
        TEST_ASSERT(result[i] == expected[i], 
            "Element %d: expected 0x%08x, got 0x%08x", i, expected[i], result[i]);
    }
    
    printf("PASS\n");
    TEST_PASS();
}

static int test_vror_vi_u32_basic() {
    printf("Testing vror.vi u32 basic... ");
    
    size_t vl = vsetvl_e32m1(4);
    uint32_t data[4] = {0x12345678, 0xABCDEF00, 0x00112233, 0xFFFFFFFF};
    uint32_t expected[4];
    uint32_t result[4];
    
    // Rotate right by 4 bits (immediate)
    for (int i = 0; i < 4; i++) {
        expected[i] = ror_u32_ref(data[i], 4);
    }
    
    vuint32m1_t vec_data = vle32_v_u32m1(data, vl);
    vuint32m1_t vec_result = vror_vi_u32m1_emu(vec_data, 4, vl);
    vse32_v_u32m1(result, vec_result, vl);
    
    for (int i = 0; i < 4; i++) {
        TEST_ASSERT(result[i] == expected[i], 
            "Element %d: expected 0x%08x, got 0x%08x", i, expected[i], result[i]);
    }
    
    printf("PASS\n");
    TEST_PASS();
}

static int test_vror_vv_u32_basic() {
    printf("Testing vror.vv u32 basic... ");
    
    size_t vl = vsetvl_e32m1(4);
    uint32_t data[4] = {0x12345678, 0xABCDEF00, 0x00112233, 0xFFFFFFFF};
    uint32_t shifts[4] = {1, 4, 8, 16};
    uint32_t expected[4];
    uint32_t result[4];
    
    for (int i = 0; i < 4; i++) {
        expected[i] = ror_u32_ref(data[i], shifts[i]);
    }
    
    vuint32m1_t vec_data = vle32_v_u32m1(data, vl);
    vuint32m1_t vec_shifts = vle32_v_u32m1(shifts, vl);
    vuint32m1_t vec_result = vror_vv_u32m1_emu(vec_data, vec_shifts, vl);
    vse32_v_u32m1(result, vec_result, vl);
    
    for (int i = 0; i < 4; i++) {
        TEST_ASSERT(result[i] == expected[i], 
            "Element %d: expected 0x%08x, got 0x%08x", i, expected[i], result[i]);
    }
    
    printf("PASS\n");
    TEST_PASS();
}

// =============================================================================
// Edge Case Tests
// =============================================================================

static int test_vror_rotate_by_zero() {
    printf("Testing vror rotate by 0... ");
    
    size_t vl = vsetvl_e32m1(4);
    uint32_t data[4] = {0x12345678, 0xABCDEF00, 0x00112233, 0xFFFFFFFF};
    uint32_t result[4];
    
    vuint32m1_t vec_data = vle32_v_u32m1(data, vl);
    vuint32m1_t vec_result = vror_vx_u32m1_emu(vec_data, 0, vl);
    vse32_v_u32m1(result, vec_result, vl);
    
    for (int i = 0; i < 4; i++) {
        TEST_ASSERT(result[i] == data[i], 
            "Element %d: expected 0x%08x, got 0x%08x", i, data[i], result[i]);
    }
    
    printf("PASS\n");
    TEST_PASS();
}

static int test_vror_rotate_by_width() {
    printf("Testing vror rotate by full width... ");
    
    size_t vl = vsetvl_e32m1(4);
    uint32_t data[4] = {0x12345678, 0xABCDEF00, 0x00112233, 0xFFFFFFFF};
    uint32_t result[4];
    
    // Rotate by 32 should be same as rotate by 0
    vuint32m1_t vec_data = vle32_v_u32m1(data, vl);
    vuint32m1_t vec_result = vror_vx_u32m1_emu(vec_data, 32, vl);
    vse32_v_u32m1(result, vec_result, vl);
    
    for (int i = 0; i < 4; i++) {
        TEST_ASSERT(result[i] == data[i], 
            "Element %d: expected 0x%08x, got 0x%08x", i, data[i], result[i]);
    }
    
    printf("PASS\n");
    TEST_PASS();
}

static int test_vror_all_ones() {
    printf("Testing vror with all ones... ");
    
    size_t vl = vsetvl_e32m1(4);
    uint32_t data[4] = {0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF};
    uint32_t result[4];
    
    // Rotating all 1s should still be all 1s
    vuint32m1_t vec_data = vle32_v_u32m1(data, vl);
    vuint32m1_t vec_result = vror_vx_u32m1_emu(vec_data, 13, vl);
    vse32_v_u32m1(result, vec_result, vl);
    
    for (int i = 0; i < 4; i++) {
        TEST_ASSERT(result[i] == 0xFFFFFFFF, 
            "Element %d: expected 0xFFFFFFFF, got 0x%08x", i, result[i]);
    }
    
    printf("PASS\n");
    TEST_PASS();
}

// =============================================================================
// Multi-width Tests
// =============================================================================

static int test_vror_u8() {
    printf("Testing vror u8... ");
    
    size_t vl = vsetvl_e8m1(8);
    uint8_t data[8] = {0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0};
    uint8_t expected[8];
    uint8_t result[8];
    
    for (int i = 0; i < 8; i++) {
        expected[i] = ror_u8_ref(data[i], 3);
    }
    
    vuint8m1_t vec_data = vle8_v_u8m1(data, vl);
    vuint8m1_t vec_result = vror_vx_u8m1_emu(vec_data, 3, vl);
    vse8_v_u8m1(result, vec_result, vl);
    
    for (int i = 0; i < 8; i++) {
        TEST_ASSERT(result[i] == expected[i], 
            "Element %d: expected 0x%02x, got 0x%02x", i, expected[i], result[i]);
    }
    
    printf("PASS\n");
    TEST_PASS();
}

static int test_vror_u16() {
    printf("Testing vror u16... ");
    
    size_t vl = vsetvl_e16m1(8);
    uint16_t data[8] = {0x1234, 0x5678, 0x9ABC, 0xDEF0, 0x0123, 0x4567, 0x89AB, 0xCDEF};
    uint16_t expected[8];
    uint16_t result[8];
    
    for (int i = 0; i < 8; i++) {
        expected[i] = ror_u16_ref(data[i], 5);
    }
    
    vuint16m1_t vec_data = vle16_v_u16m1(data, vl);
    vuint16m1_t vec_result = vror_vx_u16m1_emu(vec_data, 5, vl);
    vse16_v_u16m1(result, vec_result, vl);
    
    for (int i = 0; i < 8; i++) {
        TEST_ASSERT(result[i] == expected[i], 
            "Element %d: expected 0x%04x, got 0x%04x", i, expected[i], result[i]);
    }
    
    printf("PASS\n");
    TEST_PASS();
}

static int test_vror_u64() {
    printf("Testing vror u64... ");
    
    size_t vl = vsetvl_e64m1(4);
    uint64_t data[4] = {
        0x123456789ABCDEF0ULL,
        0xFEDCBA9876543210ULL,
        0x0011223344556677ULL,
        0xFFFFFFFFFFFFFFFFULL
    };
    uint64_t expected[4];
    uint64_t result[4];
    
    for (int i = 0; i < 4; i++) {
        expected[i] = ror_u64_ref(data[i], 12);
    }
    
    vuint64m1_t vec_data = vle64_v_u64m1(data, vl);
    vuint64m1_t vec_result = vror_vx_u64m1_emu(vec_data, 12, vl);
    vse64_v_u64m1(result, vec_result, vl);
    
    for (int i = 0; i < 4; i++) {
        TEST_ASSERT(result[i] == expected[i], 
            "Element %d: expected 0x%016llx, got 0x%016llx", i, 
            (unsigned long long)expected[i], (unsigned long long)result[i]);
    }
    
    printf("PASS\n");
    TEST_PASS();
}

// =============================================================================
// Random Testing
// =============================================================================

#define NUM_RANDOM_TESTS 1000
#define MAX_VL 16

static int test_vror_random_u32() {
    printf("Testing vror u32 random (%d iterations)... ", NUM_RANDOM_TESTS);
    
    for (int iter = 0; iter < NUM_RANDOM_TESTS; iter++) {
        size_t num_elements = 1 + (rand() % MAX_VL);
        size_t vl = vsetvl_e32m1(num_elements);
        
        uint32_t data[MAX_VL];
        uint32_t shifts[MAX_VL];
        uint32_t expected[MAX_VL];
        uint32_t result[MAX_VL];
        
        // Generate random data and shifts
        for (size_t i = 0; i < num_elements; i++) {
            data[i] = rand();
            shifts[i] = rand() % 64; // Some values > 32 to test masking
        }
        
        // Test vror.vv
        for (size_t i = 0; i < num_elements; i++) {
            expected[i] = ror_u32_ref(data[i], shifts[i]);
        }
        
        vuint32m1_t vec_data = vle32_v_u32m1(data, vl);
        vuint32m1_t vec_shifts = vle32_v_u32m1(shifts, vl);
        vuint32m1_t vec_result = vror_vv_u32m1_emu(vec_data, vec_shifts, vl);
        vse32_v_u32m1(result, vec_result, vl);
        
        for (size_t i = 0; i < num_elements; i++) {
            TEST_ASSERT(result[i] == expected[i], 
                "Iteration %d, element %zu: expected 0x%08x, got 0x%08x (data=0x%08x, shift=%u)",
                iter, i, expected[i], result[i], data[i], shifts[i]);
        }
        
        // Test vror.vx with first shift value
        uint32_t scalar_shift = shifts[0];
        for (size_t i = 0; i < num_elements; i++) {
            expected[i] = ror_u32_ref(data[i], scalar_shift);
        }
        
        vec_result = vror_vx_u32m1_emu(vec_data, scalar_shift, vl);
        vse32_v_u32m1(result, vec_result, vl);
        
        for (size_t i = 0; i < num_elements; i++) {
            TEST_ASSERT(result[i] == expected[i], 
                "vror.vx iteration %d, element %zu: expected 0x%08x, got 0x%08x",
                iter, i, expected[i], result[i]);
        }
    }
    
    printf("PASS\n");
    TEST_PASS();
}

static int test_vror_random_u64() {
    printf("Testing vror u64 random (%d iterations)... ", NUM_RANDOM_TESTS);
    
    for (int iter = 0; iter < NUM_RANDOM_TESTS; iter++) {
        size_t num_elements = 1 + (rand() % (MAX_VL / 2));
        size_t vl = vsetvl_e64m1(num_elements);
        
        uint64_t data[MAX_VL];
        uint64_t shifts[MAX_VL];
        uint64_t expected[MAX_VL];
        uint64_t result[MAX_VL];
        
        // Generate random data and shifts
        for (size_t i = 0; i < num_elements; i++) {
            data[i] = ((uint64_t)rand() << 32) | rand();
            shifts[i] = rand() % 128; // Some values > 64 to test masking
        }
        
        // Test vror.vv
        for (size_t i = 0; i < num_elements; i++) {
            expected[i] = ror_u64_ref(data[i], shifts[i]);
        }
        
        vuint64m1_t vec_data = vle64_v_u64m1(data, vl);
        vuint64m1_t vec_shifts = vle64_v_u64m1(shifts, vl);
        vuint64m1_t vec_result = vror_vv_u64m1_emu(vec_data, vec_shifts, vl);
        vse64_v_u64m1(result, vec_result, vl);
        
        for (size_t i = 0; i < num_elements; i++) {
            TEST_ASSERT(result[i] == expected[i], 
                "Iteration %d, element %zu: expected 0x%016llx, got 0x%016llx",
                iter, i, (unsigned long long)expected[i], (unsigned long long)result[i]);
        }
    }
    
    printf("PASS\n");
    TEST_PASS();
}

// =============================================================================
// Main Test Runner
// =============================================================================

int main() {
    printf("===============================================\n");
    printf("RISC-V Zvbb vror* Emulation Test Suite\n");
    printf("===============================================\n\n");
    
    // Seed random number generator
    srand(time(NULL));
    
    // Basic correctness tests
    printf("--- Basic Correctness Tests ---\n");
    test_vror_vx_u32_basic();
    test_vror_vi_u32_basic();
    test_vror_vv_u32_basic();
    
    // Edge case tests
    printf("\n--- Edge Case Tests ---\n");
    test_vror_rotate_by_zero();
    test_vror_rotate_by_width();
    test_vror_all_ones();
    
    // Multi-width tests
    printf("\n--- Multi-Width Tests ---\n");
    test_vror_u8();
    test_vror_u16();
    test_vror_u64();
    
    // Random tests
    printf("\n--- Random Tests ---\n");
    test_vror_random_u32();
    test_vror_random_u64();
    
    // Summary
    printf("\n===============================================\n");
    printf("Test Summary:\n");
    printf("  Passed: %d\n", tests_passed);
    printf("  Failed: %d\n", tests_failed);
    printf("  Total:  %d\n", tests_passed + tests_failed);
    printf("===============================================\n");
    
    if (tests_failed == 0) {
        printf("\n✓ All tests passed!\n\n");
        return 0;
    } else {
        printf("\n✗ Some tests failed!\n\n");
        return 1;
    }
}
