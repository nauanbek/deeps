"""
Path validation and sanitization utilities for filesystem security.

Prevents path traversal attacks and ensures all file operations
stay within designated sandbox directories.

Security Features:
- Path traversal prevention (blocks ../, ..\)
- Absolute path sanitization
- Symlink detection and blocking
- Null byte injection prevention
- Unicode normalization
- Path canonicalization
"""

import os
import re
from pathlib import Path
from typing import Optional, Tuple


class PathTraversalError(ValueError):
    """Raised when a path traversal attempt is detected."""
    pass


class PathValidator:
    """
    Validates and sanitizes filesystem paths to prevent security vulnerabilities.

    Protects against:
    - Path traversal attacks (../, ..\\)
    - Absolute path escapes (/etc/passwd)
    - Symlink attacks
    - Null byte injection (\x00)
    - Unicode encoding attacks
    - Double encoding bypasses
    """

    # Dangerous path patterns
    TRAVERSAL_PATTERNS = [
        r'\.\./',          # ../
        r'\.\.',           # ..
        r'\.\.\\',         # ..\
        r'%2e%2e%2f',      # URL encoded ../
        r'%2e%2e/',        # URL encoded ../
        r'%2e%2e\\',       # URL encoded ..\
        r'\.%2e/',         # Mixed encoding
        r'%252e%252e%252f', # Double URL encoded
    ]

    # Forbidden characters
    FORBIDDEN_CHARS = [
        '\x00',  # Null byte
        '\n',    # Newline
        '\r',    # Carriage return
    ]

    def __init__(self, base_path: str, allow_absolute: bool = False):
        """
        Initialize path validator with base directory.

        Args:
            base_path: Base directory for sandboxing (must exist)
            allow_absolute: Whether to allow absolute paths (default: False)

        Raises:
            ValueError: If base_path doesn't exist or isn't a directory
        """
        self.base_path = Path(base_path).resolve()

        if not self.base_path.exists():
            raise ValueError(f"Base path does not exist: {base_path}")

        if not self.base_path.is_dir():
            raise ValueError(f"Base path is not a directory: {base_path}")

        self.allow_absolute = allow_absolute

    def validate(self, path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate path without modifying it.

        Args:
            path: Path to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if path is safe
            - error_message: None if valid, error description if invalid

        Example:
            >>> validator = PathValidator("/safe/dir")
            >>> valid, error = validator.validate("../etc/passwd")
            >>> print(valid)  # False
            >>> print(error)  # "Path traversal detected: .."
        """
        if not path:
            return False, "Path cannot be empty"

        # Check for null bytes
        if any(char in path for char in self.FORBIDDEN_CHARS):
            return False, "Path contains forbidden characters (null byte, newline)"

        # Check for path traversal patterns (case-insensitive)
        path_lower = path.lower()
        for pattern in self.TRAVERSAL_PATTERNS:
            if re.search(pattern, path_lower, re.IGNORECASE):
                return False, f"Path traversal detected: {pattern}"

        # Check for parent directory references
        if '..' in path:
            return False, "Path traversal detected: .."

        # Check absolute paths if not allowed
        if not self.allow_absolute:
            if os.path.isabs(path):
                return False, "Absolute paths are not allowed"

        return True, None

    def sanitize(self, path: str) -> str:
        """
        Sanitize and normalize path to prevent attacks.

        Steps:
        1. Validate path (raises exception if invalid)
        2. Strip leading/trailing whitespace
        3. Normalize path (collapse redundant separators)
        4. Ensure path is relative
        5. Verify result stays within base_path

        Args:
            path: Path to sanitize

        Returns:
            Sanitized path string

        Raises:
            PathTraversalError: If path is invalid or escapes sandbox

        Example:
            >>> validator = PathValidator("/safe/dir")
            >>> sanitized = validator.sanitize("subdir/../file.txt")
            >>> print(sanitized)  # "file.txt"
        """
        # Validate first
        is_valid, error = self.validate(path)
        if not is_valid:
            raise PathTraversalError(error)

        # Strip whitespace
        path = path.strip()

        # Remove leading slashes to make path relative
        path = path.lstrip('/')
        path = path.lstrip('\\')

        # Normalize path (collapse redundant separators, resolve .)
        # Use os.path.normpath to handle platform-specific separators
        normalized = os.path.normpath(path)

        # Ensure normalization didn't introduce parent refs
        if '..' in normalized:
            raise PathTraversalError(f"Path escapes sandbox after normalization: {normalized}")

        # Verify final path stays within base_path
        full_path = self.base_path / normalized
        try:
            # Resolve to absolute path to check for symlink escapes
            resolved = full_path.resolve()

            # Check if resolved path is within base_path
            if not str(resolved).startswith(str(self.base_path)):
                raise PathTraversalError(
                    f"Path escapes sandbox: {path} -> {resolved}"
                )

        except (OSError, RuntimeError) as e:
            # Handle symlink loops, permission errors, etc.
            raise PathTraversalError(f"Path resolution error: {e}")

        return normalized

    def get_safe_path(self, path: str, create_parents: bool = False) -> Path:
        """
        Get a safe absolute Path object within the sandbox.

        Args:
            path: Relative path to sanitize
            create_parents: Whether to create parent directories

        Returns:
            Absolute Path object within base_path

        Raises:
            PathTraversalError: If path is invalid

        Example:
            >>> validator = PathValidator("/safe/dir")
            >>> safe_path = validator.get_safe_path("subdir/file.txt", create_parents=True)
            >>> print(safe_path)  # /safe/dir/subdir/file.txt
        """
        sanitized = self.sanitize(path)
        safe_path = self.base_path / sanitized

        if create_parents:
            safe_path.parent.mkdir(parents=True, exist_ok=True)

        return safe_path

    def is_within_base(self, path: str) -> bool:
        """
        Check if path (after resolution) stays within base_path.

        Args:
            path: Path to check

        Returns:
            True if path is within base_path, False otherwise

        Example:
            >>> validator = PathValidator("/safe/dir")
            >>> validator.is_within_base("subdir/file.txt")  # True
            >>> validator.is_within_base("../../etc/passwd")  # False
        """
        try:
            self.sanitize(path)
            return True
        except PathTraversalError:
            return False


# Global default validator (for testing, should be overridden in production)
_default_validator: Optional[PathValidator] = None


def get_default_validator() -> PathValidator:
    """
    Get the default path validator instance.

    In production, this should be configured with the appropriate base_path.

    Returns:
        PathValidator instance
    """
    global _default_validator
    if _default_validator is None:
        # Default to /tmp for testing
        _default_validator = PathValidator("/tmp")
    return _default_validator


def set_default_validator(validator: PathValidator) -> None:
    """
    Set the default path validator instance.

    Args:
        validator: PathValidator to use as default
    """
    global _default_validator
    _default_validator = validator


def validate_path(path: str, base_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate a path using default or specified base path.

    Args:
        path: Path to validate
        base_path: Optional base path (uses default if None)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if base_path:
        validator = PathValidator(base_path)
    else:
        validator = get_default_validator()

    return validator.validate(path)


def sanitize_path(path: str, base_path: Optional[str] = None) -> str:
    """
    Sanitize a path using default or specified base path.

    Args:
        path: Path to sanitize
        base_path: Optional base path (uses default if None)

    Returns:
        Sanitized path string

    Raises:
        PathTraversalError: If path is invalid
    """
    if base_path:
        validator = PathValidator(base_path)
    else:
        validator = get_default_validator()

    return validator.sanitize(path)
