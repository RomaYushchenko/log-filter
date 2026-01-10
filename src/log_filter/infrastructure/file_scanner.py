"""
File scanner for discovering and filtering log files.

This module provides efficient file discovery with lazy evaluation,
filtering, and metadata collection. Uses iterator pattern to avoid
loading all file paths into memory.
"""

import fnmatch
import logging
from pathlib import Path
from typing import Iterator, Optional, Set

from log_filter.core.exceptions import FileHandlingError
from log_filter.domain.models import FileMetadata

logger = logging.getLogger(__name__)


class FileScanner:
    """Lazy file scanner with filtering capabilities.

    Scans directories for log files matching specified criteria.
    Uses iterator pattern for memory efficiency - files are discovered
    and filtered on-demand rather than loading all paths upfront.

    Attributes:
        root_path: Root directory to scan
        file_masks: List of filename substrings to match
        allowed_extensions: Set of allowed file extensions
        max_file_size_mb: Maximum file size in MB (None = unlimited)
        recursive: Whether to scan subdirectories

    Example:
        >>> scanner = FileScanner(
        ...     root_path=Path("/var/log"),
        ...     file_masks=["kafka"],
        ...     allowed_extensions={".log", ".gz"}
        ... )
        >>> for file_meta in scanner.scan():
        ...     if not file_meta.should_skip:
        ...         process(file_meta.path)
    """

    DEFAULT_EXTENSIONS = {".log", ".gz"}

    def __init__(
        self,
        root_path: Path,
        file_masks: Optional[list[str]] = None,
        include_patterns: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
        allowed_extensions: Optional[set[str]] = None,
        max_file_size_mb: Optional[int] = None,
        recursive: bool = True,
    ) -> None:
        """Initialize the file scanner.

        Args:
            root_path: Root directory to scan for files
            file_masks: List of filename substrings to match.
                       If None or empty, all files are considered.
            include_patterns: Glob patterns for files to include (e.g., ["*.log", "app-*.txt"]).
                            If None or empty, all files are considered.
            exclude_patterns: Glob patterns for files to exclude (e.g., ["*.old", "debug.log"]).
            allowed_extensions: Set of allowed file extensions (e.g., {".log", ".gz"}).
                              If None, uses DEFAULT_EXTENSIONS.
            max_file_size_mb: Maximum file size in MB. Files larger than this
                            will be marked as should_skip.
            recursive: If True, scan subdirectories recursively.

        Raises:
            FileHandlingError: If root_path doesn't exist or isn't a directory
        """
        if not isinstance(root_path, Path):
            root_path = Path(root_path)

        if not root_path.exists():
            raise FileHandlingError(f"Root path does not exist: {root_path}", file_path=root_path)

        if not root_path.is_dir():
            raise FileHandlingError(
                f"Root path is not a directory: {root_path}", file_path=root_path
            )

        self.root_path = root_path
        self.file_masks = file_masks or []
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        self.allowed_extensions = allowed_extensions or self.DEFAULT_EXTENSIONS
        self.max_file_size_mb = max_file_size_mb
        self.recursive = recursive

    def scan(self) -> Iterator[FileMetadata]:
        """Scan for files matching criteria.

        Lazily discovers files in the root path and yields FileMetadata
        for each file. Files are filtered and validated on-demand.

        OPTIMIZATION: When include_patterns are specified, use them directly
        in the glob pattern instead of scanning all files and filtering.
        This provides massive performance improvement (seconds vs minutes).

        Yields:
            FileMetadata objects with skip information
        """
        # Optimization: Use include_patterns directly in glob for much faster scanning
        if self.include_patterns:
            logger.info(f"Scanning for files matching patterns: {self.include_patterns}")
            seen_paths: Set[Path] = set()

            for pattern in self.include_patterns:
                # Construct glob pattern with recursion if needed
                glob_pattern = f"**/{pattern}" if self.recursive else pattern

                for path in self.root_path.glob(glob_pattern):
                    # Skip directories
                    if not path.is_file():
                        continue

                    # Skip duplicates (same file can match multiple patterns)
                    if path in seen_paths:
                        continue
                    seen_paths.add(path)

                    # Create metadata with filtering
                    metadata = self._create_metadata(path)
                    yield metadata
        else:
            # Fallback: scan all files (slower)
            logger.info(f"Scanning all files in {self.root_path}...")
            glob_pattern = "**/*" if self.recursive else "*"

            for path in self.root_path.glob(glob_pattern):
                # Skip directories
                if not path.is_file():
                    continue

                # Create metadata with filtering
                metadata = self._create_metadata(path)
                yield metadata

    def _create_metadata(self, path: Path) -> FileMetadata:
        """Create FileMetadata with filtering logic.

        Args:
            path: Path to the file

        Returns:
            FileMetadata with should_skip and skip_reason set
        """
        # Extract extension and check if compressed
        extension = path.suffix.lower()
        is_compressed = extension in {".gz", ".bz2", ".xz", ".zip"}

        # Check extension
        if not self._has_allowed_extension(path):
            return FileMetadata(
                path=path,
                size_bytes=0,
                extension=extension,
                is_compressed=is_compressed,
                skip_reason="extension-not-allowed",
            )

        # Get file size
        try:
            size_bytes = path.stat().st_size
        except OSError as e:
            return FileMetadata(
                path=path,
                size_bytes=0,
                extension=extension,
                is_compressed=is_compressed,
                skip_reason=f"stat-error: {e}",
            )

        # Check file mask
        if not self._matches_file_mask(path):
            return FileMetadata(
                path=path,
                size_bytes=size_bytes,
                extension=extension,
                is_compressed=is_compressed,
                skip_reason="name-filter",
            )

        # Check include patterns
        if self.include_patterns and not self._matches_include_pattern(path):
            return FileMetadata(
                path=path,
                size_bytes=size_bytes,
                extension=extension,
                is_compressed=is_compressed,
                skip_reason="include-pattern",
            )

        # Check exclude patterns
        if self.exclude_patterns and self._matches_exclude_pattern(path):
            return FileMetadata(
                path=path,
                size_bytes=size_bytes,
                extension=extension,
                is_compressed=is_compressed,
                skip_reason="exclude-pattern",
            )

        # Check file size limit
        if self.max_file_size_mb is not None:
            size_mb = size_bytes / (1024 * 1024)
            if size_mb > self.max_file_size_mb:
                return FileMetadata(
                    path=path,
                    size_bytes=size_bytes,
                    extension=extension,
                    is_compressed=is_compressed,
                    skip_reason="size-limit",
                )

        # Check read access
        if not path.is_file() or not self._is_readable(path):
            return FileMetadata(
                path=path,
                size_bytes=size_bytes,
                extension=extension,
                is_compressed=is_compressed,
                skip_reason="access-denied",
            )

        # File passes all filters
        return FileMetadata(
            path=path,
            size_bytes=size_bytes,
            extension=extension,
            is_compressed=is_compressed,
            skip_reason=None,
        )

    def _matches_include_pattern(self, path: Path) -> bool:
        """Check if filename matches any include pattern (glob).

        Args:
            path: File path to check

        Returns:
            True if file matches any include pattern
        """
        if not self.include_patterns:
            return True

        filename = path.name
        return any(fnmatch.fnmatch(filename, pattern) for pattern in self.include_patterns)

    def _matches_exclude_pattern(self, path: Path) -> bool:
        """Check if filename matches any exclude pattern (glob).

        Args:
            path: File path to check

        Returns:
            True if file matches any exclude pattern
        """
        if not self.exclude_patterns:
            return False

        filename = path.name
        return any(fnmatch.fnmatch(filename, pattern) for pattern in self.exclude_patterns)

    def _has_allowed_extension(self, path: Path) -> bool:
        """Check if file has an allowed extension.

        Args:
            path: File path to check

        Returns:
            True if extension is allowed
        """
        return path.suffix.lower() in self.allowed_extensions

    def _matches_file_mask(self, path: Path) -> bool:
        """Check if filename matches any file mask.

        Args:
            path: File path to check

        Returns:
            True if file matches (or no masks specified)
        """
        # If no masks specified, all files match
        if not self.file_masks:
            return True

        filename = path.name.lower()
        return any(mask.lower() in filename for mask in self.file_masks)

    def _is_readable(self, path: Path) -> bool:
        """Check if file is readable.

        Args:
            path: File path to check

        Returns:
            True if file can be opened for reading
        """
        try:
            with open(path, "rb") as f:
                f.read(1)
            return True
        except (OSError, PermissionError):
            return False

    def count_files(self) -> dict[str, int]:
        """Count files by status.

        Returns:
            Dictionary with counts:
            - total: Total files scanned
            - eligible: Files passing all filters
            - skipped: Files that should be skipped
            - by_reason: Dict of skip reasons and counts
        """
        total = 0
        eligible = 0
        skipped = 0
        by_reason: dict[str, int] = {}

        for metadata in self.scan():
            total += 1
            if metadata.should_skip:
                skipped += 1
                reason = metadata.skip_reason or "unknown"
                by_reason[reason] = by_reason.get(reason, 0) + 1
            else:
                eligible += 1

        return {"total": total, "eligible": eligible, "skipped": skipped, "by_reason": by_reason}

    def __repr__(self) -> str:
        """String representation of the scanner."""
        return (
            f"FileScanner(root={self.root_path}, "
            f"masks={self.file_masks}, "
            f"extensions={self.allowed_extensions})"
        )
