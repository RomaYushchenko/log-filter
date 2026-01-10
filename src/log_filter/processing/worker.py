"""
Worker module for processing individual log files.

This module provides the worker logic for processing a single file
including reading, parsing, filtering, matching, and writing results.
"""

import logging
import time

from log_filter.config.models import ApplicationConfig
from log_filter.core.evaluator import ExpressionEvaluator, compile_patterns_from_ast
from log_filter.core.exceptions import (
    FileHandlingError,
    RecordSizeExceededError,
)
from log_filter.domain.filters import RecordFilter
from log_filter.domain.models import ASTNode, FileMetadata, SearchResult
from log_filter.infrastructure.file_handler_factory import FileHandlerFactory
from log_filter.infrastructure.file_writer import BufferedLogWriter
from log_filter.processing.record_parser import StreamingRecordParser
from log_filter.statistics.collector import StatisticsCollector
from log_filter.utils.highlighter import TextHighlighter

logger = logging.getLogger(__name__)


class FileWorker:
    """Worker for processing a single log file.

    Encapsulates the logic for:
    1. Opening and reading the file
    2. Parsing log records
    3. Filtering by date/time
    4. Evaluating search expression
    5. Writing matching records
    6. Collecting statistics

    Attributes:
        handler_factory: Factory for creating file handlers
        record_parser: Parser for extracting log records
        record_filter: Filter for date/time constraints
        stats_collector: Collector for statistics

    Example:
        >>> worker = FileWorker(
        ...     handler_factory=factory,
        ...     record_parser=parser,
        ...     record_filter=filter,
        ...     stats_collector=stats
        ... )
        >>> worker.process_file(file_meta, ast, writer, config)
    """

    def __init__(
        self,
        handler_factory: FileHandlerFactory,
        record_parser: StreamingRecordParser,
        record_filter: RecordFilter,
        stats_collector: StatisticsCollector,
    ) -> None:
        """Initialize the file worker.

        Args:
            handler_factory: Factory for creating file handlers
            record_parser: Parser for extracting log records
            record_filter: Filter for date/time constraints
            stats_collector: Collector for statistics
        """
        self.handler_factory = handler_factory
        self.record_parser = record_parser
        self.record_filter = record_filter
        self.stats_collector = stats_collector
        self.highlighter = TextHighlighter()

    def process_file(
        self,
        file_meta: FileMetadata,
        ast: ASTNode,
        writer: BufferedLogWriter,
        config: ApplicationConfig,
    ) -> int:
        """Process a single log file.

        Args:
            file_meta: File metadata
            ast: Parsed search expression AST
            writer: Output writer
            config: Application configuration

        Returns:
            Number of matching records found

        Raises:
            FileHandlingError: If file cannot be processed
        """
        file_path = file_meta.path
        matches_found = 0

        # Pre-compile regex patterns for performance (if using regex mode)
        compiled_patterns = None
        if config.search.use_regex:
            compiled_patterns = compile_patterns_from_ast(
                ast, ignore_case=config.search.ignore_case
            )

        # Create evaluator with config settings and compiled patterns
        evaluator = ExpressionEvaluator(
            ignore_case=config.search.ignore_case,
            use_regex=config.search.use_regex,
            compiled_patterns=compiled_patterns,
        )

        # Extract patterns for highlighting if needed
        patterns = evaluator.extract_patterns(ast) if config.output.highlight_matches else []

        try:
            # Create appropriate handler
            handler = self.handler_factory.create_handler(file_path)

            # Validate file can be read
            is_valid, error_msg = handler.validate()
            if not is_valid:
                logger.warning(f"Skipping {file_path}: {error_msg}")
                self.stats_collector.increment_files_skipped(error_msg or "validation-failed")
                return 0

            # Read lines from file
            lines = handler.read_lines()

            # Parse into log records
            records = self.record_parser.parse_lines(lines, str(file_path))

            # Process each record with periodic progress updates
            records_processed = 0
            bytes_processed_in_file = 0
            last_progress_time = time.time()

            for record in records:
                records_processed += 1
                bytes_processed_in_file += record.size_bytes
                self.stats_collector.increment_records_total()
                self.stats_collector.add_bytes_processed(record.size_bytes)
                self.stats_collector.add_lines_processed(record.line_count)

                # Log progress every 50,000 records or every 30 seconds
                current_time = time.time()
                if (records_processed % 50000 == 0) or (current_time - last_progress_time > 30):
                    mb_processed = bytes_processed_in_file / (1024 * 1024)
                    logger.debug(
                        f"Processing {file_path.name}: {records_processed:,} records, "
                        f"{mb_processed:.1f} MB processed"
                    )
                    last_progress_time = current_time

                # Apply date/time filter
                if not self.record_filter.matches(record):
                    self.stats_collector.increment_records_skipped()
                    continue

                # Evaluate search expression
                matches = evaluator.evaluate(ast, record.content)

                if matches:
                    matches_found += 1
                    self.stats_collector.increment_records_matched()

                    # Apply highlighting if configured
                    highlighted_content = None
                    if config.output.highlight_matches and patterns:
                        highlighted_content = self.highlighter.highlight(
                            record.content,
                            patterns,
                            ignore_case=config.search.ignore_case,
                            use_regex=config.search.use_regex,
                        )

                    # Create search result
                    result = SearchResult(
                        record=record,
                        matched=bool(patterns),
                        match_positions=patterns if patterns else [],
                        highlighted_content=highlighted_content,
                    )

                    # Write to output
                    writer.write_result(
                        result, source_path=file_path, use_highlight=config.output.highlight_matches
                    )

            self.stats_collector.increment_files_processed()
            logger.debug(f"Processed {file_path}: {matches_found} matches")

            return matches_found

        except RecordSizeExceededError as e:
            logger.warning(f"Record size exceeded in {file_path}: {e}")
            self.stats_collector.increment_files_skipped("record-size-exceeded")
            return matches_found

        except FileHandlingError as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.stats_collector.increment_files_skipped("error")
            return matches_found

        except Exception as e:
            logger.error(f"Unexpected error processing {file_path}: {e}", exc_info=True)
            self.stats_collector.increment_files_skipped("unexpected-error")
            return matches_found

    def __repr__(self) -> str:
        """String representation of the worker."""
        return f"FileWorker(factory={self.handler_factory})"
