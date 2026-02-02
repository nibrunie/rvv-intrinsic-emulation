/**
 * @file bench_vror.c
 * @brief Performance benchmark suite for RISC-V Zvbb vror* emulation
 * 
 * Measures:
 * - Throughput (operations per second)
 * - Latency (cycles per operation)
 * - Different element widths
 * - Different vector lengths
 */

#include "../include/zvbb_emu.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

// =============================================================================
// Timing Utilities
// =============================================================================

#if defined(__riscv)
static inline uint64_t read_cycles() {
    uint64_t cycles;
    __asm__ volatile("rdcycle %0" : "=r"(cycles));
    return cycles;
}
#else
// Fallback for non-RISC-V platforms
static inline uint64_t read_cycles() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}
#endif

// =============================================================================
// Benchmark Configuration
// =============================================================================

#define WARMUP_ITERATIONS 100
#define BENCH_ITERATIONS 10000
#define NUM_ELEMENTS 16

// =============================================================================
// Throughput Benchmarks
// =============================================================================

static void bench_vror_vx_u32_throughput() {
    printf("Benchmarking vror.vx u32 throughput...\n");
    
    size_t vl = vsetvl_e32m1(NUM_ELEMENTS);
    uint32_t data[NUM_ELEMENTS];
    uint32_t result[NUM_ELEMENTS];
    
    // Initialize data
    for (int i = 0; i < NUM_ELEMENTS; i++) {
        data[i] = rand();
    }
    
    vuint32m1_t vec_data = vle32_v_u32m1(data, vl);
    vuint32m1_t vec_result;
    
    // Warmup
    for (int i = 0; i < WARMUP_ITERATIONS; i++) {
        vec_result = vror_vx_u32m1_emu(vec_data, 8, vl);
    }
    
    // Benchmark
    uint64_t start = read_cycles();
    for (int i = 0; i < BENCH_ITERATIONS; i++) {
        vec_result = vror_vx_u32m1_emu(vec_data, 8, vl);
    }
    uint64_t end = read_cycles();
    
    // Store result to prevent optimization
    vse32_v_u32m1(result, vec_result, vl);
    
    uint64_t total_cycles = end - start;
    double cycles_per_op = (double)total_cycles / BENCH_ITERATIONS;
    double cycles_per_element = cycles_per_op / vl;
    
    printf("  Operations: %d\n", BENCH_ITERATIONS);
    printf("  Elements per op: %zu\n", vl);
    printf("  Total cycles: %llu\n", (unsigned long long)total_cycles);
    printf("  Cycles/op: %.2f\n", cycles_per_op);
    printf("  Cycles/element: %.2f\n", cycles_per_element);
    printf("\n");
}

static void bench_vror_vv_u32_throughput() {
    printf("Benchmarking vror.vv u32 throughput...\n");
    
    size_t vl = vsetvl_e32m1(NUM_ELEMENTS);
    uint32_t data[NUM_ELEMENTS];
    uint32_t shifts[NUM_ELEMENTS];
    uint32_t result[NUM_ELEMENTS];
    
    // Initialize data
    for (int i = 0; i < NUM_ELEMENTS; i++) {
        data[i] = rand();
        shifts[i] = rand() % 32;
    }
    
    vuint32m1_t vec_data = vle32_v_u32m1(data, vl);
    vuint32m1_t vec_shifts = vle32_v_u32m1(shifts, vl);
    vuint32m1_t vec_result;
    
    // Warmup
    for (int i = 0; i < WARMUP_ITERATIONS; i++) {
        vec_result = vror_vv_u32m1_emu(vec_data, vec_shifts, vl);
    }
    
    // Benchmark
    uint64_t start = read_cycles();
    for (int i = 0; i < BENCH_ITERATIONS; i++) {
        vec_result = vror_vv_u32m1_emu(vec_data, vec_shifts, vl);
    }
    uint64_t end = read_cycles();
    
    // Store result to prevent optimization
    vse32_v_u32m1(result, vec_result, vl);
    
    uint64_t total_cycles = end - start;
    double cycles_per_op = (double)total_cycles / BENCH_ITERATIONS;
    double cycles_per_element = cycles_per_op / vl;
    
    printf("  Operations: %d\n", BENCH_ITERATIONS);
    printf("  Elements per op: %zu\n", vl);
    printf("  Total cycles: %llu\n", (unsigned long long)total_cycles);
    printf("  Cycles/op: %.2f\n", cycles_per_op);
    printf("  Cycles/element: %.2f\n", cycles_per_element);
    printf("\n");
}

static void bench_vror_vi_u32_throughput() {
    printf("Benchmarking vror.vi u32 throughput...\n");
    
    size_t vl = vsetvl_e32m1(NUM_ELEMENTS);
    uint32_t data[NUM_ELEMENTS];
    uint32_t result[NUM_ELEMENTS];
    
    // Initialize data
    for (int i = 0; i < NUM_ELEMENTS; i++) {
        data[i] = rand();
    }
    
    vuint32m1_t vec_data = vle32_v_u32m1(data, vl);
    vuint32m1_t vec_result;
    
    // Warmup
    for (int i = 0; i < WARMUP_ITERATIONS; i++) {
        vec_result = vror_vi_u32m1_emu(vec_data, 8, vl);
    }
    
    // Benchmark
    uint64_t start = read_cycles();
    for (int i = 0; i < BENCH_ITERATIONS; i++) {
        vec_result = vror_vi_u32m1_emu(vec_data, 8, vl);
    }
    uint64_t end = read_cycles();
    
    // Store result to prevent optimization
    vse32_v_u32m1(result, vec_result, vl);
    
    uint64_t total_cycles = end - start;
    double cycles_per_op = (double)total_cycles / BENCH_ITERATIONS;
    double cycles_per_element = cycles_per_op / vl;
    
    printf("  Operations: %d\n", BENCH_ITERATIONS);
    printf("  Elements per op: %zu\n", vl);
    printf("  Total cycles: %llu\n", (unsigned long long)total_cycles);
    printf("  Cycles/op: %.2f\n", cycles_per_op);
    printf("  Cycles/element: %.2f\n", cycles_per_element);
    printf("\n");
}

// =============================================================================
// Multi-Width Benchmarks
// =============================================================================

static void bench_vror_vx_u8_throughput() {
    printf("Benchmarking vror.vx u8 throughput...\n");
    
    size_t vl = vsetvl_e8m1(NUM_ELEMENTS * 4);
    uint8_t data[NUM_ELEMENTS * 4];
    uint8_t result[NUM_ELEMENTS * 4];
    
    for (size_t i = 0; i < NUM_ELEMENTS * 4; i++) {
        data[i] = rand() & 0xFF;
    }
    
    vuint8m1_t vec_data = vle8_v_u8m1(data, vl);
    vuint8m1_t vec_result;
    
    // Warmup
    for (int i = 0; i < WARMUP_ITERATIONS; i++) {
        vec_result = vror_vx_u8m1_emu(vec_data, 3, vl);
    }
    
    // Benchmark
    uint64_t start = read_cycles();
    for (int i = 0; i < BENCH_ITERATIONS; i++) {
        vec_result = vror_vx_u8m1_emu(vec_data, 3, vl);
    }
    uint64_t end = read_cycles();
    
    vse8_v_u8m1(result, vec_result, vl);
    
    uint64_t total_cycles = end - start;
    double cycles_per_op = (double)total_cycles / BENCH_ITERATIONS;
    double cycles_per_element = cycles_per_op / vl;
    
    printf("  Operations: %d\n", BENCH_ITERATIONS);
    printf("  Elements per op: %zu\n", vl);
    printf("  Total cycles: %llu\n", (unsigned long long)total_cycles);
    printf("  Cycles/op: %.2f\n", cycles_per_op);
    printf("  Cycles/element: %.2f\n", cycles_per_element);
    printf("\n");
}

static void bench_vror_vx_u64_throughput() {
    printf("Benchmarking vror.vx u64 throughput...\n");
    
    size_t vl = vsetvl_e64m1(NUM_ELEMENTS / 2);
    uint64_t data[NUM_ELEMENTS / 2];
    uint64_t result[NUM_ELEMENTS / 2];
    
    for (size_t i = 0; i < NUM_ELEMENTS / 2; i++) {
        data[i] = ((uint64_t)rand() << 32) | rand();
    }
    
    vuint64m1_t vec_data = vle64_v_u64m1(data, vl);
    vuint64m1_t vec_result;
    
    // Warmup
    for (int i = 0; i < WARMUP_ITERATIONS; i++) {
        vec_result = vror_vx_u64m1_emu(vec_data, 12, vl);
    }
    
    // Benchmark
    uint64_t start = read_cycles();
    for (int i = 0; i < BENCH_ITERATIONS; i++) {
        vec_result = vror_vx_u64m1_emu(vec_data, 12, vl);
    }
    uint64_t end = read_cycles();
    
    vse64_v_u64m1(result, vec_result, vl);
    
    uint64_t total_cycles = end - start;
    double cycles_per_op = (double)total_cycles / BENCH_ITERATIONS;
    double cycles_per_element = cycles_per_op / vl;
    
    printf("  Operations: %d\n", BENCH_ITERATIONS);
    printf("  Elements per op: %zu\n", vl);
    printf("  Total cycles: %llu\n", (unsigned long long)total_cycles);
    printf("  Cycles/op: %.2f\n", cycles_per_op);
    printf("  Cycles/element: %.2f\n", cycles_per_element);
    printf("\n");
}

// =============================================================================
// Latency Benchmarks (Dependency Chain)
// =============================================================================

static void bench_vror_vx_u32_latency() {
    printf("Benchmarking vror.vx u32 latency (dependency chain)...\n");
    
    size_t vl = vsetvl_e32m1(NUM_ELEMENTS);
    uint32_t data[NUM_ELEMENTS];
    uint32_t result[NUM_ELEMENTS];
    
    for (int i = 0; i < NUM_ELEMENTS; i++) {
        data[i] = rand();
    }
    
    vuint32m1_t vec_data = vle32_v_u32m1(data, vl);
    vuint32m1_t vec_result = vec_data;
    
    // Warmup
    for (int i = 0; i < WARMUP_ITERATIONS; i++) {
        vec_result = vror_vx_u32m1_emu(vec_result, 1, vl);
    }
    
    // Benchmark - create dependency chain
    uint64_t start = read_cycles();
    for (int i = 0; i < BENCH_ITERATIONS; i++) {
        vec_result = vror_vx_u32m1_emu(vec_result, 1, vl);
    }
    uint64_t end = read_cycles();
    
    vse32_v_u32m1(result, vec_result, vl);
    
    uint64_t total_cycles = end - start;
    double cycles_per_op = (double)total_cycles / BENCH_ITERATIONS;
    
    printf("  Operations: %d (chained)\n", BENCH_ITERATIONS);
    printf("  Elements per op: %zu\n", vl);
    printf("  Total cycles: %llu\n", (unsigned long long)total_cycles);
    printf("  Latency (cycles/op): %.2f\n", cycles_per_op);
    printf("\n");
}

// =============================================================================
// CSV Output for Analysis
// =============================================================================

static void print_csv_header() {
    printf("\n=== CSV Format Output ===\n");
    printf("Variant,ElemWidth,NumElements,Iterations,TotalCycles,CyclesPerOp,CyclesPerElement\n");
}

static void bench_all_csv() {
    // This would be expanded to include all benchmarks in CSV format
    // For now, a representative sample
    
    // vror.vx u32
    {
        size_t vl = vsetvl_e32m1(NUM_ELEMENTS);
        uint32_t data[NUM_ELEMENTS];
        for (int i = 0; i < NUM_ELEMENTS; i++) data[i] = rand();
        
        vuint32m1_t vec_data = vle32_v_u32m1(data, vl);
        vuint32m1_t vec_result;
        
        for (int i = 0; i < WARMUP_ITERATIONS; i++) {
            vec_result = vror_vx_u32m1_emu(vec_data, 8, vl);
        }
        
        uint64_t start = read_cycles();
        for (int i = 0; i < BENCH_ITERATIONS; i++) {
            vec_result = vror_vx_u32m1_emu(vec_data, 8, vl);
        }
        uint64_t end = read_cycles();
        
        uint32_t result[NUM_ELEMENTS];
        vse32_v_u32m1(result, vec_result, vl);
        
        uint64_t total = end - start;
        double per_op = (double)total / BENCH_ITERATIONS;
        double per_elem = per_op / vl;
        
        printf("vror.vx,32,%zu,%d,%llu,%.2f,%.2f\n", 
            vl, BENCH_ITERATIONS, (unsigned long long)total, per_op, per_elem);
    }
}

// =============================================================================
// Main Benchmark Runner
// =============================================================================

int main() {
    printf("===============================================\n");
    printf("RISC-V Zvbb vror* Emulation Benchmark Suite\n");
    printf("===============================================\n\n");
    
    srand(time(NULL));
    
    printf("Configuration:\n");
    printf("  Warmup iterations: %d\n", WARMUP_ITERATIONS);
    printf("  Benchmark iterations: %d\n", BENCH_ITERATIONS);
    printf("  Test vector length: %d elements\n\n", NUM_ELEMENTS);
    
    // Throughput benchmarks
    printf("--- Throughput Benchmarks ---\n\n");
    bench_vror_vx_u32_throughput();
    bench_vror_vv_u32_throughput();
    bench_vror_vi_u32_throughput();
    
    // Multi-width benchmarks
    printf("--- Multi-Width Benchmarks ---\n\n");
    bench_vror_vx_u8_throughput();
    bench_vror_vx_u64_throughput();
    
    // Latency benchmarks
    printf("--- Latency Benchmarks ---\n\n");
    bench_vror_vx_u32_latency();
    
    // CSV output
    print_csv_header();
    bench_all_csv();
    
    printf("\n===============================================\n");
    printf("Benchmark complete!\n");
    printf("===============================================\n\n");
    
    return 0;
}
