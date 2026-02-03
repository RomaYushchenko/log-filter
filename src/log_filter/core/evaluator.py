"""Evaluator for boolean search expressions."""

import re
from typing import Pattern

from ..domain.models import ASTNode
from .exceptions import ConfigurationError, EvaluationError


def validate_regex_pattern(pattern: str, ignore_case: bool = False) -> None:
    """Validate a regex pattern to ensure it can be compiled.

    This function validates regex patterns during initialization to fail fast
    and provide better error messages before processing begins.

    Args:
        pattern: The regex pattern string to validate
        ignore_case: Whether to validate with IGNORECASE flag

    Raises:
        ConfigurationError: If the pattern is invalid

    Example:
        >>> validate_regex_pattern(r"\\d+")  # Pattern for one or more digits
        # No error - pattern is valid

        >>> validate_regex_pattern(r"[unclosed")
        # Raises ConfigurationError
    """
    if not pattern:
        raise ConfigurationError("Empty regex pattern is not allowed")

    flags = re.IGNORECASE if ignore_case else 0

    try:
        re.compile(pattern, flags)
    except re.error as e:
        raise ConfigurationError(
            f"Invalid regex pattern '{pattern}': {e}. "
            f"Please check the pattern syntax and try again."
        ) from e


def compile_patterns_from_ast(ast: ASTNode, ignore_case: bool = False) -> dict[str, Pattern[str]]:
    """Pre-compile all regex patterns from an AST with validation.

    This function extracts all WORD nodes from the AST and compiles
    them as regex patterns. All patterns are validated upfront to fail fast
    if any pattern is invalid, providing better error messages before processing.

    Args:
        ast: The AST to extract patterns from
        ignore_case: Whether to compile with IGNORECASE flag

    Returns:
        Dictionary mapping pattern strings to compiled regex Pattern objects

    Raises:
        ConfigurationError: If any pattern is invalid or empty

    Note:
        - Empty patterns raise ConfigurationError
        - Invalid patterns raise ConfigurationError with detailed message
        - Duplicate patterns are compiled only once
    """
    patterns: dict[str, Pattern[str]] = {}
    flags = re.IGNORECASE if ignore_case else 0

    def collect_and_compile(node: ASTNode) -> None:
        """Recursively collect and compile patterns with validation."""
        if not node or len(node) == 0:
            return

        node_type = node[0]

        if node_type == "WORD" and len(node) >= 2:
            pattern_str = node[1]
            if pattern_str and pattern_str not in patterns:
                # Validate pattern before compilation
                validate_regex_pattern(pattern_str, ignore_case)
                patterns[pattern_str] = re.compile(pattern_str, flags)

        elif node_type in ("AND", "OR") and len(node) >= 3:
            collect_and_compile(node[1])
            collect_and_compile(node[2])

        elif node_type == "NOT" and len(node) >= 2:
            collect_and_compile(node[1])

    collect_and_compile(ast)
    return patterns


class ExpressionEvaluator:
    """Evaluates boolean expressions (AST) against text.

    The evaluator supports:
    - Boolean operators: AND, OR, NOT
    - Case-sensitive and case-insensitive matching
    - Regular expression and substring matching
    - Word boundary matching (exact words only)
    - Quote character stripping (for structured data)
    """

    def __init__(
        self,
        ignore_case: bool = False,
        use_regex: bool = False,
        word_boundary: bool = False,
        strip_quotes: bool = False,
        compiled_patterns: dict[str, Pattern[str]] | None = None,
    ) -> None:
        """Initialize evaluator.

        Args:
            ignore_case: Whether to perform case-insensitive matching
            use_regex: Whether to interpret search terms as regular expressions
            word_boundary: Whether to match whole words only (not substrings)
            strip_quotes: Whether to strip quote characters before matching
            compiled_patterns: Pre-compiled regex patterns (for performance)
        """
        self.ignore_case = ignore_case
        self.use_regex = use_regex
        self.word_boundary = word_boundary
        self.strip_quotes = strip_quotes
        self.compiled_patterns = compiled_patterns or {}
        self._regex_flags = re.IGNORECASE if ignore_case else 0
        # Characters to strip when strip_quotes is enabled
        self._quote_chars = ['"', "'", "`"]
        # Performance optimization: cache normalized patterns for substring search
        # This avoids calling str.lower() on patterns for every match
        self._normalized_patterns: dict[str, str] = {}

    def evaluate(self, ast: ASTNode, text: str) -> bool:
        """Evaluate an AST node against text.

        Args:
            ast: The AST node to evaluate
            text: The text to search in

        Returns:
            True if the expression matches the text, False otherwise

        Raises:
            EvaluationError: If evaluation fails
        """
        try:
            return self._evaluate_node(ast, text)
        except Exception as e:
            if isinstance(e, EvaluationError):
                raise
            raise EvaluationError(f"Evaluation failed: {e}") from e

    def _evaluate_node(self, node: ASTNode, text: str) -> bool:
        """Recursively evaluate an AST node.

        Args:
            node: The AST node
            text: The text to search in

        Returns:
            Boolean result of evaluation
        """
        if not node or len(node) == 0:
            raise EvaluationError("Empty AST node")

        node_type = node[0]

        if node_type == "WORD":
            if len(node) != 2:
                raise EvaluationError(f"Invalid WORD node: {node}")
            pattern = node[1]
            return self._match_pattern(pattern, text)

        elif node_type == "NOT":
            if len(node) != 2:
                raise EvaluationError(f"Invalid NOT node: {node}")
            return not self._evaluate_node(node[1], text)

        elif node_type == "AND":
            if len(node) != 3:
                raise EvaluationError(f"Invalid AND node: {node}")
            return self._evaluate_node(node[1], text) and self._evaluate_node(node[2], text)

        elif node_type == "OR":
            if len(node) != 3:
                raise EvaluationError(f"Invalid OR node: {node}")
            return self._evaluate_node(node[1], text) or self._evaluate_node(node[2], text)

        else:
            raise EvaluationError(f"Unknown node type: {node_type}")

    def _match_pattern(self, pattern: str, text: str) -> bool:
        """Match a pattern against text.

        Args:
            pattern: The search pattern
            text: The text to search in

        Returns:
            True if pattern matches, False otherwise
        """
        if not pattern:
            return False

        # Apply quote stripping if enabled
        if self.strip_quotes:
            pattern = self._strip_quotes(pattern)
            text = self._strip_quotes(text)

        if self.use_regex:
            return self._match_regex(pattern, text)
        else:
            return self._match_substring(pattern, text)

    def _match_regex(self, pattern: str, text: str) -> bool:
        """Match using regular expression with pre-compiled pattern optimization.

        Performance optimization: Prefers pre-compiled patterns but supports
        fallback compilation for backward compatibility. Pre-compiled patterns
        are significantly faster for repeated evaluations.

        Args:
            pattern: The regex pattern (preferably pre-compiled)
            text: The text to search in

        Returns:
            True if pattern matches, False otherwise

        Raises:
            EvaluationError: If pattern compilation or matching fails
        """
        try:
            # Try to use pre-compiled pattern first (fast path)
            if pattern in self.compiled_patterns:
                regex = self.compiled_patterns[pattern]
            else:
                # Fallback: compile on-demand (for backward compatibility)
                # This is slower but maintains compatibility with code that
                # doesn't pre-compile patterns
                regex = re.compile(pattern, self._regex_flags)
                # Cache for future use
                self.compiled_patterns[pattern] = regex

            return regex.search(text) is not None

        except re.error as e:
            raise EvaluationError(f"Invalid regex pattern '{pattern}': {e}") from e

    def _match_substring(self, pattern: str, text: str) -> bool:
        """Match using substring search.

        Performance optimization: Caches normalized patterns to avoid repeated
        string allocations. Uses str.casefold() for better Unicode support.

        Args:
            pattern: The substring to find
            text: The text to search in

        Returns:
            True if substring found, False otherwise
        """
        if self.word_boundary:
            # Use regex word boundary matching
            flags = re.IGNORECASE if self.ignore_case else 0
            # Escape special regex chars in pattern, then add word boundaries
            escaped_pattern = re.escape(pattern)
            try:
                regex = re.compile(rf"\b{escaped_pattern}\b", flags)
                return regex.search(text) is not None
            except re.error:
                # Fallback to substring matching if regex fails
                if self.ignore_case:
                    # Cache normalized pattern for repeated use
                    if pattern not in self._normalized_patterns:
                        self._normalized_patterns[pattern] = pattern.casefold()
                    return self._normalized_patterns[pattern] in text.casefold()
                return pattern in text

        # Optimized substring matching with pattern caching
        if self.ignore_case:
            # Cache the normalized pattern to avoid repeated casefold() calls
            # str.casefold() is more robust than lower() for Unicode text
            if pattern not in self._normalized_patterns:
                self._normalized_patterns[pattern] = pattern.casefold()
            return self._normalized_patterns[pattern] in text.casefold()

        return pattern in text

    def extract_patterns(self, ast: ASTNode) -> list[str]:
        """Extract all search patterns from an AST.

        Args:
            ast: The AST to extract patterns from

        Returns:
            List of search patterns
        """
        patterns: list[str] = []
        self._collect_patterns(ast, patterns)
        return patterns

    def _collect_patterns(self, node: ASTNode, patterns: list[str]) -> None:
        """Recursively collect patterns from AST nodes.

        Args:
            node: The AST node
            patterns: List to accumulate patterns
        """
        if not node or len(node) == 0:
            return

        node_type = node[0]

        if node_type == "WORD":
            if len(node) >= 2:
                patterns.append(node[1])

        elif node_type in ("AND", "OR"):
            if len(node) >= 3:
                self._collect_patterns(node[1], patterns)
                self._collect_patterns(node[2], patterns)

        elif node_type == "NOT":
            if len(node) >= 2:
                self._collect_patterns(node[1], patterns)

    def _strip_quotes(self, text: str) -> str:
        """Strip quote characters from text.

        Args:
            text: Text to strip quotes from

        Returns:
            Text with quotes removed
        """
        for quote in self._quote_chars:
            text = text.replace(quote, "")
        return text


def evaluate(
    ast: ASTNode,
    text: str,
    ignore_case: bool = False,
    use_regex: bool = False,
    word_boundary: bool = False,
    strip_quotes: bool = False,
) -> bool:
    """Convenience function to evaluate an AST against text.

    Args:
        ast: The AST node to evaluate
        text: The text to search in
        ignore_case: Whether to perform case-insensitive matching
        use_regex: Whether to interpret search terms as regular expressions
        word_boundary: Whether to match whole words only (not substrings)
        strip_quotes: Whether to strip quote characters before matching

    Returns:
        True if the expression matches the text, False otherwise

    Raises:
        EvaluationError: If evaluation fails
    """
    evaluator = ExpressionEvaluator(
        ignore_case=ignore_case,
        use_regex=use_regex,
        word_boundary=word_boundary,
        strip_quotes=strip_quotes,
    )
    return evaluator.evaluate(ast, text)
