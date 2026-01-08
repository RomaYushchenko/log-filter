"""
Factory for creating file handlers based on file type.

This module provides a factory for creating appropriate file handlers
(LogFileHandler, GzipFileHandler) based on file extensions.
"""

from pathlib import Path
from typing import Optional

from log_filter.core.exceptions import FileHandlingError
from log_filter.infrastructure.file_handlers import (
    AbstractFileHandler,
    GzipFileHandler,
    LogFileHandler,
)


class FileHandlerFactory:
    """Factory for creating file handlers based on file type.
    
    Determines the appropriate handler based on file extension
    and creates instances with consistent configuration.
    
    Attributes:
        encoding: Default encoding for text files
        errors: Default error handling mode
        
    Example:
        >>> factory = FileHandlerFactory()
        >>> handler = factory.create_handler(Path("app.log.gz"))
        >>> print(type(handler))
        <class 'GzipFileHandler'>
    """
    
    def __init__(
        self,
        encoding: str = "utf-8",
        errors: str = "replace"
    ) -> None:
        """Initialize the factory.
        
        Args:
            encoding: Character encoding for text files
            errors: Error handling mode ('strict', 'ignore', 'replace')
        """
        self.encoding = encoding
        self.errors = errors
    
    def create_handler(
        self,
        file_path: Path,
        encoding: Optional[str] = None,
        errors: Optional[str] = None
    ) -> AbstractFileHandler:
        """Create appropriate handler for the file.
        
        Determines handler type based on file extension:
        - .gz → GzipFileHandler
        - .log or others → LogFileHandler
        
        Args:
            file_path: Path to the file
            encoding: Character encoding (uses factory default if None)
            errors: Error handling mode (uses factory default if None)
            
        Returns:
            Appropriate file handler instance
            
        Raises:
            FileHandlingError: If file doesn't exist or has unsupported type
        """
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileHandlingError(
                f"File not found: {file_path}",
                file_path=file_path
            )
        
        # Use provided values or fall back to factory defaults
        enc = encoding if encoding is not None else self.encoding
        err = errors if errors is not None else self.errors
        
        # Determine handler based on extension
        extension = file_path.suffix.lower()
        
        if extension == ".gz":
            return GzipFileHandler(file_path, encoding=enc, errors=err)
        elif extension == ".log" or extension == "":
            return LogFileHandler(file_path, encoding=enc, errors=err)
        else:
            # Default to LogFileHandler for unknown extensions
            return LogFileHandler(file_path, encoding=enc, errors=err)
    
    def supports_file(self, file_path: Path) -> bool:
        """Check if factory supports the file type.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file type is supported
        """
        extension = file_path.suffix.lower()
        return extension in {".log", ".gz", ""}
    
    def __repr__(self) -> str:
        """String representation of the factory."""
        return (
            f"FileHandlerFactory(encoding={self.encoding}, "
            f"errors={self.errors})"
        )
