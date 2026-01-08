"""
Buffered log writer with thread-safe batch writing.

This module provides efficient, thread-safe writing of log records
to output files. Uses buffering to minimize I/O operations and
a write lock to ensure thread safety in concurrent environments.
"""

import threading
from pathlib import Path
from typing import Optional

from log_filter.core.exceptions import FileHandlingError
from log_filter.domain.models import LogRecord, SearchResult


class BufferedLogWriter:
    """Thread-safe buffered writer for log output.
    
    Writes log records or search results to a file with buffering
    to improve performance. Thread-safe for use in concurrent processing.
    
    The writer accumulates records in a buffer and flushes to disk
    either when the buffer is full or when explicitly requested.
    
    Attributes:
        output_path: Path to output file
        buffer_size: Number of records to buffer before auto-flush
        include_path: Whether to include source file path in output
        encoding: Character encoding for output file
        
    Example:
        >>> writer = BufferedLogWriter("results.log", buffer_size=100)
        >>> with writer:
        ...     for result in search_results:
        ...         writer.write_result(result)
        ... # Auto-flushes on context exit
    """
    
    DEFAULT_BUFFER_SIZE = 50
    
    def __init__(
        self,
        output_path: Path,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        include_path: bool = True,
        encoding: str = "utf-8"
    ) -> None:
        """Initialize the buffered writer.
        
        Args:
            output_path: Path to output file
            buffer_size: Number of records to buffer before auto-flush.
                        Use 1 for immediate writing (no buffering).
            include_path: Whether to include source file path before records
            encoding: Character encoding for output file
            
        Raises:
            FileHandlingError: If output path is invalid
        """
        if not isinstance(output_path, Path):
            output_path = Path(output_path)
        
        # Validate parent directory exists
        if not output_path.parent.exists():
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise FileHandlingError(
                    f"Cannot create output directory: {output_path.parent}",
                    file_path=output_path.parent,
                    cause=e
                )
        
        self.output_path = output_path
        self.buffer_size = max(1, buffer_size)
        self.include_path = include_path
        self.encoding = encoding
        
        self._buffer: list[str] = []
        self._lock = threading.Lock()
        self._file_handle: Optional[object] = None
        self._total_written = 0
    
    def __enter__(self) -> "BufferedLogWriter":
        """Context manager entry."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with automatic flush and close."""
        self.close()
    
    def open(self) -> None:
        """Open the output file for writing.
        
        Raises:
            FileHandlingError: If file cannot be opened
        """
        try:
            self._file_handle = open(
                self.output_path,
                "w",
                encoding=self.encoding
            )
        except OSError as e:
            raise FileHandlingError(
                f"Cannot open output file: {self.output_path}",
                file_path=self.output_path,
                cause=e
            )
    
    def close(self) -> None:
        """Flush buffer and close output file."""
        with self._lock:
            self._flush_unlocked()
            if self._file_handle:
                try:
                    self._file_handle.close()
                except OSError:
                    pass  # Best effort
                finally:
                    self._file_handle = None
    
    def write_record(
        self,
        record: LogRecord,
        source_path: Optional[Path] = None
    ) -> None:
        """Write a log record to the output.
        
        Args:
            record: LogRecord to write
            source_path: Optional path to source file (for header)
        """
        with self._lock:
            # Add source path header if needed
            if self.include_path and source_path:
                self._buffer.append(f"\n=== {source_path} ===\n")
            
            # Add record content
            self._buffer.append(record.content)
            self._buffer.append("\n")
            
            # Auto-flush if buffer full
            if len(self._buffer) >= self.buffer_size:
                self._flush_unlocked()
    
    def write_result(
        self,
        result: SearchResult,
        source_path: Optional[Path] = None,
        use_highlight: bool = False
    ) -> None:
        """Write a search result to the output.
        
        Args:
            result: SearchResult to write
            source_path: Optional path to source file (for header)
            use_highlight: Whether to use highlighted content if available
        """
        with self._lock:
            # Add source path header if needed
            if self.include_path and source_path:
                self._buffer.append(f"\n=== {source_path} ===\n")
            
            # Add record content (highlighted or original)
            content = (
                result.highlighted_content
                if use_highlight and result.highlighted_content
                else result.record.content
            )
            self._buffer.append(content)
            self._buffer.append("\n")
            
            # Auto-flush if buffer full
            if len(self._buffer) >= self.buffer_size:
                self._flush_unlocked()
    
    def write_text(self, text: str) -> None:
        """Write arbitrary text to output.
        
        Args:
            text: Text to write
        """
        with self._lock:
            self._buffer.append(text)
            
            # Auto-flush if buffer full
            if len(self._buffer) >= self.buffer_size:
                self._flush_unlocked()
    
    def flush(self) -> None:
        """Flush buffer to disk (thread-safe)."""
        with self._lock:
            self._flush_unlocked()
    
    def _flush_unlocked(self) -> None:
        """Flush buffer to disk (not thread-safe, must hold lock).
        
        Raises:
            FileHandlingError: If write fails
        """
        if not self._buffer:
            return
        
        if not self._file_handle:
            raise FileHandlingError(
                "Cannot flush: output file not open",
                file_path=self.output_path
            )
        
        try:
            content = "".join(self._buffer)
            self._file_handle.write(content)
            self._file_handle.flush()
            self._total_written += len(self._buffer)
            self._buffer.clear()
        except OSError as e:
            raise FileHandlingError(
                f"Error writing to output file: {self.output_path}",
                file_path=self.output_path,
                cause=e
            )
    
    def get_total_written(self) -> int:
        """Get total number of items written.
        
        Returns:
            Total number of buffer items written to disk
        """
        with self._lock:
            return self._total_written
    
    def __repr__(self) -> str:
        """String representation of the writer."""
        return (
            f"BufferedLogWriter(output_path={self.output_path}, "
            f"buffer_size={self.buffer_size})"
        )
