"""
Processing pipeline orchestrator.

This module provides the main pipeline for orchestrating the log
filtering process including scanning, parsing, filtering, and writing.
"""

import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import Literal

from log_filter.config.models import ApplicationConfig, ProcessingConfig
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
from log_filter.infrastructure.chunked_writer import ChunkedLogWriter
from log_filter.infrastructure.file_scanner import FileScanner
from log_filter.infrastructure.file_utils import sort_files_by_date_and_index
from log_filter.processing.record_parser import StreamingRecordParser
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
        parser = StreamingRecordParser(
            max_record_size_bytes=max_record_size_bytes,
            normalize_levels=config.processing.normalize_log_levels,
        )

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
            # For level-normalized records, prepend the normalized level to enable
            # searching for "ERROR" to match records with "E" level
            search_text = record.content
            if record.level:
                # Prepend normalized level to search text for matching
                search_text = f"{record.level} {record.content}"

            if evaluate(
                ast,
                search_text,
                config.search.ignore_case,
                config.search.use_regex,
                config.search.word_boundary,
                config.search.strip_quotes,
            ):
                stats_collector.increment_records_matched()
                match_count += 1

                # Store matched record as dict with metadata for sorting
                record_dict = {
                    "content": record.content,
                    "timestamp": record.timestamp,
                    "level": record.level,
                    "source_file": str(file_meta.path) if include_path else None,
                }
                matched_records.append(record_dict)

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
        # Pre-sort files by date/index if enabled
        if self.config.processing.sort_input_files:
            logger.info("Pre-sorting input files by date and index from filenames...")
            files = sort_files_by_date_and_index(files, fallback_sort_key="name")
            logger.info(f"Files sorted: processing {len(files)} files in chronological order")

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
        recent_times = []  # Track last 10 file completion times

        if use_multiprocessing:
            # Use ProcessPoolExecutor for true parallelism
            with ProcessPoolExecutor(max_workers=worker_count) as executor:
                # Submit all files for processing with index tracking
                futures = {
                    executor.submit(_process_file_worker, args): (idx, args[0])
                    for idx, args in enumerate(worker_args)
                }

                # Store results by index to preserve order when sort_by_timestamp is disabled
                results_by_index = {}

                # Wait for completion and collect results
                for future in as_completed(futures):
                    file_idx, file_meta = futures[future]
                    file_start_time = time.time()
                    processed_count += 1

                    try:
                        _, matches, stats_dict, matched_records, error = future.result()
                        file_duration = time.time() - file_start_time

                        # Store result with its original index
                        results_by_index[file_idx] = {
                            "matched_records": matched_records if not error else [],
                            "stats_dict": stats_dict,
                            "error": error,
                        }

                        if error:
                            logger.error(f"Error processing {file_meta.path}: {error}")

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
                        # Store empty result for failed file
                        results_by_index[file_idx] = {
                            "matched_records": [],
                            "stats_dict": None,
                            "error": str(e),
                        }

                # Aggregate results in original file order to preserve sort_input_files order
                for idx in sorted(results_by_index.keys()):
                    result = results_by_index[idx]

                    # Collect matched records in order
                    if result["matched_records"]:
                        all_matched_records.extend(result["matched_records"])

                    # Aggregate stats from worker process
                    if result["stats_dict"]:
                        self.stats.stats.records_total += result["stats_dict"]["records_total"]
                        self.stats.stats.records_matched += result["stats_dict"]["records_matched"]
                        self.stats.stats.records_skipped += result["stats_dict"]["records_skipped"]
                        self.stats.stats.total_bytes_processed += result["stats_dict"][
                            "total_bytes_processed"
                        ]
                        self.stats.stats.total_lines_processed += result["stats_dict"][
                            "total_lines_processed"
                        ]
                        if result["stats_dict"]["files_processed"] > 0:
                            self.stats.increment_files_processed()
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

        # Sort and write matched records
        if all_matched_records:
            self._write_sorted_results(all_matched_records)
        else:
            logger.info("No matching records found")

        # Log final statistics
        if self.config.output.show_stats:
            self._print_statistics()

    def _sort_records_by_timestamp(
        self,
        records: list[dict],
        missing_timestamp_strategy: Literal["end", "start", "skip"] = "end",
    ) -> list[dict]:
        """
        Sort log records chronologically by timestamp.

        Records with valid timestamps are sorted chronologically (oldest first).
        Records without timestamps are handled according to the strategy:
        - "end": Place at the end in original order
        - "start": Place at the start in original order
        - "skip": Exclude from result

        Args:
            records: List of record dictionaries with 'timestamp' field
            missing_timestamp_strategy: How to handle records without timestamp

        Returns:
            Sorted list of records

        Complexity:
            Time: O(n log n) where n is number of records with timestamp
            Space: O(n) for creating separate lists

        References:
            - Sorting: https://docs.python.org/3/howto/sorting.html
            - datetime comparison: https://docs.python.org/3/library/datetime.html#datetime.datetime
        """
        # Separate records by timestamp presence
        with_timestamp = []
        without_timestamp = []

        for record in records:
            timestamp = record.get("timestamp")
            if timestamp and isinstance(timestamp, datetime):
                with_timestamp.append(record)
            else:
                without_timestamp.append(record)

        # Sort records with timestamp
        # datetime objects support comparison operators (<, >, ==)
        with_timestamp.sort(key=lambda r: r["timestamp"])

        # Log statistics
        if without_timestamp:
            logger.warning(
                f"Found {len(without_timestamp)} records without valid timestamp "
                f"(strategy: {missing_timestamp_strategy})"
            )

        # Apply strategy for records without timestamp
        if missing_timestamp_strategy == "end":
            # Place records without timestamp at the end
            result = with_timestamp + without_timestamp
        elif missing_timestamp_strategy == "start":
            # Place records without timestamp at the start
            result = without_timestamp + with_timestamp
        elif missing_timestamp_strategy == "skip":
            # Exclude records without timestamp
            logger.warning(f"Skipping {len(without_timestamp)} records without timestamp")
            result = with_timestamp
        else:
            # Default to "end"
            logger.warning(f"Unknown strategy '{missing_timestamp_strategy}', defaulting to 'end'")
            result = with_timestamp + without_timestamp

        logger.info(
            f"Sorted {len(with_timestamp)} records by timestamp "
            f"({len(without_timestamp)} without timestamp)"
        )

        return result

    def _write_sorted_results(self, all_matched_records: list[dict]) -> None:
        """
        Sort and write results with optional chunking.

        Args:
            all_matched_records: List of record dicts with 'content', 'timestamp', etc.
        """
        output_config = self.config.output

        # Sort records by timestamp if enabled
        if output_config.sort_by_timestamp:
            logger.info(f"Sorting {len(all_matched_records)} records by timestamp...")
            all_matched_records = self._sort_records_by_timestamp(
                all_matched_records, missing_timestamp_strategy="end"
            )

        # Prepare records for writing (format with file path if needed)
        formatted_records = []
        for record in all_matched_records:
            content = record["content"]

            # Add source file path if enabled and available
            if output_config.include_file_path and record.get("source_file"):
                formatted_record = f"{record['source_file']}: {content}"
            else:
                formatted_record = content

            formatted_records.append(
                {"content": formatted_record, "timestamp": record.get("timestamp")}
            )

        # Write using ChunkedLogWriter
        try:
            # Determine if chunking is enabled
            max_records = output_config.max_records_per_file
            if max_records == 0:
                max_records = None  # Unlimited

            with ChunkedLogWriter(
                base_output_path=output_config.output_file,
                max_records_per_file=max_records,
                file_pattern=output_config.output_file_pattern,
            ) as writer:
                logger.info(f"Writing {len(formatted_records)} records to output...")
                for record in formatted_records:
                    writer.write_record(record)

                created_files = writer.get_created_files()

                if len(created_files) == 1:
                    logger.info(f"Output written to: {created_files[0]}")
                else:
                    logger.info(f"Output split into {len(created_files)} files:")
                    for file_path in created_files:
                        logger.info(f"  - {file_path.name}")

        except Exception as e:
            logger.error(f"Error writing output: {e}", exc_info=True)
            raise

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
