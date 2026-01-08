"""
Unit tests for progress tracking module.

Tests ProgressTracker and ProgressCounter classes:
- Progress bar display for files and records
- Manual progress counter with context manager
- Enable/disable functionality
- Description and formatting
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from log_filter.domain.models import FileMetadata, LogRecord
from log_filter.utils.progress import ProgressCounter, ProgressTracker


class TestProgressTracker:
    """Test ProgressTracker wrapper."""

    def test_initialization_default(self):
        """Test tracker initialization with defaults."""
        tracker = ProgressTracker()
        
        assert tracker.enable is True
        assert tracker.desc_width == 25

    def test_initialization_disabled(self):
        """Test tracker initialization disabled."""
        tracker = ProgressTracker(enable=False)
        
        assert tracker.enable is False

    def test_initialization_custom_width(self):
        """Test tracker initialization with custom width."""
        tracker = ProgressTracker(desc_width=30)
        
        assert tracker.desc_width == 30

    def test_track_files_disabled(self):
        """Test track_files with progress disabled."""
        tracker = ProgressTracker(enable=False)
        
        files = [
            FileMetadata(
                path=Path(f"file{i}.log"),
                size_bytes=100,
                extension=".log",
                is_compressed=False,
                is_readable=True
            )
            for i in range(3)
        ]
        
        result = list(tracker.track_files(iter(files), total=3))
        
        assert len(result) == 3
        assert result == files

    def test_track_files_enabled(self):
        """Test track_files with progress enabled."""
        tracker = ProgressTracker(enable=True)
        
        files = [
            FileMetadata(
                path=Path(f"file{i}.log"),
                size_bytes=100,
                extension=".log",
                is_compressed=False,
                is_readable=True
            )
            for i in range(3)
        ]
        
        with patch("log_filter.utils.progress.tqdm") as mock_tqdm:
            # Create mock progress bar
            mock_pbar = Mock()
            mock_pbar.set_postfix_str = Mock()
            mock_pbar.__iter__ = Mock(return_value=iter(files))
            mock_tqdm.return_value.__enter__.return_value = mock_pbar
            mock_tqdm.return_value.__exit__.return_value = None
            
            result = list(tracker.track_files(iter(files), total=3))
            
            assert len(result) == 3
            mock_tqdm.assert_called_once()

    def test_track_files_description(self):
        """Test track_files with custom description."""
        tracker = ProgressTracker(enable=True)
        
        files = [
            FileMetadata(
                path=Path("file.log"),
                size_bytes=100,
                extension=".log",
                is_compressed=False,
                is_readable=True
            )
        ]
        
        with patch("log_filter.utils.progress.tqdm") as mock_tqdm:
            mock_pbar = Mock()
            mock_pbar.set_postfix_str = Mock()
            mock_pbar.__iter__ = Mock(return_value=iter(files))
            mock_tqdm.return_value.__enter__.return_value = mock_pbar
            mock_tqdm.return_value.__exit__.return_value = None
            
            list(tracker.track_files(iter(files), total=1, desc="Scanning"))
            
            call_kwargs = mock_tqdm.call_args[1]
            assert "Scanning" in call_kwargs["desc"]

    def test_track_records_disabled(self):
        """Test track_records with progress disabled."""
        tracker = ProgressTracker(enable=False)
        
        records = [
            LogRecord(
                content=f"Record {i}",
                first_line=f"Record {i}",
                source_file=Path("test.log"),
                start_line=i,
                end_line=i,
                timestamp=datetime.now(),
                size_bytes=20
            )
            for i in range(5)
        ]
        
        result = list(tracker.track_records(iter(records), total=5))
        
        assert len(result) == 5
        assert result == records

    def test_track_records_enabled(self):
        """Test track_records with progress enabled."""
        tracker = ProgressTracker(enable=True)
        
        records = [
            LogRecord(
                content=f"Record {i}",
                first_line=f"Record {i}",
                source_file=Path("test.log"),
                start_line=i,
                end_line=i,
                timestamp=datetime.now(),
                size_bytes=20
            )
            for i in range(5)
        ]
        
        with patch("log_filter.utils.progress.tqdm") as mock_tqdm:
            mock_tqdm.return_value.__enter__.return_value = iter(records)
            mock_tqdm.return_value.__exit__.return_value = None
            
            result = list(tracker.track_records(iter(records), total=5))
            
            assert len(result) == 5
            mock_tqdm.assert_called_once()
            call_kwargs = mock_tqdm.call_args[1]
            assert call_kwargs["unit"] == "rec"
            assert call_kwargs["unit_scale"] is True

    def test_track_generic_disabled(self):
        """Test track_generic with progress disabled."""
        tracker = ProgressTracker(enable=False)
        
        items = list(range(10))
        result = list(tracker.track_generic(iter(items), total=10))
        
        assert result == items

    def test_track_generic_enabled(self):
        """Test track_generic with progress enabled."""
        tracker = ProgressTracker(enable=True)
        
        items = list(range(10))
        
        with patch("log_filter.utils.progress.tqdm") as mock_tqdm:
            mock_tqdm.return_value.__enter__.return_value = iter(items)
            mock_tqdm.return_value.__exit__.return_value = None
            
            result = list(tracker.track_generic(iter(items), total=10, desc="Items", unit="item"))
            
            assert len(result) == 10
            mock_tqdm.assert_called_once()
            call_kwargs = mock_tqdm.call_args[1]
            assert call_kwargs["unit"] == "item"

    def test_create_counter_enabled(self):
        """Test create_counter with progress enabled."""
        tracker = ProgressTracker(enable=True)
        
        counter = tracker.create_counter(total=100, desc="Counter", unit="op")
        
        assert isinstance(counter, ProgressCounter)
        assert counter.enable is True
        assert counter._total == 100
        assert counter._unit == "op"

    def test_create_counter_disabled(self):
        """Test create_counter with progress disabled."""
        tracker = ProgressTracker(enable=False)
        
        counter = tracker.create_counter(total=100)
        
        assert isinstance(counter, ProgressCounter)
        assert counter.enable is False


class TestProgressCounter:
    """Test ProgressCounter manual counter."""

    def test_initialization(self):
        """Test counter initialization."""
        counter = ProgressCounter(
            enable=True,
            total=100,
            desc="Test",
            unit="item"
        )
        
        assert counter.enable is True
        assert counter._total == 100
        assert counter._desc == "Test"
        assert counter._unit == "item"
        assert counter._pbar is None

    def test_context_manager_enabled(self):
        """Test context manager with progress enabled."""
        counter = ProgressCounter(enable=True, total=100, desc="Test", unit="item")
        
        with patch("log_filter.utils.progress.tqdm") as mock_tqdm:
            mock_pbar = Mock()
            mock_tqdm.return_value = mock_pbar
            
            with counter as ctx:
                assert ctx is counter
                assert counter._pbar is mock_pbar
            
            mock_pbar.close.assert_called_once()

    def test_context_manager_disabled(self):
        """Test context manager with progress disabled."""
        counter = ProgressCounter(enable=False, total=100, desc="Test", unit="item")
        
        with counter as ctx:
            assert ctx is counter
            assert counter._pbar is None

    def test_update_enabled(self):
        """Test update with progress enabled."""
        counter = ProgressCounter(enable=True, total=100, desc="Test", unit="item")
        
        with patch("log_filter.utils.progress.tqdm") as mock_tqdm:
            mock_pbar = Mock()
            mock_tqdm.return_value = mock_pbar
            
            with counter:
                counter.update(5)
                counter.update(10)
            
            assert mock_pbar.update.call_count == 2
            mock_pbar.update.assert_any_call(5)
            mock_pbar.update.assert_any_call(10)

    def test_update_disabled(self):
        """Test update with progress disabled."""
        counter = ProgressCounter(enable=False, total=100, desc="Test", unit="item")
        
        with counter:
            counter.update(5)  # Should not raise error
            assert counter._pbar is None

    def test_update_default_increment(self):
        """Test update with default increment."""
        counter = ProgressCounter(enable=True, total=100, desc="Test", unit="item")
        
        with patch("log_filter.utils.progress.tqdm") as mock_tqdm:
            mock_pbar = Mock()
            mock_tqdm.return_value = mock_pbar
            
            with counter:
                counter.update()  # Default n=1
            
            mock_pbar.update.assert_called_once_with(1)

    def test_set_postfix_str_enabled(self):
        """Test set_postfix_str with progress enabled."""
        counter = ProgressCounter(enable=True, total=100, desc="Test", unit="item")
        
        with patch("log_filter.utils.progress.tqdm") as mock_tqdm:
            mock_pbar = Mock()
            mock_tqdm.return_value = mock_pbar
            
            with counter:
                counter.set_postfix_str("Status message")
            
            mock_pbar.set_postfix_str.assert_called_once_with("Status message", refresh=False)

    def test_set_postfix_str_disabled(self):
        """Test set_postfix_str with progress disabled."""
        counter = ProgressCounter(enable=False, total=100, desc="Test", unit="item")
        
        with counter:
            counter.set_postfix_str("Status")  # Should not raise error
            assert counter._pbar is None

    def test_set_description_enabled(self):
        """Test set_description with progress enabled."""
        counter = ProgressCounter(enable=True, total=100, desc="Test", unit="item")
        
        with patch("log_filter.utils.progress.tqdm") as mock_tqdm:
            mock_pbar = Mock()
            mock_tqdm.return_value = mock_pbar
            
            with counter:
                counter.set_description("New Description")
            
            assert mock_pbar.set_description.called

    def test_set_description_disabled(self):
        """Test set_description with progress disabled."""
        counter = ProgressCounter(enable=False, total=100, desc="Test", unit="item")
        
        with counter:
            counter.set_description("New")  # Should not raise error
            assert counter._pbar is None

    def test_context_manager_exception_handling(self):
        """Test that progress bar is closed even on exception."""
        counter = ProgressCounter(enable=True, total=100, desc="Test", unit="item")
        
        with patch("log_filter.utils.progress.tqdm") as mock_tqdm:
            mock_pbar = Mock()
            mock_tqdm.return_value = mock_pbar
            
            try:
                with counter:
                    raise RuntimeError("Test error")
            except RuntimeError:
                pass
            
            mock_pbar.close.assert_called_once()

    def test_multiple_updates_in_sequence(self):
        """Test multiple sequential updates."""
        counter = ProgressCounter(enable=True, total=100, desc="Test", unit="item")
        
        with patch("log_filter.utils.progress.tqdm") as mock_tqdm:
            mock_pbar = Mock()
            mock_tqdm.return_value = mock_pbar
            
            with counter:
                for i in range(10):
                    counter.update(1)
            
            assert mock_pbar.update.call_count == 10


class TestProgressTrackerIntegration:
    """Integration tests for progress tracking."""

    def test_track_files_with_long_filename(self):
        """Test tracking files with long filenames."""
        tracker = ProgressTracker(enable=True)
        
        files = [
            FileMetadata(
                path=Path("a" * 100 + ".log"),  # Very long filename
                size_bytes=100,
                extension=".log",
                is_compressed=False,
                is_readable=True
            )
        ]
        
        with patch("log_filter.utils.progress.tqdm") as mock_tqdm:
            mock_pbar = Mock()
            mock_pbar.set_postfix_str = Mock()
            mock_pbar.__iter__ = Mock(return_value=iter(files))
            mock_tqdm.return_value.__enter__.return_value = mock_pbar
            mock_tqdm.return_value.__exit__.return_value = None
            
            list(tracker.track_files(iter(files), total=1))
            
            # Should truncate to 30 chars
            assert mock_pbar.set_postfix_str.called

    def test_empty_iterator(self):
        """Test tracking empty iterator."""
        tracker = ProgressTracker(enable=True)
        
        result = list(tracker.track_generic(iter([]), total=0))
        
        assert result == []

    def test_none_total(self):
        """Test tracking with None total (unknown size)."""
        tracker = ProgressTracker(enable=True)
        
        items = [1, 2, 3]
        
        with patch("log_filter.utils.progress.tqdm") as mock_tqdm:
            mock_tqdm.return_value.__enter__.return_value = iter(items)
            mock_tqdm.return_value.__exit__.return_value = None
            
            result = list(tracker.track_generic(iter(items), total=None))
            
            assert len(result) == 3
            call_kwargs = mock_tqdm.call_args[1]
            assert call_kwargs["total"] is None
