"""
Chunked log writer with automatic file splitting.

This module provides a writer that automatically creates new output files
when a record limit is reached, preventing excessively large output files.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO

logger = logging.getLogger(__name__)


class ChunkedLogWriter:
    """
    Writer that splits output across multiple files based on record count.

    Automatically creates new output files when the record limit is reached.
    Supports configurable file naming patterns with template variables.

    Features:
        - Automatic file rotation on record limit
        - Configurable filename patterns with variables
        - Context manager support
        - Tracks all created files

    Template Variables:
        {base}      - Base filename without extension
        {index}     - Sequential file index (1-based)
        {ext}       - File extension (including dot)
        {timestamp} - Current timestamp (YYYYMMDD_HHMMSS)

    Example:
        >>> writer = ChunkedLogWriter(
        ...     base_output_path=Path("output.log"),
        ...     max_records_per_file=500,
        ...     file_pattern="{base}-{index:03d}{ext}"
        ... )
        >>> with writer:
        ...     for record in records:
        ...         writer.write_record(record)
        >>> print(f"Created {len(writer.get_created_files())} files")
        Created 3 files

    References:
        - Context managers: https://docs.python.org/3/reference/datamodel.html#with-statement-context-managers
        - String formatting: https://docs.python.org/3/library/string.html#format-string-syntax
    """

    def __init__(
        self,
        base_output_path: Path,
        max_records_per_file: Optional[int] = 500,
        file_pattern: str = "{base}-{index:03d}{ext}",
        encoding: str = "utf-8",
    ):
        """
        Initialize chunked writer.

        Args:
            base_output_path: Base path for output files
            max_records_per_file: Maximum records per file (None or 0 = unlimited)
            file_pattern: Template for generating filenames
            encoding: File encoding
        """
        self.base_output_path = base_output_path
        self.max_records_per_file = max_records_per_file if max_records_per_file else None
        self.file_pattern = file_pattern
        self.encoding = encoding

        # State
        self.current_file: Optional[TextIO] = None
        self.current_file_path: Optional[Path] = None
        self.current_file_index: int = 0
        self.current_record_count: int = 0
        self.total_records_written: int = 0
        self.created_files: list[Path] = []

        # Ensure output directory exists
        self.base_output_path.parent.mkdir(parents=True, exist_ok=True)

    def __enter__(self) -> "ChunkedLogWriter":
        """
        Context manager entry.

        Opens the first output file.

        Returns:
            Self for use in with statement
        """
        self._open_next_file()
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object
    ) -> None:
        """
        Context manager exit.

        Closes current file and logs summary.
        """
        self.close()

    def _generate_file_path(self, index: int) -> Path:
        """
        Generate file path for given index using template.

        Args:
            index: File index (1-based)

        Returns:
            Generated file path

        Template variables:
            {base}      - Base filename without extension
            {index}     - File index
            {ext}       - File extension (including dot)
            {timestamp} - Current timestamp (YYYYMMDD_HHMMSS)

        Examples:
            >>> writer._generate_file_path(1)
            Path("output-001.log")
            >>> writer._generate_file_path(42)
            Path("output-042.log")
        """
        base = self.base_output_path.stem
        ext = self.base_output_path.suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = self.file_pattern.format(base=base, index=index, ext=ext, timestamp=timestamp)

        return self.base_output_path.parent / filename

    def _open_next_file(self) -> None:
        """
        Close current file (if any) and open next file.

        Increments file index and resets record counter.
        Updates tracking lists.
        """
        # Close current file if open
        if self.current_file:
            self.current_file.close()
            if self.current_file_path:
                logger.info(
                    f"Closed '{self.current_file_path.name}' "
                    f"with {self.current_record_count} records"
                )

        # Increment index and generate new path
        self.current_file_index += 1

        # If unlimited (no chunking), use base path directly
        if self.max_records_per_file is None:
            self.current_file_path = self.base_output_path
        else:
            self.current_file_path = self._generate_file_path(self.current_file_index)

        # Open new file
        self.current_file = open(self.current_file_path, "w", encoding=self.encoding)
        self.current_record_count = 0
        self.created_files.append(self.current_file_path)

        logger.info(f"Opened new output file: '{self.current_file_path}'")

    def write_record(self, record_dict: dict) -> None:
        """
        Write a single record to output.

        Automatically rotates to new file if record limit reached.

        Args:
            record_dict: Record dictionary with 'content' key and optional metadata

        Expected record_dict keys:
            content (required): The log record content to write
            timestamp (optional): Record timestamp
            source_file (optional): Source file path
            level (optional): Log level

        Raises:
            ValueError: If record_dict doesn't contain 'content' key
            IOError: If writing to file fails
        """
        if "content" not in record_dict:
            raise ValueError("record_dict must contain 'content' key")

        # Check if we need to rotate to a new file
        if (
            self.max_records_per_file is not None
            and self.current_record_count >= self.max_records_per_file
        ):
            self._open_next_file()

        # Write the record content
        content = record_dict["content"]
        if not content.endswith("\n"):
            content += "\n"

        if self.current_file:
            self.current_file.write(content)

        # Update counters
        self.current_record_count += 1
        self.total_records_written += 1

    def close(self) -> None:
        """
        Close current file and log final statistics.

        Safe to call multiple times.
        """
        if self.current_file:
            self.current_file.close()
            if self.current_file_path:
                logger.info(
                    f"Closed '{self.current_file_path.name}' "
                    f"with {self.current_record_count} records"
                )
            self.current_file = None

        if self.created_files:
            logger.info(
                f"ChunkedLogWriter complete: "
                f"{self.total_records_written} total records written to "
                f"{len(self.created_files)} file(s)"
            )

            # Log file details
            for i, file_path in enumerate(self.created_files, 1):
                if file_path.exists():
                    size_kb = file_path.stat().st_size / 1024
                    logger.info(f"  [{i}] {file_path.name} ({size_kb:.1f} KB)")

    def get_created_files(self) -> list[Path]:
        """
        Get list of all files created by this writer.

        Returns:
            List of Path objects for created files

        Example:
            >>> writer.get_created_files()
            [Path("output-001.log"), Path("output-002.log")]
        """
        return self.created_files.copy()

    @property
    def current_output_file(self) -> Optional[Path]:
        """Get path to currently open output file."""
        return self.current_file_path

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"ChunkedLogWriter(base={self.base_output_path}, "
            f"max_records={self.max_records_per_file}, "
            f"files_created={len(self.created_files)}, "
            f"total_records={self.total_records_written})"
        )
