Core Module
===========

The core module provides the foundational components for boolean expression parsing and evaluation.

.. contents:: Contents
   :local:
   :depth: 2

Tokenizer
---------

.. automodule:: log_filter.core.tokenizer
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

The tokenizer converts boolean expressions into a sequence of tokens.

Example
^^^^^^^

.. code-block:: python

    from log_filter.core.tokenizer import tokenize, TokenType

    # Tokenize an expression
    tokens = tokenize("ERROR AND (database OR timeout)")

    for token in tokens:
        print(f"{token.type}: {token.value}")

    # Output:
    # WORD: ERROR
    # AND: AND
    # LPAREN: (
    # WORD: database
    # OR: OR
    # WORD: timeout
    # RPAREN: )

Parser
------

.. automodule:: log_filter.core.parser
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

The parser converts tokens into an Abstract Syntax Tree (AST).

Example
^^^^^^^

.. code-block:: python

    from log_filter.core.parser import parse

    # Parse an expression
    ast = parse("ERROR AND database")

    # The AST can be passed to the Evaluator
    print(type(ast))  # <class 'log_filter.core.parser.ASTNode'>

Evaluator
---------

.. automodule:: log_filter.core.evaluator
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

The evaluator traverses the AST and evaluates expressions against text.

Example
^^^^^^^

.. code-block:: python

    from log_filter.core.parser import parse
    from log_filter.core.evaluator import Evaluator

    # Create evaluator from expression
    ast = parse("ERROR OR WARNING")
    evaluator = Evaluator(ast, case_sensitive=False)

    # Evaluate against text
    result1 = evaluator.evaluate("Error in database connection")
    print(result1)  # True

    result2 = evaluator.evaluate("Info: Operation completed")
    print(result2)  # False

Exceptions
----------

.. automodule:: log_filter.core.exceptions
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Custom exceptions for error handling.

Exception Hierarchy
^^^^^^^^^^^^^^^^^^^

.. code-block:: text

    LogFilterException
    ├── ParseError
    │   └── TokenizationError
    ├── EvaluationError
    ├── ConfigurationError
    ├── FileHandlingError
    └── RecordSizeExceededError

Example
^^^^^^^

.. code-block:: python

    from log_filter.core.parser import parse
    from log_filter.core.exceptions import ParseError

    try:
        ast = parse("ERROR AND AND database")  # Invalid syntax
    except ParseError as e:
        print(f"Parse error: {e}")

Complete Workflow
-----------------

Here's a complete example combining tokenizer, parser, and evaluator:

.. code-block:: python

    from log_filter.core.tokenizer import tokenize
    from log_filter.core.parser import ExpressionParser
    from log_filter.core.evaluator import Evaluator

    # Full tokenize → parse → evaluate workflow
    expression = "(ERROR OR WARNING) AND database"

    # Step 1: Tokenize
    tokens = tokenize(expression)
    print(f"Tokens: {[t.value for t in tokens]}")

    # Step 2: Parse
    parser = ExpressionParser(tokens)
    ast = parser.parse()

    # Step 3: Evaluate
    evaluator = Evaluator(ast, case_sensitive=False)

    test_texts = [
        "ERROR: Database connection lost",      # True
        "WARNING: Database slow response",      # True
        "INFO: Database backup completed",      # False
        "ERROR: Network timeout",               # False
    ]

    for text in test_texts:
        result = evaluator.evaluate(text)
        print(f"{result:5} | {text}")

Performance Considerations
--------------------------

* **Tokenization**: O(n) where n is the expression length (~30μs for typical expressions)
* **Parsing**: O(n) where n is the number of tokens
* **Evaluation**: O(m) where m is the text length being searched
* **Regex Compilation**: Patterns are compiled once and reused

Best Practices
--------------

1. **Compile Once**: Create the evaluator once and reuse it for multiple evaluations
2. **Case Sensitivity**: Use ``case_sensitive=False`` for case-insensitive matching (default is True)
3. **Error Handling**: Always catch ``ParseError`` when parsing user-provided expressions
4. **Expression Validation**: Validate expressions before creating the evaluator

Thread Safety
-------------

* **Tokenizer**: Thread-safe (no shared state)
* **Parser**: Thread-safe (no shared state)
* **Evaluator**: Thread-safe for evaluation (read-only operations)

The evaluator can be safely shared across multiple threads for concurrent evaluations.
