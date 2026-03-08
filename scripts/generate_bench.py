#!/usr/bin/env python3
"""
Generate bench_all.c from a prototype header file.

Parses C prototype declarations from the given header and generates
a benchmark C file that measures each intrinsic using Linux perf_event.

Usage:
    python3 scripts/generate_bench.py emulation_decl_all.h -o tests/src/bench_all.c
"""

import re
import sys
import argparse
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Prototype parsing
# ---------------------------------------------------------------------------

# Match: return_type func_name(param1, param2, ...);
PROTO_RE = re.compile(
    r'^\s*(\w[\w\s]*?\w)\s+(__riscv_\w+)\s*\(([^)]*)\)\s*;',
    re.MULTILINE,
)

# Map vector type names to (element_width_bits, lmul_num, signedness)
# e.g. vuint8m1_t  -> (8, 1, 'u')
#      vint32m4_t  -> (32, 4, 'i')
#      vbool8_t    -> mask type
VTYPE_RE = re.compile(r'^v(u?int)(\d+)m(\d+)_t$')
VBOOL_RE = re.compile(r'^vbool(\d+)_t$')
SCALAR_RE = re.compile(r'^(u?int)(\d+)_t$')


@dataclass
class Param:
    type_str: str
    is_vector: bool
    is_mask: bool
    is_scalar: bool
    is_size_t: bool
    ew: int          # element width in bits (for vector/scalar)
    lmul: int        # LMUL (for vector types)
    signed: bool     # True if signed


@dataclass
class Prototype:
    ret_type: str
    name: str
    params: list   # list of Param
    raw_line: str


def classify_type(type_str: str) -> Param:
    """Classify a C type string into our Param descriptor."""
    ts = type_str.strip()

    if ts == 'size_t':
        return Param(ts, False, False, False, True, 0, 0, False)

    m = VTYPE_RE.match(ts)
    if m:
        sign = m.group(1)  # 'uint' or 'int'
        ew = int(m.group(2))
        lmul = int(m.group(3))
        return Param(ts, True, False, False, False, ew, lmul, sign == 'int')

    m = VBOOL_RE.match(ts)
    if m:
        return Param(ts, False, True, False, False, int(m.group(1)), 0, False)

    m = SCALAR_RE.match(ts)
    if m:
        sign = m.group(1)
        ew = int(m.group(2))
        return Param(ts, False, False, True, False, ew, 0, sign == 'int')

    # Fallback — treat as opaque
    return Param(ts, False, False, False, False, 0, 0, False)


def parse_prototypes(header_text: str) -> list:
    """Extract all __riscv_* prototypes from header text."""
    protos = []
    for m in PROTO_RE.finditer(header_text):
        ret_type = m.group(1).strip()
        func_name = m.group(2).strip()
        param_str = m.group(3).strip()

        params = []
        if param_str:
            for p in param_str.split(','):
                p = p.strip()
                params.append(classify_type(p))

        protos.append(Prototype(ret_type, func_name, params, m.group(0).strip()))

    return protos


# ---------------------------------------------------------------------------
# Determine vsetvlmax call for a prototype
# ---------------------------------------------------------------------------

def extract_lmul_and_ew(proto: Prototype):
    """
    Extract the primary element width and LMUL from the prototype.
    We look at the function name's type tag (e.g. _u8m1, _i32m4).
    """
    # Try to extract from the function name: last _<type><lmul> segment
    # Pattern: ..._u8m1_tumu or ..._i32m2 etc.
    name_tag_re = re.compile(r'_([ui])(\d+)m(\d+)')
    matches = list(name_tag_re.finditer(proto.name))
    if matches:
        last = matches[-1]
        ew = int(last.group(2))
        lmul = int(last.group(3))
        return ew, lmul

    # Fallback to return type
    ret_p = classify_type(proto.ret_type)
    if ret_p.is_vector:
        return ret_p.ew, ret_p.lmul

    # Default
    return 8, 1


def vsetvlmax_call(ew: int, lmul: int) -> str:
    """Generate a __riscv_vsetvlmax_eNmL() call."""
    return f"__riscv_vsetvlmax_e{ew}m{lmul}()"


# ---------------------------------------------------------------------------
# Generate argument expressions
# ---------------------------------------------------------------------------

def gen_load_vector(param: Param, buf_name: str = "rand_buf") -> str:
    """Generate a vle load from the random buffer."""
    sign_char = 'i' if param.signed else 'u'
    return f"__riscv_vle{param.ew}_v_{sign_char}{param.ew}m{param.lmul}((const {param.type_str.replace('_t', '_t*').replace('vuint', 'uint').replace('vint', 'int').split('_t')[0]}_t*){buf_name}, vl)"


def gen_load_vector_simple(param: Param) -> str:
    """Generate a vle load expression using explicit type mapping."""
    sign_char = 'i' if param.signed else 'u'
    scalar_type = f"{'int' if param.signed else 'uint'}{param.ew}_t"
    return f"__riscv_vle{param.ew}_v_{sign_char}{param.ew}m{param.lmul}((const {scalar_type}*)rand_buf, vl)"


def gen_load_mask(param: Param) -> str:
    """Generate a vlm load for a mask type."""
    return f"__riscv_vlm_v_b{param.ew}((const uint8_t*)rand_buf, vl)"


def gen_scalar_val(param: Param) -> str:
    """Generate a random scalar value expression."""
    return f"({param.type_str})0x5A"


# ---------------------------------------------------------------------------
# C code generation
# ---------------------------------------------------------------------------

C_PREAMBLE = """\
/*
 * Auto-generated benchmark for RVV intrinsic emulations.
 * Generated by scripts/generate_bench.py
 *
 * Usage:
 *   ./bench_all [-m cycles|insns] [-n NUM_OUTER] [-i NUM_INNER]
 */

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <riscv_vector.h>

/* Linux perf_event */
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/perf_event.h>
#include <sys/syscall.h>

/* ---------- perf helpers ---------- */

static long perf_event_open(struct perf_event_attr *attr, pid_t pid,
                            int cpu, int group_fd, unsigned long flags) {
    return syscall(__NR_perf_event_open, attr, pid, cpu, group_fd, flags);
}

static int setup_perf_counter(int config) {
    struct perf_event_attr pe;
    memset(&pe, 0, sizeof(pe));
    pe.type = PERF_TYPE_HARDWARE;
    pe.size = sizeof(pe);
    pe.config = config;
    pe.disabled = 1;
    pe.exclude_kernel = 1;
    pe.exclude_hv = 1;
    int fd = perf_event_open(&pe, 0, -1, -1, 0);
    if (fd < 0) {
        perror("perf_event_open");
        exit(1);
    }
    return fd;
}

static inline void perf_start(int fd) {
    ioctl(fd, PERF_EVENT_IOC_RESET, 0);
    ioctl(fd, PERF_EVENT_IOC_ENABLE, 0);
}

static inline long long perf_stop(int fd) {
    ioctl(fd, PERF_EVENT_IOC_DISABLE, 0);
    long long count;
    read(fd, &count, sizeof(count));
    return count;
}

/* ---------- random data buffer ---------- */
/* Large enough for LMUL=8, any element width. Assumes VLEN <= 16384. */
#define RAND_BUF_SIZE (8 * 2048)
// buffer should be 64-bit align to allow any access alignment
__attribute__((aligned(64))) static uint8_t rand_buf[RAND_BUF_SIZE];

static void fill_random(void) {
    for (int i = 0; i < RAND_BUF_SIZE; i++)
        rand_buf[i] = (uint8_t)rand();
}

/* ---------- vl array for inner loop ---------- */
/* Pre-filled with vlmax; read via volatile to prevent hoisting of vsetvl. */
#define VL_ARRAY_SIZE 64
static volatile size_t vl_array[VL_ARRAY_SIZE];

static void fill_vl_array(size_t vlmax) {
    for (int i = 0; i < VL_ARRAY_SIZE; i++)
        vl_array[i] = vlmax;
}

/* ---------- benchmark entry ---------- */
/*
 * Each benchmark wrapper:
 *   1. Loads all input data from rand_buf (outside measurement)
 *   2. Runs a tight inner loop of inner_iters calls (inside measurement),
 *      reading vl from vl_array at each iteration
 *   3. Returns the measured perf counter value (per iteration) via *out_count
 */
typedef void (*bench_fn_t)(size_t vl, int inner_iters, int perf_fd, long long *out_count);

typedef struct {
    const char *name;
    bench_fn_t fn;
    int ew;    /* element width for vsetvlmax */
    int lmul;  /* LMUL value for vsetvlmax */
} bench_entry_t;

"""

C_MAIN = """\
/* ---------- empty-loop calibration ---------- */
/* Measures the overhead of the inner loop itself (volatile vl_array read). */
static void __attribute__((noinline)) bench_empty_loop(size_t vl, int inner_iters,
                                                       int perf_fd, long long *out_count) {
    perf_start(perf_fd);
    for (int _i = 0; _i < inner_iters; _i++) {
        size_t _vl = vl_array[_i & (VL_ARRAY_SIZE - 1)];
        (void)_vl;
    }
    *out_count = perf_stop(perf_fd) / inner_iters;
}

/* ---------- main ---------- */

int main(int argc, char *argv[]) {
    int num_outer = 100;   /* outer repetitions (for min/max/avg stats) */
    int num_inner = 10;    /* inner loop iterations (measured as one block) */
    int perf_config = PERF_COUNT_HW_CPU_CYCLES;
    const char *metric_name = "cycles";

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-n") == 0 && i + 1 < argc) {
            num_outer = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-i") == 0 && i + 1 < argc) {
            num_inner = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-m") == 0 && i + 1 < argc) {
            i++;
            if (strcmp(argv[i], "cycles") == 0) {
                perf_config = PERF_COUNT_HW_CPU_CYCLES;
                metric_name = "cycles";
            } else if (strcmp(argv[i], "insns") == 0) {
                perf_config = PERF_COUNT_HW_INSTRUCTIONS;
                metric_name = "insns";
            } else {
                fprintf(stderr, "Unknown metric: %s (use cycles or insns)\\n", argv[i]);
                return 1;
            }
        }
    }

    srand(42);
    fill_random();

    int perf_fd = setup_perf_counter(perf_config);
    int num_entries = sizeof(bench_entries) / sizeof(bench_entries[0]);
    long long loop_overhead;

    /* --- Calibrate empty loop overhead --- */
    {
        size_t cal_vl = __riscv_vsetvlmax_e8m1();
        long long overhead_total = 0;
        fill_vl_array(cal_vl);
        for (int it = 0; it < num_outer; it++) {
            long long val;
            bench_empty_loop(cal_vl, num_inner, perf_fd, &val);
            overhead_total += val;
        }
        /* Use average as the per-iteration overhead */
        loop_overhead = overhead_total / num_outer;
        printf("# empty_loop overhead per iteration: %lld %s\\n", loop_overhead, metric_name);
        printf("# (subtracted from all measurements below)\\n");
    }

    printf("intrinsic_name, inner_iters, min_%s, max_%s, avg_%s\\n",
           metric_name, metric_name, metric_name);

    for (int e = 0; e < num_entries; e++) {
        const bench_entry_t *entry = &bench_entries[e];
        long long min_val = __LONG_LONG_MAX__;
        long long max_val = 0;
        long long total = 0;

        /* Determine vl = vlmax for this entry's EW/LMUL */
        size_t vl;
        switch (entry->ew * 100 + entry->lmul) {
            case  801: vl = __riscv_vsetvlmax_e8m1(); break;
            case  802: vl = __riscv_vsetvlmax_e8m2(); break;
            case  804: vl = __riscv_vsetvlmax_e8m4(); break;
            case  808: vl = __riscv_vsetvlmax_e8m8(); break;
            case 1601: vl = __riscv_vsetvlmax_e16m1(); break;
            case 1602: vl = __riscv_vsetvlmax_e16m2(); break;
            case 1604: vl = __riscv_vsetvlmax_e16m4(); break;
            case 1608: vl = __riscv_vsetvlmax_e16m8(); break;
            case 3201: vl = __riscv_vsetvlmax_e32m1(); break;
            case 3202: vl = __riscv_vsetvlmax_e32m2(); break;
            case 3204: vl = __riscv_vsetvlmax_e32m4(); break;
            case 3208: vl = __riscv_vsetvlmax_e32m8(); break;
            case 6401: vl = __riscv_vsetvlmax_e64m1(); break;
            case 6402: vl = __riscv_vsetvlmax_e64m2(); break;
            case 6404: vl = __riscv_vsetvlmax_e64m4(); break;
            case 6408: vl = __riscv_vsetvlmax_e64m8(); break;
            default:   vl = __riscv_vsetvlmax_e8m1(); break;
        }

        for (int it = 0; it < num_outer; it++) {
            long long val;
            fill_vl_array(vl);
            entry->fn(vl, num_inner, perf_fd, &val);
            long long adjusted = val - loop_overhead;
            if (adjusted < 0) adjusted = 0;
            if (adjusted < min_val) min_val = adjusted;
            if (adjusted > max_val) max_val = adjusted;
            total += adjusted;
        }

        double avg = (double)total / num_outer;
        printf("%s, %d, %lld, %lld, %.1f\\n",
               entry->name, num_inner, min_val, max_val, avg);
    }

    close(perf_fd);
    return 0;
}
"""


def gen_wrapper_function(proto: Prototype, idx: int) -> str:
    """Generate a noinline wrapper that loads data once, then loops the intrinsic call."""
    ew, lmul = extract_lmul_and_ew(proto)
    lines = []
    lines.append(f"/* {proto.name} */")
    lines.append(f"static void __attribute__((noinline)) bench_{idx}(size_t vl, int inner_iters, int perf_fd, long long *out_count) {{")

    # Step 1: Load all input data into local variables (outside the measurement)
    arg_names = []   # variable names to pass to the intrinsic call
    var_idx = 0
    for p in proto.params:
        if p.is_size_t:
            arg_names.append("vl")
        elif p.is_mask:
            vname = f"mask_{var_idx}"
            lines.append(f"    {p.type_str} {vname} = __riscv_vlm_v_b{p.ew}((const uint8_t*)rand_buf, vl);")
            arg_names.append(vname)
            var_idx += 1
        elif p.is_vector:
            vname = f"vec_{var_idx}"
            sign_char = 'i' if p.signed else 'u'
            scalar_type = f"{'int' if p.signed else 'uint'}{p.ew}_t"
            lines.append(
                f"    {p.type_str} {vname} = __riscv_vle{p.ew}_v_{sign_char}{p.ew}m{p.lmul}"
                f"((const {scalar_type}*)rand_buf, vl);"
            )
            arg_names.append(vname)
            var_idx += 1
        elif p.is_scalar:
            vname = f"scalar_{var_idx}"
            lines.append(f"    {p.type_str} {vname} = ({p.type_str})0x5A;")
            arg_names.append(vname)
            var_idx += 1
        else:
            arg_names.append("0 /* unknown */")

    call_args = ", ".join(arg_names)
    ret_p = classify_type(proto.ret_type)

    # Step 2: Measured inner loop — read vl from volatile array each iteration
    lines.append("    perf_start(perf_fd);")
    lines.append("    for (int _i = 0; _i < inner_iters; _i++) {")
    lines.append("        size_t _vl = vl_array[_i & (VL_ARRAY_SIZE - 1)];")

    # Replace 'vl' with '_vl' in the call args
    call_args_inner = call_args.replace("vl", "_vl") if "vl" in arg_names else call_args

    if ret_p.is_vector or ret_p.is_mask:
        lines.append(f"        {proto.ret_type} volatile result = {proto.name}({call_args_inner});")
        lines.append(f"        (void)result;")
    else:
        lines.append(f"        {proto.name}({call_args_inner});")

    lines.append("    }")
    lines.append("    *out_count = perf_stop(perf_fd) / inner_iters;")

    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def gen_bench_table(protos: list) -> str:
    """Generate the bench_entries[] table."""
    lines = []
    lines.append("static const bench_entry_t bench_entries[] = {")
    for idx, proto in enumerate(protos):
        ew, lmul = extract_lmul_and_ew(proto)
        lines.append(f'    {{ "{proto.name}", bench_{idx}, {ew}, {lmul} }},')
    lines.append("};")
    return "\n".join(lines)


def generate_bench_c(protos: list) -> str:
    """Generate the full bench_all.c source."""
    parts = [C_PREAMBLE]

    # Forward declarations for the emulated intrinsics
    parts.append("/* ---------- intrinsic prototypes (from header) ---------- */")
    seen = set()
    for proto in protos:
        if proto.raw_line not in seen:
            parts.append(proto.raw_line)
            seen.add(proto.raw_line)
    parts.append("")

    # Wrapper functions
    parts.append("/* ---------- benchmark wrapper functions ---------- */")
    parts.append("")
    for idx, proto in enumerate(protos):
        parts.append(gen_wrapper_function(proto, idx))

    # Entry table
    parts.append("/* ---------- benchmark entry table ---------- */")
    parts.append(gen_bench_table(protos))

    # Main
    parts.append(C_MAIN)

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate bench_all.c from an intrinsic prototype header"
    )
    parser.add_argument("header", help="Path to the prototype header (e.g. emulation_decl_all.h)")
    parser.add_argument("-o", "--output", default=None, help="Output file (default: stdout)")
    args = parser.parse_args()

    with open(args.header, 'r') as f:
        header_text = f.read()

    protos = parse_prototypes(header_text)
    if not protos:
        print("Warning: no prototypes found in input", file=sys.stderr)
        sys.exit(1)

    print(f"Parsed {len(protos)} prototypes", file=sys.stderr)

    result = generate_bench_c(protos)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
        print(f"Generated benchmark written to: {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
