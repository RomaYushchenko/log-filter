"""
Abstract base class for file handlers.

This module defines the interface for file handlers that support different
file formats (plain text, gzip, etc.). Each handler is responsible for:
- Opening files in the appropriate mode
- Reading content line by line
- Handling format-specific errors
- Cleanup and resource management
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Optional

from log_filter.core.exceptions import FileHandlingError


class AbstractFileHandler(ABC):
    """Abstract base class for file handlers.
    
    File handlers are responsible for opening and reading files in different
    formats. Implementations must handle format-specific operations like
    decompression, encoding detection, and error recovery.
    
    Attributes:
        file_path: Path to the file being handled
        encoding: Character encoding (default: utf-8)
    """
    
    def __init__(self, file_path: Path, encoding: str = "utf-8") -> None:
        """Initialize the file handler.
        
        Args:
            file_path: Path to the file to handle
            encoding: Character encoding for text files
            
        Raises:
            FileHandlingError: If file_path is not a valid file
        """
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
            
        self.file_path = file_path
        self.encoding = encoding
        
        if not self.file_path.exists():
            raise FileHandlingError(
                f"File not found: {file_path}",
                file_path=file_path
            )
            
        if not self.file_path.is_file():
            raise FileHandlingError(
                f"Not a file: {file_path}",
                file_path=file_path
            )
    
    @abstractmethod
    def read_lines(self) -> Iterator[str]:
        """Read file line by line.
        
        Yields lines from the file. Implementation must handle:
        - Format-specific reading (decompression, etc.)
        - Proper encoding/decoding
        - Resource cleanup on errors
        
        Yields:
            Lines from the file (without trailing newlines)
            
        Raises:
            FileHandlingError: If reading fails
        """
        pass
    
    @abstractmethod
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate that the file can be read.
        
        Check if the file is in the expected format and can be opened.
        This should be a lightweight check without reading the entire file.
        
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if file can be read
            - error_message: None if valid, error description otherwise
        """
        pass
    
    def get_size_bytes(self) -> int:
        """Get file size in bytes.
        
        Returns:
            File size in bytes
        """
        return self.file_path.stat().st_size
    
    def get_size_mb(self) -> float:
        """Get file size in megabytes.
        
        Returns:
            File size in MB (rounded to 2 decimal places)
        """
        return round(self.get_size_bytes() / (1024 * 1024), 2)
    
    def __repr__(self) -> str:
        """String representation of the handler."""
        return f"{self.__class__.__name__}(file_path={self.file_path})"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.__class__.__name__} for {self.file_path.name}"
