"""
Processing pipeline orchestrator.

This module provides the main pipeline for orchestrating the log
filtering process including scanning, parsing, filtering, and writing.
"""

import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import Manager
from pathlib import Path
from typing import Optional

from log_filter.config.models import (
    ApplicationConfig,
    FileConfig,
    OutputConfig,
    ProcessingConfig,
    SearchConfig,
)
from log_filter.core.evaluator import evaluate
from log_filter.core.exceptions import ConfigurationError
from log_filter.core.parser import parse
from log_filter.domain.filters import (
    AlwaysPassFilter,
    CompositeFilter,
    DateRangeFilter,
    RecordFilter,
    TimeRangeFilter,
)
from log_filter.domain.models import ASTNode
from log_filter.infrastructure.file_handler_factory import FileHandlerFactory
from log_filter.infrastructure.file_scanner import FileScanner
from log_filter.infrastructure.file_writer import BufferedLogWriter
from log_filter.processing.record_parser import StreamingRecordParser
from log_filter.processing.worker import FileWorker
from log_filter.statistics.collector import StatisticsCollector

logger = logging.getLogger(__name__)


def _process_file_worker(args: tuple) -> tuple:
    """Top-level worker function for multiprocessing.

    This function must be at module level to be picklable.

    Args:
        args: Tuple of (file_meta, ast, config, max_record_size_bytes, include_path)

    Returns:
        Tuple of (file_meta, matches, stats_dict, matched_records, error)
    """
    file_meta, ast, config, max_record_size_bytes, include_path = args

    try:
        # Create per-process instances
        from log_filter.core.evaluator import evaluate
        from log_filter.domain.filters import (
            AlwaysPassFilter,
            CompositeFilter,
            DateRangeFilter,
            TimeRangeFilter,
        )
        from log_filter.infrastructure.file_handler_factory import FileHandlerFactory
        from log_filter.processing.record_parser import StreamingRecordParser
        from log_filter.statistics.collector import StatisticsCollector

        # Create local stats collector for this process
        stats_collector = StatisticsCollector()
        stats_collector.start()

        # Create record filter
        filters: list = []
        parser = StreamingRecordParser(max_record_size_bytes=max_record_size_bytes)

        if config.search.date_from or config.search.date_to:
            date_filter = DateRangeFilter(
                date_from=config.search.date_from, date_to=config.search.date_to, parser=parser
            )
            filters.append(date_filter)

        if config.search.time_from or config.search.time_to:
            time_filter = TimeRangeFilter(
                time_from=config.search.time_from, time_to=config.search.time_to, parser=parser
            )
            filters.append(time_filter)

        record_filter = CompositeFilter(*filters) if filters else AlwaysPassFilter()

        # Create handler and process file
        handler_factory = FileHandlerFactory()
        handler = handler_factory.create_handler(file_meta.path)

        matched_records = []
        match_count = 0

        for record in parser.parse_lines(handler.read_lines()):
            stats_collector.increment_records_total()

            # Apply date/time filters
            if not record_filter.matches(record):
                stats_collector.increment_records_skipped()
                continue

            # Evaluate expression
            if evaluate(ast, record.content, config.search.ignore_case, config.search.use_regex):
                stats_collector.increment_records_matched()
                match_count += 1

                # Store matched record with file path if needed
                if include_path:
                    matched_records.append(f"{file_meta.path}: {record.content}")
                else:
                    matched_records.append(record.content)

        # Get stats snapshot
        stats_collector.stop()
        stats_dict = {
            "files_processed": 1,
            "records_total": stats_collector.stats.records_total,
            "records_matched": stats_collector.stats.records_matched,
            "records_skipped": stats_collector.stats.records_skipped,
            "total_bytes_processed": stats_collector.stats.total_bytes_processed,
            "total_lines_processed": stats_collector.stats.total_lines_processed,
        }

        return (file_meta, match_count, stats_dict, matched_records, None)

    except Exception as e:
        import traceback

        error = f"{e}\n{traceback.format_exc()}"
        return (file_meta, 0, None, [], error)


class ProcessingPipeline:
    """Main processing pipeline for log filtering.

    Orchestrates the complete processing flow:
    1. Parse search expression
    2. Scan for eligible files
    3. Create worker pool
    4. Process files in parallel
    5. Collect statistics
    6. Write results

    Uses dependency injection throughout - no global state.

    Attributes:
        config: Application configuration
        stats: Statistics collector

    Example:
        >>> config = ApplicationConfig(...)
        >>> pipeline = ProcessingPipeline(config)
        >>> pipeline.run()
        >>> print(pipeline.stats.stats.records_matched)
    """

    def __init__(self, config: ApplicationConfig) -> None:
        """Initialize the processing pipeline.

        Args:
            config: Application configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config = config
        self.stats = StatisticsCollector()

        # Validate configuration
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.config.search.expression:
            raise ConfigurationError("Search expression is required")

        if not self.config.files.path.exists():
            raise ConfigurationError(f"Path does not exist: {self.config.files.path}")

    def run(self) -> None:
        """Run the complete processing pipeline.

        This is the main entry point for processing.
        """
        logger.info("Starting log filter pipeline")
        self.stats.start()

        try:
            # Parse search expression
            ast = self._parse_expression()
            logger.debug(f"Parsed expression: {ast}")

            # Build record filter
            record_filter = self._build_record_filter()

            # Scan for files
            file_scanner = self._create_file_scanner()
            files_to_process = []

            for file_meta in file_scanner.scan():
                self.stats.increment_files_scanned()

                if file_meta.should_skip:
                    self.stats.increment_files_skipped(file_meta.skip_reason or "unknown")
                    logger.debug(f"Skipping {file_meta.path}: {file_meta.skip_reason}")
                else:
                    files_to_process.append(file_meta)

            logger.info(
                f"Found {len(files_to_process)} files to process "
                f"({self.stats.stats.files_skipped} skipped)"
            )

            # Check dry-run mode
            if self.config.output.dry_run or self.config.output.dry_run_details:
                self._handle_dry_run(files_to_process)
                return

            # Process files
            if files_to_process:
                self._process_files(files_to_process, ast, record_filter)

        finally:
            self.stats.stop()
            logger.info(f"Pipeline completed in {self.stats.stats.duration_seconds:.2f}s")

    def _parse_expression(self) -> ASTNode:
        """Parse the search expression into AST.

        Returns:
            Parsed AST

        Raises:
            ConfigurationError: If expression parsing fails
        """
        try:
            return parse(self.config.search.expression)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to parse expression '{self.config.search.expression}': {e}"
            ) from e

    def _build_record_filter(self) -> RecordFilter:
        """Build composite record filter from configuration.

        Returns:
            Composite filter with date/time filters
        """
        filters: list = []
        parser = StreamingRecordParser()

        # Add date filter if specified
        if self.config.search.date_from or self.config.search.date_to:
            date_filter = DateRangeFilter(
                date_from=self.config.search.date_from,
                date_to=self.config.search.date_to,
                parser=parser,
            )
            filters.append(date_filter)

        # Add time filter if specified
        if self.config.search.time_from or self.config.search.time_to:
            time_filter = TimeRangeFilter(
                time_from=self.config.search.time_from,
                time_to=self.config.search.time_to,
                parser=parser,
            )
            filters.append(time_filter)

        # Return composite or always-pass filter
        if filters:
            return CompositeFilter(*filters)
        else:
            return AlwaysPassFilter()

    def _create_file_scanner(self) -> FileScanner:
        """Create file scanner from configuration.

        Returns:
            Configured file scanner
        """
        return FileScanner(
            root_path=self.config.files.path,
            file_masks=self.config.files.file_masks,
            include_patterns=self.config.files.include_patterns,
            exclude_patterns=self.config.files.exclude_patterns,
            allowed_extensions=set(self.config.files.extensions),
            max_file_size_mb=self.config.files.max_file_size_mb,
            recursive=True,
        )

    def _handle_dry_run(self, files: list) -> None:
        """Handle dry-run mode.

        Args:
            files: List of file metadata
        """
        if self.config.output.dry_run_details:
            # Just print summary
            total_size_mb = sum(f.size_mb for f in files)
            logger.info(f"Dry-run: {len(files)} files, {total_size_mb:.2f} MB total")
        else:
            # Print file list
            logger.info("Dry-run: Files to process:")
            for file_meta in files:
                logger.info(f"  {file_meta.path} ({file_meta.size_mb:.2f} MB)")

    def _process_files(self, files: list, ast: ASTNode, record_filter: RecordFilter) -> None:
        """Process files in parallel using multiprocessing.

        Args:
            files: List of file metadata
            ast: Parsed search expression
            record_filter: Filter for records (not used in multiprocessing mode)
        """
        # Determine worker count
        worker_count = self.config.processing.worker_count
        if worker_count is None:
            # Auto-detect but cap to platform maximum to prevent resource exhaustion
            detected_count = os.cpu_count() or 4
            max_workers = ProcessingConfig._get_max_workers_for_platform()
            worker_count = min(detected_count, max_workers)
            if detected_count > max_workers:
                logger.info(
                    f"Auto-detected worker count ({detected_count}) exceeds platform maximum. "
                    f"Capping to {max_workers} workers to prevent resource exhaustion."
                )
        else:
            # Warn if worker count significantly exceeds CPU count
            cpu_count = os.cpu_count() or 4
            if worker_count > cpu_count * 4:
                logger.warning(
                    f"Worker count ({worker_count}) is significantly higher than CPU count ({cpu_count}). "
                    f"This may cause memory pressure and reduced performance."
                )

        # Use processes for true parallelism (avoid GIL)
        use_multiprocessing = worker_count > 1

        if use_multiprocessing:
            logger.info(f"Using {worker_count} worker processes (multiprocessing mode)")
        else:
            logger.info(f"Using {worker_count} worker thread (single-threaded mode)")

        # Prepare arguments for workers
        max_record_size_bytes = (
            self.config.files.max_record_size_kb * 1024
            if self.config.files.max_record_size_kb
            else None
        )
        include_path = self.config.output.include_file_path

        worker_args = [
            (file_meta, ast, self.config, max_record_size_bytes, include_path)
            for file_meta in files
        ]

        # Open output writer for collecting results
        output_path = self.config.output.output_file
        all_matched_records = []

        # Track progress
        processed_count = 0
        total_files = len(files)
        start_time = time.time()
        recent_times = []  # Track last 10 file completion times

        if use_multiprocessing:
            # Use ProcessPoolExecutor for true parallelism
            with ProcessPoolExecutor(max_workers=worker_count) as executor:
                # Submit all files for processing
                futures = {
                    executor.submit(_process_file_worker, args): args[0] for args in worker_args
                }

                # Wait for completion and aggregate results
                for future in as_completed(futures):
                    file_meta = futures[future]
                    file_start_time = time.time()
                    processed_count += 1

                    try:
                        file_meta_result, matches, stats_dict, matched_records, error = (
                            future.result()
                        )
                        file_duration = time.time() - file_start_time

                        if error:
                            logger.error(f"Error processing {file_meta.path}: {error}")
                        else:
                            # Collect matched records
                            if matched_records:
                                all_matched_records.extend(matched_records)

                            # Aggregate stats from worker process
                            if stats_dict:
                                self.stats.stats.records_total += stats_dict["records_total"]
                                self.stats.stats.records_matched += stats_dict["records_matched"]
                                self.stats.stats.records_skipped += stats_dict["records_skipped"]
                                self.stats.stats.total_bytes_processed += stats_dict[
                                    "total_bytes_processed"
                                ]
                                self.stats.stats.total_lines_processed += stats_dict[
                                    "total_lines_processed"
                                ]
                                if stats_dict["files_processed"] > 0:
                                    self.stats.increment_files_processed()

                        # Track recent file times for moving average
                        recent_times.append(file_duration)
                        if len(recent_times) > 10:
                            recent_times.pop(0)

                        # Calculate ETA using moving average
                        avg_time_per_file = sum(recent_times) / len(recent_times)
                        remaining = total_files - processed_count
                        eta_seconds = remaining * avg_time_per_file

                        # Format file size
                        file_size_str = (
                            f"{file_meta.size_mb:.1f} MB"
                            if file_meta.size_mb < 1024
                            else f"{file_meta.size_mb/1024:.1f} GB"
                        )

                        # Always show progress
                        logger.info(
                            f"[{processed_count}/{total_files}] {file_meta.path.name} ({file_size_str}): "
                            f"{matches} matches in {file_duration:.1f}s | ETA: {eta_seconds/60:.1f} min"
                        )

                    except Exception as e:
                        logger.error(f"Error processing {file_meta.path}: {e}", exc_info=True)
        else:
            # Single-threaded mode (for debugging or small workloads)
            for args in worker_args:
                file_meta = args[0]
                file_start_time = time.time()
                processed_count += 1

                try:
                    file_meta_result, matches, stats_dict, matched_records, error = (
                        _process_file_worker(args)
                    )
                    file_duration = time.time() - file_start_time

                    if error:
                        logger.error(f"Error processing {file_meta.path}: {error}")
                    else:
                        # Collect matched records
                        if matched_records:
                            all_matched_records.extend(matched_records)

                        # Aggregate stats
                        if stats_dict:
                            self.stats.stats.records_total += stats_dict["records_total"]
                            self.stats.stats.records_matched += stats_dict["records_matched"]
                            self.stats.stats.records_skipped += stats_dict["records_skipped"]
                            self.stats.stats.total_bytes_processed += stats_dict[
                                "total_bytes_processed"
                            ]
                            self.stats.stats.total_lines_processed += stats_dict[
                                "total_lines_processed"
                            ]
                            if stats_dict["files_processed"] > 0:
                                self.stats.increment_files_processed()
                            self.stats.stats.records_skipped += stats_dict["records_skipped"]
                            self.stats.stats.total_bytes_processed += stats_dict["bytes_processed"]
                            self.stats.stats.total_lines_processed += stats_dict["lines_processed"]
                            if stats_dict["files_processed"] > 0:
                                self.stats.increment_files_processed()

                    # Track recent times
                    recent_times.append(file_duration)
                    if len(recent_times) > 10:
                        recent_times.pop(0)

                    # Calculate ETA
                    avg_time_per_file = sum(recent_times) / len(recent_times)
                    remaining = total_files - processed_count
                    eta_seconds = remaining * avg_time_per_file

                    # Format file size
                    file_size_str = (
                        f"{file_meta.size_mb:.1f} MB"
                        if file_meta.size_mb < 1024
                        else f"{file_meta.size_mb/1024:.1f} GB"
                    )

                    # Show progress
                    logger.info(
                        f"[{processed_count}/{total_files}] {file_meta.path.name} ({file_size_str}): "
                        f"{matches} matches in {file_duration:.1f}s | ETA: {eta_seconds/60:.1f} min"
                    )

                except Exception as e:
                    logger.error(f"Error processing {file_meta.path}: {e}", exc_info=True)

        # Write all matched records to output file
        if all_matched_records:
            logger.info(f"Writing {len(all_matched_records)} matched records to {output_path}")
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    for record in all_matched_records:
                        f.write(record)
                        if not record.endswith("\n"):
                            f.write("\n")
            except Exception as e:
                logger.error(f"Error writing output file: {e}", exc_info=True)
        else:
            logger.info("No matching records found")

        # Log final statistics
        if self.config.output.show_stats:
            self._print_statistics()

    def _print_statistics(self) -> None:
        """Print final statistics."""
        stats = self.stats.get_snapshot()

        logger.info("=" * 60)
        logger.info("Processing Statistics")
        logger.info("=" * 60)
        logger.info(f"Duration: {stats.duration_seconds:.2f}s")
        logger.info(f"Files scanned: {stats.files_scanned}")
        logger.info(f"Files processed: {stats.files_processed}")
        logger.info(f"Files skipped: {stats.files_skipped}")

        if stats.skip_reasons:
            logger.info("Skip reasons:")
            for reason, count in sorted(stats.skip_reasons.items()):
                logger.info(f"  {reason}: {count}")

        logger.info(f"Records total: {stats.records_total}")
        logger.info(f"Records matched: {stats.records_matched}")
        logger.info(f"Records skipped: {stats.records_skipped}")
        logger.info(f"Data processed: {stats.megabytes_processed:.2f} MB")
        logger.info(f"Throughput: {stats.records_per_second:.0f} records/sec")
        logger.info("=" * 60)
