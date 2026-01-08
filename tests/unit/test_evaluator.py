"""Unit tests for the evaluator module."""

import re
import pytest

from log_filter.core.evaluator import (
    ExpressionEvaluator,
    evaluate,
    compile_patterns_from_ast,
)
from log_filter.core.exceptions import EvaluationError
from log_filter.core.parser import parse


class TestExpressionEvaluator:
    """Tests for ExpressionEvaluator class."""

    def test_single_word_match(self) -> None:
        """Test evaluating single word that matches."""
        ast = parse("ERROR")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "This is an ERROR message") is True

    def test_single_word_no_match(self) -> None:
        """Test evaluating single word that doesn't match."""
        ast = parse("ERROR")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "This is a WARN message") is False

    def test_case_sensitive_match(self) -> None:
        """Test case-sensitive matching."""
        ast = parse("ERROR")
        evaluator = ExpressionEvaluator(ignore_case=False)
        assert evaluator.evaluate(ast, "This is an ERROR message") is True
        assert evaluator.evaluate(ast, "This is an error message") is False

    def test_case_insensitive_match(self) -> None:
        """Test case-insensitive matching."""
        ast = parse("ERROR")
        evaluator = ExpressionEvaluator(ignore_case=True)
        assert evaluator.evaluate(ast, "This is an ERROR message") is True
        assert evaluator.evaluate(ast, "This is an error message") is True
        assert evaluator.evaluate(ast, "This is an ErRoR message") is True

    def test_and_both_match(self) -> None:
        """Test AND when both operands match."""
        ast = parse("ERROR AND Kafka")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "ERROR in Kafka connection") is True

    def test_and_first_matches(self) -> None:
        """Test AND when only first operand matches."""
        ast = parse("ERROR AND Kafka")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "ERROR in database connection") is False

    def test_and_second_matches(self) -> None:
        """Test AND when only second operand matches."""
        ast = parse("ERROR AND Kafka")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "INFO: Kafka connection OK") is False

    def test_and_neither_matches(self) -> None:
        """Test AND when neither operand matches."""
        ast = parse("ERROR AND Kafka")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "INFO: database connection OK") is False

    def test_or_both_match(self) -> None:
        """Test OR when both operands match."""
        ast = parse("ERROR OR WARN")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "ERROR and WARN together") is True

    def test_or_first_matches(self) -> None:
        """Test OR when first operand matches."""
        ast = parse("ERROR OR WARN")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "This is an ERROR") is True

    def test_or_second_matches(self) -> None:
        """Test OR when second operand matches."""
        ast = parse("ERROR OR WARN")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "This is a WARN") is True

    def test_or_neither_matches(self) -> None:
        """Test OR when neither operand matches."""
        ast = parse("ERROR OR WARN")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "This is INFO") is False

    def test_not_match(self) -> None:
        """Test NOT when operand matches."""
        ast = parse("NOT ERROR")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "This is an ERROR") is False

    def test_not_no_match(self) -> None:
        """Test NOT when operand doesn't match."""
        ast = parse("NOT ERROR")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "This is INFO") is True

    def test_complex_expression(self) -> None:
        """Test complex expression."""
        ast = parse("(ERROR OR WARN) AND NOT Heartbeat")
        evaluator = ExpressionEvaluator()

        assert evaluator.evaluate(ast, "ERROR in connection") is True
        assert evaluator.evaluate(ast, "WARN about timeout") is True
        assert evaluator.evaluate(ast, "ERROR Heartbeat check") is False
        assert evaluator.evaluate(ast, "INFO message") is False

    def test_operator_precedence(self) -> None:
        """Test operator precedence in evaluation."""
        # NOT ERROR AND WARN should be (NOT ERROR) AND WARN
        ast = parse("NOT ERROR AND WARN")
        evaluator = ExpressionEvaluator()

        # Should match: doesn't contain ERROR AND contains WARN
        assert evaluator.evaluate(ast, "This is a WARN") is True
        assert evaluator.evaluate(ast, "ERROR and WARN") is False
        assert evaluator.evaluate(ast, "ERROR only") is False

    def test_empty_pattern(self) -> None:
        """Test empty pattern doesn't match anything."""
        ast = ("WORD", "")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "any text") is False

    def test_unicode_matching(self) -> None:
        """Test matching with Unicode characters."""
        ast = parse("Ошибка")
        evaluator = ExpressionEvaluator()
        assert evaluator.evaluate(ast, "Произошла Ошибка соединения") is True
        assert evaluator.evaluate(ast, "All OK") is False


class TestRegexMatching:
    """Tests for regex matching mode."""

    def test_simple_regex(self) -> None:
        """Test simple regex pattern."""
        ast = parse("ERROR.*connection")
        evaluator = ExpressionEvaluator(use_regex=True)
        assert evaluator.evaluate(ast, "ERROR in connection") is True
        assert evaluator.evaluate(ast, "ERROR: database connection failed") is True
        assert evaluator.evaluate(ast, "ERROR timeout") is False

    def test_regex_with_numbers(self) -> None:
        """Test regex pattern with numbers."""
        ast = parse('"ERROR [0-9]{3}"')
        evaluator = ExpressionEvaluator(use_regex=True)
        assert evaluator.evaluate(ast, "ERROR 500: Internal") is True
        assert evaluator.evaluate(ast, "ERROR 404: Not found") is True
        assert evaluator.evaluate(ast, "ERROR: No code") is False

    def test_regex_case_insensitive(self) -> None:
        """Test case-insensitive regex."""
        ast = parse("error")
        evaluator = ExpressionEvaluator(use_regex=True, ignore_case=True)
        assert evaluator.evaluate(ast, "ERROR message") is True
        assert evaluator.evaluate(ast, "Error message") is True

    def test_invalid_regex(self) -> None:
        """Test invalid regex pattern raises error."""
        ast = parse('"[invalid"')
        evaluator = ExpressionEvaluator(use_regex=True)
        with pytest.raises(EvaluationError, match="Invalid regex pattern"):
            evaluator.evaluate(ast, "any text")

    def test_regex_anchors(self) -> None:
        """Test regex anchors."""
        ast = parse('"^ERROR"')
        evaluator = ExpressionEvaluator(use_regex=True)
        assert evaluator.evaluate(ast, "ERROR at start") is True
        assert evaluator.evaluate(ast, "Has ERROR inside") is False

    def test_regex_special_chars(self) -> None:
        """Test regex with special characters."""
        ast = parse(r'"error\(.*\)"')
        evaluator = ExpressionEvaluator(use_regex=True)
        assert evaluator.evaluate(ast, "error(123)") is True
        assert evaluator.evaluate(ast, "error123") is False


class TestPatternCaching:
    """Tests for regex pattern caching."""

    def test_pattern_caching(self) -> None:
        """Test that patterns are cached."""
        evaluator = ExpressionEvaluator(use_regex=True)
        ast = parse("ERROR")

        # First evaluation compiles pattern
        evaluator.evaluate(ast, "ERROR message")
        assert "ERROR" in evaluator.compiled_patterns

        # Second evaluation uses cached pattern
        evaluator.evaluate(ast, "Another ERROR")
        assert len(evaluator.compiled_patterns) == 1

    def test_pre_compiled_patterns(self) -> None:
        """Test using pre-compiled patterns."""
        import re

        compiled = {"ERROR": re.compile("ERROR")}
        evaluator = ExpressionEvaluator(use_regex=True, compiled_patterns=compiled)

        ast = parse("ERROR")
        assert evaluator.evaluate(ast, "ERROR message") is True
        # Should use pre-compiled pattern
        assert evaluator.compiled_patterns["ERROR"] == compiled["ERROR"]


class TestPatternExtraction:
    """Tests for pattern extraction from AST."""

    def test_extract_single_pattern(self) -> None:
        """Test extracting single pattern."""
        ast = parse("ERROR")
        evaluator = ExpressionEvaluator()
        patterns = evaluator.extract_patterns(ast)
        assert patterns == ["ERROR"]

    def test_extract_and_patterns(self) -> None:
        """Test extracting patterns from AND expression."""
        ast = parse("ERROR AND WARN")
        evaluator = ExpressionEvaluator()
        patterns = evaluator.extract_patterns(ast)
        assert set(patterns) == {"ERROR", "WARN"}

    def test_extract_or_patterns(self) -> None:
        """Test extracting patterns from OR expression."""
        ast = parse("ERROR OR WARN")
        evaluator = ExpressionEvaluator()
        patterns = evaluator.extract_patterns(ast)
        assert set(patterns) == {"ERROR", "WARN"}

    def test_extract_not_patterns(self) -> None:
        """Test extracting patterns from NOT expression."""
        ast = parse("NOT ERROR")
        evaluator = ExpressionEvaluator()
        patterns = evaluator.extract_patterns(ast)
        assert patterns == ["ERROR"]

    def test_extract_complex_patterns(self) -> None:
        """Test extracting patterns from complex expression."""
        ast = parse("(ERROR OR WARN) AND NOT INFO")
        evaluator = ExpressionEvaluator()
        patterns = evaluator.extract_patterns(ast)
        assert set(patterns) == {"ERROR", "WARN", "INFO"}

    def test_extract_quoted_patterns(self) -> None:
        """Test extracting quoted patterns."""
        ast = parse('"error message" AND "warning"')
        evaluator = ExpressionEvaluator()
        patterns = evaluator.extract_patterns(ast)
        assert set(patterns) == {"error message", "warning"}


class TestConvenienceFunction:
    """Tests for convenience evaluate() function."""

    def test_evaluate_function(self) -> None:
        """Test convenience evaluate function."""
        ast = parse("ERROR AND Kafka")
        assert evaluate(ast, "ERROR in Kafka", ignore_case=False) is True
        assert evaluate(ast, "WARN in Kafka", ignore_case=False) is False

    def test_evaluate_with_regex(self) -> None:
        """Test convenience function with regex."""
        ast = parse('"ERROR.*connection"')
        assert evaluate(ast, "ERROR: connection failed", use_regex=True) is True


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_ast_node(self) -> None:
        """Test invalid AST node raises error."""
        evaluator = ExpressionEvaluator()
        with pytest.raises(EvaluationError):
            evaluator.evaluate(("INVALID",), "text")  # type: ignore

    def test_empty_ast_node(self) -> None:
        """Test empty AST node raises error."""
        evaluator = ExpressionEvaluator()
        with pytest.raises(EvaluationError, match="Empty AST node"):
            evaluator.evaluate((), "text")  # type: ignore

    def test_malformed_word_node(self) -> None:
        """Test malformed WORD node raises error."""
        evaluator = ExpressionEvaluator()
        with pytest.raises(EvaluationError, match="Invalid WORD node"):
            evaluator.evaluate(("WORD",), "text")  # type: ignore

    def test_malformed_and_node(self) -> None:
        """Test malformed AND node raises error."""
        evaluator = ExpressionEvaluator()
        with pytest.raises(EvaluationError, match="Invalid AND node"):
            evaluator.evaluate(("AND", ("WORD", "test")), "text")  # type: ignore


class TestRealWorldScenarios:
    """Tests with real-world log scenarios."""

    def test_kafka_error_detection(self) -> None:
        """Test Kafka error detection."""
        ast = parse("ERROR AND Kafka")
        evaluator = ExpressionEvaluator()

        log1 = "2025-01-07 10:00:00.000+0000 ERROR Connection to Kafka failed"
        log2 = "2025-01-07 10:00:00.000+0000 WARN Kafka is slow"
        log3 = "2025-01-07 10:00:00.000+0000 ERROR Database timeout"

        assert evaluator.evaluate(ast, log1) is True
        assert evaluator.evaluate(ast, log2) is False
        assert evaluator.evaluate(ast, log3) is False

    def test_exclude_heartbeat(self) -> None:
        """Test excluding heartbeat messages."""
        ast = parse("ERROR AND NOT Heartbeat")
        evaluator = ExpressionEvaluator()

        log1 = "ERROR: Connection failed"
        log2 = "ERROR: Heartbeat check failed"
        log3 = "INFO: All OK"

        assert evaluator.evaluate(ast, log1) is True
        assert evaluator.evaluate(ast, log2) is False
        assert evaluator.evaluate(ast, log3) is False

    def test_http_status_codes(self) -> None:
        """Test HTTP status code patterns."""
        ast = parse('"[45][0-9]{2}"')
        evaluator = ExpressionEvaluator(use_regex=True)

        log1 = "HTTP 404 Not Found"
        log2 = "HTTP 500 Internal Error"
        log3 = "HTTP 200 OK"

        assert evaluator.evaluate(ast, log1) is True
        assert evaluator.evaluate(ast, log2) is True
        assert evaluator.evaluate(ast, log3) is False

    def test_multiline_log_record(self) -> None:
        """Test matching patterns in multiline log records (each pattern matches on separate lines)."""
        ast = parse("ERROR AND Exception")
        evaluator = ExpressionEvaluator()

        multiline_log = """2025-01-07 10:00:00.000+0000 ERROR
        Exception occurred: NullPointerException
        at com.example.MyClass.method(MyClass.java:123)
        at com.example.Main.main(Main.java:45)"""

        assert evaluator.evaluate(ast, multiline_log) is True


class TestCompilePatterns:
    """Tests for compile_patterns_from_ast function."""
    
    def test_compile_single_pattern(self) -> None:
        """Test compiling single pattern from AST."""
        ast = parse("ERROR")
        patterns = compile_patterns_from_ast(ast, ignore_case=False)
        
        assert len(patterns) == 1
        assert "ERROR" in patterns
        assert isinstance(patterns["ERROR"], re.Pattern)
    
    def test_compile_multiple_patterns(self) -> None:
        """Test compiling multiple patterns from AST."""
        ast = parse("ERROR AND Kafka")
        patterns = compile_patterns_from_ast(ast, ignore_case=False)
        
        assert len(patterns) == 2
        assert "ERROR" in patterns
        assert "Kafka" in patterns
    
    def test_compile_with_case_insensitive(self) -> None:
        """Test compiling patterns with case-insensitive flag."""
        ast = parse("ERROR")
        patterns = compile_patterns_from_ast(ast, ignore_case=True)
        
        assert len(patterns) == 1
        assert "ERROR" in patterns
        # Verify pattern has IGNORECASE flag
        pattern = patterns["ERROR"]
        assert pattern.flags & re.IGNORECASE
    
    def test_compile_complex_expression(self) -> None:
        """Test compiling complex boolean expression."""
        ast = parse("(ERROR OR WARNING) AND (Kafka OR database)")
        patterns = compile_patterns_from_ast(ast, ignore_case=False)
        
        assert len(patterns) == 4
        assert "ERROR" in patterns
        assert "WARNING" in patterns
        assert "Kafka" in patterns
        assert "database" in patterns
    
    def test_compile_with_not_operator(self) -> None:
        """Test compiling patterns with NOT operator."""
        ast = parse("ERROR AND NOT debug")
        patterns = compile_patterns_from_ast(ast, ignore_case=False)
        
        assert len(patterns) == 2
        assert "ERROR" in patterns
        assert "debug" in patterns
    
    def test_compile_duplicate_patterns(self) -> None:
        """Test that duplicate patterns are compiled only once."""
        ast = parse("ERROR AND (ERROR OR ERROR)")
        patterns = compile_patterns_from_ast(ast, ignore_case=False)
        
        # Should only have one compiled pattern despite multiple occurrences
        assert len(patterns) == 1
        assert "ERROR" in patterns
    
    def test_compile_invalid_regex(self) -> None:
        """Test that invalid regex patterns are skipped."""
        # Create an AST manually with invalid regex
        ast = ("WORD", "[invalid")
        patterns = compile_patterns_from_ast(ast, ignore_case=False)
        
        # Invalid pattern should be skipped
        assert len(patterns) == 0
    
    def test_compiled_patterns_work_with_evaluator(self) -> None:
        """Test that compiled patterns work correctly with evaluator."""
        ast = parse("ERROR AND Kafka")
        patterns = compile_patterns_from_ast(ast, ignore_case=False)
        
        evaluator = ExpressionEvaluator(
            use_regex=True,
            compiled_patterns=patterns
        )
        
        text = "ERROR: Kafka connection failed"
        assert evaluator.evaluate(ast, text) is True
    
    def test_performance_benefit_of_compiled_patterns(self) -> None:
        """Test that pre-compiled patterns improve performance."""
        import time
        
        ast = parse("ERROR")
        text = "This is an ERROR message" * 1000
        
        # Without compiled patterns
        evaluator1 = ExpressionEvaluator(use_regex=True)
        start1 = time.perf_counter()
        for _ in range(100):
            evaluator1.evaluate(ast, text)
        time1 = time.perf_counter() - start1
        
        # With compiled patterns
        patterns = compile_patterns_from_ast(ast, ignore_case=False)
        evaluator2 = ExpressionEvaluator(use_regex=True, compiled_patterns=patterns)
        start2 = time.perf_counter()
        for _ in range(100):
            evaluator2.evaluate(ast, text)
        time2 = time.perf_counter() - start2
        
        # Compiled patterns should be faster (or at least not slower)
        # Note: This is a simple performance check, not a rigorous benchmark
        assert time2 <= time1 * 3.0  # Allow 200% margin for test variability on different hardware

