"""Unit tests for the parser module."""

import pytest

from log_filter.core.exceptions import ParseError, TokenizationError
from log_filter.core.parser import ExpressionParser, parse
from log_filter.core.tokenizer import tokenize


class TestExpressionParser:
    """Tests for ExpressionParser class."""

    def test_single_word(self) -> None:
        """Test parsing a single word."""
        ast = parse("ERROR")
        assert ast == ("WORD", "ERROR")

    def test_two_words_implicit_and(self) -> None:
        """Test that consecutive words without operator is not valid."""
        # This should fail because there's no operator between words
        with pytest.raises(ParseError, match="Unexpected token"):
            parse("ERROR WARN")

    def test_and_expression(self) -> None:
        """Test parsing AND expression."""
        ast = parse("ERROR AND WARN")
        assert ast == ("AND", ("WORD", "ERROR"), ("WORD", "WARN"))

    def test_or_expression(self) -> None:
        """Test parsing OR expression."""
        ast = parse("ERROR OR WARN")
        assert ast == ("OR", ("WORD", "ERROR"), ("WORD", "WARN"))

    def test_not_expression(self) -> None:
        """Test parsing NOT expression."""
        ast = parse("NOT ERROR")
        assert ast == ("NOT", ("WORD", "ERROR"))

    def test_parentheses(self) -> None:
        """Test parsing with parentheses."""
        ast = parse("(ERROR)")
        assert ast == ("WORD", "ERROR")

    def test_nested_parentheses(self) -> None:
        """Test parsing nested parentheses."""
        ast = parse("((ERROR))")
        assert ast == ("WORD", "ERROR")

    def test_operator_precedence_not_and(self) -> None:
        """Test that NOT has higher precedence than AND."""
        ast = parse("NOT ERROR AND WARN")
        # Should be: (NOT ERROR) AND WARN
        assert ast == ("AND", ("NOT", ("WORD", "ERROR")), ("WORD", "WARN"))

    def test_operator_precedence_and_or(self) -> None:
        """Test that AND has higher precedence than OR."""
        ast = parse("ERROR AND WARN OR INFO")
        # Should be: (ERROR AND WARN) OR INFO
        assert ast == ("OR", ("AND", ("WORD", "ERROR"), ("WORD", "WARN")), ("WORD", "INFO"))

    def test_operator_precedence_complex(self) -> None:
        """Test complex operator precedence."""
        ast = parse("ERROR OR WARN AND INFO")
        # Should be: ERROR OR (WARN AND INFO)
        assert ast == ("OR", ("WORD", "ERROR"), ("AND", ("WORD", "WARN"), ("WORD", "INFO")))

    def test_parentheses_override_precedence(self) -> None:
        """Test that parentheses override precedence."""
        ast = parse("(ERROR OR WARN) AND INFO")
        assert ast == ("AND", ("OR", ("WORD", "ERROR"), ("WORD", "WARN")), ("WORD", "INFO"))

    def test_multiple_not(self) -> None:
        """Test multiple NOT operators."""
        ast = parse("NOT NOT ERROR")
        assert ast == ("NOT", ("NOT", ("WORD", "ERROR")))

    def test_complex_expression(self) -> None:
        """Test parsing a complex expression."""
        ast = parse("(ERROR AND Kafka) OR (WARN AND NOT timeout)")
        assert ast == (
            "OR",
            ("AND", ("WORD", "ERROR"), ("WORD", "Kafka")),
            ("AND", ("WORD", "WARN"), ("NOT", ("WORD", "timeout"))),
        )

    def test_quoted_strings(self) -> None:
        """Test parsing quoted strings."""
        ast = parse('"ERROR message" AND WARN')
        assert ast == ("AND", ("WORD", "ERROR message"), ("WORD", "WARN"))

    def test_empty_expression(self) -> None:
        """Test parsing empty expression raises error."""
        with pytest.raises(TokenizationError, match="Empty expression"):
            parse("")

    def test_only_operator(self) -> None:
        """Test parsing only operator raises error."""
        with pytest.raises(ParseError):
            parse("AND")

    def test_missing_operand_and(self) -> None:
        """Test missing operand in AND expression."""
        with pytest.raises(ParseError):
            parse("ERROR AND")

    def test_missing_operand_or(self) -> None:
        """Test missing operand in OR expression."""
        with pytest.raises(ParseError):
            parse("ERROR OR")

    def test_missing_operand_not(self) -> None:
        """Test missing operand in NOT expression."""
        with pytest.raises(ParseError):
            parse("NOT")

    def test_unbalanced_left_paren(self) -> None:
        """Test unbalanced left parenthesis."""
        with pytest.raises(ParseError, match="Unbalanced parentheses"):
            parse("(ERROR")

    def test_unbalanced_right_paren(self) -> None:
        """Test unbalanced right parenthesis."""
        with pytest.raises(ParseError, match="Unexpected token"):
            parse("ERROR)")

    def test_empty_parentheses(self) -> None:
        """Test empty parentheses."""
        with pytest.raises(ParseError):
            parse("()")

    def test_multiple_and(self) -> None:
        """Test multiple AND operators."""
        ast = parse("ERROR AND WARN AND INFO")
        # Should be left-associative: (ERROR AND WARN) AND INFO
        assert ast == (
            "AND",
            ("AND", ("WORD", "ERROR"), ("WORD", "WARN")),
            ("WORD", "INFO"),
        )

    def test_multiple_or(self) -> None:
        """Test multiple OR operators."""
        ast = parse("ERROR OR WARN OR INFO")
        # Should be left-associative: (ERROR OR WARN) OR INFO
        assert ast == (
            "OR",
            ("OR", ("WORD", "ERROR"), ("WORD", "WARN")),
            ("WORD", "INFO"),
        )

    def test_mixed_operators(self) -> None:
        """Test mixing all operators."""
        ast = parse("NOT ERROR AND WARN OR INFO")
        assert ast == (
            "OR",
            ("AND", ("NOT", ("WORD", "ERROR")), ("WORD", "WARN")),
            ("WORD", "INFO"),
        )


class TestParserEdgeCases:
    """Tests for parser edge cases."""

    def test_very_deep_nesting(self) -> None:
        """Test very deep nesting."""
        expr = "(" * 10 + "ERROR" + ")" * 10
        ast = parse(expr)
        assert ast == ("WORD", "ERROR")

    def test_long_chain_of_ands(self) -> None:
        """Test long chain of AND operators."""
        words = ["ERROR", "WARN", "INFO", "DEBUG", "TRACE"]
        expr = " AND ".join(words)
        ast = parse(expr)

        # Verify it's deeply nested ANDs
        def count_depth(node):  # type: ignore
            if node[0] == "WORD":
                return 0
            elif node[0] == "AND":
                return 1 + max(count_depth(node[1]), count_depth(node[2]))
            return 0

        assert count_depth(ast) == len(words) - 1

    def test_complex_nested_expression(self) -> None:
        """Test complex nested expression."""
        expr = "((ERROR OR WARN) AND (INFO OR DEBUG)) OR (NOT TRACE)"
        ast = parse(expr)

        # Just verify it parses without error and has correct structure
        assert ast[0] == "OR"
        assert ast[1][0] == "AND"
        assert ast[2][0] == "NOT"

    def test_whitespace_variations(self) -> None:
        """Test that whitespace doesn't affect parsing."""
        ast1 = parse("ERROR AND WARN")
        ast2 = parse("ERROR  AND  WARN")
        ast3 = parse("ERROR\tAND\nWARN")
        assert ast1 == ast2 == ast3

    def test_case_insensitive_operators(self) -> None:
        """Test that operator keywords are case-insensitive."""
        ast1 = parse("ERROR AND WARN")
        ast2 = parse("ERROR and WARN")
        ast3 = parse("ERROR AnD WARN")
        assert ast1 == ast2 == ast3

    def test_error_message_includes_position(self) -> None:
        """Test that error messages include position information."""
        try:
            parse("ERROR AND")
            pytest.fail("Should have raised ParseError")
        except ParseError as e:
            assert "Expected WORD" in str(e)

    def test_unicode_in_words(self) -> None:
        """Test Unicode characters in word tokens."""
        ast = parse('"Ошибка" AND "警告"')
        assert ast == ("AND", ("WORD", "Ошибка"), ("WORD", "警告"))


class TestParserWithTokenizer:
    """Integration tests with tokenizer."""

    def test_parser_uses_tokenizer_output(self) -> None:
        """Test that parser correctly uses tokenizer output."""
        tokens = tokenize("ERROR AND WARN")
        parser = ExpressionParser(tokens)
        ast = parser.parse()
        assert ast == ("AND", ("WORD", "ERROR"), ("WORD", "WARN"))

    def test_parser_error_on_empty_tokens(self) -> None:
        """Test parser with empty token list."""
        parser = ExpressionParser([])
        with pytest.raises(ParseError, match="No tokens to parse"):
            parser.parse()


class TestRealWorldExpressions:
    """Tests with real-world expression examples."""

    def test_kafka_error_search(self) -> None:
        """Test Kafka error search expression."""
        ast = parse("ERROR AND Kafka")
        assert ast == ("AND", ("WORD", "ERROR"), ("WORD", "Kafka"))

    def test_exclude_heartbeat(self) -> None:
        """Test excluding heartbeat messages."""
        ast = parse("ERROR AND NOT Heartbeat")
        assert ast == ("AND", ("WORD", "ERROR"), ("NOT", ("WORD", "Heartbeat")))

    def test_error_or_warn(self) -> None:
        """Test ERROR or WARN search."""
        ast = parse("(ERROR AND Kafka) OR WARN")
        assert ast == (
            "OR",
            ("AND", ("WORD", "ERROR"), ("WORD", "Kafka")),
            ("WORD", "WARN"),
        )

    def test_complex_diagnostic_query(self) -> None:
        """Test complex diagnostic query."""
        expr = '(ERROR OR WARN) AND ("connection" OR "timeout") AND NOT "test"'
        ast = parse(expr)

        # Verify structure
        assert ast[0] == "AND"
        assert ast[2][0] == "NOT"

    def test_regex_pattern_in_quotes(self) -> None:
        """Test regex pattern in quotes."""
        ast = parse('"ERROR [0-9]{3}" AND WARN')
        assert ast == ("AND", ("WORD", "ERROR [0-9]{3}"), ("WORD", "WARN"))
