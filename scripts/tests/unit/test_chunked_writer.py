"""Unit tests for ChunkedLogWriter."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from log_filter.infrastructure.chunked_writer import ChunkedLogWriter


class TestChunkedLogWriter:
    """Tests for ChunkedLogWriter class."""

    def test_single_file_unlimited(self, tmp_path: Path) -> None:
        """Test writing to single file when max_records is None."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file, max_records_per_file=None) as writer:
            for i in range(10):
                writer.write_record({"content": f"Record {i}\n"})

        # Should create only one file
        created_files = writer.get_created_files()
        assert len(created_files) == 1
        assert created_files[0] == output_file

        # Verify content
        content = output_file.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 10
        assert lines[0] == "Record 0"
        assert lines[9] == "Record 9"

    def test_single_file_zero_limit(self, tmp_path: Path) -> None:
        """Test that max_records_per_file=0 means unlimited."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file, max_records_per_file=0) as writer:
            for i in range(100):
                writer.write_record({"content": f"Record {i}\n"})

        created_files = writer.get_created_files()
        assert len(created_files) == 1

    def test_chunking_basic(self, tmp_path: Path) -> None:
        """Test basic chunking with small limit."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file, max_records_per_file=5) as writer:
            for i in range(12):
                writer.write_record({"content": f"Record {i}\n"})

        created_files = writer.get_created_files()

        # Should create 3 files: 5 + 5 + 2 records
        assert len(created_files) == 3
        assert created_files[0].name == "output-001.log"
        assert created_files[1].name == "output-002.log"
        assert created_files[2].name == "output-003.log"

        # Verify first file has 5 records
        content1 = created_files[0].read_text(encoding="utf-8")
        assert len(content1.strip().split("\n")) == 5

        # Verify second file has 5 records
        content2 = created_files[1].read_text(encoding="utf-8")
        assert len(content2.strip().split("\n")) == 5

        # Verify third file has 2 records
        content3 = created_files[2].read_text(encoding="utf-8")
        assert len(content3.strip().split("\n")) == 2

    def test_exact_chunk_boundary(self, tmp_path: Path) -> None:
        """Test when records exactly fill chunks."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file, max_records_per_file=10) as writer:
            for i in range(30):
                writer.write_record({"content": f"Record {i}\n"})

        created_files = writer.get_created_files()
        assert len(created_files) == 3

        for file_path in created_files:
            content = file_path.read_text(encoding="utf-8")
            assert len(content.strip().split("\n")) == 10

    def test_custom_pattern(self, tmp_path: Path) -> None:
        """Test custom filename pattern."""
        output_file = tmp_path / "result.log"

        with ChunkedLogWriter(
            output_file, max_records_per_file=3, file_pattern="{base}_part{index:02d}{ext}"
        ) as writer:
            for i in range(7):
                writer.write_record({"content": f"Record {i}\n"})

        created_files = writer.get_created_files()
        assert len(created_files) == 3
        assert created_files[0].name == "result_part01.log"
        assert created_files[1].name == "result_part02.log"
        assert created_files[2].name == "result_part03.log"

    def test_pattern_with_timestamp(self, tmp_path: Path) -> None:
        """Test pattern with timestamp variable."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(
            output_file, max_records_per_file=5, file_pattern="{base}_{timestamp}-{index}{ext}"
        ) as writer:
            for i in range(6):
                writer.write_record({"content": f"Record {i}\n"})

        created_files = writer.get_created_files()
        assert len(created_files) == 2

        # Filenames should contain timestamp
        for file_path in created_files:
            # Format: output_YYYYMMDD_HHMMSS-N.log
            assert "_" in file_path.name
            assert "-" in file_path.name

    def test_content_without_newline(self, tmp_path: Path) -> None:
        """Test that newlines are added if missing."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file, max_records_per_file=None) as writer:
            writer.write_record({"content": "Line without newline"})
            writer.write_record({"content": "Line with newline\n"})

        content = output_file.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Should have 3 elements: 2 lines + empty string after final newline
        assert len(lines) == 3
        assert lines[0] == "Line without newline"
        assert lines[1] == "Line with newline"

    def test_record_without_content_raises_error(self, tmp_path: Path) -> None:
        """Test that record without 'content' key raises error."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file) as writer:
            with pytest.raises(ValueError, match="must contain 'content' key"):
                writer.write_record({"timestamp": datetime.now()})

    def test_get_created_files_returns_copy(self, tmp_path: Path) -> None:
        """Test that get_created_files returns a copy."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file, max_records_per_file=2) as writer:
            for i in range(3):
                writer.write_record({"content": f"Record {i}\n"})

            files1 = writer.get_created_files()
            files2 = writer.get_created_files()

            # Should be equal but not same object
            assert files1 == files2
            assert files1 is not files2

    def test_current_output_file_property(self, tmp_path: Path) -> None:
        """Test current_output_file property."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file, max_records_per_file=2) as writer:
            # After opening, should have current file
            assert writer.current_output_file is not None
            first_file = writer.current_output_file

            writer.write_record({"content": "Record 1\n"})
            writer.write_record({"content": "Record 2\n"})

            # Still on first file
            assert writer.current_output_file == first_file

            # This should trigger rotation
            writer.write_record({"content": "Record 3\n"})

            # Should have rotated to new file
            assert writer.current_output_file != first_file

    def test_close_idempotent(self, tmp_path: Path) -> None:
        """Test that close() can be called multiple times safely."""
        output_file = tmp_path / "output.log"

        writer = ChunkedLogWriter(output_file)
        writer.__enter__()
        writer.write_record({"content": "Test\n"})

        # Close multiple times should not raise error
        writer.close()
        writer.close()
        writer.close()

    def test_context_manager_cleanup(self, tmp_path: Path) -> None:
        """Test that context manager properly closes files."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file) as writer:
            writer.write_record({"content": "Test\n"})
            # File should be open here
            assert writer.current_file is not None

        # After context, file should be closed
        assert writer.current_file is None

    def test_directory_creation(self, tmp_path: Path) -> None:
        """Test that output directory is created if it doesn't exist."""
        nested_dir = tmp_path / "nested" / "output" / "dir"
        output_file = nested_dir / "output.log"

        # Directory shouldn't exist yet
        assert not nested_dir.exists()

        with ChunkedLogWriter(output_file, max_records_per_file=None) as writer:
            writer.write_record({"content": "Test\n"})

        # Directory should have been created
        assert nested_dir.exists()
        assert output_file.exists()

    def test_total_records_counter(self, tmp_path: Path) -> None:
        """Test that total_records_written counter is accurate."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file, max_records_per_file=5) as writer:
            for i in range(17):
                writer.write_record({"content": f"Record {i}\n"})

        assert writer.total_records_written == 17

    def test_repr_string(self, tmp_path: Path) -> None:
        """Test __repr__ returns useful information."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file, max_records_per_file=10) as writer:
            for i in range(5):
                writer.write_record({"content": f"Record {i}\n"})

            repr_str = repr(writer)

            assert "ChunkedLogWriter" in repr_str
            assert str(output_file) in repr_str
            assert "max_records=10" in repr_str
            assert "total_records=5" in repr_str

    def test_unicode_content(self, tmp_path: Path) -> None:
        """Test writing Unicode content."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file, max_records_per_file=None) as writer:
            writer.write_record({"content": "Test with émojis: 🚀 ✅ 📊\n"})
            writer.write_record({"content": "Cyrillic: Привет мир\n"})
            writer.write_record({"content": "Chinese: 你好世界\n"})

        # With unlimited records, file is created at base path
        content = output_file.read_text(encoding="utf-8")
        assert "🚀" in content
        assert "Привет" in content
        assert "你好" in content

    def test_large_records(self, tmp_path: Path) -> None:
        """Test writing large records."""
        output_file = tmp_path / "output.log"

        # Create a large record (10KB)
        large_content = "A" * 10000 + "\n"

        with ChunkedLogWriter(output_file, max_records_per_file=2) as writer:
            for i in range(3):
                writer.write_record({"content": large_content})

        created_files = writer.get_created_files()
        assert len(created_files) == 2

        # Verify file sizes are reasonable
        for file_path in created_files[:1]:  # First file should have 2 records
            size = file_path.stat().st_size
            assert size > 20000  # At least 20KB

    def test_empty_content(self, tmp_path: Path) -> None:
        """Test writing empty content."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file, max_records_per_file=None) as writer:
            writer.write_record({"content": ""})
            writer.write_record({"content": "\n"})

        content = output_file.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Should have empty lines
        assert lines[0] == ""
        assert lines[1] == ""

    def test_metadata_preserved(self, tmp_path: Path) -> None:
        """Test that extra metadata in record dict doesn't cause issues."""
        output_file = tmp_path / "output.log"

        with ChunkedLogWriter(output_file, max_records_per_file=None) as writer:
            writer.write_record(
                {
                    "content": "Test log\n",
                    "timestamp": datetime.now(),
                    "level": "ERROR",
                    "source_file": "/var/log/app.log",
                }
            )

        # Should write successfully (extra keys ignored)
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "Test log" in content
