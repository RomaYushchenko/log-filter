"""
Unit tests for log level normalization in StreamingRecordParser.

Tests the level normalization feature that converts single-character
abbreviations (E, W, I, D, T, F) to full level names (ERROR, WARN, INFO, etc.).
"""

import pytest

from log_filter.processing.record_parser import StreamingRecordParser


class TestLevelNormalization:
    """Test log level normalization."""

    def test_normalize_single_char_levels(self):
        """Test normalization of single-character levels."""
        parser = StreamingRecordParser(normalize_levels=True)

        assert parser._normalize_level("E") == "ERROR"
        assert parser._normalize_level("W") == "WARN"
        assert parser._normalize_level("I") == "INFO"
        assert parser._normalize_level("D") == "DEBUG"
        assert parser._normalize_level("T") == "TRACE"
        assert parser._normalize_level("F") == "FATAL"

    def test_normalize_full_levels(self):
        """Test full level names pass through unchanged."""
        parser = StreamingRecordParser(normalize_levels=True)

        assert parser._normalize_level("ERROR") == "ERROR"
        assert parser._normalize_level("WARN") == "WARN"
        assert parser._normalize_level("INFO") == "INFO"
        assert parser._normalize_level("DEBUG") == "DEBUG"
        assert parser._normalize_level("TRACE") == "TRACE"
        assert parser._normalize_level("FATAL") == "FATAL"
        assert parser._normalize_level("CRITICAL") == "CRITICAL"

    def test_normalize_warning_variant(self):
        """Test WARNING is normalized to WARN."""
        parser = StreamingRecordParser(normalize_levels=True)
        assert parser._normalize_level("WARNING") == "WARN"

    def test_normalize_case_insensitive(self):
        """Test normalization is case-insensitive."""
        parser = StreamingRecordParser(normalize_levels=True)

        # Lowercase
        assert parser._normalize_level("e") == "ERROR"
        assert parser._normalize_level("w") == "WARN"
        assert parser._normalize_level("i") == "INFO"

        # Mixed case
        assert parser._normalize_level("Error") == "ERROR"
        assert parser._normalize_level("Warn") == "WARN"
        assert parser._normalize_level("Info") == "INFO"

    def test_normalization_disabled(self):
        """Test normalization can be disabled."""
        parser = StreamingRecordParser(normalize_levels=False)

        # Abbreviated levels should pass through unchanged
        assert parser._normalize_level("E") == "E"
        assert parser._normalize_level("W") == "W"
        assert parser._normalize_level("I") == "I"

        # Full levels should also pass through unchanged
        assert parser._normalize_level("ERROR") == "ERROR"
        assert parser._normalize_level("WARN") == "WARN"

    def test_unknown_level_unchanged(self):
        """Test unknown levels pass through unchanged."""
        parser = StreamingRecordParser(normalize_levels=True)

        # Custom levels not in mapping should pass through
        assert parser._normalize_level("CUSTOM") == "CUSTOM"
        assert parser._normalize_level("VERBOSE") == "VERBOSE"
        assert parser._normalize_level("X") == "X"

    def test_parse_abbreviated_levels(self):
        """Test parsing logs with abbreviated levels."""
        parser = StreamingRecordParser(normalize_levels=True)

        lines = [
            "2025-01-08 10:00:00.000+0000 E Error message",
            "2025-01-08 10:00:01.000+0000 W Warning message",
            "2025-01-08 10:00:02.000+0000 I Info message",
            "2025-01-08 10:00:03.000+0000 D Debug message",
        ]

        records = list(parser.parse_lines(iter(lines)))

        assert len(records) == 4
        assert records[0].level == "ERROR"
        assert records[1].level == "WARN"
        assert records[2].level == "INFO"
        assert records[3].level == "DEBUG"

    def test_parse_full_level_names(self):
        """Test parsing logs with full level names."""
        parser = StreamingRecordParser(normalize_levels=True)

        lines = [
            "2025-01-08 10:00:00.000+0000 ERROR Error message",
            "2025-01-08 10:00:01.000+0000 WARN Warning message",
            "2025-01-08 10:00:02.000+0000 INFO Info message",
        ]

        records = list(parser.parse_lines(iter(lines)))

        assert len(records) == 3
        assert records[0].level == "ERROR"
        assert records[1].level == "WARN"
        assert records[2].level == "INFO"

    def test_parse_mixed_level_formats(self):
        """Test parsing logs with mixed level formats (abbreviated and full)."""
        parser = StreamingRecordParser(normalize_levels=True)

        lines = [
            "2025-01-08 10:00:00.000+0000 ERROR Full level name",
            "2025-01-08 10:00:01.000+0000 E Abbreviated level",
            "2025-01-08 10:00:02.000+0000 WARN Another full name",
            "2025-01-08 10:00:03.000+0000 W Another abbreviation",
            "2025-01-08 10:00:04.000+0000 WARNING Third variant",
        ]

        records = list(parser.parse_lines(iter(lines)))

        assert len(records) == 5
        assert records[0].level == "ERROR"
        assert records[1].level == "ERROR"  # E normalized to ERROR
        assert records[2].level == "WARN"
        assert records[3].level == "WARN"  # W normalized to WARN
        assert records[4].level == "WARN"  # WARNING normalized to WARN

    def test_parse_with_normalization_disabled(self):
        """Test parsing preserves raw levels when normalization is disabled."""
        parser = StreamingRecordParser(normalize_levels=False)

        lines = [
            "2025-01-08 10:00:00.000+0000 E Error message",
            "2025-01-08 10:00:01.000+0000 ERROR Error message",
        ]

        records = list(parser.parse_lines(iter(lines)))

        assert len(records) == 2
        assert records[0].level == "E"  # Raw abbreviated level
        assert records[1].level == "ERROR"  # Raw full level

    def test_original_content_preserved(self):
        """Test that original log content is preserved regardless of normalization."""
        parser = StreamingRecordParser(normalize_levels=True)

        original_line = "2025-01-08 10:00:00.000+0000 E Database connection failed"
        lines = [original_line]

        records = list(parser.parse_lines(iter(lines)))

        assert len(records) == 1
        # Level is normalized
        assert records[0].level == "ERROR"
        # But content still has original 'E'
        assert records[0].content == original_line
        assert " E " in records[0].content
        assert "ERROR" not in records[0].content  # Content not modified

    def test_multiline_record_with_abbreviated_level(self):
        """Test multiline log records with abbreviated levels."""
        parser = StreamingRecordParser(normalize_levels=True)

        lines = [
            "2025-01-08 10:00:00.000+0000 E Database connection failed",
            "  Stack trace line 1",
            "  Stack trace line 2",
            "2025-01-08 10:00:01.000+0000 I Application recovered",
        ]

        records = list(parser.parse_lines(iter(lines)))

        assert len(records) == 2
        assert records[0].level == "ERROR"
        assert records[0].line_count == 3
        assert records[1].level == "INFO"
        assert records[1].line_count == 1


class TestLevelNormalizationMapping:
    """Test the LEVEL_NORMALIZATION mapping dictionary."""

    def test_mapping_contains_standard_abbreviations(self):
        """Test mapping contains all standard single-char abbreviations."""
        mapping = StreamingRecordParser.LEVEL_NORMALIZATION

        assert mapping["E"] == "ERROR"
        assert mapping["W"] == "WARN"
        assert mapping["I"] == "INFO"
        assert mapping["D"] == "DEBUG"
        assert mapping["T"] == "TRACE"
        assert mapping["F"] == "FATAL"

    def test_mapping_contains_full_names(self):
        """Test mapping contains full level names for passthrough."""
        mapping = StreamingRecordParser.LEVEL_NORMALIZATION

        assert mapping["ERROR"] == "ERROR"
        assert mapping["WARN"] == "WARN"
        assert mapping["WARNING"] == "WARN"
        assert mapping["INFO"] == "INFO"
        assert mapping["DEBUG"] == "DEBUG"
        assert mapping["TRACE"] == "TRACE"
        assert mapping["FATAL"] == "FATAL"
        assert mapping["CRITICAL"] == "CRITICAL"

    def test_mapping_is_immutable(self):
        """Test that LEVEL_NORMALIZATION is a class attribute (not modified per instance)."""
        parser1 = StreamingRecordParser()
        parser2 = StreamingRecordParser()

        # Should be the same object (class attribute)
        assert parser1.LEVEL_NORMALIZATION is parser2.LEVEL_NORMALIZATION


class TestParserInitialization:
    """Test StreamingRecordParser initialization with normalize_levels parameter."""

    def test_default_normalization_enabled(self):
        """Test normalization is enabled by default."""
        parser = StreamingRecordParser()
        assert parser.normalize_levels is True

    def test_explicit_normalization_enabled(self):
        """Test explicitly enabling normalization."""
        parser = StreamingRecordParser(normalize_levels=True)
        assert parser.normalize_levels is True

    def test_explicit_normalization_disabled(self):
        """Test explicitly disabling normalization."""
        parser = StreamingRecordParser(normalize_levels=False)
        assert parser.normalize_levels is False

    def test_normalization_with_other_parameters(self):
        """Test normalize_levels works with other initialization parameters."""
        parser = StreamingRecordParser(max_record_size_bytes=1024 * 100, normalize_levels=False)

        assert parser.normalize_levels is False
        assert parser.max_record_size_bytes == 1024 * 100
