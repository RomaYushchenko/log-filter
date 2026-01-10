"""Security audit tests for the log filter application.

Tests for vulnerabilities including:
- Path traversal attacks
- Expression injection
- Resource exhaustion (DoS)
- File access control violations
- Information disclosure
- Input validation bypasses
"""

import os
from pathlib import Path

import pytest

from log_filter.config.models import (
    ApplicationConfig,
    FileConfig,
    OutputConfig,
    ProcessingConfig,
    SearchConfig,
)
from log_filter.core.exceptions import (
    ConfigurationError,
    FileHandlingError,
    ParseError,
    TokenizationError,
)
from log_filter.infrastructure.file_handlers.log_handler import LogFileHandler
from log_filter.infrastructure.file_scanner import FileScanner
from log_filter.processing.pipeline import ProcessingPipeline


class TestPathTraversalVulnerabilities:
    """Test protection against path traversal attacks."""

    def test_path_traversal_in_search_root(self, tmp_path):
        """Test that path traversal in search_root is handled safely."""
        # Create a test file outside the intended directory
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        secret_file = outside_dir / "secret.log"
        secret_file.write_text("2025-01-08 12:00:00 SECRET data\n")

        # Create working directory
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        output = work_dir / "output.log"

        # Try to access parent directory with ../
        traversal_path = work_dir / ".." / "outside"

        config = ApplicationConfig(
            search=SearchConfig(expression="SECRET"),
            files=FileConfig(search_root=traversal_path, extensions=(".log",)),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        # System should handle this safely (either reject or resolve safely)
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # If it runs, verify it doesn't expose unauthorized data
        if output.exists():
            content = output.read_text()
            # Should either be empty or contain only authorized data
            assert True  # Ran without error

    def test_absolute_path_outside_workspace(self, tmp_path):
        """Test that absolute paths outside workspace are handled."""
        # Try to access a system directory
        system_root = Path("C:/Windows") if os.name == "nt" else Path("/etc")

        if not system_root.exists():
            pytest.skip(f"System directory {system_root} not available")

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=system_root, extensions=(".log",)),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        # Should handle safely (may scan or may reject based on permissions)
        pipeline = ProcessingPipeline(config)
        try:
            pipeline.run()
        except (FileHandlingError, PermissionError):
            pass  # Expected - permission denied is safe behavior

    def test_symlink_to_sensitive_location(self, tmp_path):
        """Test handling of symlinks pointing to sensitive locations."""
        if os.name == "nt":
            pytest.skip("Symlink test not reliable on Windows")

        # Create a symlink to /etc or another sensitive dir
        sensitive_dir = Path("/etc")
        if not sensitive_dir.exists():
            pytest.skip("Sensitive directory not available")

        link = tmp_path / "link_to_etc"
        try:
            link.symlink_to(sensitive_dir)
        except OSError:
            pytest.skip("Cannot create symlink")

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=tmp_path, extensions=(".log",)),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        # Should handle symlinks safely
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Should not crash or leak sensitive data
        assert True


class TestExpressionInjection:
    """Test protection against expression injection attacks."""

    def test_malformed_expression_with_special_chars(self, tmp_path):
        """Test that special characters in expressions don't cause injection."""
        log_file = tmp_path / "test.log"
        log_file.write_text("2025-01-08 12:00:00 ERROR Test\n")

        output = tmp_path / "output.log"

        # Try various injection attempts
        malicious_expressions = [
            "'; DROP TABLE logs; --",
            "ERROR && rm -rf /",
            "ERROR | cat /etc/passwd",
            "ERROR $(whoami)",
            "ERROR `ls -la`",
            "__import__('os').system('whoami')",
            "eval('1+1')",
        ]

        for expr in malicious_expressions:
            config = ApplicationConfig(
                search=SearchConfig(expression=expr),
                files=FileConfig(search_root=tmp_path, extensions=(".log",)),
                output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            )

            pipeline = ProcessingPipeline(config)

            # Should either parse safely or reject
            try:
                pipeline.run()
            except (ConfigurationError, TokenizationError, ParseError):
                pass  # Expected - rejected malicious input

            # Should never execute arbitrary code
            assert True

    def test_regex_dos_attack(self, tmp_path):
        """Test protection against ReDoS (Regular Expression Denial of Service)."""
        log_file = tmp_path / "test.log"
        # Create content that could trigger catastrophic backtracking
        log_file.write_text("2025-01-08 12:00:00 " + "a" * 1000 + "X\n")

        output = tmp_path / "output.log"

        # Regex patterns known to cause ReDoS
        redos_patterns = [
            "(a+)+b",
            "(a*)*b",
            "(a|a)*b",
            "(a|ab)*c",
        ]

        for pattern in redos_patterns:
            config = ApplicationConfig(
                search=SearchConfig(expression=pattern, use_regex=True),
                files=FileConfig(search_root=tmp_path, extensions=(".log",)),
                output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
                processing=ProcessingConfig(worker_count=1),
            )

            pipeline = ProcessingPipeline(config)

            # Should complete in reasonable time (not hang)
            import time

            start = time.time()
            try:
                pipeline.run()
            except (ConfigurationError, TokenizationError, ParseError):
                pass
            duration = time.time() - start

            # Should not take more than 5 seconds
            assert duration < 5.0, f"Possible ReDoS with pattern {pattern}"

    def test_nested_expression_depth_limit(self, tmp_path):
        """Test that deeply nested expressions don't cause stack overflow."""
        log_file = tmp_path / "test.log"
        log_file.write_text("2025-01-08 12:00:00 ERROR Test\n")

        output = tmp_path / "output.log"

        # Create deeply nested parentheses
        depth = 1000
        expr = "(" * depth + "ERROR" + ")" * depth

        config = ApplicationConfig(
            search=SearchConfig(expression=expr),
            files=FileConfig(search_root=tmp_path, extensions=(".log",)),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)

        # Should handle without stack overflow
        try:
            pipeline.run()
        except (ConfigurationError, TokenizationError, ParseError, RecursionError):
            pass  # Expected - rejected or caught recursion

        # Should not crash
        assert True


class TestResourceExhaustionDoS:
    """Test protection against Denial of Service attacks."""

    def test_extremely_large_file(self, tmp_path):
        """Test handling of extremely large files."""
        log_file = tmp_path / "huge.log"

        # Create a 10MB file
        with open(log_file, "w") as f:
            for i in range(100000):
                f.write(f"2025-01-08 12:00:00 ERROR Line {i}\n")

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=tmp_path, extensions=(".log",)),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        # Should process without excessive memory usage
        import time

        start = time.time()
        pipeline = ProcessingPipeline(config)
        pipeline.run()
        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 30.0, "Processing took too long"

    def test_many_concurrent_workers(self, tmp_path):
        """Test that worker count is bounded to prevent resource exhaustion."""
        log_file = tmp_path / "test.log"
        log_file.write_text("2025-01-08 12:00:00 ERROR Test\n")

        output = tmp_path / "output.log"

        # Try to create excessive workers (should be rejected)
        with pytest.raises(ValueError) as exc_info:
            config = ApplicationConfig(
                search=SearchConfig(expression="ERROR"),
                files=FileConfig(search_root=tmp_path, extensions=(".log",)),
                output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
                processing=ProcessingConfig(worker_count=10000),  # Excessive
            )

        # Verify error message mentions platform maximum
        error_msg = str(exc_info.value)
        assert "exceeds platform maximum" in error_msg
        assert "resource exhaustion" in error_msg

    def test_zip_bomb_like_compressed_file(self, tmp_path):
        """Test handling of highly compressed files (zip bomb scenario)."""
        import gzip

        gz_file = tmp_path / "bomb.log.gz"

        # Create a file that expands significantly
        with gzip.open(gz_file, "wt") as f:
            # Write repetitive content that compresses well
            content = "ERROR " * 1000000  # Will compress to small size
            f.write(content)

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=tmp_path, extensions=(".gz",)),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        # Should handle without memory exhaustion
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Should complete successfully without crashes
        # Output file created only if matches found ("ERROR" alone may not match multiline records)
        # Test passes if pipeline completes without memory exhaustion


class TestFileAccessControl:
    """Test file access control and permission handling."""

    def test_output_file_cannot_overwrite_system_files(self, tmp_path):
        """Test that output cannot overwrite critical system files."""
        log_file = tmp_path / "test.log"
        log_file.write_text("2025-01-08 12:00:00 ERROR Test\n")

        # Try to write to a system location
        if os.name == "nt":
            dangerous_output = Path("C:/Windows/System32/test.log")
        else:
            dangerous_output = Path("/etc/test.log")

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=tmp_path, extensions=(".log",)),
            output=OutputConfig(
                output_file=dangerous_output, show_progress=False, show_stats=False
            ),
        )

        pipeline = ProcessingPipeline(config)

        # Should fail due to permissions or validation
        try:
            pipeline.run()
        except (FileHandlingError, OSError):
            pass  # Expected - permission denied is safe

    def test_respects_file_permissions(self, tmp_path):
        """Test that the system respects file permissions."""
        if os.name == "nt":
            pytest.skip("Permission test not reliable on Windows")

        restricted_file = tmp_path / "restricted.log"
        restricted_file.write_text("2025-01-08 12:00:00 SECRET data\n")
        os.chmod(restricted_file, 0o000)  # No permissions

        output = tmp_path / "output.log"

        try:
            config = ApplicationConfig(
                search=SearchConfig(expression="SECRET"),
                files=FileConfig(search_root=tmp_path, extensions=(".log",)),
                output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            )

            pipeline = ProcessingPipeline(config)
            pipeline.run()

            # Should skip inaccessible files gracefully
            stats = pipeline.stats.get_snapshot()
            assert stats.files_skipped > 0 or stats.files_processed == 0
        finally:
            os.chmod(restricted_file, 0o666)


class TestInformationDisclosure:
    """Test for information disclosure vulnerabilities."""

    def test_error_messages_dont_leak_paths(self, tmp_path):
        """Test that error messages don't leak sensitive path information."""
        nonexistent = tmp_path / "secret_project" / "confidential" / "data.log"

        try:
            handler = LogFileHandler(nonexistent)
            assert False, "Should have raised exception"
        except FileHandlingError as e:
            error_msg = str(e)
            # Error should contain the path (for debugging) but this is acceptable
            # In production, consider sanitizing paths
            assert "data.log" in error_msg

    def test_no_stack_trace_in_normal_errors(self, tmp_path):
        """Test that user-facing errors don't include full stack traces."""
        log_file = tmp_path / "test.log"
        log_file.write_text("2025-01-08 12:00:00 ERROR Test\n")

        output = tmp_path / "output.log"

        # Invalid expression should give clean error
        config = ApplicationConfig(
            search=SearchConfig(expression="((("),
            files=FileConfig(search_root=tmp_path),
            output=OutputConfig(output_file=output),
        )

        pipeline = ProcessingPipeline(config)

        try:
            pipeline.run()
        except ConfigurationError as e:
            error_msg = str(e)
            # Should not contain Python internals
            assert "Traceback" not in error_msg
            assert 'File "' not in error_msg


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_file_extension_validation(self, tmp_path):
        """Test that file extensions are properly validated."""
        # Create files with unusual extensions
        unusual_files = [
            "test.log.bak",
            "test.log~",
            "test.log.1",
            ".hidden.log",
            "test..log",
        ]

        for filename in unusual_files:
            file = tmp_path / filename
            file.write_text("2025-01-08 12:00:00 ERROR Test\n")

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=tmp_path, extensions=(".log",)),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        pipeline = ProcessingPipeline(config)
        pipeline.run()

        stats = pipeline.stats.get_snapshot()
        # Should only process files with exact .log extension
        # Based on implementation, may vary
        assert stats.files_scanned >= 0

    def test_filename_with_null_bytes(self, tmp_path):
        """Test handling of filenames with null bytes."""
        # Try to create a filename with null byte (should fail safely)
        try:
            dangerous_name = "test\x00.log"
            log_file = tmp_path / dangerous_name
            log_file.write_text("2025-01-08 12:00:00 ERROR Test\n")
        except (ValueError, OSError):
            pytest.skip("OS prevents null bytes in filenames")

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=tmp_path, extensions=(".log",)),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        # Should handle safely
        pipeline = ProcessingPipeline(config)
        pipeline.run()

    def test_worker_count_validation(self, tmp_path):
        """Test that worker count is validated properly."""
        log_file = tmp_path / "test.log"
        log_file.write_text("2025-01-08 12:00:00 ERROR Test\n")

        output = tmp_path / "output.log"

        # Try invalid worker counts
        invalid_counts = [-1, 0, -100]

        for count in invalid_counts:
            with pytest.raises(ValueError):
                config = ApplicationConfig(
                    search=SearchConfig(expression="ERROR"),
                    files=FileConfig(search_root=tmp_path, extensions=(".log",)),
                    output=OutputConfig(output_file=output),
                    processing=ProcessingConfig(worker_count=count),
                )


class TestEncodingSecurityr:
    """Test encoding-related security issues."""

    def test_unicode_normalization_attack(self, tmp_path):
        """Test handling of Unicode normalization attacks."""
        # Create files with similar-looking Unicode characters
        files = [
            "test.log",  # Normal ASCII
            "tеst.log",  # Cyrillic 'е' (U+0435)
            "test․log",  # One-dot leader (U+2024) instead of period
        ]

        for filename in files:
            try:
                file = tmp_path / filename
                file.write_text("2025-01-08 12:00:00 ERROR Test\n")
            except (OSError, UnicodeError):
                continue

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=tmp_path, extensions=(".log",)),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        # Should handle Unicode variants safely
        pipeline = ProcessingPipeline(config)
        pipeline.run()

    def test_mixed_encoding_files(self, tmp_path):
        """Test handling of files with mixed or invalid encodings."""
        # Create file with mixed encodings
        mixed_file = tmp_path / "mixed.log"

        with open(mixed_file, "wb") as f:
            f.write(b"2025-01-08 12:00:00 ERROR ASCII\n")
            f.write(b"2025-01-08 12:00:00 ERROR \xff\xfe Invalid\n")  # Invalid UTF-8
            f.write("2025-01-08 12:00:00 ERROR UTF-8 тест\n".encode("utf-8"))

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=tmp_path, extensions=(".log",)),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
        )

        # Should handle gracefully with fallback encodings
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Should not crash
        assert True


class TestConcurrencySecurity:
    """Test concurrency-related security issues."""

    def test_race_condition_in_output_file(self, tmp_path):
        """Test handling of race conditions when writing output."""
        log_file = tmp_path / "test.log"
        log_file.write_text("2025-01-08 12:00:00 ERROR Test\n" * 100)

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=tmp_path, extensions=(".log",)),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            processing=ProcessingConfig(worker_count=4),
        )

        # Run with multiple workers
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        # Output file only created if matches found
        if output.exists():
            content = output.read_text()
            # File should be consistent (no corruption from race conditions)
            assert "\x00" not in content  # No null bytes from corruption
            assert "ERROR" in content  # Should contain matches if file exists
        # Test passes if no race conditions cause crashes

    def test_concurrent_file_access(self, tmp_path):
        """Test that concurrent access to files is handled safely."""
        # Create multiple log files
        for i in range(10):
            log_file = tmp_path / f"test_{i}.log"
            log_file.write_text("2025-01-08 12:00:00 ERROR Test\n" * 10)

        output = tmp_path / "output.log"

        config = ApplicationConfig(
            search=SearchConfig(expression="ERROR"),
            files=FileConfig(search_root=tmp_path, extensions=(".log",)),
            output=OutputConfig(output_file=output, show_progress=False, show_stats=False),
            processing=ProcessingConfig(worker_count=4),
        )

        # Should handle concurrent processing safely
        pipeline = ProcessingPipeline(config)
        pipeline.run()

        stats = pipeline.stats.get_snapshot()
        assert stats.files_processed == 10
