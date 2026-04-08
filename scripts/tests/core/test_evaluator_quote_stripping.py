"""Tests for quote stripping feature."""

import pytest

from log_filter.core.evaluator import ExpressionEvaluator


class TestQuoteStripping:
    """Test quote stripping feature."""

    def test_basic_quote_stripping(self):
        """Basic quote stripping."""
        evaluator = ExpressionEvaluator(strip_quotes=True)
        ast = ("WORD", "MOVE")

        # Should match both quoted and unquoted
        assert evaluator.evaluate(ast, "MOVE")
        assert evaluator.evaluate(ast, '"MOVE"')
        assert evaluator.evaluate(ast, "'MOVE'")
        assert evaluator.evaluate(ast, "`MOVE`")

    def test_strip_quotes_in_json(self):
        """Quote stripping in JSON."""
        evaluator = ExpressionEvaluator(strip_quotes=True)
        ast = ("WORD", "MOVE_SNAPSHOT")

        json_text = '{"eventEntity":"MOVE_SNAPSHOT"}'
        assert evaluator.evaluate(ast, json_text)

    def test_strip_quotes_double(self):
        """Strip double quotes."""
        evaluator = ExpressionEvaluator(strip_quotes=True)
        ast = ("WORD", "value")

        assert evaluator.evaluate(ast, '"value"')
        assert evaluator.evaluate(ast, 'key:"value"')
        assert evaluator.evaluate(ast, '{"key":"value"}')

    def test_strip_quotes_single(self):
        """Strip single quotes."""
        evaluator = ExpressionEvaluator(strip_quotes=True)
        ast = ("WORD", "value")

        assert evaluator.evaluate(ast, "'value'")
        assert evaluator.evaluate(ast, "key:'value'")
        assert evaluator.evaluate(ast, "{'key':'value'}")

    def test_strip_quotes_backtick(self):
        """Strip backticks."""
        evaluator = ExpressionEvaluator(strip_quotes=True)
        ast = ("WORD", "value")

        assert evaluator.evaluate(ast, "`value`")
        assert evaluator.evaluate(ast, "key:`value`")

    def test_strip_quotes_mixed(self):
        """Strip mixed quote types."""
        evaluator = ExpressionEvaluator(strip_quotes=True)
        ast = ("WORD", "MOVE")

        assert evaluator.evaluate(ast, '"MOVE"')
        assert evaluator.evaluate(ast, "'MOVE'")
        assert evaluator.evaluate(ast, "`MOVE`")
        assert evaluator.evaluate(ast, '\'"MOVE"`')  # Mixed quotes

    def test_strip_quotes_from_pattern(self):
        """Quote stripping from pattern too."""
        evaluator = ExpressionEvaluator(strip_quotes=True)
        # User might type quoted pattern
        ast = ("WORD", '"MOVE"')

        # Pattern quotes are stripped, so it matches unquoted text
        assert evaluator.evaluate(ast, "MOVE")
        assert evaluator.evaluate(ast, '"MOVE"')
        assert evaluator.evaluate(ast, "'MOVE'")

    def test_strip_quotes_case_sensitive(self):
        """Quote stripping respects case sensitivity."""
        evaluator = ExpressionEvaluator(strip_quotes=True, ignore_case=False)
        ast = ("WORD", "MOVE")

        assert evaluator.evaluate(ast, '"MOVE"')
        assert not evaluator.evaluate(ast, '"move"')

    def test_strip_quotes_case_insensitive(self):
        """Quote stripping with case insensitive."""
        evaluator = ExpressionEvaluator(strip_quotes=True, ignore_case=True)
        ast = ("WORD", "MOVE")

        assert evaluator.evaluate(ast, '"MOVE"')
        assert evaluator.evaluate(ast, '"move"')
        assert evaluator.evaluate(ast, '"Move"')

    def test_strip_quotes_disabled(self):
        """Verify strip_quotes=False treats quotes as literal."""
        evaluator = ExpressionEvaluator(strip_quotes=False)
        ast = ("WORD", "MOVE")

        # Should match both quoted and unquoted (substring matching)
        assert evaluator.evaluate(ast, "MOVE")
        assert evaluator.evaluate(ast, "action MOVE")

        # With strip_quotes=False, quotes are part of text but substring matching still works
        assert evaluator.evaluate(ast, '"MOVE"')  # MOVE is a substring
        assert evaluator.evaluate(ast, "'MOVE'")  # MOVE is a substring

        # Substring search works regardless of quotes
        assert evaluator.evaluate(ast, 'This "MOVE" action')  # MOVE appears as substring

    def test_strip_quotes_csv_scenario(self):
        """Real-world CSV scenario."""
        evaluator = ExpressionEvaluator(strip_quotes=True)
        ast = ("WORD", "COMPLETED")

        csv1 = "status,COMPLETED,timestamp"
        assert evaluator.evaluate(ast, csv1)

        csv2 = 'status,"COMPLETED",timestamp'
        assert evaluator.evaluate(ast, csv2)

        csv3 = "status,'COMPLETED',timestamp"
        assert evaluator.evaluate(ast, csv3)

    def test_strip_quotes_json_nested(self):
        """Quote stripping in nested JSON."""
        evaluator = ExpressionEvaluator(strip_quotes=True)
        ast = ("WORD", "ERROR")

        json_text = '{"level":"ERROR","message":"An error occurred","code":"ERROR_500"}'
        assert evaluator.evaluate(ast, json_text)

    def test_strip_quotes_empty_string(self):
        """Quote stripping with empty values."""
        evaluator = ExpressionEvaluator(strip_quotes=True)
        ast = ("WORD", "")

        # Empty pattern should not match
        assert not evaluator.evaluate(ast, '""')
        assert not evaluator.evaluate(ast, "''")
        assert not evaluator.evaluate(ast, "")


class TestCombinedWordBoundaryAndQuoteStripping:
    """Test combined word boundary + quote stripping."""

    def test_exact_match_json(self):
        """Exact word match in JSON with quotes."""
        evaluator = ExpressionEvaluator(word_boundary=True, strip_quotes=True)
        ast = ("WORD", "MOVE")

        # Should match standalone MOVE
        assert evaluator.evaluate(ast, '{"action":"MOVE"}')
        assert evaluator.evaluate(ast, 'action: "MOVE"')

        # Should NOT match MOVE as part of compound word
        assert not evaluator.evaluate(ast, '{"entity":"MOVE_SNAPSHOT"}')
        assert not evaluator.evaluate(ast, '"MOVE_RESOURCE"')

    def test_exact_match_with_case_insensitive(self):
        """All three features combined."""
        evaluator = ExpressionEvaluator(word_boundary=True, strip_quotes=True, ignore_case=True)
        ast = ("WORD", "move")

        # Should match exact word, any case, with or without quotes
        assert evaluator.evaluate(ast, "MOVE")
        assert evaluator.evaluate(ast, "move")
        assert evaluator.evaluate(ast, '"Move"')
        assert evaluator.evaluate(ast, "'MOVE'")

        # Should NOT match as substring
        assert not evaluator.evaluate(ast, "MOVEMENT")
        assert not evaluator.evaluate(ast, '"move_snapshot"')
        assert not evaluator.evaluate(ast, "MOVE_RESOURCE")

    def test_real_world_scenario(self):
        """Real-world JSON log scenario from the issue."""
        evaluator = ExpressionEvaluator(word_boundary=True, strip_quotes=True, ignore_case=False)

        # User searches for exact word MOVE
        ast = ("WORD", "MOVE")

        log1 = '{"eventEntity":"MOVE","action":"CREATE"}'
        log2 = '{"eventEntity":"MOVE_SNAPSHOT","action":"UPDATE"}'
        log3 = '{"eventEntity":"MOVE_RESOURCE","action":"UPDATE"}'
        log4 = '{"action":"MOVE","entity":"ORDER"}'

        assert evaluator.evaluate(ast, log1)  # ✅ Exact match
        assert not evaluator.evaluate(ast, log2)  # ❌ MOVE_SNAPSHOT
        assert not evaluator.evaluate(ast, log3)  # ❌ MOVE_RESOURCE
        assert evaluator.evaluate(ast, log4)  # ✅ Exact match

    def test_complex_boolean_with_both_features(self):
        """Complex boolean expression with both features."""
        evaluator = ExpressionEvaluator(word_boundary=True, strip_quotes=True)

        # AND expression
        ast = ("AND", ("WORD", "MOVE"), ("WORD", "eventEntity"))

        log1 = '{"eventEntity":"MOVE"}'
        log2 = '{"eventEntity":"MOVE_SNAPSHOT"}'

        assert evaluator.evaluate(ast, log1)  # Both terms present, MOVE is exact word
        assert not evaluator.evaluate(ast, log2)  # eventEntity present, but MOVE is substring

    def test_csv_exact_matching(self):
        """CSV with exact matching."""
        evaluator = ExpressionEvaluator(word_boundary=True, strip_quotes=True)
        ast = ("WORD", "COMPLETED")

        # Should match
        assert evaluator.evaluate(ast, "status,COMPLETED,timestamp")
        assert evaluator.evaluate(ast, 'status,"COMPLETED",timestamp')
        assert evaluator.evaluate(ast, "status,'COMPLETED',timestamp")

        # Should NOT match
        assert not evaluator.evaluate(ast, "status,COMPLETED_WITH_ERRORS,timestamp")
        assert not evaluator.evaluate(ast, 'status,"COMPLETED_SUCCESSFULLY",timestamp')
