"""
Text highlighting utilities for search matches.

This module provides functions to highlight matching patterns
in text using configurable markers.
"""

import re
from typing import List, Pattern


class TextHighlighter:
    """Highlights matching patterns in text.

    Uses markers to wrap matched text patterns, making them
    visually distinct in output. Supports both substring and
    regex matching with case sensitivity control.

    Attributes:
        start_marker: Text to insert before matches
        end_marker: Text to insert after matches

    Example:
        >>> highlighter = TextHighlighter()
        >>> text = "Error: Connection failed"
        >>> patterns = ["Error", "failed"]
        >>> highlighter.highlight(text, patterns, ignore_case=True)
        '<<<Error>>>: Connection <<<failed>>>'
    """

    DEFAULT_START_MARKER = "<<<"
    DEFAULT_END_MARKER = ">>>"

    def __init__(
        self, start_marker: str = DEFAULT_START_MARKER, end_marker: str = DEFAULT_END_MARKER
    ) -> None:
        """Initialize the highlighter.

        Args:
            start_marker: Text to insert before matches
            end_marker: Text to insert after matches
        """
        self.start_marker = start_marker
        self.end_marker = end_marker

    def highlight(
        self, text: str, patterns: List[str], ignore_case: bool = False, use_regex: bool = False
    ) -> str:
        """Highlight all occurrences of patterns in text.

        Args:
            text: The text to highlight
            patterns: List of patterns to find and highlight
            ignore_case: Whether to perform case-insensitive matching
            use_regex: Whether patterns are regular expressions

        Returns:
            Text with patterns wrapped in markers

        Note:
            - Patterns are highlighted in order provided
            - Already-highlighted text is not re-highlighted
            - Empty patterns are skipped
        """
        if not patterns or not text:
            return text

        result = text

        for pattern in patterns:
            if not pattern:
                continue

            if use_regex:
                result = self._highlight_regex(result, pattern, ignore_case)
            else:
                result = self._highlight_substring(result, pattern, ignore_case)

        return result

    def _highlight_substring(self, text: str, pattern: str, ignore_case: bool) -> str:
        """Highlight a substring pattern.

        Args:
            text: The text to highlight
            pattern: The substring pattern to find
            ignore_case: Whether to perform case-insensitive matching

        Returns:
            Text with pattern highlighted
        """
        if not pattern:
            return text

        # Build replacement with markers
        replacement = f"{self.start_marker}\\g<0>{self.end_marker}"

        # Escape special regex characters in pattern
        escaped_pattern = re.escape(pattern)

        # Create regex with appropriate flags
        flags = re.IGNORECASE if ignore_case else 0

        # Replace all occurrences
        try:
            result = re.sub(escaped_pattern, replacement, text, flags=flags)
            return result
        except re.error:
            # If regex fails, return original text
            return text

    def _highlight_regex(self, text: str, pattern: str, ignore_case: bool) -> str:
        """Highlight a regex pattern.

        Args:
            text: The text to highlight
            pattern: The regex pattern to find
            ignore_case: Whether to perform case-insensitive matching

        Returns:
            Text with pattern highlighted
        """
        if not pattern:
            return text

        # Build replacement with markers
        replacement = f"{self.start_marker}\\g<0>{self.end_marker}"

        # Create regex with appropriate flags
        flags = re.IGNORECASE if ignore_case else 0

        # Replace all occurrences
        try:
            result = re.sub(pattern, replacement, text, flags=flags)
            return result
        except re.error:
            # If regex fails, return original text
            return text

    def highlight_with_compiled_pattern(self, text: str, compiled_pattern: Pattern[str]) -> str:
        """Highlight using a pre-compiled regex pattern.

        Args:
            text: The text to highlight
            compiled_pattern: Pre-compiled regex pattern

        Returns:
            Text with pattern highlighted
        """
        replacement = f"{self.start_marker}\\g<0>{self.end_marker}"

        try:
            result = compiled_pattern.sub(replacement, text)
            return result
        except Exception:
            # If highlighting fails, return original text
            return text


def highlight_text(
    text: str,
    patterns: List[str],
    ignore_case: bool = False,
    use_regex: bool = False,
    start_marker: str = TextHighlighter.DEFAULT_START_MARKER,
    end_marker: str = TextHighlighter.DEFAULT_END_MARKER,
) -> str:
    """Convenience function to highlight text.

    Args:
        text: The text to highlight
        patterns: List of patterns to find and highlight
        ignore_case: Whether to perform case-insensitive matching
        use_regex: Whether patterns are regular expressions
        start_marker: Text to insert before matches
        end_marker: Text to insert after matches

    Returns:
        Text with patterns wrapped in markers

    Example:
        >>> highlight_text("Error occurred", ["Error"], ignore_case=True)
        '<<<Error>>> occurred'
    """
    highlighter = TextHighlighter(start_marker, end_marker)
    return highlighter.highlight(text, patterns, ignore_case, use_regex)
