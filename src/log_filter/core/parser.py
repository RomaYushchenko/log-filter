"""Parser for boolean search expressions."""

from typing import Union

from ..domain.models import ASTNode
from .exceptions import ParseError
from .tokenizer import Token, TokenType, tokenize


class ExpressionParser:
    """Recursive descent parser for boolean expressions.

    Grammar:
        expression := term (OR term)*
        term       := unary (AND unary)*
        unary      := NOT unary | factor
        factor     := LPAREN expression RPAREN | WORD

    Operator precedence (highest to lowest):
        NOT > AND > OR
    """

    def __init__(self, tokens: list[Token]) -> None:
        """Initialize parser with tokens.

        Args:
            tokens: List of tokens to parse
        """
        self.tokens = tokens
        self.position = 0
        self.length = len(tokens)

    def parse(self) -> ASTNode:
        """Parse the tokens into an Abstract Syntax Tree.

        Returns:
            Root node of the AST

        Raises:
            ParseError: If parsing fails
        """
        if not self.tokens:
            raise ParseError("No tokens to parse")

        ast = self._parse_expression()

        # Ensure all tokens were consumed
        if self.position < self.length:
            token = self.tokens[self.position]
            raise ParseError(
                f"Unexpected token '{token.value}'",
                position=token.position,
                expression=self._reconstruct_expression(),
            )

        return ast

    def _current_token(self) -> Token | None:
        """Get the current token without consuming it.

        Returns:
            Current token or None if at end
        """
        if self.position < self.length:
            return self.tokens[self.position]
        return None

    def _match(self, token_type: TokenType) -> bool:
        """Check if current token matches the given type.

        Args:
            token_type: Type to check for

        Returns:
            True if current token matches, False otherwise
        """
        token = self._current_token()
        return token is not None and token.type == token_type

    def _consume(self, token_type: TokenType) -> Token:
        """Consume a token of the expected type.

        Args:
            token_type: Expected token type

        Returns:
            The consumed token

        Raises:
            ParseError: If current token doesn't match expected type
        """
        if not self._match(token_type):
            if self.position >= self.length:
                raise ParseError(
                    f"Expected {token_type.value} but reached end of expression",
                    position=len(self._reconstruct_expression()),
                    expression=self._reconstruct_expression(),
                )

            token = self.tokens[self.position]
            raise ParseError(
                f"Expected {token_type.value} but got '{token.value}'",
                position=token.position,
                expression=self._reconstruct_expression(),
            )

        token = self.tokens[self.position]
        self.position += 1
        return token

    def _parse_expression(self) -> ASTNode:
        """Parse: expression := term (OR term)*"""
        left = self._parse_term()

        while self._match(TokenType.OR):
            self._consume(TokenType.OR)
            right = self._parse_term()
            left = ("OR", left, right)

        return left

    def _parse_term(self) -> ASTNode:
        """Parse: term := unary (AND unary)*"""
        left = self._parse_unary()

        while self._match(TokenType.AND):
            self._consume(TokenType.AND)
            right = self._parse_unary()
            left = ("AND", left, right)

        return left

    def _parse_unary(self) -> ASTNode:
        """Parse: unary := NOT unary | factor"""
        if self._match(TokenType.NOT):
            self._consume(TokenType.NOT)
            operand = self._parse_unary()
            return ("NOT", operand)

        return self._parse_factor()

    def _parse_factor(self) -> ASTNode:
        """Parse: factor := LPAREN expression RPAREN | WORD"""
        # Handle parentheses
        if self._match(TokenType.LPAREN):
            lparen_token = self._consume(TokenType.LPAREN)
            expr = self._parse_expression()

            if not self._match(TokenType.RPAREN):
                raise ParseError(
                    "Unbalanced parentheses — missing ')'",
                    position=lparen_token.position,
                    expression=self._reconstruct_expression(),
                )

            self._consume(TokenType.RPAREN)
            return expr

        # Handle words
        if self._match(TokenType.WORD):
            token = self._consume(TokenType.WORD)
            return ("WORD", token.value)

        # Error: unexpected token
        if self.position < self.length:
            token = self.tokens[self.position]
            raise ParseError(
                f"Expected WORD or '(' but got '{token.value}'",
                position=token.position,
                expression=self._reconstruct_expression(),
            )
        else:
            raise ParseError(
                "Expected WORD or '(' but reached end of expression",
                position=len(self._reconstruct_expression()),
                expression=self._reconstruct_expression(),
            )

    def _reconstruct_expression(self) -> str:
        """Reconstruct the original expression from tokens for error messages.

        Returns:
            Reconstructed expression string
        """
        if not self.tokens:
            return ""

        # Simple reconstruction: join token values
        parts = []
        for token in self.tokens:
            if token.type == TokenType.WORD and " " in token.value:
                parts.append(f'"{token.value}"')
            else:
                parts.append(token.value)

        return " ".join(parts)


def parse(expression: str) -> ASTNode:
    """Parse a boolean expression into an AST.

    Args:
        expression: The boolean expression to parse

    Returns:
        Root node of the AST

    Raises:
        TokenizationError: If tokenization fails
        ParseError: If parsing fails
    """
    tokens = tokenize(expression)
    parser = ExpressionParser(tokens)
    return parser.parse()
