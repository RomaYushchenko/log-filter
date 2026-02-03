"""CPU profiling script for log filter.

Usage:
    python benchmarks/profile_cpu.py --scenario large_file
    python benchmarks/profile_cpu.py --scenario many_files
    python benchmarks/profile_cpu.py --scenario compressed

Then analyze:
    python -m pstats profile_output.stats
    > sort cumtime
    > stats 30
"""

import argparse
import cProfile
import pstats
import tempfile
from pathlib import Path

from log_filter.core.evaluator import ExpressionEvaluator
from log_filter.core.parser import ExpressionParser
from log_filter.infrastructure.file_handlers.gzip_handler import GzipFileHandler
from log_filter.infrastructure.file_handlers.log_handler import LogFileHandler


def generate_test_file(size_mb: int, compressed: bool = False) -> Path:
    """Generate a test log file.

    Args:
        size_mb: Target size in megabytes
        compressed: Whether to create a gzip file

    Returns:
        Path to the generated file
    """
    temp_file = tempfile.NamedTemporaryFile(
        delete=False, suffix=".log.gz" if compressed else ".log"
    )
    temp_path = Path(temp_file.name)

    lines_needed = (size_mb * 1024 * 1024) // 200  # ~200 bytes per line

    log_template = "2026-02-03 10:30:45.123+0000 INFO [com.example.Service] Processing request for user {user_id} - Operation completed successfully in {ms}ms\n"

    if compressed:
        import gzip

        with gzip.open(temp_path, "wt", encoding="utf-8") as f:
            for i in range(lines_needed):
                line = log_template.format(user_id=i % 10000, ms=10 + (i % 100))
                f.write(line)
    else:
        with open(temp_path, "w", encoding="utf-8") as f:
            for i in range(lines_needed):
                line = log_template.format(user_id=i % 10000, ms=10 + (i % 100))
                f.write(line)

    return temp_path


def profile_large_file():
    """Profile processing a single large log file (100MB)."""
    print("Generating 100MB test file...")
    test_file = generate_test_file(100, compressed=False)

    print("Profiling file reading and evaluation...")
    handler = LogFileHandler(test_file)
    parser = ExpressionParser()
    ast = parser.parse("ERROR OR FATAL")
    evaluator = ExpressionEvaluator(ast)

    match_count = 0
    for line in handler.read_lines():
        if evaluator.evaluate(line):
            match_count += 1

    print(f"Matched {match_count} lines")
    test_file.unlink()  # Cleanup


def profile_many_files():
    """Profile processing many small log files (100 × 1MB)."""
    print("Generating 100 small test files...")
    test_files = []
    for i in range(100):
        test_file = generate_test_file(1, compressed=False)
        test_files.append(test_file)

    print("Profiling multi-file processing...")
    parser = ExpressionParser()
    ast = parser.parse("ERROR OR FATAL")
    evaluator = ExpressionEvaluator(ast)

    total_matches = 0
    for test_file in test_files:
        handler = LogFileHandler(test_file)
        for line in handler.read_lines():
            if evaluator.evaluate(line):
                total_matches += 1

    print(f"Matched {total_matches} lines across {len(test_files)} files")

    # Cleanup
    for test_file in test_files:
        test_file.unlink()


def profile_compressed():
    """Profile processing compressed log files (10MB compressed → ~100MB uncompressed)."""
    print("Generating 10MB compressed test file...")
    test_file = generate_test_file(100, compressed=True)

    print("Profiling compressed file reading and evaluation...")
    handler = GzipFileHandler(test_file)
    parser = ExpressionParser()
    ast = parser.parse("ERROR OR FATAL")
    evaluator = ExpressionEvaluator(ast)

    match_count = 0
    for line in handler.read_lines():
        if evaluator.evaluate(line):
            match_count += 1

    print(f"Matched {match_count} lines")
    test_file.unlink()  # Cleanup


def main():
    """Run CPU profiling based on scenario."""
    arg_parser = argparse.ArgumentParser(description="Profile log filter performance")
    arg_parser.add_argument(
        "--scenario",
        choices=["large_file", "many_files", "compressed"],
        default="large_file",
        help="Scenario to profile",
    )
    arg_parser.add_argument(
        "--output", default="profile_output.stats", help="Output stats file"
    )

    args = arg_parser.parse_args()

    scenarios = {
        "large_file": profile_large_file,
        "many_files": profile_many_files,
        "compressed": profile_compressed,
    }

    print(f"\nProfiling scenario: {args.scenario}\n")

    profiler = cProfile.Profile()
    profiler.enable()

    scenarios[args.scenario]()

    profiler.disable()

    print(f"\nSaving profile to {args.output}")
    profiler.dump_stats(args.output)

    print("\nTop 20 functions by cumulative time:")
    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats("cumtime")
    stats.print_stats(20)

    print(f"\nTo analyze further, run:")
    print(f"  python -m pstats {args.output}")
    print(f"  > sort cumtime")
    print(f"  > stats 30")


if __name__ == "__main__":
    main()
