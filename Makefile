# RISC-V Zvbb vror* Emulation Library - Makefile
# Requires RISC-V GCC with vector extension support

# Compiler configuration
CC = riscv64-unknown-linux-gnu-gcc
CFLAGS = -march=rv64gcv -O2 -Wall -Wextra -I./include
LDFLAGS = -static

# Paths
TEST_SRC = tests/test_vror.c
BENCH_SRC = bench/bench_vror.c
TEST_BIN = tests/test_vror
BENCH_BIN = bench/bench_vror

# Default target
.PHONY: all
all: test bench

# Build test suite
.PHONY: test-build
test-build: $(TEST_BIN)

$(TEST_BIN): $(TEST_SRC) include/zvbb_emu.h
	@echo "Building test suite..."
	$(CC) $(CFLAGS) $(TEST_SRC) -o $(TEST_BIN) $(LDFLAGS)
	@echo "Test suite built: $(TEST_BIN)"

# Build benchmark suite
.PHONY: bench-build
bench-build: $(BENCH_BIN)

$(BENCH_BIN): $(BENCH_SRC) include/zvbb_emu.h
	@echo "Building benchmark suite..."
	$(CC) $(CFLAGS) $(BENCH_SRC) -o $(BENCH_BIN) $(LDFLAGS)
	@echo "Benchmark suite built: $(BENCH_BIN)"

# Run tests
.PHONY: test
test: test-build
	@echo ""
	@echo "Running test suite..."
	@echo ""
	./$(TEST_BIN)

# Run benchmarks
.PHONY: bench
bench: bench-build
	@echo ""
	@echo "Running benchmarks..."
	@echo ""
	./$(BENCH_BIN)

# Clean build artifacts
.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	rm -f $(TEST_BIN) $(BENCH_BIN)
	@echo "Clean complete."

# Help target
.PHONY: help
help:
	@echo "RISC-V Zvbb vror* Emulation Library - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  all         - Build test and benchmark suites (default)"
	@echo "  test        - Build and run test suite"
	@echo "  test-build  - Build test suite only"
	@echo "  bench       - Build and run benchmark suite"
	@echo "  bench-build - Build benchmark suite only"
	@echo "  clean       - Remove build artifacts"
	@echo "  help        - Show this help message"
	@echo ""
	@echo "Requirements:"
	@echo "  - RISC-V GCC with vector extension support"
	@echo "  - Target architecture: rv64gcv (RISC-V 64-bit with vector extension)"
	@echo ""
	@echo "Environment variables:"
	@echo "  CC      - C compiler (default: riscv64-unknown-linux-gnu-gcc)"
	@echo "  CFLAGS  - Additional compiler flags"
	@echo ""
	@echo "Examples:"
	@echo "  make test              # Build and run tests"
	@echo "  make bench             # Build and run benchmarks"
	@echo "  make CC=clang test     # Use different compiler"
