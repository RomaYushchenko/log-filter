"""Benchmarks for expression evaluation performance.

Tests pattern matching, regex compilation, and evaluation operations.
"""

from log_filter.core.evaluator import ExpressionEvaluator, compile_patterns_from_ast
from log_filter.core.parser import ExpressionParser


class TestEvaluation:
    """Benchmark expression evaluation operations."""

    def test_simple_word_match(self, benchmark):
        """Benchmark simple word matching (substring search).

        Target: < 1ms for 1000 evaluations
        """
        parser = ExpressionParser()
        ast = parser.parse("ERROR")
        evaluator = ExpressionEvaluator(ast)

        # Mix of matching and non-matching lines
        texts = [
            "2026-02-03 10:30:45.123+0000 ERROR Connection timeout",
            "2026-02-03 10:30:46.123+0000 INFO Request completed",
        ] * 500

        def evaluate_all():
            return sum(1 for text in texts if evaluator.evaluate(text))

        match_count = benchmark(evaluate_all)
        assert match_count == 500  # Half should match

    def test_and_expression(self, benchmark):
        """Benchmark AND expression evaluation.

        Target: < 2ms for 1000 evaluations
        """
        parser = ExpressionParser()
        ast = parser.parse("ERROR AND timeout")
        evaluator = ExpressionEvaluator(ast)

        texts = [
            "2026-02-03 10:30:45.123+0000 ERROR Connection timeout",
            "2026-02-03 10:30:46.123+0000 ERROR Database error",
            "2026-02-03 10:30:47.123+0000 INFO Request completed",
        ] * 333

        def evaluate_all():
            return sum(1 for text in texts if evaluator.evaluate(text))

        match_count = benchmark(evaluate_all)
        assert match_count == 333  # Only lines with both ERROR and timeout

    def test_complex_expression(self, benchmark):
        """Benchmark complex expression evaluation.

        Target: < 5ms for 1000 evaluations
        """
        parser = ExpressionParser()
        ast = parser.parse("(ERROR OR FATAL) AND NOT heartbeat")
        evaluator = ExpressionEvaluator(ast)

        texts = [
            "2026-02-03 10:30:45.123+0000 ERROR Connection failed",
            "2026-02-03 10:30:46.123+0000 FATAL System shutdown",
            "2026-02-03 10:30:47.123+0000 INFO heartbeat received",
            "2026-02-03 10:30:48.123+0000 ERROR heartbeat timeout",
            "2026-02-03 10:30:49.123+0000 INFO Request completed",
        ] * 200

        def evaluate_all():
            return sum(1 for text in texts if evaluator.evaluate(text))

        match_count = benchmark(evaluate_all)
        # Should match ERROR and FATAL lines, but not heartbeat lines
        assert match_count == 400

    def test_regex_match(self, benchmark):
        """Benchmark regex pattern matching.

        Target: < 10ms for 1000 evaluations
        """
        parser = ExpressionParser()
        ast = parser.parse(r"/\d{3}-\d{4}/")  # Match phone number pattern
        compiled_patterns = compile_patterns_from_ast(ast, use_regex=True)
        evaluator = ExpressionEvaluator(ast, use_regex=True, compiled_patterns=compiled_patterns)

        texts = [
            "Contact support at 555-1234",
            "Error code: ABC-9876",
            "Call 123-4567 for help",
            "No phone number here",
        ] * 250

        def evaluate_all():
            return sum(1 for text in texts if evaluator.evaluate(text))

        match_count = benchmark(evaluate_all)
        assert match_count == 500  # Lines with NNN-NNNN pattern

    def test_case_insensitive_match(self, benchmark):
        """Benchmark case-insensitive substring matching.

        Target: < 2ms for 1000 evaluations
        """
        parser = ExpressionParser()
        ast = parser.parse("error")
        evaluator = ExpressionEvaluator(ast, ignore_case=True)

        texts = [
            "ERROR: Connection failed",
            "Error processing request",
            "error in module",
            "INFO: All systems operational",
        ] * 250

        def evaluate_all():
            return sum(1 for text in texts if evaluator.evaluate(text))

        match_count = benchmark(evaluate_all)
        assert match_count == 750  # Lines with error/Error/ERROR


class TestPatternCompilation:
    """Benchmark pattern compilation operations."""

    def test_compile_patterns_from_ast(self, benchmark):
        """Benchmark pattern compilation from AST.

        Should be done once during initialization, not per-evaluation.

        Target: < 5ms
        """
        parser = ExpressionParser()
        ast = parser.parse("(ERROR OR FATAL) AND NOT heartbeat")

        def compile_patterns():
            return compile_patterns_from_ast(ast, use_regex=False, ignore_case=True)

        patterns = benchmark(compile_patterns)
        assert len(patterns) > 0

    def test_regex_pattern_compilation(self, benchmark):
        """Benchmark regex pattern compilation.

        Target: < 10ms for complex regex
        """
        parser = ExpressionParser()
        ast = parser.parse(r"/ERROR.*timeout.*connection/")

        def compile_patterns():
            return compile_patterns_from_ast(ast, use_regex=True)

        patterns = benchmark(compile_patterns)
        assert len(patterns) > 0
