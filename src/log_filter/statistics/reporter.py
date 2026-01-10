"""
Statistics reporter for formatting and displaying processing statistics.

This module provides formatted output of processing statistics with
support for console output, JSON export, and CSV export.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO

from log_filter.statistics.collector import ProcessingStats


class StatisticsReporter:
    """Reporter for formatting and displaying statistics.

    Provides multiple output formats:
    - Console (human-readable)
    - JSON (machine-readable)
    - CSV (spreadsheet-friendly)

    Example:
        >>> reporter = StatisticsReporter()
        >>> reporter.print_console(stats)
        >>> reporter.export_json(stats, Path("stats.json"))
    """

    def print_console(self, stats: ProcessingStats, file: Optional[TextIO] = None) -> None:
        """Print statistics to console in human-readable format.

        Args:
            stats: Statistics to print
            file: Output file (default: sys.stdout)
        """
        import sys

        out = file or sys.stdout

        # Print header
        print("=" * 70, file=out)
        print("LOG FILTER PROCESSING STATISTICS", file=out)
        print("=" * 70, file=out)
        print(file=out)

        # Execution metrics
        print("Execution:", file=out)
        print(f"  Duration: {stats.duration_seconds:.2f}s", file=out)
        if stats.duration_seconds > 0:
            print(f"  Throughput: {stats.records_per_second:.0f} records/sec", file=out)
        print(file=out)

        # File statistics
        print("Files:", file=out)
        print(f"  Scanned: {stats.files_scanned}", file=out)
        print(f"  Processed: {stats.files_processed}", file=out)
        print(f"  Skipped: {stats.files_skipped}", file=out)

        if stats.skip_reasons:
            print("  Skip Reasons:", file=out)
            for reason, count in sorted(
                stats.skip_reasons.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"    {reason}: {count}", file=out)
        print(file=out)

        # Record statistics
        print("Records:", file=out)
        print(f"  Total: {stats.records_total:,}", file=out)
        print(f"  Matched: {stats.records_matched:,}", file=out)
        print(f"  Skipped: {stats.records_skipped:,}", file=out)

        if stats.records_total > 0:
            match_rate = (stats.records_matched / stats.records_total) * 100
            print(f"  Match Rate: {match_rate:.2f}%", file=out)
        print(file=out)

        # Data volume
        print("Data Processed:", file=out)
        print(f"  Volume: {stats.megabytes_processed:.2f} MB", file=out)
        print(f"  Lines: {stats.total_lines_processed:,}", file=out)

        if stats.records_total > 0:
            avg_lines = stats.total_lines_processed / stats.records_total
            avg_bytes = stats.total_bytes_processed / stats.records_total
            print(f"  Avg Record Size: {avg_bytes:.0f} bytes, {avg_lines:.1f} lines", file=out)

        print("=" * 70, file=out)

    def export_json(self, stats: ProcessingStats, output_path: Path, pretty: bool = True) -> None:
        """Export statistics to JSON file.

        Args:
            stats: Statistics to export
            output_path: Output file path
            pretty: Whether to pretty-print JSON
        """
        data = {
            "timestamp": datetime.now().isoformat(),
            "execution": {
                "duration_seconds": stats.duration_seconds,
                "records_per_second": stats.records_per_second,
                "start_time": stats.start_time,
                "end_time": stats.end_time,
            },
            "files": {
                "scanned": stats.files_scanned,
                "processed": stats.files_processed,
                "skipped": stats.files_skipped,
                "skip_reasons": stats.skip_reasons,
            },
            "records": {
                "total": stats.records_total,
                "matched": stats.records_matched,
                "skipped": stats.records_skipped,
                "match_rate": (
                    (stats.records_matched / stats.records_total * 100)
                    if stats.records_total > 0
                    else 0
                ),
            },
            "data": {
                "bytes_processed": stats.total_bytes_processed,
                "megabytes_processed": stats.megabytes_processed,
                "lines_processed": stats.total_lines_processed,
                "avg_record_bytes": (
                    stats.total_bytes_processed / stats.records_total
                    if stats.records_total > 0
                    else 0
                ),
                "avg_record_lines": (
                    stats.total_lines_processed / stats.records_total
                    if stats.records_total > 0
                    else 0
                ),
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(data, f, indent=2)
            else:
                json.dump(data, f)

    def export_csv(self, stats: ProcessingStats, output_path: Path) -> None:
        """Export statistics to CSV file.

        Args:
            stats: Statistics to export
            output_path: Output file path
        """
        import csv

        rows = [
            ["Metric", "Value"],
            ["Timestamp", datetime.now().isoformat()],
            ["", ""],
            ["Duration (seconds)", f"{stats.duration_seconds:.2f}"],
            ["Records per second", f"{stats.records_per_second:.0f}"],
            ["", ""],
            ["Files scanned", str(stats.files_scanned)],
            ["Files processed", str(stats.files_processed)],
            ["Files skipped", str(stats.files_skipped)],
            ["", ""],
            ["Records total", str(stats.records_total)],
            ["Records matched", str(stats.records_matched)],
            ["Records skipped", str(stats.records_skipped)],
            ["", ""],
            ["Data processed (MB)", f"{stats.megabytes_processed:.2f}"],
            ["Lines processed", str(stats.total_lines_processed)],
        ]

        # Add skip reasons
        if stats.skip_reasons:
            rows.append(["", ""])
            rows.append(["Skip Reasons", "Count"])
            for reason, count in sorted(stats.skip_reasons.items()):
                rows.append([reason, str(count)])

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def format_summary(self, stats: ProcessingStats) -> str:
        """Format a one-line summary of statistics.

        Args:
            stats: Statistics to summarize

        Returns:
            One-line summary string
        """
        return (
            f"Processed {stats.files_processed} files, "
            f"{stats.records_total:,} records, "
            f"{stats.records_matched:,} matches "
            f"in {stats.duration_seconds:.2f}s "
            f"({stats.records_per_second:.0f} rec/s)"
        )
