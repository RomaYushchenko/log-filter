"""Generate test data for benchmarks.

Creates realistic log files of various sizes for performance testing.

Usage:
    python benchmarks/generate_test_data.py
    python benchmarks/generate_test_data.py --output-dir custom_data
    python benchmarks/generate_test_data.py --skip-large  # Skip 100MB files
"""

import argparse
import gzip
import random
from pathlib import Path


def generate_log_line(counter: int, level: str = None) -> str:
    """Generate a realistic log line.

    Args:
        counter: Line counter for variation
        level: Log level (INFO, WARN, ERROR, etc.) or None for random

    Returns:
        Formatted log line
    """
    levels = ["INFO", "WARN", "ERROR", "DEBUG", "FATAL"]
    services = ["UserService", "PaymentService", "NotificationService", "DatabasePool"]
    operations = [
        "Processing request",
        "Database query",
        "Cache lookup",
        "External API call",
    ]

    if level is None:
        # 70% INFO, 20% WARN, 8% ERROR, 2% FATAL
        rand = random.random()
        if rand < 0.70:
            level = "INFO"
        elif rand < 0.90:
            level = "WARN"
        elif rand < 0.98:
            level = "ERROR"
        else:
            level = "FATAL"

    service = services[counter % len(services)]
    operation = operations[counter % len(operations)]
    user_id = counter % 10000
    duration_ms = 10 + (counter % 500)

    line = f"2026-02-03 {10 + (counter // 36000):02d}:{(counter // 600) % 60:02d}:{counter % 60:02d}.{counter % 1000:03d}+0000 {level} [{service}] {operation} for user {user_id} - completed in {duration_ms}ms\n"

    # Occasionally add stack traces for errors
    if level in ["ERROR", "FATAL"] and counter % 100 == 0:
        line += "java.lang.RuntimeException: Connection timeout\n"
        line += f"    at com.example.{service}.process({service}.java:42)\n"
        line += "    at com.example.Handler.handle(Handler.java:123)\n"
        line += "    at com.example.Processor.run(Processor.java:89)\n"

    return line


def generate_file(
    output_path: Path, size_mb: int, compressed: bool = False, verbose: bool = True
):
    """Generate a log file of specified size.

    Args:
        output_path: Path where file will be created
        size_mb: Target size in megabytes (for uncompressed content)
        compressed: Whether to create a gzip file
        verbose: Whether to print progress
    """
    if verbose:
        print(f"  Creating {output_path.name} ({size_mb}MB{'compressed' if compressed else ''})...", end="", flush=True)

    lines_needed = (size_mb * 1024 * 1024) // 200  # ~200 bytes per line

    if compressed:
        with gzip.open(output_path, "wt", encoding="utf-8") as f:
            for i in range(lines_needed):
                f.write(generate_log_line(i))
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            for i in range(lines_needed):
                f.write(generate_log_line(i))

    actual_size = output_path.stat().st_size / (1024 * 1024)
    if verbose:
        print(f" done ({actual_size:.1f}MB actual)")


def main():
    """Generate all test data files."""
    parser = argparse.ArgumentParser(description="Generate test data for benchmarks")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("test_data"),
        help="Output directory for test files",
    )
    parser.add_argument(
        "--skip-large", action="store_true", help="Skip generating large (100MB) files"
    )

    args = parser.parse_args()

    output_dir = args.output_dir
    output_dir.mkdir(exist_ok=True)

    print("Generating test data...")
    print()

    # Small files (1MB each)
    print("Small files (1MB each):")
    small_dir = output_dir / "small"
    small_dir.mkdir(exist_ok=True)
    for i in range(10):
        generate_file(small_dir / f"app-{i:03d}.log", 1, compressed=False)

    print()

    # Medium files (10MB each)
    print("Medium files (10MB each):")
    medium_dir = output_dir / "medium"
    medium_dir.mkdir(exist_ok=True)
    for i in range(5):
        generate_file(medium_dir / f"app-{i:03d}.log", 10, compressed=False)

    print()

    # Large files (100MB each) - optional
    if not args.skip_large:
        print("Large files (100MB each):")
        large_dir = output_dir / "large"
        large_dir.mkdir(exist_ok=True)
        for i in range(2):
            generate_file(large_dir / f"app-{i:03d}.log", 100, compressed=False)
        print()

    # Compressed files (various sizes)
    print("Compressed files:")
    compressed_dir = output_dir / "compressed"
    compressed_dir.mkdir(exist_ok=True)
    generate_file(compressed_dir / "small.log.gz", 5, compressed=True)
    generate_file(compressed_dir / "medium.log.gz", 50, compressed=True)
    if not args.skip_large:
        generate_file(compressed_dir / "large.log.gz", 100, compressed=True)

    print()
    print(f"Test data generated in: {output_dir.absolute()}")
    print()
    print("To run benchmarks with this data:")
    print(f"  pytest benchmarks/ -v")


if __name__ == "__main__":
    main()
