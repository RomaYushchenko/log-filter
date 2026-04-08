"""Integration tests for exact matching feature (--exact-match flag)."""

import pytest

from log_filter.core.evaluator import ExpressionEvaluator
from log_filter.core.parser import ExpressionParser
from log_filter.core.tokenizer import Tokenizer


class TestExactMatchingIntegration:
    """Integration tests for exact matching feature."""

    def test_word_boundary_prevents_substring_matches(self):
        """Word boundary prevents MOVE from matching MOVE_SNAPSHOT."""
        # Parse expression (tokenize first, then parse)
        tokenizer = Tokenizer("MOVE")
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        # Test without word boundary (substring matching)
        evaluator_substring = ExpressionEvaluator(word_boundary=False)
        assert evaluator_substring.evaluate(ast, "MOVE")
        assert evaluator_substring.evaluate(ast, "MOVE_SNAPSHOT")  # Matches substring
        assert evaluator_substring.evaluate(ast, "MOVE_RESOURCE")  # Matches substring

        # Test with word boundary (exact word matching)
        evaluator_exact = ExpressionEvaluator(word_boundary=True)
        assert evaluator_exact.evaluate(ast, "MOVE")
        assert not evaluator_exact.evaluate(ast, "MOVE_SNAPSHOT")  # No match
        assert not evaluator_exact.evaluate(ast, "MOVE_RESOURCE")  # No match

    def test_strip_quotes_in_json_logs(self):
        """Quote stripping allows matching values in JSON logs."""
        tokenizer = Tokenizer("MOVE")
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        # Test without quote stripping
        evaluator_no_strip = ExpressionEvaluator(strip_quotes=False)
        assert evaluator_no_strip.evaluate(ast, "MOVE")
        assert evaluator_no_strip.evaluate(ast, '{"action":"MOVE"}')  # MOVE as substring

        # Test with quote stripping
        evaluator_strip = ExpressionEvaluator(strip_quotes=True)
        assert evaluator_strip.evaluate(ast, "MOVE")
        assert evaluator_strip.evaluate(ast, '{"action":"MOVE"}')  # Quotes stripped

    def test_exact_match_flag_combines_both_features(self):
        """--exact-match combines word_boundary and strip_quotes."""
        tokenizer = Tokenizer("MOVE")
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        # Simulate --exact-match flag
        evaluator = ExpressionEvaluator(word_boundary=True, strip_quotes=True)

        # Should match exact word with or without quotes
        assert evaluator.evaluate(ast, "MOVE")
        assert evaluator.evaluate(ast, '{"action":"MOVE"}')

        # Should NOT match compound words even with quotes
        assert not evaluator.evaluate(ast, '{"entity":"MOVE_SNAPSHOT"}')
        assert not evaluator.evaluate(ast, "MOVE_RESOURCE")

    def test_real_world_scenario_unkn540406(self):
        """Real-world scenario: UNKN540406 AND eventEntity AND MOVE."""
        tokenizer = Tokenizer("UNKN540406 AND eventEntity AND MOVE")
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        evaluator = ExpressionEvaluator(word_boundary=True, strip_quotes=True)

        # This log has MOVE as exact value - should match
        log1 = '{"id":"UNKN540406","eventEntity":"MOVE","action":"CREATE"}'
        assert evaluator.evaluate(ast, log1)

        # These logs have MOVE_SNAPSHOT/MOVE_RESOURCE - should NOT match
        log2 = '{"id":"UNKN540406","eventEntity":"MOVE_SNAPSHOT","action":"UPDATE"}'
        log3 = '{"id":"UNKN540406","eventEntity":"MOVE_RESOURCE","action":"UPDATE"}'
        assert not evaluator.evaluate(ast, log2)
        assert not evaluator.evaluate(ast, log3)

        # This log is missing UNKN540406 - should NOT match
        log4 = '{"id":"OTHER123","eventEntity":"MOVE","action":"CREATE"}'
        assert not evaluator.evaluate(ast, log4)

    def test_exact_match_with_ignore_case(self):
        """Exact match works with ignore_case."""
        tokenizer = Tokenizer("move")
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        evaluator = ExpressionEvaluator(word_boundary=True, strip_quotes=True, ignore_case=True)

        # Should match different cases
        assert evaluator.evaluate(ast, "MOVE")
        assert evaluator.evaluate(ast, "move")
        assert evaluator.evaluate(ast, '{"action":"Move"}')

        # Should NOT match compound words
        assert not evaluator.evaluate(ast, "MOVEMENT")
        assert not evaluator.evaluate(ast, "move_snapshot")

    def test_compound_word_search_still_works(self):
        """Searching for compound words like MOVE_SNAPSHOT should still work."""
        tokenizer = Tokenizer("MOVE_SNAPSHOT")
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        evaluator = ExpressionEvaluator(word_boundary=True, strip_quotes=True)

        # Should match exact compound word
        assert evaluator.evaluate(ast, "MOVE_SNAPSHOT")
        assert evaluator.evaluate(ast, '{"entity":"MOVE_SNAPSHOT"}')

        # Should NOT match standalone MOVE
        assert not evaluator.evaluate(ast, "MOVE")
        assert not evaluator.evaluate(ast, '{"action":"MOVE"}')

    def test_backward_compatibility_without_exact_match(self):
        """Without exact-match flags, behavior should be unchanged."""
        tokenizer = Tokenizer("MOVE")
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        # Default behavior (substring matching)
        evaluator = ExpressionEvaluator(word_boundary=False, strip_quotes=False)

        # Should match as substring
        assert evaluator.evaluate(ast, "MOVE")
        assert evaluator.evaluate(ast, "MOVE_SNAPSHOT")
        assert evaluator.evaluate(ast, "MOVE_RESOURCE")
        assert evaluator.evaluate(ast, "MOVEMENT")
