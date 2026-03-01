# RIE Generator — Makefile
# Generates emulation headers and compiles C sanity tests

# Configurable variables
PYTHON    ?= python3
CC        ?= riscv64-elf-gcc
MARCH     ?= rv64gcv
MABI      ?= lp64d
CFLAGS    ?= -O2 -Wall -Wextra -Werror -ffreestanding

GEN_SCRIPT = scripts/generate_emulation.py
GEN_DIR    = tests/generated
BUILD_DIR  = tests/build

# Generation filters for tests (keep small for fast compile)
ZVKB_GEN_FLAGS    = -e zvkb --lmul m1 --elt-width 32 --tail-policy tu --mask-policy um
ZVDOT_GEN_FLAGS   = -e zvdot4a8i --lmul m1 --tail-policy tu --mask-policy um
ZVZIP_GEN_FLAGS   = -e zvzip --lmul m1 --tail-policy ta --mask-policy um

# --- Targets ---

.PHONY: all generate build clean

all: build

# Generate emulation headers from Python
generate: $(GEN_DIR)/zvkb_emu.h $(GEN_DIR)/zvdot4a8i_emu.h $(GEN_DIR)/zvzip_emu.h

$(GEN_DIR)/zvkb_emu.h: $(GEN_SCRIPT) src/rie_generator/*.py | $(GEN_DIR)
	$(PYTHON) $(GEN_SCRIPT) $(ZVKB_GEN_FLAGS) -o $@

$(GEN_DIR)/zvdot4a8i_emu.h: $(GEN_SCRIPT) src/rie_generator/*.py | $(GEN_DIR)
	$(PYTHON) $(GEN_SCRIPT) $(ZVDOT_GEN_FLAGS) -o $@

$(GEN_DIR)/zvzip_emu.h: $(GEN_SCRIPT) src/rie_generator/*.py | $(GEN_DIR)
	$(PYTHON) $(GEN_SCRIPT) $(ZVZIP_GEN_FLAGS) -o $@

$(GEN_DIR) $(BUILD_DIR):
	mkdir -p $@

# Compile C sanity tests (compile-only, no runtime execution)
build: $(BUILD_DIR)/test_zvkb.o $(BUILD_DIR)/test_zvdot4a8i.o $(BUILD_DIR)/test_zvzip.o

$(BUILD_DIR)/test_zvkb.o: tests/test_zvkb.c $(GEN_DIR)/zvkb_emu.h | $(BUILD_DIR)
	$(CC) -march=$(MARCH) -mabi=$(MABI) $(CFLAGS) -I$(GEN_DIR) -c $< -o $@

$(BUILD_DIR)/test_zvdot4a8i.o: tests/test_zvdot4a8i.c $(GEN_DIR)/zvdot4a8i_emu.h | $(BUILD_DIR)
	$(CC) -march=$(MARCH) -mabi=$(MABI) $(CFLAGS) -I$(GEN_DIR) -c $< -o $@

$(BUILD_DIR)/test_zvzip.o: tests/src/test_zvzip.c $(GEN_DIR)/zvzip_emu.h | $(BUILD_DIR)
	$(CC) -march=$(MARCH) -mabi=$(MABI) $(CFLAGS) -I$(GEN_DIR) -c $< -o $@

# Clean all generated and built files
clean:
	rm -rf $(GEN_DIR) $(BUILD_DIR)
