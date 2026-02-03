# Quick Start: Running Benchmarks

## Install Dependencies

pytest-benchmark is already in your dev requirements. Verify it's installed:

```bash
pip install -e ".[dev]"
```

## Running Benchmarks

### Quick Test - Single Benchmark
```bash
# Test that benchmarks work
python -m pytest benchmarks/test_record_parsing.py::TestRecordParsing::test_is_record_start_fast_path -v
```

### Run All Benchmarks
```bash
# All benchmarks with verbose output
python -m pytest benchmarks/ -v --benchmark-only

# Skip unit tests, only run benchmarks
python -m pytest benchmarks/ --benchmark-only
```

### Run Specific Category
```bash
# File reading benchmarks
python -m pytest benchmarks/test_file_reading.py -v

# Record parsing benchmarks  
python -m pytest benchmarks/test_record_parsing.py -v

# Expression evaluation benchmarks
python -m pytest benchmarks/test_evaluation.py -v
```

## Understanding Results

The benchmark output shows:

```
Name (time in ms)               Min      Max     Mean  StdDev
--------------------------------------------------------------
test_read_small_file          3.87     5.96    4.45    0.53
test_is_record_start_fast    0.14     3.74    0.20    0.12
```

**Key Metrics:**
- **Mean**: Average time (lower is better)
- **StdDev**: Consistency (lower = more consistent)
- **Min/Max**: Performance range

## Profiling for Deep Analysis

### CPU Profile
```bash
# Profile a scenario
python benchmarks/profile_cpu.py --scenario large_file

# Analyze results
python -m pstats profile_output.stats
> sort cumtime
> stats 30
```

**Scenarios available:**
- `large_file`: Single 100MB file
- `many_files`: 100 × 1MB files
- `compressed`: Compressed file processing

### What to Look For

In the profiling output, look for functions with:
1. **High cumtime** - Total time including called functions
2. **High percall** - Time per individual call
3. **High ncalls** - Called very frequently

These are your optimization targets!

## Comparing Before/After Changes

### Save Baseline
```bash
# Before making changes
python -m pytest benchmarks/ --benchmark-save=before
```

### Make Your Changes
Edit code, implement optimizations...

### Compare
```bash
# After changes
python -m pytest benchmarks/ --benchmark-compare=before
```

Output will show:
- ✓ **Faster** operations (green)
- ✗ **Slower** operations (red)  
- Percentage change for each benchmark

## Example: Verifying Fast-Path Optimization

The fast-path optimization should show dramatic improvement:

```bash
python -m pytest benchmarks/test_record_parsing.py -v --benchmark-only
```

Look for:
- `test_is_record_start_best_case`: ~100x faster (most lines filtered by fast-path)
- `test_is_record_start_worst_case`: Similar speed (all lines pass fast-path, hit regex)
- `test_is_record_start_fast_path`: 20-40% faster (realistic mix)

## Tips

**For Accurate Results:**
1. Close other applications
2. Run on AC power (laptops)
3. Run multiple times: `--benchmark-min-rounds=10`
4. Warm up: `--benchmark-warmup=on`

**For Quick Feedback:**
```bash
# Fast benchmarks only (skip slow ones)
python -m pytest benchmarks/test_record_parsing.py -v
```

## Next Steps

1. Run baseline benchmarks now
2. Make your optimization changes
3. Run benchmarks again to measure improvement
4. Use profiler to find next bottleneck

See [benchmarks/README.md](benchmarks/README.md) for complete documentation.
