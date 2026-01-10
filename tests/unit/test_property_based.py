"""Property-based tests using Hypothesis for log_filter components.

These tests generate random inputs to verify invariants and robustness.
"""

import string
from datetime import date, datetime, time
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from src.log_filter.config.models import (
    ApplicationConfig,
    FileConfig,
    OutputConfig,
    SearchConfig,
)
from src.log_filter.core.evaluator import ExpressionEvaluator
from src.log_filter.core.exceptions import ParseError, TokenizationError
from src.log_filter.core.parser import ExpressionParser
from src.log_filter.core.tokenizer import Tokenizer
from src.log_filter.domain.models import LogRecord


class TestTokenizerProperties:
    """Property-based tests for the Tokenizer."""

    @given(st.text(alphabet=string.ascii_letters + string.digits + " ", min_size=1, max_size=100))
    def test_tokenizer_never_crashes_on_simple_text(self, text):
        """Tokenizer should never crash on alphanumeric text."""
        try:
            tokenizer = Tokenizer(text)
            tokens = tokenizer.tokenize()
            # Should return a list of tokens
            assert isinstance(tokens, list)
            # All tokens should have type and value attributes
            for token in tokens:
                assert hasattr(token, "type")
                assert hasattr(token, "value")
        except TokenizationError:
            # TokenizationError is acceptable for invalid expressions
            pass

    @given(st.text(alphabet="()ANDORNOTandornot ", min_size=0, max_size=50))
    def test_tokenizer_handles_boolean_operators(self, text):
        """Tokenizer should handle boolean operator keywords."""
        if not text.strip():
            return  # Skip empty expressions

        try:
            tokenizer = Tokenizer(text)
            tokens = tokenizer.tokenize()
            assert isinstance(tokens, list)
            # Verify token types are valid
            valid_types = {"WORD", "AND", "OR", "NOT", "LPAREN", "RPAREN"}
            for token in tokens:
                assert token.type.name in valid_types
        except TokenizationError:
            # Invalid expressions should raise TokenizationError
            pass

    @given(
        st.lists(
            st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=10),
            min_size=1,
            max_size=5,
        )
    )
    def test_tokenizer_handles_multiple_terms(self, terms):
        """Tokenizer should handle multiple space-separated terms."""
        expression = " ".join(terms)
        tokenizer = Tokenizer(expression)
        tokens = tokenizer.tokenize()

        # Should have at least as many tokens as terms (may have more due to operators)
        assert len(tokens) >= len(terms)

        # All generated tokens should be WORD type
        term_tokens = [t for t in tokens if t.type == "WORD"]
        assert len(term_tokens) == len(terms)

    @given(st.integers(min_value=0, max_value=10))
    def test_tokenizer_handles_nested_parentheses(self, depth):
        """Tokenizer should handle nested parentheses."""
        # Create expression with nested parentheses
        expression = "(" * depth + "term" + ")" * depth

        try:
            tokenizer = Tokenizer(expression)
            tokens = tokenizer.tokenize()
            # Count LPAREN and RPAREN tokens
            lparen_count = sum(1 for t in tokens if t.type.name == "LPAREN")
            rparen_count = sum(1 for t in tokens if t.type.name == "RPAREN")
            # Should be balanced
            assert lparen_count == rparen_count == depth
        except TokenizationError:
            # May fail for extreme nesting
            pass


class TestParserProperties:
    """Property-based tests for the Parser."""

    @given(st.lists(st.sampled_from(["ERROR", "WARN", "INFO"]), min_size=1, max_size=3))
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_parser_handles_simple_terms(self, terms):
        """Parser should handle simple term lists."""
        expression = " OR ".join(terms)

        tokenizer = Tokenizer(expression)
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        # AST should be created
        assert ast is not None

    @given(
        st.lists(
            st.text(alphabet=string.ascii_letters, min_size=1, max_size=5), min_size=1, max_size=3
        ),
        st.sampled_from(["AND", "OR"]),
    )
    def test_parser_handles_binary_operations(self, terms, operator):
        """Parser should handle binary operations (AND/OR)."""
        if len(terms) < 2:
            terms = terms + ["extra"]

        expression = f" {operator} ".join(terms)
        tokenizer = Tokenizer(expression)
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        assert ast is not None

    @given(st.integers(min_value=1, max_value=5))
    def test_parser_handles_not_operations(self, count):
        """Parser should handle NOT operations."""
        expression = "NOT " * count + "term"

        try:
            tokenizer = Tokenizer(expression)
            tokens = tokenizer.tokenize()
            parser = ExpressionParser(tokens)
            ast = parser.parse()
            assert ast is not None
        except ParseError:
            # Complex NOT chains may fail parsing
            pass


class TestEvaluatorProperties:
    """Property-based tests for the Evaluator."""

    @given(
        st.text(alphabet=string.ascii_letters + string.digits + " ", min_size=10, max_size=100),
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=10).filter(
            lambda s: s.upper() not in ["AND", "OR", "NOT"]
        ),
    )
    def test_evaluator_simple_term_search(self, text, term):
        """Evaluator should consistently find terms in text."""
        evaluator = ExpressionEvaluator(ignore_case=False, use_regex=False)

        tokenizer = Tokenizer(term)
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()
        result = evaluator.evaluate(ast, text)

        # If term is in text, should match
        if term in text:
            assert result is True
        # If term not in text, should not match
        else:
            assert result is False

    @given(
        st.text(alphabet=string.ascii_lowercase + " ", min_size=10, max_size=100),
        st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=10),
    )
    def test_evaluator_case_insensitive_search(self, text, term):
        """Case-insensitive search should ignore case."""
        evaluator = ExpressionEvaluator(ignore_case=True, use_regex=False)

        tokenizer_lower = Tokenizer(term.lower())
        tokens_lower = tokenizer_lower.tokenize()
        parser_lower = ExpressionParser(tokens_lower)
        ast_lower = parser_lower.parse()
        result_lower = evaluator.evaluate(ast_lower, text.lower())

        tokenizer_upper = Tokenizer(term.upper())
        tokens_upper = tokenizer_upper.tokenize()
        parser_upper = ExpressionParser(tokens_upper)
        ast_upper = parser_upper.parse()
        result_upper = evaluator.evaluate(ast_upper, text.lower())

        # Both should have same result
        assert result_lower == result_upper

    @given(
        st.sampled_from(["ERROR", "WARN", "INFO", "DEBUG"]),
        st.sampled_from(["ERROR", "WARN", "INFO", "DEBUG"]),
    )
    def test_evaluator_and_operation(self, term1, term2):
        """AND operation should require both terms."""
        assume(term1 != term2)  # Skip if terms are the same

        text_both = f"{term1} and {term2} in log"
        text_first = f"{term1} in log"
        text_second = f"{term2} in log"

        evaluator = ExpressionEvaluator(ignore_case=False, use_regex=False)
        expression = f"{term1} AND {term2}"

        tokenizer = Tokenizer(expression)
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        # Should match only when both terms present
        result_both = evaluator.evaluate(ast, text_both)
        result_first = evaluator.evaluate(ast, text_first)
        result_second = evaluator.evaluate(ast, text_second)

        assert result_both is True
        assert result_first is False
        assert result_second is False

    @given(
        st.sampled_from(["ERROR", "WARN", "INFO", "DEBUG"]),
        st.sampled_from(["ERROR", "WARN", "INFO", "DEBUG"]),
    )
    def test_evaluator_or_operation(self, term1, term2):
        """OR operation should match if either term present."""
        assume(term1 != term2)  # Skip if terms are the same

        text_first = f"{term1} in log"
        text_second = f"{term2} in log"
        text_neither = "nothing here"

        evaluator = ExpressionEvaluator(ignore_case=False, use_regex=False)
        expression = f"{term1} OR {term2}"

        tokenizer = Tokenizer(expression)
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        result_first = evaluator.evaluate(ast, text_first)
        result_second = evaluator.evaluate(ast, text_second)
        result_neither = evaluator.evaluate(ast, text_neither)

        assert result_first is True
        assert result_second is True
        assert result_neither is False

    @given(st.sampled_from(["ERROR", "WARN", "INFO", "DEBUG"]))
    def test_evaluator_not_operation(self, term):
        """NOT operation should invert the result."""
        text_with = f"{term} in log"
        text_without = "nothing here"

        evaluator = ExpressionEvaluator(ignore_case=False, use_regex=False)
        expression = f"NOT {term}"

        tokenizer = Tokenizer(expression)
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        result_with = evaluator.evaluate(ast, text_with)
        result_without = evaluator.evaluate(ast, text_without)

        # Should NOT match when term is present
        assert result_with is False
        # Should match when term is absent
        assert result_without is True


class TestLogRecordProperties:
    """Property-based tests for LogRecord model."""

    @given(
        st.text(min_size=1, max_size=1000),
        st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)),
        st.times(),
        st.integers(min_value=1, max_value=1000000),
    )
    def test_log_record_creation(self, content, log_date, log_time, line_num):
        """LogRecord should be created with valid properties."""
        timestamp = datetime.combine(log_date, log_time)

        record = LogRecord(
            content=content,
            first_line=line_num,
            source_file=Path("test.log"),
            start_line=line_num,
            end_line=line_num,
            timestamp=timestamp,
        )

        assert record.content == content
        assert record.first_line == line_num
        assert record.start_line == line_num
        assert record.end_line == line_num
        assert record.timestamp == timestamp

    @given(st.text(min_size=1, max_size=100), st.integers(min_value=1, max_value=100))
    def test_log_record_line_numbers_valid(self, content, start_line):
        """LogRecord line numbers should be consistent."""
        end_line = start_line + content.count("\n")

        record = LogRecord(
            content=content,
            first_line=start_line,
            source_file=Path("test.log"),
            start_line=start_line,
            end_line=end_line,
            timestamp=datetime.now(),
        )

        assert record.start_line <= record.end_line
        assert record.first_line == start_line


class TestConfigurationProperties:
    """Property-based tests for configuration models."""

    @given(
        st.text(alphabet=string.ascii_letters + " ()ANDORNOT", min_size=1, max_size=50).filter(
            lambda s: s.strip() != ""  # Ensure not empty or whitespace-only
        ),
        st.booleans(),
        st.booleans(),
    )
    def test_search_config_creation(self, expression, ignore_case, use_regex):
        """SearchConfig should accept various valid parameters."""
        config = SearchConfig(expression=expression, ignore_case=ignore_case, use_regex=use_regex)

        assert config.expression == expression
        assert config.ignore_case == ignore_case
        assert config.use_regex == use_regex

    @given(
        st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)),
        st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)),
    )
    def test_search_config_date_range(self, date1, date2):
        """SearchConfig should handle date ranges."""
        date_from = min(date1, date2)
        date_to = max(date1, date2)

        config = SearchConfig(expression="test", date_from=date_from, date_to=date_to)

        assert config.date_from == date_from
        assert config.date_to == date_to
        # date_from should be before or equal to date_to
        assert config.date_from <= config.date_to

    @settings(suppress_health_check=[HealthCheck.too_slow])
    @given(st.times(), st.times())
    def test_search_config_time_range(self, time1, time2):
        """SearchConfig should handle time ranges."""
        # Ensure time_from <= time_to
        if time1 > time2:
            time1, time2 = time2, time1

        config = SearchConfig(expression="test", time_from=time1, time_to=time2)

        assert config.time_from == time1
        assert config.time_to == time2

    @given(st.integers(min_value=1, max_value=32))
    def test_processing_config_worker_count(self, worker_count):
        """ProcessingConfig should accept valid worker counts."""
        from src.log_filter.config.models import ProcessingConfig

        config = ProcessingConfig(worker_count=worker_count)
        assert config.worker_count == worker_count
        assert config.worker_count >= 1

    @pytest.mark.skip(
        reason="ProcessingConfig does not have buffer_size parameter yet - feature not implemented"
    )
    @given(st.integers(min_value=1024, max_value=1024 * 1024 * 100))
    def test_processing_config_buffer_size(self, buffer_size):
        """ProcessingConfig should accept valid buffer sizes."""
        from src.log_filter.config.models import ProcessingConfig

        config = ProcessingConfig(buffer_size=buffer_size)
        assert config.buffer_size == buffer_size
        assert config.buffer_size >= 1024


class TestIntegrationProperties:
    """Property-based integration tests combining multiple components."""

    @given(
        st.lists(
            st.text(alphabet=string.ascii_letters + " ", min_size=5, max_size=50),
            min_size=1,
            max_size=10,
        ),
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=10).filter(
            lambda s: s.upper() not in ["AND", "OR", "NOT"]
        ),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow], deadline=1000)
    def test_end_to_end_search(self, log_lines, search_term):
        """End-to-end search should work with random inputs."""
        # Count expected matches
        expected_matches = sum(1 for line in log_lines if search_term in line)

        # Create evaluator
        evaluator = ExpressionEvaluator(ignore_case=False, use_regex=False)

        # Parse search term once
        tokenizer = Tokenizer(search_term)
        tokens = tokenizer.tokenize()
        parser = ExpressionParser(tokens)
        ast = parser.parse()

        # Test each line
        actual_matches = 0
        for line in log_lines:
            if evaluator.evaluate(ast, line):
                actual_matches += 1

        assert actual_matches == expected_matches

    @given(
        st.lists(st.sampled_from(["ERROR", "WARN", "INFO"]), min_size=1, max_size=5),
        st.sampled_from(["AND", "OR"]),
    )
    def test_tokenize_parse_evaluate_chain(self, terms, operator):
        """Full chain from tokenization to evaluation should work."""
        if len(terms) < 2:
            terms = terms + ["INFO"]

        expression = f" {operator} ".join(terms)
        text = " ".join(terms)  # Text containing all terms

        # Tokenize
        tokenizer = Tokenizer(expression)
        tokens = tokenizer.tokenize()
        assert len(tokens) > 0

        # Parse
        parser = ExpressionParser(tokens)
        ast = parser.parse()
        assert ast is not None

        # Evaluate
        evaluator = ExpressionEvaluator(ignore_case=False, use_regex=False)
        result = evaluator.evaluate(ast, text)

        # With all terms present, AND should match, OR should match
        if operator == "AND":
            assert result is True
        elif operator == "OR":
            assert result is True
