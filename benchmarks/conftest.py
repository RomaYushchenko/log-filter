"""Pytest configuration and fixtures for benchmarks.

This module provides common fixtures and test data for performance benchmarks.
"""

import gzip
import tempfile
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="session")
def small_log_file(test_data_dir: Path) -> Path:
    """Generate a small log file (1MB, ~5000 lines).

    Returns:
        Path to the generated log file
    """
    file_path = test_data_dir / "small.log"
    
    # Generate ~5000 lines of realistic log data (~200 bytes per line)
    log_template = "2026-02-03 10:30:45.123+0000 INFO [com.example.Service] Processing request for user {user_id} - Operation completed successfully in {ms}ms\n"
    
    with open(file_path, "w", encoding="utf-8") as f:
        for i in range(5000):
            line = log_template.format(user_id=i % 1000, ms=10 + (i % 100))
            f.write(line)
            
            # Add occasional multi-line stack traces
            if i % 500 == 0:
                f.write("java.lang.NullPointerException: Cannot invoke method\n")
                f.write("    at com.example.Service.process(Service.java:42)\n")
                f.write("    at com.example.Handler.handle(Handler.java:123)\n")
    
    return file_path


@pytest.fixture(scope="session")
def medium_log_file(test_data_dir: Path) -> Path:
    """Generate a medium log file (10MB, ~50000 lines).

    Returns:
        Path to the generated log file
    """
    file_path = test_data_dir / "medium.log"
    
    log_template = "2026-02-03 10:30:45.123+0000 INFO [com.example.Service] Processing request for user {user_id} - Operation completed successfully in {ms}ms\n"
    
    with open(file_path, "w", encoding="utf-8") as f:
        for i in range(50000):
            line = log_template.format(user_id=i % 10000, ms=10 + (i % 100))
            f.write(line)
            
            if i % 5000 == 0:
                f.write("java.lang.RuntimeException: Error processing\n")
                f.write("    at com.example.Service.process(Service.java:42)\n")
    
    return file_path


@pytest.fixture(scope="session")
def large_log_file(test_data_dir: Path) -> Path:
    """Generate a large log file (100MB, ~500000 lines).

    Returns:
        Path to the generated log file
    """
    file_path = test_data_dir / "large.log"
    
    log_template = "2026-02-03 10:30:45.123+0000 INFO [com.example.Service] Processing request for user {user_id} - Operation completed successfully in {ms}ms\n"
    
    with open(file_path, "w", encoding="utf-8") as f:
        for i in range(500000):
            line = log_template.format(user_id=i % 100000, ms=10 + (i % 100))
            f.write(line)
    
    return file_path


@pytest.fixture(scope="session")
def compressed_log_file(test_data_dir: Path) -> Path:
    """Generate a compressed log file (5-8MB compressed, ~50MB uncompressed).

    Returns:
        Path to the generated compressed log file
    """
    file_path = test_data_dir / "compressed.log.gz"
    
    log_template = "2026-02-03 10:30:45.123+0000 INFO [com.example.Service] Processing request for user {user_id} - Operation completed successfully in {ms}ms\n"
    
    with gzip.open(file_path, "wt", encoding="utf-8") as f:
        for i in range(250000):
            line = log_template.format(user_id=i % 50000, ms=10 + (i % 100))
            f.write(line)
    
    return file_path


@pytest.fixture(scope="session")
def many_small_files(test_data_dir: Path) -> Path:
    """Generate many small log files (100 files × 100KB).

    Returns:
        Path to directory containing the files
    """
    files_dir = test_data_dir / "many_small"
    files_dir.mkdir(exist_ok=True)
    
    log_template = "2026-02-03 10:30:45.123+0000 INFO [Service] Request {req_id} completed\n"
    
    for file_num in range(100):
        file_path = files_dir / f"app-{file_num:03d}.log"
        with open(file_path, "w", encoding="utf-8") as f:
            for i in range(500):  # ~100KB per file
                line = log_template.format(req_id=i)
                f.write(line)
    
    return files_dir


@pytest.fixture
def sample_log_lines() -> list[str]:
    """Generate sample log lines for testing.

    Returns:
        List of log lines (mix of record starts and continuations)
    """
    lines = []
    
    # Record start lines
    for i in range(100):
        lines.append(
            f"2026-02-03 10:30:{i:02d}.123+0000 INFO [Service] Processing request {i}"
        )
        
        # Continuation lines (don't start with digit)
        if i % 10 == 0:
            lines.append("    at com.example.Service.process(Service.java:42)")
            lines.append("    at com.example.Handler.handle(Handler.java:123)")
    
    return lines


@pytest.fixture
def sample_expressions() -> dict[str, str]:
    """Generate sample search expressions for testing.

    Returns:
        Dictionary of expression name to expression string
    """
    return {
        "simple_word": "ERROR",
        "simple_and": "ERROR AND timeout",
        "simple_or": "ERROR OR FATAL",
        "complex": "(ERROR OR FATAL) AND NOT heartbeat",
        "regex_simple": r"/\\d{3}-\\d{4}/",
        "regex_complex": r"/ERROR.*timeout.*connection/",
    }
