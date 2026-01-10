"""
Tests for text highlighting utilities.
"""

import pytest

from log_filter.utils.highlighter import TextHighlighter, highlight_text


class TestTextHighlighter:
    """Tests for TextHighlighter class."""

    def test_default_markers(self) -> None:
        """Test highlighter uses default markers."""
        highlighter = TextHighlighter()
        assert highlighter.start_marker == "<<<"
        assert highlighter.end_marker == ">>>"

    def test_custom_markers(self) -> None:
        """Test highlighter with custom markers."""
        highlighter = TextHighlighter(start_marker="**", end_marker="**")
        assert highlighter.start_marker == "**"
        assert highlighter.end_marker == "**"

    def test_highlight_single_pattern_case_sensitive(self) -> None:
        """Test highlighting single pattern case-sensitively."""
        highlighter = TextHighlighter()
        text = "Error occurred in the system"
        result = highlighter.highlight(text, ["Error"], ignore_case=False)
        assert result == "<<<Error>>> occurred in the system"

    def test_highlight_single_pattern_case_insensitive(self) -> None:
        """Test highlighting single pattern case-insensitively."""
        highlighter = TextHighlighter()
        text = "Error occurred in the system"
        result = highlighter.highlight(text, ["error"], ignore_case=True)
        assert result == "<<<Error>>> occurred in the system"

    def test_highlight_multiple_patterns(self) -> None:
        """Test highlighting multiple patterns."""
        highlighter = TextHighlighter()
        text = "Error occurred while connecting"
        result = highlighter.highlight(text, ["Error", "connecting"], ignore_case=False)
        assert result == "<<<Error>>> occurred while <<<connecting>>>"

    def test_highlight_pattern_multiple_times(self) -> None:
        """Test highlighting pattern that appears multiple times."""
        highlighter = TextHighlighter()
        text = "Error: connection error detected"
        result = highlighter.highlight(text, ["error"], ignore_case=True)
        assert result == "<<<Error>>>: connection <<<error>>> detected"

    def test_highlight_with_regex(self) -> None:
        """Test highlighting with regex patterns."""
        highlighter = TextHighlighter()
        text = "Error code 404 detected"
        result = highlighter.highlight(text, [r"\d+"], use_regex=True)
        assert result == "Error code <<<404>>> detected"

    def test_highlight_empty_text(self) -> None:
        """Test highlighting empty text."""
        highlighter = TextHighlighter()
        result = highlighter.highlight("", ["Error"], ignore_case=False)
        assert result == ""

    def test_highlight_empty_patterns(self) -> None:
        """Test highlighting with no patterns."""
        highlighter = TextHighlighter()
        text = "Error occurred"
        result = highlighter.highlight(text, [], ignore_case=False)
        assert result == "Error occurred"

    def test_highlight_none_patterns(self) -> None:
        """Test highlighting with None pattern in list."""
        highlighter = TextHighlighter()
        text = "Error occurred"
        result = highlighter.highlight(text, ["Error", None, "occurred"], ignore_case=False)
        assert result == "<<<Error>>> <<<occurred>>>"

    def test_highlight_pattern_not_found(self) -> None:
        """Test highlighting pattern that doesn't exist."""
        highlighter = TextHighlighter()
        text = "Everything is fine"
        result = highlighter.highlight(text, ["Error"], ignore_case=False)
        assert result == "Everything is fine"

    def test_highlight_with_special_regex_chars(self) -> None:
        """Test highlighting with special regex characters (non-regex mode)."""
        highlighter = TextHighlighter()
        text = "Found (error) in logs"
        result = highlighter.highlight(text, ["(error)"], ignore_case=False, use_regex=False)
        assert result == "Found <<<(error)>>> in logs"

    def test_highlight_regex_with_case_insensitive(self) -> None:
        """Test regex highlighting with case insensitivity."""
        highlighter = TextHighlighter()
        text = "ERROR Code 500 error"
        result = highlighter.highlight(text, [r"error"], use_regex=True, ignore_case=True)
        assert result == "<<<ERROR>>> Code 500 <<<error>>>"

    def test_highlight_overlapping_patterns(self) -> None:
        """Test highlighting with potentially overlapping patterns."""
        highlighter = TextHighlighter()
        text = "Error message: ErrorCode"
        result = highlighter.highlight(text, ["Error"], ignore_case=False)
        # Both instances should be highlighted
        assert result.count("<<<Error>>>") == 2

    def test_highlight_with_custom_markers(self) -> None:
        """Test highlighting with custom markers."""
        highlighter = TextHighlighter(start_marker="[[", end_marker="]]")
        text = "Error occurred"
        result = highlighter.highlight(text, ["Error"], ignore_case=False)
        assert result == "[[Error]] occurred"

    def test_highlight_invalid_regex(self) -> None:
        """Test highlighting with invalid regex (should return original text)."""
        highlighter = TextHighlighter()
        text = "Error occurred"
        result = highlighter.highlight(text, ["[invalid"], use_regex=True)
        # Should return original text if regex is invalid
        assert result == "Error occurred"


class TestHighlightTextFunction:
    """Tests for highlight_text convenience function."""

    def test_highlight_text_default_markers(self) -> None:
        """Test highlight_text with default markers."""
        text = "Error in system"
        result = highlight_text(text, ["Error"])
        assert result == "<<<Error>>> in system"

    def test_highlight_text_custom_markers(self) -> None:
        """Test highlight_text with custom markers."""
        text = "Error in system"
        result = highlight_text(text, ["Error"], start_marker="**", end_marker="**")
        assert result == "**Error** in system"

    def test_highlight_text_case_insensitive(self) -> None:
        """Test highlight_text with case insensitivity."""
        text = "ERROR in system"
        result = highlight_text(text, ["error"], ignore_case=True)
        assert result == "<<<ERROR>>> in system"

    def test_highlight_text_regex(self) -> None:
        """Test highlight_text with regex."""
        text = "Code 404 not found"
        result = highlight_text(text, [r"\d+"], use_regex=True)
        assert result == "Code <<<404>>> not found"

    def test_highlight_text_multiple_patterns(self) -> None:
        """Test highlight_text with multiple patterns."""
        text = "Error: connection failed"
        result = highlight_text(text, ["Error", "failed"])
        assert result == "<<<Error>>>: connection <<<failed>>>"


class TestHighlighterIntegration:
    """Integration tests for highlighter."""

    def test_real_log_message_highlighting(self) -> None:
        """Test highlighting in real log message."""
        highlighter = TextHighlighter()
        log_msg = "2025-01-08 10:30:45 [ERROR] Connection to database failed: timeout"
        patterns = ["ERROR", "failed"]
        result = highlighter.highlight(log_msg, patterns, ignore_case=True)
        assert "<<<ERROR>>>" in result
        assert "<<<failed>>>" in result

    def test_complex_boolean_expression_highlighting(self) -> None:
        """Test highlighting for complex boolean expression match."""
        highlighter = TextHighlighter()
        log_msg = "ERROR: Kafka broker connection timeout on host kafka-prod-01"
        patterns = ["ERROR", "Kafka", "timeout"]
        result = highlighter.highlight(log_msg, patterns, ignore_case=False)
        assert "<<<ERROR>>>:" in result
        assert "<<<Kafka>>>" in result
        assert "<<<timeout>>>" in result

    def test_regex_pattern_in_log(self) -> None:
        """Test regex pattern matching in log message."""
        highlighter = TextHighlighter()
        log_msg = "Request failed with status code 500 after 3 retries"
        patterns = [r"\d+"]
        result = highlighter.highlight(log_msg, patterns, use_regex=True)
        assert "<<<500>>>" in result
        assert "<<<3>>>" in result

    def test_no_highlighting_when_no_match(self) -> None:
        """Test no highlighting when patterns don't match."""
        highlighter = TextHighlighter()
        log_msg = "INFO: System started successfully"
        patterns = ["ERROR", "WARNING"]
        result = highlighter.highlight(log_msg, patterns, ignore_case=False)
        assert result == log_msg  # Unchanged
        assert "<<<" not in result

    def test_case_sensitivity_matters(self) -> None:
        """Test that case sensitivity is respected."""
        highlighter = TextHighlighter()
        log_msg = "Error and ERROR both present"

        # Case sensitive - only exact match
        result_sensitive = highlighter.highlight(log_msg, ["Error"], ignore_case=False)
        assert result_sensitive == "<<<Error>>> and ERROR both present"

        # Case insensitive - both match
        result_insensitive = highlighter.highlight(log_msg, ["Error"], ignore_case=True)
        assert result_insensitive == "<<<Error>>> and <<<ERROR>>> both present"
