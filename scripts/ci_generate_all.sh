#!/usr/bin/env bash
# ci_generate_all.sh — Generate all supported extension × mode combinations.
# Exits with non-zero status on the first generation failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
GEN="$SCRIPT_DIR/generate_emulation.py"
PYTHON="${PYTHON:-python3}"
OUT_DIR=$(mktemp -d)

# trap 'rm -rf "$OUT_DIR"' EXIT

pass=0
fail=0

run_gen() {
    local label="$1"
    shift
    echo "--- Generating: $label"
    if $PYTHON "$GEN" "$@" -o "$OUT_DIR/output.h"; then
        echo "    ✓ OK"
        pass=$((pass + 1))
    else
        echo "    ✗ FAILED"
        fail=$((fail + 1))
        return 1
    fi
}

echo "============================================"
echo "  RIE Generator — CI Generation Smoke Tests"
echo "============================================"
echo ""

# ---------------------------------------------------------------
# 1. Full generation (no filters) — each extension and combined
# ---------------------------------------------------------------
run_gen "zvkb (all modes)"        -e zvkb
run_gen "zvdot4a8i (all modes)"   -e zvdot4a8i
run_gen "zvzip (all modes)"       -e zvzip
run_gen "all extensions combined" -e all

# ---------------------------------------------------------------
# 2. Zvkb — individual filter combinations
# ---------------------------------------------------------------
for lmul in m1 m2 m4 m8; do
    for ew in 8 16 32 64; do
        run_gen "zvkb lmul=$lmul ew=$ew" \
            -e zvkb --lmul "$lmul" --elt-width "$ew"
    done
done

for tp in tu ta; do
    for mp in mu ma; do
        run_gen "zvkb tail=$tp mask=$mp" \
            -e zvkb --tail-policy "$tp" --mask-policy "$mp"
    done
done

# ---------------------------------------------------------------
# 3. Zvdot4a8i — individual filter combinations
# ---------------------------------------------------------------
for lmul in m1 m2 m4 m8; do
    run_gen "zvdot4a8i lmul=$lmul" \
        -e zvdot4a8i --lmul "$lmul"
done

for tp in tu ta; do
    for mp in mu ma um; do
        run_gen "zvdot4a8i tail=$tp mask=$mp" \
            -e zvdot4a8i --tail-policy "$tp" --mask-policy "$mp"
    done
done

# ---------------------------------------------------------------
# 4. Zvzip — individual filter combinations
# ---------------------------------------------------------------
for lmul in m1 m2 m4; do
    for ew in 8 16 32 64; do
        run_gen "zvzip lmul=$lmul ew=$ew" \
            -e zvzip --lmul "$lmul" --elt-width "$ew"
    done
done

for tp in tu ta; do
    for mp in mu ma um; do
        run_gen "zvzip tail=$tp mask=$mp" \
            -e zvzip --tail-policy "$tp" --mask-policy "$mp"
    done
done

# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------
echo ""
echo "============================================"
echo "  Results: $pass passed, $fail failed"
echo "============================================"

if [ "$fail" -ne 0 ]; then
    exit 1
fi
