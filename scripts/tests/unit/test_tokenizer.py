"""Unit tests for the tokenizer module."""

import pytest

from log_filter.core.exceptions import TokenizationError
from log_filter.core.tokenizer import Token, Tokenizer, TokenType, tokenize


class TestTokenType:
    """Tests for TokenType enum."""

    def test_token_types_exist(self) -> None:
        """Test that all token types are defined."""
        assert TokenType.WORD == "WORD"
        assert TokenType.AND == "AND"
        assert TokenType.OR == "OR"
        assert TokenType.NOT == "NOT"
        assert TokenType.LPAREN == "("
        assert TokenType.RPAREN == ")"


class TestToken:
    """Tests for Token namedtuple."""

    def test_token_creation(self) -> None:
        """Test creating a token."""
        token = Token(TokenType.WORD, "ERROR", 0)
        assert token.type == TokenType.WORD
        assert token.value == "ERROR"
        assert token.position == 0

    def test_token_immutable(self) -> None:
        """Test that tokens are immutable."""
        token = Token(TokenType.WORD, "ERROR", 0)
        with pytest.raises(AttributeError):
            token.type = TokenType.AND  # type: ignore


class TestTokenizer:
    """Tests for Tokenizer class."""

    def test_empty_expression(self) -> None:
        """Test tokenizing empty expression raises error."""
        with pytest.raises(TokenizationError, match="Empty expression"):
            tokenize("")

    def test_whitespace_only(self) -> None:
        """Test tokenizing whitespace-only expression raises error."""
        with pytest.raises(TokenizationError, match="No tokens found"):
            Tokenizer("   \t\n  ").tokenize()

    def test_single_word(self) -> None:
        """Test tokenizing a single word."""
        tokens = tokenize("ERROR")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.WORD
        assert tokens[0].value == "ERROR"

    def test_multiple_words(self) -> None:
        """Test tokenizing multiple words."""
        tokens = tokenize("ERROR WARN INFO")
        assert len(tokens) == 3
        assert all(t.type == TokenType.WORD for t in tokens)
        assert [t.value for t in tokens] == ["ERROR", "WARN", "INFO"]

    def test_and_operator(self) -> None:
        """Test tokenizing AND operator."""
        tokens = tokenize("ERROR AND WARN")
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.WORD
        assert tokens[1].type == TokenType.AND
        assert tokens[2].type == TokenType.WORD

    def test_or_operator(self) -> None:
        """Test tokenizing OR operator."""
        tokens = tokenize("ERROR OR WARN")
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.WORD
        assert tokens[1].type == TokenType.OR
        assert tokens[2].type == TokenType.WORD

    def test_not_operator(self) -> None:
        """Test tokenizing NOT operator."""
        tokens = tokenize("NOT ERROR")
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.NOT
        assert tokens[1].type == TokenType.WORD

    def test_parentheses(self) -> None:
        """Test tokenizing parentheses."""
        tokens = tokenize("(ERROR AND WARN)")
        assert len(tokens) == 5
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[1].type == TokenType.WORD
        assert tokens[2].type == TokenType.AND
        assert tokens[3].type == TokenType.WORD
        assert tokens[4].type == TokenType.RPAREN

    def test_nested_parentheses(self) -> None:
        """Test tokenizing nested parentheses."""
        tokens = tokenize("((ERROR))")
        assert len(tokens) == 5
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[1].type == TokenType.LPAREN
        assert tokens[2].type == TokenType.WORD
        assert tokens[3].type == TokenType.RPAREN
        assert tokens[4].type == TokenType.RPAREN

    def test_double_quoted_string(self) -> None:
        """Test tokenizing double-quoted string."""
        tokens = tokenize('"ERROR message"')
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.WORD
        assert tokens[0].value == "ERROR message"

    def test_single_quoted_string(self) -> None:
        """Test tokenizing single-quoted string."""
        tokens = tokenize("'ERROR message'")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.WORD
        assert tokens[0].value == "ERROR message"

    def test_quoted_string_with_special_chars(self) -> None:
        """Test tokenizing quoted string with special characters."""
        tokens = tokenize('"ERROR: [0-9]+"')
        assert len(tokens) == 1
        assert tokens[0].value == "ERROR: [0-9]+"

    def test_unterminated_double_quote(self) -> None:
        """Test unterminated double quote raises error."""
        with pytest.raises(TokenizationError, match="Unterminated quoted string"):
            tokenize('"ERROR')

    def test_unterminated_single_quote(self) -> None:
        """Test unterminated single quote raises error."""
        with pytest.raises(TokenizationError, match="Unterminated quoted string"):
            tokenize("'ERROR")

    def test_case_insensitive_operators(self) -> None:
        """Test that operators are case-insensitive."""
        tokens = tokenize("error and warn or info")
        assert tokens[1].type == TokenType.AND
        assert tokens[3].type == TokenType.OR

        tokens = tokenize("error AnD warn Or info")
        assert tokens[1].type == TokenType.AND
        assert tokens[3].type == TokenType.OR

    def test_operator_as_part_of_word(self) -> None:
        """Test that operators within words are not tokenized."""
        tokens = tokenize("ANDROID ORANGE NOTION")
        assert len(tokens) == 3
        assert all(t.type == TokenType.WORD for t in tokens)

    def test_complex_expression(self) -> None:
        """Test tokenizing a complex expression."""
        expr = '(ERROR AND "Kafka connection") OR (WARN AND NOT timeout)'
        tokens = tokenize(expr)

        assert len(tokens) == 12
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[1].type == TokenType.WORD
        assert tokens[1].value == "ERROR"
        assert tokens[2].type == TokenType.AND
        assert tokens[3].type == TokenType.WORD
        assert tokens[3].value == "Kafka connection"
        assert tokens[4].type == TokenType.RPAREN

    def test_token_positions(self) -> None:
        """Test that token positions are correct."""
        tokens = tokenize("ERROR AND WARN")
        assert tokens[0].position == 0  # ERROR
        assert tokens[1].position == 6  # AND
        assert tokens[2].position == 10  # WARN

    def test_whitespace_handling(self) -> None:
        """Test various whitespace is handled correctly."""
        tokens = tokenize("ERROR  \t  AND\n\nWARN")
        assert len(tokens) == 3
        assert [t.type for t in tokens] == [
            TokenType.WORD,
            TokenType.AND,
            TokenType.WORD,
        ]

    def test_no_whitespace(self) -> None:
        """Test expression with no whitespace."""
        tokens = tokenize("(ERROR)AND(WARN)")
        assert len(tokens) == 7
        assert [t.type for t in tokens] == [
            TokenType.LPAREN,
            TokenType.WORD,
            TokenType.RPAREN,
            TokenType.AND,
            TokenType.LPAREN,
            TokenType.WORD,
            TokenType.RPAREN,
        ]


class TestTokenizerEdgeCases:
    """Tests for edge cases."""

    def test_only_operators(self) -> None:
        """Test expression with only operators."""
        tokens = tokenize("AND OR NOT")
        # Should treat them as operators, not words
        assert tokens[0].type == TokenType.AND
        assert tokens[1].type == TokenType.OR
        assert tokens[2].type == TokenType.NOT

    def test_empty_quoted_string(self) -> None:
        """Test empty quoted string."""
        tokens = tokenize('""')
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.WORD
        assert tokens[0].value == ""

    def test_special_characters_in_words(self) -> None:
        """Test special characters in unquoted words."""
        tokens = tokenize("ERROR:500 user@example.com file.log")
        assert len(tokens) == 3
        assert all(t.type == TokenType.WORD for t in tokens)

    def test_unicode_characters(self) -> None:
        """Test Unicode characters in expressions."""
        tokens = tokenize('"Ошибка соединения"')
        assert len(tokens) == 1
        assert tokens[0].value == "Ошибка соединения"

    def test_very_long_expression(self) -> None:
        """Test very long expression."""
        words = ["ERROR"] * 100
        expr = " AND ".join(words)
        tokens = tokenize(expr)
        assert len(tokens) == 199  # 100 words + 99 ANDs

    def test_mixed_quotes(self) -> None:
        """Test expression with both quote types."""
        tokens = tokenize("\"ERROR\" AND 'WARN'")
        assert len(tokens) == 3
        assert tokens[0].value == "ERROR"
        assert tokens[2].value == "WARN"
