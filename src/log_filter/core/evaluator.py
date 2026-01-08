"""Evaluator for boolean search expressions."""

import re
from typing import Pattern

from ..domain.models import ASTNode
from .exceptions import EvaluationError


def compile_patterns_from_ast(
    ast: ASTNode,
    ignore_case: bool = False
) -> dict[str, Pattern[str]]:
    """Pre-compile all regex patterns from an AST.
    
    This function extracts all WORD nodes from the AST and compiles
    them as regex patterns. This improves performance when evaluating
    the same AST multiple times against different text.
    
    Args:
        ast: The AST to extract patterns from
        ignore_case: Whether to compile with IGNORECASE flag
        
    Returns:
        Dictionary mapping pattern strings to compiled regex Pattern objects
        
    Note:
        - Invalid regex patterns are skipped (not compiled)
        - Empty patterns are skipped
        - Duplicate patterns are compiled only once
    """
    patterns: dict[str, Pattern[str]] = {}
    flags = re.IGNORECASE if ignore_case else 0
    
    def collect_and_compile(node: ASTNode) -> None:
        """Recursively collect and compile patterns."""
        if not node or len(node) == 0:
            return
        
        node_type = node[0]
        
        if node_type == "WORD" and len(node) >= 2:
            pattern_str = node[1]
            if pattern_str and pattern_str not in patterns:
                try:
                    patterns[pattern_str] = re.compile(pattern_str, flags)
                except re.error:
                    # Skip invalid regex patterns
                    pass
        
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
    """

    def __init__(
        self,
        ignore_case: bool = False,
        use_regex: bool = False,
        compiled_patterns: dict[str, Pattern[str]] | None = None,
    ) -> None:
        """Initialize evaluator.

        Args:
            ignore_case: Whether to perform case-insensitive matching
            use_regex: Whether to interpret search terms as regular expressions
            compiled_patterns: Pre-compiled regex patterns (for performance)
        """
        self.ignore_case = ignore_case
        self.use_regex = use_regex
        self.compiled_patterns = compiled_patterns or {}
        self._regex_flags = re.IGNORECASE if ignore_case else 0

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

        if self.use_regex:
            return self._match_regex(pattern, text)
        else:
            return self._match_substring(pattern, text)

    def _match_regex(self, pattern: str, text: str) -> bool:
        """Match using regular expression.

        Args:
            pattern: The regex pattern
            text: The text to search in

        Returns:
            True if pattern matches, False otherwise
        """
        try:
            # Try to use cached compiled pattern
            if pattern in self.compiled_patterns:
                regex = self.compiled_patterns[pattern]
            else:
                regex = re.compile(pattern, self._regex_flags)
                self.compiled_patterns[pattern] = regex

            return regex.search(text) is not None

        except re.error as e:
            raise EvaluationError(f"Invalid regex pattern '{pattern}': {e}") from e

    def _match_substring(self, pattern: str, text: str) -> bool:
        """Match using substring search.

        Args:
            pattern: The substring to find
            text: The text to search in

        Returns:
            True if substring found, False otherwise
        """
        if self.ignore_case:
            return pattern.lower() in text.lower()
        else:
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


def evaluate(
    ast: ASTNode,
    text: str,
    ignore_case: bool = False,
    use_regex: bool = False,
) -> bool:
    """Convenience function to evaluate an AST against text.

    Args:
        ast: The AST node to evaluate
        text: The text to search in
        ignore_case: Whether to perform case-insensitive matching
        use_regex: Whether to interpret search terms as regular expressions

    Returns:
        True if the expression matches the text, False otherwise

    Raises:
        EvaluationError: If evaluation fails
    """
    evaluator = ExpressionEvaluator(ignore_case=ignore_case, use_regex=use_regex)
    return evaluator.evaluate(ast, text)
