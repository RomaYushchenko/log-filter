"""
Summary report generation for log processing operations.

This module provides comprehensive summary reports combining
statistics, performance metrics, and processing results.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TextIO

from log_filter.statistics.collector import ProcessingStats
from log_filter.statistics.performance import PerformanceMetrics, FilePerformance


@dataclass
class ProcessingSummary:
    """Complete processing summary.
    
    Attributes:
        statistics: Basic processing statistics
        performance: Performance metrics
        timestamp: When summary was generated
        errors: List of errors encountered
        warnings: List of warnings
    """
    statistics: ProcessingStats
    performance: PerformanceMetrics
    timestamp: datetime
    errors: List[str]
    warnings: List[str]


class SummaryReportGenerator:
    """Generator for comprehensive processing summary reports.
    
    Combines statistics, performance metrics, and error information
    into formatted reports suitable for console output or file export.
    
    Example:
        >>> generator = SummaryReportGenerator()
        >>> summary = ProcessingSummary(...)
        >>> generator.generate_console_report(summary)
    """
    
    def generate_console_report(
        self,
        summary: ProcessingSummary,
        file: Optional[TextIO] = None,
        show_top_files: int = 5
    ) -> None:
        """Generate comprehensive console report.
        
        Args:
            summary: Processing summary to report
            file: Output file (default: sys.stdout)
            show_top_files: Number of top files to show
        """
        import sys
        out = file or sys.stdout
        
        stats = summary.statistics
        perf = summary.performance
        
        # Print header
        self._print_header(out, "PROCESSING SUMMARY REPORT")
        print(file=out)
        
        # Timestamp
        print(f"Report Generated: {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", file=out)
        print(file=out)
        
        # Overall execution
        self._print_section(out, "EXECUTION")
        print(f"  Duration: {stats.duration_seconds:.2f}s", file=out)
        print(f"  Start Time: {stats.start_time}", file=out)
        print(f"  End Time: {stats.end_time}", file=out)
        print(file=out)
        
        # Files summary
        self._print_section(out, "FILES")
        print(f"  Total Scanned: {stats.files_scanned}", file=out)
        print(f"  Processed: {stats.files_processed} ({self._percentage(stats.files_processed, stats.files_scanned)})", file=out)
        print(f"  Skipped: {stats.files_skipped} ({self._percentage(stats.files_skipped, stats.files_scanned)})", file=out)
        
        if stats.skip_reasons:
            print("  Skip Breakdown:", file=out)
            for reason, count in sorted(stats.skip_reasons.items(), key=lambda x: x[1], reverse=True):
                print(f"    - {reason}: {count}", file=out)
        print(file=out)
        
        # Records summary
        self._print_section(out, "RECORDS")
        print(f"  Total Processed: {stats.records_total:,}", file=out)
        print(f"  Matched: {stats.records_matched:,} ({self._percentage(stats.records_matched, stats.records_total)})", file=out)
        print(f"  Skipped: {stats.records_skipped:,} ({self._percentage(stats.records_skipped, stats.records_total)})", file=out)
        print(file=out)
        
        # Data volume
        self._print_section(out, "DATA VOLUME")
        print(f"  Total Bytes: {stats.total_bytes_processed:,} bytes ({stats.megabytes_processed:.2f} MB)", file=out)
        print(f"  Total Lines: {stats.total_lines_processed:,}", file=out)
        
        if stats.records_total > 0:
            avg_record_size = stats.total_bytes_processed / stats.records_total
            avg_record_lines = stats.total_lines_processed / stats.records_total
            print(f"  Avg Record: {avg_record_size:.0f} bytes, {avg_record_lines:.1f} lines", file=out)
        print(file=out)
        
        # Performance metrics
        self._print_section(out, "PERFORMANCE")
        print(f"  Throughput: {stats.records_per_second:.0f} records/sec", file=out)
        print(f"  Bandwidth: {perf.avg_mb_per_sec:.2f} MB/sec", file=out)
        print(f"  Avg File Time: {perf.avg_file_time_seconds:.3f}s", file=out)
        
        if perf.worker_times:
            print(f"  Workers Used: {len(perf.worker_times)}", file=out)
            total_worker_time = sum(perf.worker_times.values())
            print(f"  Total Worker Time: {total_worker_time:.2f}s", file=out)
            if perf.total_time_seconds > 0:
                efficiency = (total_worker_time / perf.total_time_seconds) * 100
                print(f"  Parallelization Efficiency: {efficiency:.1f}%", file=out)
        print(file=out)
        
        # Top files by processing time
        if perf.file_performances and show_top_files > 0:
            self._print_section(out, f"TOP {show_top_files} SLOWEST FILES")
            slowest = perf.get_slowest_files(show_top_files)
            self._print_file_table(out, slowest)
            print(file=out)
        
        # Top files by size
        if perf.file_performances and show_top_files > 0:
            self._print_section(out, f"TOP {show_top_files} LARGEST FILES")
            largest = perf.get_largest_files(show_top_files)
            self._print_file_table(out, largest)
            print(file=out)
        
        # Errors and warnings
        if summary.errors:
            self._print_section(out, f"ERRORS ({len(summary.errors)})")
            for i, error in enumerate(summary.errors, 1):
                print(f"  {i}. {error}", file=out)
            print(file=out)
        
        if summary.warnings:
            self._print_section(out, f"WARNINGS ({len(summary.warnings)})")
            for i, warning in enumerate(summary.warnings, 1):
                print(f"  {i}. {warning}", file=out)
            print(file=out)
        
        # Footer
        self._print_header(out, "END OF REPORT")
    
    def generate_markdown_report(
        self,
        summary: ProcessingSummary,
        output_path: Path,
        show_top_files: int = 10
    ) -> None:
        """Generate markdown-formatted report file.
        
        Args:
            summary: Processing summary to report
            output_path: Output file path
            show_top_files: Number of top files to show
        """
        stats = summary.statistics
        perf = summary.performance
        
        with open(output_path, "w", encoding="utf-8") as f:
            # Header
            f.write("# Log Processing Summary Report\n\n")
            f.write(f"**Generated:** {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Execution
            f.write("## Execution\n\n")
            f.write(f"- **Duration:** {stats.duration_seconds:.2f}s\n")
            f.write(f"- **Start Time:** {stats.start_time}\n")
            f.write(f"- **End Time:** {stats.end_time}\n\n")
            
            # Files
            f.write("## Files\n\n")
            f.write(f"- **Scanned:** {stats.files_scanned}\n")
            f.write(f"- **Processed:** {stats.files_processed} ({self._percentage(stats.files_processed, stats.files_scanned)})\n")
            f.write(f"- **Skipped:** {stats.files_skipped} ({self._percentage(stats.files_skipped, stats.files_scanned)})\n\n")
            
            if stats.skip_reasons:
                f.write("### Skip Reasons\n\n")
                for reason, count in sorted(stats.skip_reasons.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {reason}: {count}\n")
                f.write("\n")
            
            # Records
            f.write("## Records\n\n")
            f.write(f"- **Total:** {stats.records_total:,}\n")
            f.write(f"- **Matched:** {stats.records_matched:,} ({self._percentage(stats.records_matched, stats.records_total)})\n")
            f.write(f"- **Skipped:** {stats.records_skipped:,}\n\n")
            
            # Performance
            f.write("## Performance\n\n")
            f.write(f"- **Throughput:** {stats.records_per_second:.0f} records/sec\n")
            f.write(f"- **Bandwidth:** {perf.avg_mb_per_sec:.2f} MB/sec\n")
            f.write(f"- **Avg File Time:** {perf.avg_file_time_seconds:.3f}s\n\n")
            
            # Top files
            if perf.file_performances and show_top_files > 0:
                f.write(f"## Top {show_top_files} Slowest Files\n\n")
                f.write("| File | Size (MB) | Time (s) | Records | Throughput |\n")
                f.write("|------|-----------|----------|---------|------------|\n")
                for fp in perf.get_slowest_files(show_top_files):
                    size_mb = fp.file_size_bytes / (1024 * 1024)
                    f.write(f"| {Path(fp.file_path).name} | {size_mb:.2f} | {fp.processing_time_seconds:.3f} | {fp.records_processed:,} | {fp.throughput_records_per_sec:.0f} rec/s |\n")
                f.write("\n")
            
            # Errors
            if summary.errors:
                f.write(f"## Errors ({len(summary.errors)})\n\n")
                for i, error in enumerate(summary.errors, 1):
                    f.write(f"{i}. {error}\n")
                f.write("\n")
            
            # Warnings
            if summary.warnings:
                f.write(f"## Warnings ({len(summary.warnings)})\n\n")
                for i, warning in enumerate(summary.warnings, 1):
                    f.write(f"{i}. {warning}\n")
                f.write("\n")
    
    @staticmethod
    def _print_header(file: TextIO, title: str) -> None:
        """Print a section header."""
        print("=" * 70, file=file)
        print(title.center(70), file=file)
        print("=" * 70, file=file)
    
    @staticmethod
    def _print_section(file: TextIO, title: str) -> None:
        """Print a section title."""
        print(f"─── {title} {'─' * (65 - len(title))}", file=file)
    
    @staticmethod
    def _percentage(part: int, total: int) -> str:
        """Format percentage string."""
        if total == 0:
            return "0.00%"
        return f"{(part / total) * 100:.2f}%"
    
    @staticmethod
    def _print_file_table(file: TextIO, performances: List[FilePerformance]) -> None:
        """Print a table of file performances."""
        if not performances:
            print("  (none)", file=file)
            return
        
        # Calculate column widths
        max_name_width = min(40, max(len(Path(p.file_path).name) for p in performances))
        
        # Header
        print(f"  {'File':<{max_name_width}} | {'Size (MB)':>10} | {'Time (s)':>10} | {'Records':>10} | {'Rate':>12}", file=file)
        print(f"  {'-' * max_name_width}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 12}", file=file)
        
        # Rows
        for perf in performances:
            name = Path(perf.file_path).name
            if len(name) > max_name_width:
                name = "..." + name[-(max_name_width-3):]
            
            size_mb = perf.file_size_bytes / (1024 * 1024)
            
            print(
                f"  {name:<{max_name_width}} | "
                f"{size_mb:>10.2f} | "
                f"{perf.processing_time_seconds:>10.3f} | "
                f"{perf.records_processed:>10,} | "
                f"{perf.throughput_records_per_sec:>10.0f} r/s",
                file=file
            )
