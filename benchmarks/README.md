# Performance Benchmarks

This directory contains performance benchmarks for the log filter application.

## Quick Start

```bash
# Run all benchmarks
python -m pytest benchmarks/ -v

# Run specific benchmark
python -m pytest benchmarks/test_file_reading.py -v

# Run with benchmark output
python -m pytest benchmarks/ -v --benchmark-only

# Compare with baseline
python -m pytest benchmarks/ --benchmark-compare
```

## Benchmark Categories

### 1. File Reading (`test_file_reading.py`)
- Small files (1MB)
- Medium files (10MB)
- Large files (100MB)
- Compressed files (.gz)

### 2. Record Parsing (`test_record_parsing.py`)
- Pattern matching performance
- Fast-path optimization effectiveness
- Multi-line record handling

### 3. Expression Evaluation (`test_evaluation.py`)
- Regex vs substring search
- Simple vs complex expressions
- Pattern compilation overhead

### 4. End-to-End (`test_integration.py`)
- Many small files (1000 × 1MB)
- Few large files (10 × 100MB)
- Mixed workload
- Compressed vs uncompressed

## Profiling

### CPU Profiling
```bash
# Profile a specific scenario
python benchmarks/profile_cpu.py --scenario large_files

# Generate report
python -m pstats profile_output.stats
> sort cumtime
> stats 30
```

### Memory Profiling
```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler benchmarks/profile_memory.py
```

### Line Profiling
```bash
# Install line profiler
pip install line-profiler

# Profile specific functions
kernprof -l -v benchmarks/profile_lines.py
```

## Creating Test Data

```bash
# Generate test files
python benchmarks/generate_test_data.py

# This creates:
# - test_data/small/*.log (1000 files × 1MB)
# - test_data/medium/*.log (100 files × 10MB)
# - test_data/large/*.log (10 files × 100MB)
# - test_data/compressed/*.log.gz (various sizes)
```

## Interpreting Results

### Benchmark Output
```
Name (time in ms)          Min      Max     Mean  StdDev
----------------------------------------------------------
test_read_small_file     5.234    6.891   5.567   0.234
test_read_large_file   450.123  478.456 462.789  10.234
```

**What to look for:**
- **Mean**: Average execution time (lower is better)
- **StdDev**: Consistency (lower is better)
- **Min/Max**: Range of performance

### Comparison with Baseline
```bash
# Save current results as baseline
python -m pytest benchmarks/ --benchmark-save=baseline

# After changes, compare
python -m pytest benchmarks/ --benchmark-compare=baseline
```

Output shows:
- **Faster**: ✓ (green) - improvement
- **Slower**: ✗ (red) - regression
- **Percent change**: e.g., "15% faster"

## Performance Targets

Based on the performance analysis, target improvements:

| Operation | Current | Target | Actual |
|-----------|---------|--------|--------|
| File scanning (1000 files) | 2.5s | 1.5s | TBD |
| Record parsing (1M lines) | 3.0s | 1.8s | TBD |
| Pattern matching (10M ops) | 5.0s | 4.0s | TBD |
| Large file read (100MB) | 8.0s | 5.0s | TBD |

## Continuous Integration

Add to CI pipeline:
```yaml
# .github/workflows/benchmarks.yml
- name: Run benchmarks
  run: |
    pytest benchmarks/ --benchmark-only
    pytest benchmarks/ --benchmark-compare
```

## Adding New Benchmarks

1. Create test file in `benchmarks/test_*.py`
2. Use `pytest-benchmark` fixture:
```python
def test_my_operation(benchmark):
    # Setup
    data = prepare_data()
    
    # Benchmark the operation
    result = benchmark(my_operation, data)
    
    # Optional assertions
    assert result is not None
```

3. Run and verify:
```bash
pytest benchmarks/test_my_new_benchmark.py -v
```

## Notes

- Benchmarks should be run on a **quiet system** (no heavy background processes)
- Run multiple times and take the median: `--benchmark-min-rounds=5`
- Warm up the code: `--benchmark-warmup=on`
- For very fast operations, increase iterations: `--benchmark-min-time=0.1`

## Resources

- [pytest-benchmark docs](https://pytest-benchmark.readthedocs.io/)
- [Python profiling guide](https://docs.python.org/3/library/profile.html)
- [Performance Analysis](../PERFORMANCE_ANALYSIS.md)
