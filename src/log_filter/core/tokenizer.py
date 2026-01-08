"""Tokenizer for boolean search expressions."""

import re
from enum import Enum
from typing import NamedTuple

from .exceptions import TokenizationError


class TokenType(str, Enum):
    """Token types for boolean expressions."""

    WORD = "WORD"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    LPAREN = "("
    RPAREN = ")"


class Token(NamedTuple):
    """Represents a single token.

    Attributes:
        type: The type of the token
        value: The token's value (text)
        position: Character position in the original expression
    """

    type: TokenType
    value: str
    position: int


class Tokenizer:
    """Tokenizes boolean search expressions into a list of tokens.

    The tokenizer supports:
    - Logical operators: AND, OR, NOT
    - Parentheses for grouping: ( )
    - Quoted strings: "..." or '...'
    - Unquoted words
    """

    def __init__(self, expression: str) -> None:
        """Initialize tokenizer with expression.

        Args:
            expression: The boolean expression to tokenize
        """
        self.expression = expression
        self.position = 0
        self.length = len(expression)

    def tokenize(self) -> list[Token]:
        """Tokenize the expression into a list of tokens.

        Returns:
            List of tokens

        Raises:
            TokenizationError: If tokenization fails or no tokens found
        """
        tokens: list[Token] = []

        while self.position < self.length:
            char = self.expression[self.position]

            # Skip whitespace
            if char.isspace():
                self.position += 1
                continue

            # Parentheses
            if char == "(":
                tokens.append(Token(TokenType.LPAREN, char, self.position))
                self.position += 1
                continue

            if char == ")":
                tokens.append(Token(TokenType.RPAREN, char, self.position))
                self.position += 1
                continue

            # Operators
            if self._match_keyword("AND"):
                tokens.append(Token(TokenType.AND, "AND", self.position))
                self.position += 3
                continue

            if self._match_keyword("OR"):
                tokens.append(Token(TokenType.OR, "OR", self.position))
                self.position += 2
                continue

            if self._match_keyword("NOT"):
                tokens.append(Token(TokenType.NOT, "NOT", self.position))
                self.position += 3
                continue

            # Quoted strings
            if char in ('"', "'"):
                token = self._read_quoted_string(char)
                tokens.append(token)
                continue

            # Unquoted words
            token = self._read_word()
            tokens.append(token)

        # Validate that we got at least some tokens
        if not tokens:
            raise TokenizationError("No tokens found in expression")

        return tokens

    def _match_keyword(self, keyword: str) -> bool:
        """Check if the current position matches a keyword.

        Args:
            keyword: The keyword to match (case-insensitive)

        Returns:
            True if keyword matches at current position
        """
        end_pos = self.position + len(keyword)
        if end_pos > self.length:
            return False

        # Check if keyword matches (case-insensitive)
        substring = self.expression[self.position : end_pos]
        if substring.upper() != keyword.upper():
            return False

        # Ensure keyword is not part of a larger word
        # Check character before (if exists)
        if self.position > 0:
            prev_char = self.expression[self.position - 1]
            if prev_char.isalnum() or prev_char == "_":
                return False

        # Check character after (if exists)
        if end_pos < self.length:
            next_char = self.expression[end_pos]
            if next_char.isalnum() or next_char == "_":
                return False

        return True

    def _read_quoted_string(self, quote_char: str) -> Token:
        """Read a quoted string token.

        Args:
            quote_char: The quote character (" or ')

        Returns:
            Token containing the quoted string (without quotes)

        Raises:
            TokenizationError: If string is unterminated
        """
        start_pos = self.position
        self.position += 1  # Skip opening quote

        value_start = self.position

        # Find closing quote
        while self.position < self.length and self.expression[self.position] != quote_char:
            self.position += 1

        if self.position >= self.length:
            raise TokenizationError(
                f"Unterminated quoted string",
                position=start_pos,
                expression=self.expression,
            )

        value = self.expression[value_start : self.position]
        self.position += 1  # Skip closing quote

        return Token(TokenType.WORD, value, value_start)

    def _read_word(self) -> Token:
        """Read an unquoted word token.

        Returns:
            Token containing the word
        """
        start_pos = self.position

        # Read until whitespace or parentheses
        while self.position < self.length:
            char = self.expression[self.position]
            if char.isspace() or char in "()":
                break
            self.position += 1

        value = self.expression[start_pos : self.position]
        return Token(TokenType.WORD, value, start_pos)


def tokenize(expression: str) -> list[Token]:
    """Convenience function to tokenize an expression.

    Args:
        expression: The boolean expression to tokenize

    Returns:
        List of tokens

    Raises:
        TokenizationError: If tokenization fails
    """
    if not expression or not expression.strip():
        raise TokenizationError("Empty expression", position=0, expression=expression)

    tokenizer = Tokenizer(expression)
    tokens = tokenizer.tokenize()

    if not tokens:
        raise TokenizationError("No tokens found", position=0, expression=expression)

    return tokens
