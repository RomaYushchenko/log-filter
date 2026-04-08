"""Unit tests for file utilities."""

from datetime import datetime
from pathlib import Path

import pytest

from log_filter.domain.models import FileMetadata
from log_filter.infrastructure.file_utils import (
    extract_date_and_index_from_filename,
    sort_files_by_date_and_index,
)


class TestExtractDateAndIndexFromFilename:
    """Tests for extract_date_and_index_from_filename function."""

    def test_dd_mm_yyyy_format(self) -> None:
        """Test parsing DD-MM-YYYY-N format."""
        result = extract_date_and_index_from_filename("tug-integration-02-02-2026-1.log.gz")
        assert result is not None
        date, index = result
        assert date == datetime(2026, 2, 2)
        assert index == 1

    def test_dd_mm_yyyy_multiple_digits_index(self) -> None:
        """Test parsing DD-MM-YYYY-N with multi-digit index."""
        result = extract_date_and_index_from_filename("app-15-03-2025-42.log")
        assert result is not None
        date, index = result
        assert date == datetime(2025, 3, 15)
        assert index == 42

    def test_mm_dd_yyyy_format(self) -> None:
        """Test parsing MM-DD-YYYY-N format (American format)."""
        result = extract_date_and_index_from_filename(
            "tug-integration-service-12-15-2025-32.log.gz"
        )
        assert result is not None
        date, index = result
        assert date == datetime(2025, 12, 15)
        assert index == 32

    def test_mm_dd_yyyy_ambiguous_date(self) -> None:
        """Test that ambiguous dates (both interpretations valid) default to DD-MM-YYYY."""
        # 01-02-2026 could be either Jan 2 or Feb 1
        # Should default to DD-MM-YYYY (Feb 1)
        result = extract_date_and_index_from_filename("app-01-02-2026-1.log")
        assert result is not None
        date, index = result
        assert date == datetime(2026, 2, 1)  # DD-MM-YYYY interpretation
        assert index == 1

    def test_yyyy_mm_dd_format(self) -> None:
        """Test parsing YYYY-MM-DD-N format."""
        result = extract_date_and_index_from_filename("application-2026-02-03-2.log")
        assert result is not None
        date, index = result
        assert date == datetime(2026, 2, 3)
        assert index == 2

    def test_yyyymmdd_format(self) -> None:
        """Test parsing YYYYMMDD_N format."""
        result = extract_date_and_index_from_filename("server_20260203_3.log")
        assert result is not None
        date, index = result
        assert date == datetime(2026, 2, 3)
        assert index == 3

    def test_yyyymmdd_dash_separator(self) -> None:
        """Test parsing YYYYMMDD-N format with dash."""
        result = extract_date_and_index_from_filename("server_20251225-5.log")
        assert result is not None
        date, index = result
        assert date == datetime(2025, 12, 25)
        assert index == 5

    def test_index_only_format(self) -> None:
        """Test parsing files with only index (no date)."""
        result = extract_date_and_index_from_filename("app-5.log")
        assert result is not None
        date, index = result
        assert date == datetime(1970, 1, 1)  # Epoch
        assert index == 5

    def test_index_only_underscore(self) -> None:
        """Test parsing files with underscore and index."""
        result = extract_date_and_index_from_filename("server_10.log.gz")
        assert result is not None
        date, index = result
        assert date == datetime(1970, 1, 1)
        assert index == 10

    def test_no_pattern_match(self) -> None:
        """Test files without recognizable pattern return None."""
        result = extract_date_and_index_from_filename("unknown.log")
        assert result is None

    def test_simple_filename(self) -> None:
        """Test simple filenames without date/index."""
        result = extract_date_and_index_from_filename("application.log")
        assert result is None

    def test_invalid_date(self) -> None:
        """Test invalid date values."""
        # Invalid dates should not match date patterns but may match index-only pattern
        # Month > 12 - will fail datetime creation and continue to next pattern
        result = extract_date_and_index_from_filename("app-15-13-2025-1.log")
        # This will match index-only pattern (the "-1" at the end)
        assert result is not None
        assert result[1] == 1  # Index part

        # Test a filename that truly has no valid pattern
        result = extract_date_and_index_from_filename("app-invalid.log")
        assert result is None

    def test_with_path(self) -> None:
        """Test that function works with full paths."""
        result = extract_date_and_index_from_filename("/var/log/app/tug-02-02-2026-1.log.gz")
        assert result is not None
        date, index = result
        assert date == datetime(2026, 2, 2)
        assert index == 1

    def test_windows_path(self) -> None:
        """Test with Windows-style path."""
        result = extract_date_and_index_from_filename(r"C:\logs\application-2026-01-15-3.log")
        assert result is not None
        date, index = result
        assert date == datetime(2026, 1, 15)
        assert index == 3


class TestSortFilesByDateAndIndex:
    """Tests for sort_files_by_date_and_index function."""

    def create_file_meta(self, name: str, size_bytes: int = 1000) -> FileMetadata:
        """Helper to create FileMetadata for testing."""
        return FileMetadata(
            path=Path(name),
            size_bytes=size_bytes,
            extension=".log",
            is_compressed=name.endswith(".gz"),
        )

    def test_sort_by_date_ascending(self) -> None:
        """Test files are sorted by date (oldest first)."""
        files = [
            self.create_file_meta("tug-02-03-2026-1.log"),
            self.create_file_meta("tug-02-01-2026-1.log"),
            self.create_file_meta("tug-02-02-2026-1.log"),
        ]

        sorted_files = sort_files_by_date_and_index(files)

        assert len(sorted_files) == 3
        assert sorted_files[0].path.name == "tug-02-01-2026-1.log"
        assert sorted_files[1].path.name == "tug-02-02-2026-1.log"
        assert sorted_files[2].path.name == "tug-02-03-2026-1.log"

    def test_sort_by_index_when_same_date(self) -> None:
        """Test files with same date are sorted by index."""
        files = [
            self.create_file_meta("tug-02-02-2026-3.log"),
            self.create_file_meta("tug-02-02-2026-1.log"),
            self.create_file_meta("tug-02-02-2026-2.log"),
        ]

        sorted_files = sort_files_by_date_and_index(files)

        assert sorted_files[0].path.name == "tug-02-02-2026-1.log"
        assert sorted_files[1].path.name == "tug-02-02-2026-2.log"
        assert sorted_files[2].path.name == "tug-02-02-2026-3.log"

    def test_mixed_date_and_index(self) -> None:
        """Test combined date and index sorting."""
        files = [
            self.create_file_meta("app-02-03-2026-1.log"),
            self.create_file_meta("app-02-02-2026-2.log"),
            self.create_file_meta("app-02-02-2026-1.log"),
            self.create_file_meta("app-02-03-2026-2.log"),
        ]

        sorted_files = sort_files_by_date_and_index(files)

        expected_order = [
            "app-02-02-2026-1.log",
            "app-02-02-2026-2.log",
            "app-02-03-2026-1.log",
            "app-02-03-2026-2.log",
        ]

        for i, expected_name in enumerate(expected_order):
            assert sorted_files[i].path.name == expected_name

    def test_files_without_pattern_at_end(self) -> None:
        """Test files without date/index pattern are placed at start of their directory."""
        files = [
            self.create_file_meta("tug-02-02-2026-1.log"),
            self.create_file_meta("unknown.log"),
            self.create_file_meta("tug-02-01-2026-1.log"),
            self.create_file_meta("application.log"),
        ]

        sorted_files = sort_files_by_date_and_index(files, fallback_sort_key="name")

        # First two should be undated files (alphabetically)
        assert sorted_files[0].path.name == "application.log"
        assert sorted_files[1].path.name == "unknown.log"

        # Last two should be dated files (chronologically)
        assert sorted_files[2].path.name == "tug-02-01-2026-1.log"
        assert sorted_files[3].path.name == "tug-02-02-2026-1.log"

    def test_empty_list(self) -> None:
        """Test sorting empty list returns empty list."""
        sorted_files = sort_files_by_date_and_index([])
        assert sorted_files == []

    def test_single_file(self) -> None:
        """Test sorting single file returns same file."""
        files = [self.create_file_meta("app-01-01-2026-1.log")]
        sorted_files = sort_files_by_date_and_index(files)
        assert len(sorted_files) == 1
        assert sorted_files[0].path.name == "app-01-01-2026-1.log"

    def test_original_list_unchanged(self) -> None:
        """Test that original list is not modified."""
        files = [
            self.create_file_meta("tug-02-03-2026-1.log"),
            self.create_file_meta("tug-02-01-2026-1.log"),
        ]
        original_order = [f.path.name for f in files]

        sorted_files = sort_files_by_date_and_index(files)

        # Original list should be unchanged
        assert [f.path.name for f in files] == original_order

        # Sorted list should be different
        assert sorted_files[0].path.name == "tug-02-01-2026-1.log"

    def test_multiple_formats_mixed(self) -> None:
        """Test sorting files with different date formats."""
        files = [
            self.create_file_meta("server_20260203_1.log"),  # YYYYMMDD
            self.create_file_meta("app-02-02-2026-1.log"),  # DD-MM-YYYY
            self.create_file_meta("log-2026-02-01-1.log"),  # YYYY-MM-DD
        ]

        sorted_files = sort_files_by_date_and_index(files)

        # All should be sorted by date regardless of format
        assert sorted_files[0].path.name == "log-2026-02-01-1.log"
        assert sorted_files[1].path.name == "app-02-02-2026-1.log"
        assert sorted_files[2].path.name == "server_20260203_1.log"

    def test_fallback_sort_by_name(self) -> None:
        """Test fallback sorting by name."""
        files = [
            self.create_file_meta("zebra.log"),
            self.create_file_meta("apple.log"),
            self.create_file_meta("banana.log"),
        ]

        sorted_files = sort_files_by_date_and_index(files, fallback_sort_key="name")

        assert sorted_files[0].path.name == "apple.log"
        assert sorted_files[1].path.name == "banana.log"
        assert sorted_files[2].path.name == "zebra.log"

    def test_fallback_sort_by_size(self) -> None:
        """Test fallback sorting by size."""
        files = [
            self.create_file_meta("large.log", size_bytes=3000),
            self.create_file_meta("small.log", size_bytes=1000),
            self.create_file_meta("medium.log", size_bytes=2000),
        ]

        sorted_files = sort_files_by_date_and_index(files, fallback_sort_key="size")

        assert sorted_files[0].path.name == "small.log"
        assert sorted_files[1].path.name == "medium.log"
        assert sorted_files[2].path.name == "large.log"

    def test_year_spanning(self) -> None:
        """Test sorting files across different years."""
        files = [
            self.create_file_meta("app-01-01-2027-1.log"),
            self.create_file_meta("app-31-12-2025-1.log"),
            self.create_file_meta("app-15-06-2026-1.log"),
        ]

        sorted_files = sort_files_by_date_and_index(files)

        assert sorted_files[0].path.name == "app-31-12-2025-1.log"
        assert sorted_files[1].path.name == "app-15-06-2026-1.log"
        assert sorted_files[2].path.name == "app-01-01-2027-1.log"

    def test_multiple_directories(self) -> None:
        """Test files from different directories are grouped and sorted."""
        files = [
            # Directory 2 - has earliest date overall
            FileMetadata(
                path=Path("/logs/dir2/app-01-01-2026-1.log"),
                size_bytes=1000,
                extension=".log",
                is_compressed=False,
            ),
            FileMetadata(
                path=Path("/logs/dir2/app-01-01-2026-2.log"),
                size_bytes=1000,
                extension=".log",
                is_compressed=False,
            ),
            # Directory 1 - has later dates
            FileMetadata(
                path=Path("/logs/dir1/app-02-02-2026-1.log"),
                size_bytes=1000,
                extension=".log",
                is_compressed=False,
            ),
            FileMetadata(
                path=Path("/logs/dir1/app-02-02-2026-2.log"),
                size_bytes=1000,
                extension=".log",
                is_compressed=False,
            ),
            # Directory 1 - earlier file in same directory
            FileMetadata(
                path=Path("/logs/dir1/app-01-15-2026-1.log"),
                size_bytes=1000,
                extension=".log",
                is_compressed=False,
            ),
        ]

        sorted_files = sort_files_by_date_and_index(files)

        # Directory 2 should come first (earliest date: 2026-01-01)
        assert sorted_files[0].path == Path("/logs/dir2/app-01-01-2026-1.log")
        assert sorted_files[1].path == Path("/logs/dir2/app-01-01-2026-2.log")

        # Directory 1 should come second (earliest date: 2026-01-15)
        # Within dir1, files should be sorted by date/index
        assert sorted_files[2].path == Path("/logs/dir1/app-01-15-2026-1.log")
        assert sorted_files[3].path == Path("/logs/dir1/app-02-02-2026-1.log")
        assert sorted_files[4].path == Path("/logs/dir1/app-02-02-2026-2.log")

    def test_same_filename_different_directories(self) -> None:
        """Test files with same name in different directories are properly grouped."""
        files = [
            FileMetadata(
                path=Path("/logs/server1/app-12-15-2025-1.log.gz"),
                size_bytes=1000,
                extension=".log.gz",
                is_compressed=True,
            ),
            FileMetadata(
                path=Path("/logs/server2/app-12-15-2025-1.log.gz"),
                size_bytes=1000,
                extension=".log.gz",
                is_compressed=True,
            ),
            FileMetadata(
                path=Path("/logs/server1/app-12-15-2025-2.log.gz"),
                size_bytes=1000,
                extension=".log.gz",
                is_compressed=True,
            ),
            FileMetadata(
                path=Path("/logs/server2/app-12-16-2025-1.log.gz"),
                size_bytes=1000,
                extension=".log.gz",
                is_compressed=True,
            ),
        ]

        sorted_files = sort_files_by_date_and_index(files)

        # Both directories have 2025-12-15 as earliest, but we need consistent ordering
        # Files from same directory should be together and sorted by date/index
        dirs_seen = []
        for f in sorted_files:
            dir_name = f.path.parent
            if not dirs_seen or dirs_seen[-1] != dir_name:
                dirs_seen.append(dir_name)

        # Should have exactly 2 directory groups
        assert len(dirs_seen) == 2

        # Within each group, verify chronological order
        for i in range(len(sorted_files) - 1):
            if sorted_files[i].path.parent == sorted_files[i + 1].path.parent:
                # Same directory - should be in chronological order
                date1 = extract_date_and_index_from_filename(sorted_files[i].path.name)
                date2 = extract_date_and_index_from_filename(sorted_files[i + 1].path.name)
                if date1 and date2:
                    assert (date1[0], date1[1]) <= (date2[0], date2[1])
