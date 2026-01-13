"""Tests for word boundary matching feature."""

import pytest

from log_filter.core.evaluator import ExpressionEvaluator


class TestWordBoundaryMatching:
    """Test word boundary matching feature."""

    def test_basic_word_boundary(self):
        """Basic word boundary matching."""
        evaluator = ExpressionEvaluator(word_boundary=True)
        ast = ("WORD", "MOVE")

        # Should match standalone word
        assert evaluator.evaluate(ast, "MOVE")
        assert evaluator.evaluate(ast, "The MOVE action")
        assert evaluator.evaluate(ast, "action MOVE complete")

        # Should NOT match as substring
        assert not evaluator.evaluate(ast, "MOVE_SNAPSHOT")
        assert not evaluator.evaluate(ast, "MOVEMENT")
        assert not evaluator.evaluate(ast, "REMOVED")

    def test_word_boundary_with_punctuation(self):
        """Word boundary with punctuation."""
        evaluator = ExpressionEvaluator(word_boundary=True)
        ast = ("WORD", "MOVE")

        # Punctuation acts as word boundary
        assert evaluator.evaluate(ast, '"MOVE"')
        assert evaluator.evaluate(ast, "action:MOVE,")
        assert evaluator.evaluate(ast, "(MOVE)")
        assert evaluator.evaluate(ast, "{MOVE}")
        assert evaluator.evaluate(ast, "[MOVE]")

    def test_word_boundary_underscore_separator(self):
        """Underscore acts as word boundary."""
        evaluator = ExpressionEvaluator(word_boundary=True)
        ast = ("WORD", "MOVE")

        # MOVE should not match when part of compound word with underscore
        assert not evaluator.evaluate(ast, "MOVE_SNAPSHOT")
        assert not evaluator.evaluate(ast, "PRE_MOVE")
        assert not evaluator.evaluate(ast, "_MOVE_")

    def test_word_boundary_compound_term(self):
        """Searching for compound term should work."""
        evaluator = ExpressionEvaluator(word_boundary=True)
        ast = ("WORD", "MOVE_SNAPSHOT")

        # Should match exact compound word
        assert evaluator.evaluate(ast, "MOVE_SNAPSHOT")
        assert evaluator.evaluate(ast, '"MOVE_SNAPSHOT"')
        assert evaluator.evaluate(ast, "eventEntity:MOVE_SNAPSHOT,")

        # Should NOT match if only part appears
        assert not evaluator.evaluate(ast, "MOVE")
        assert not evaluator.evaluate(ast, "SNAPSHOT")

    def test_word_boundary_case_sensitive(self):
        """Word boundary respects case sensitivity."""
        evaluator = ExpressionEvaluator(word_boundary=True, ignore_case=False)
        ast = ("WORD", "MOVE")

        assert evaluator.evaluate(ast, "MOVE")
        assert not evaluator.evaluate(ast, "move")
        assert not evaluator.evaluate(ast, "Move")

    def test_word_boundary_case_insensitive(self):
        """Word boundary with case insensitive matching."""
        evaluator = ExpressionEvaluator(word_boundary=True, ignore_case=True)
        ast = ("WORD", "MOVE")

        # Should match different cases
        assert evaluator.evaluate(ast, "MOVE")
        assert evaluator.evaluate(ast, "move")
        assert evaluator.evaluate(ast, "Move")
        assert evaluator.evaluate(ast, "MoVe")

        # Should NOT match as substring regardless of case
        assert not evaluator.evaluate(ast, "MOVEMENT")
        assert not evaluator.evaluate(ast, "movement")
        assert not evaluator.evaluate(ast, "MOVE_SNAPSHOT")
        assert not evaluator.evaluate(ast, "move_snapshot")

    def test_word_boundary_complex_boolean(self):
        """Word boundary with complex boolean expressions."""
        evaluator = ExpressionEvaluator(word_boundary=True)

        # AND expression
        ast_and = ("AND", ("WORD", "MOVE"), ("WORD", "eventEntity"))
        assert evaluator.evaluate(ast_and, "eventEntity:MOVE")
        assert not evaluator.evaluate(ast_and, "eventEntity:MOVE_SNAPSHOT")

        # OR expression
        ast_or = ("OR", ("WORD", "MOVE"), ("WORD", "ERROR"))
        assert evaluator.evaluate(ast_or, "ERROR log")
        assert evaluator.evaluate(ast_or, "MOVE action")
        assert not evaluator.evaluate(ast_or, "MOVE_SNAPSHOT")

        # NOT expression
        ast_not = ("NOT", ("WORD", "MOVE_SNAPSHOT"))
        assert evaluator.evaluate(ast_not, "MOVE action")
        assert not evaluator.evaluate(ast_not, "MOVE_SNAPSHOT")

    def test_word_boundary_numbers(self):
        """Word boundary with numbers."""
        evaluator = ExpressionEvaluator(word_boundary=True)
        ast = ("WORD", "540406")

        # Word boundary treats UNKN540406 as a single word, so 540406 won't match
        assert not evaluator.evaluate(ast, "UNKN540406")  # Number is part of alphanumeric word
        assert evaluator.evaluate(ast, "540406")
        assert evaluator.evaluate(ast, "ID:540406")  # Colon is word boundary

    def test_word_boundary_disabled(self):
        """Verify word_boundary=False uses substring matching."""
        evaluator = ExpressionEvaluator(word_boundary=False)
        ast = ("WORD", "MOVE")

        # Should match as substring
        assert evaluator.evaluate(ast, "MOVE")
        assert evaluator.evaluate(ast, "MOVE_SNAPSHOT")
        assert evaluator.evaluate(ast, "MOVEMENT")
        assert evaluator.evaluate(ast, "REMOVED")

    def test_word_boundary_json_scenario(self):
        """Real-world JSON log scenario."""
        evaluator = ExpressionEvaluator(word_boundary=True)
        ast = ("WORD", "MOVE")

        # Should NOT match compound values
        log1 = '{"eventEntity":"MOVE_SNAPSHOT"}'
        assert not evaluator.evaluate(ast, log1)

        log2 = '{"eventEntity":"MOVE_RESOURCE"}'
        assert not evaluator.evaluate(ast, log2)

        # Should match if MOVE appears as separate value
        log3 = '{"action":"MOVE"}'
        assert evaluator.evaluate(ast, log3)

    def test_word_boundary_at_string_boundaries(self):
        """Word boundary at start/end of string."""
        evaluator = ExpressionEvaluator(word_boundary=True)
        ast = ("WORD", "ERROR")

        assert evaluator.evaluate(ast, "ERROR")
        assert evaluator.evaluate(ast, "ERROR ")
        assert evaluator.evaluate(ast, " ERROR")
        assert evaluator.evaluate(ast, " ERROR ")

        assert not evaluator.evaluate(ast, "ERRORS")
        assert not evaluator.evaluate(ast, "ERROR_CODE")
