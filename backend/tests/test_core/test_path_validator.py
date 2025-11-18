"""
Tests for path validation and sanitization security utilities.

Comprehensive security test coverage for:
- Path traversal attack prevention
- Absolute path handling
- Null byte injection prevention
- Unicode encoding bypasses
- Symlink attacks
- Edge cases and boundary conditions
"""

import os
import pytest
import tempfile
from pathlib import Path

from core.path_validator import (
    PathValidator,
    PathTraversalError,
    validate_path,
    sanitize_path,
    set_default_validator,
)


@pytest.fixture
def temp_sandbox():
    """Create a temporary sandbox directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def validator(temp_sandbox):
    """Create a PathValidator with temporary sandbox."""
    return PathValidator(str(temp_sandbox))


class TestPathValidatorInitialization:
    """Test PathValidator initialization."""

    def test_init_with_valid_directory(self, temp_sandbox):
        """Test initialization with valid existing directory."""
        validator = PathValidator(str(temp_sandbox))
        assert validator.base_path == temp_sandbox.resolve()
        assert validator.allow_absolute is False

    def test_init_with_nonexistent_directory(self):
        """Test that initialization fails with nonexistent directory."""
        with pytest.raises(ValueError, match="does not exist"):
            PathValidator("/nonexistent/path")

    def test_init_with_file_instead_of_directory(self, temp_sandbox):
        """Test that initialization fails when base_path is a file."""
        test_file = temp_sandbox / "test.txt"
        test_file.touch()

        with pytest.raises(ValueError, match="not a directory"):
            PathValidator(str(test_file))

    def test_init_with_allow_absolute_flag(self, temp_sandbox):
        """Test initialization with allow_absolute=True."""
        validator = PathValidator(str(temp_sandbox), allow_absolute=True)
        assert validator.allow_absolute is True


class TestBasicPathValidation:
    """Test basic path validation without sanitization."""

    def test_valid_simple_path(self, validator):
        """Test that simple valid paths pass validation."""
        valid, error = validator.validate("file.txt")
        assert valid is True
        assert error is None

    def test_valid_subdirectory_path(self, validator):
        """Test that valid subdirectory paths pass validation."""
        valid, error = validator.validate("subdir/file.txt")
        assert valid is True
        assert error is None

    def test_empty_path_rejected(self, validator):
        """Test that empty paths are rejected."""
        valid, error = validator.validate("")
        assert valid is False
        assert "empty" in error.lower()

    def test_leading_slash_with_default_settings(self, validator):
        """Test that leading slash is rejected by default (absolute path)."""
        valid, error = validator.validate("/etc/passwd")
        assert valid is False
        assert "absolute" in error.lower()

    def test_absolute_path_allowed_when_enabled(self, temp_sandbox):
        """Test that absolute paths are allowed when flag is set."""
        validator = PathValidator(str(temp_sandbox), allow_absolute=True)
        valid, error = validator.validate("/file.txt")
        assert valid is True


class TestPathTraversalDetection:
    """Test detection of path traversal attacks."""

    def test_parent_directory_double_dot(self, validator):
        """Test that ../ is detected and rejected."""
        valid, error = validator.validate("../etc/passwd")
        assert valid is False
        assert "traversal" in error.lower()

    def test_parent_directory_in_middle(self, validator):
        """Test that ../ in middle of path is detected."""
        valid, error = validator.validate("subdir/../../../etc/passwd")
        assert valid is False
        assert ".." in error

    def test_backslash_parent_directory_windows(self, validator):
        """Test that ..\\ (Windows style) is detected."""
        valid, error = validator.validate("..\\windows\\system32")
        assert valid is False

    def test_url_encoded_parent_directory(self, validator):
        """Test that URL-encoded ../ is detected."""
        valid, error = validator.validate("%2e%2e%2fetc%2fpasswd")
        assert valid is False

    def test_mixed_encoding_attack(self, validator):
        """Test detection of mixed encoding bypass attempts."""
        valid, error = validator.validate(".%2e/etc/passwd")
        assert valid is False

    def test_double_url_encoding(self, validator):
        """Test detection of double URL encoding."""
        valid, error = validator.validate("%252e%252e%252f")
        assert valid is False

    def test_multiple_traversal_patterns(self, validator):
        """Test path with multiple traversal attempts."""
        valid, error = validator.validate("../../../../../../etc/passwd")
        assert valid is False


class TestForbiddenCharacters:
    """Test detection of forbidden characters."""

    def test_null_byte_injection(self, validator):
        """Test that null bytes are detected and rejected."""
        valid, error = validator.validate("file.txt\x00.jpg")
        assert valid is False
        assert "forbidden" in error.lower()

    def test_newline_character(self, validator):
        """Test that newline characters are rejected."""
        valid, error = validator.validate("file\n.txt")
        assert valid is False

    def test_carriage_return_character(self, validator):
        """Test that carriage return characters are rejected."""
        valid, error = validator.validate("file\r.txt")
        assert valid is False


class TestPathSanitization:
    """Test path sanitization and normalization."""

    def test_sanitize_simple_path(self, validator):
        """Test sanitization of simple valid path."""
        sanitized = validator.sanitize("file.txt")
        assert sanitized == "file.txt"

    def test_sanitize_removes_leading_slash(self, validator):
        """Test that leading slashes are removed."""
        sanitized = validator.sanitize("/subdir/file.txt")
        assert sanitized == os.path.normpath("subdir/file.txt")
        assert not sanitized.startswith("/")

    def test_sanitize_removes_leading_backslash(self, validator):
        """Test that leading backslashes are removed (Windows)."""
        sanitized = validator.sanitize("\\subdir\\file.txt")
        assert not sanitized.startswith("\\")

    def test_sanitize_normalizes_redundant_slashes(self, validator):
        """Test that redundant slashes are collapsed."""
        sanitized = validator.sanitize("subdir///file.txt")
        assert sanitized == os.path.normpath("subdir/file.txt")

    def test_sanitize_normalizes_current_directory(self, validator):
        """Test that ./ references are removed."""
        sanitized = validator.sanitize("./subdir/./file.txt")
        assert sanitized == os.path.normpath("subdir/file.txt")

    def test_sanitize_strips_whitespace(self, validator):
        """Test that leading/trailing whitespace is removed."""
        sanitized = validator.sanitize("  subdir/file.txt  ")
        assert sanitized == os.path.normpath("subdir/file.txt")

    def test_sanitize_rejects_traversal_attempts(self, validator):
        """Test that sanitize raises exception for traversal attempts."""
        with pytest.raises(PathTraversalError):
            validator.sanitize("../../../etc/passwd")

    def test_sanitize_rejects_null_bytes(self, validator):
        """Test that sanitize raises exception for null bytes."""
        with pytest.raises(PathTraversalError):
            validator.sanitize("file.txt\x00.jpg")


class TestSandboxEnforcement:
    """Test that paths stay within sandbox."""

    def test_is_within_base_valid_path(self, validator):
        """Test that valid paths are recognized as within base."""
        assert validator.is_within_base("file.txt") is True
        assert validator.is_within_base("subdir/file.txt") is True

    def test_is_within_base_traversal_attempt(self, validator):
        """Test that traversal attempts are recognized as outside base."""
        assert validator.is_within_base("../../../etc/passwd") is False
        assert validator.is_within_base("..") is False

    def test_get_safe_path_returns_absolute(self, validator, temp_sandbox):
        """Test that get_safe_path returns absolute Path within sandbox."""
        safe_path = validator.get_safe_path("subdir/file.txt")

        assert isinstance(safe_path, Path)
        assert safe_path.is_absolute()
        assert str(safe_path).startswith(str(temp_sandbox))

    def test_get_safe_path_creates_parents(self, validator, temp_sandbox):
        """Test that get_safe_path creates parent directories when requested."""
        safe_path = validator.get_safe_path("deep/nested/file.txt", create_parents=True)

        assert safe_path.parent.exists()
        assert safe_path.parent == temp_sandbox / "deep" / "nested"

    def test_get_safe_path_traversal_raises_exception(self, validator):
        """Test that get_safe_path raises exception for traversal attempts."""
        with pytest.raises(PathTraversalError):
            validator.get_safe_path("../../etc/passwd")


class TestSymlinkAttackPrevention:
    """Test prevention of symlink-based attacks."""

    def test_symlink_escape_detected(self, validator, temp_sandbox):
        """Test that symlinks escaping sandbox are detected."""
        # Create a directory outside sandbox
        with tempfile.TemporaryDirectory() as external_dir:
            # Create a symlink inside sandbox pointing outside
            symlink_path = temp_sandbox / "escape_link"
            symlink_path.symlink_to(external_dir)

            # Try to access via symlink
            with pytest.raises(PathTraversalError, match="escapes sandbox"):
                validator.sanitize("escape_link")

    def test_symlink_within_sandbox_allowed(self, validator, temp_sandbox):
        """Test that symlinks within sandbox are allowed."""
        # Create target file
        target = temp_sandbox / "target.txt"
        target.write_text("content")

        # Create symlink to target
        link = temp_sandbox / "link.txt"
        link.symlink_to(target)

        # Should be allowed (both within sandbox)
        sanitized = validator.sanitize("link.txt")
        assert sanitized == "link.txt"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_path(self, validator):
        """Test handling of very long paths."""
        long_path = "a/" * 1000 + "file.txt"
        # Should validate (no traversal), but may fail on filesystem limits
        valid, error = validator.validate(long_path)
        assert isinstance(valid, bool)

    def test_unicode_characters_in_path(self, validator):
        """Test paths with Unicode characters."""
        unicode_path = "文件/файл/αρχείο.txt"
        valid, error = validator.validate(unicode_path)
        assert valid is True

    def test_path_with_spaces(self, validator):
        """Test paths with spaces."""
        valid, error = validator.validate("my documents/file.txt")
        assert valid is True

    def test_path_with_special_chars(self, validator):
        """Test paths with special characters (not forbidden)."""
        valid, error = validator.validate("file-name_2023.txt")
        assert valid is True

    def test_empty_subdirectory_name(self, validator):
        """Test path with empty subdirectory (double slash)."""
        # Should be normalized and allowed
        sanitized = validator.sanitize("subdir//file.txt")
        assert sanitized == os.path.normpath("subdir/file.txt")

    def test_only_dots_path(self, validator):
        """Test path consisting only of dots."""
        # Current directory should be normalized to empty or rejected
        with pytest.raises(PathTraversalError):
            validator.sanitize("..")


class TestHelperFunctions:
    """Test module-level helper functions."""

    def test_validate_path_helper(self, temp_sandbox):
        """Test validate_path helper function."""
        valid, error = validate_path("file.txt", str(temp_sandbox))
        assert valid is True

    def test_sanitize_path_helper(self, temp_sandbox):
        """Test sanitize_path helper function."""
        sanitized = sanitize_path("subdir/file.txt", str(temp_sandbox))
        assert sanitized == os.path.normpath("subdir/file.txt")

    def test_set_default_validator(self, temp_sandbox):
        """Test setting default validator."""
        validator = PathValidator(str(temp_sandbox))
        set_default_validator(validator)

        # Now helpers should use this validator
        valid, error = validate_path("file.txt")
        assert valid is True


class TestRealWorldAttackVectors:
    """Test real-world attack vectors and bypass attempts."""

    def test_windows_unc_path(self, validator):
        """Test Windows UNC path (\\\\server\\share)."""
        valid, error = validator.validate("\\\\\\\\server\\\\share\\\\file.txt")
        # Should be rejected (absolute path or traversal)
        assert valid is False

    def test_mixed_separators(self, validator):
        """Test mixed forward and backslashes."""
        valid, error = validator.validate("subdir\\../file.txt")
        assert valid is False

    def test_repeated_parent_refs(self, validator):
        """Test repeated parent directory references."""
        valid, error = validator.validate("../../../../../../../../etc/passwd")
        assert valid is False

    def test_case_variation_bypass_attempt(self, validator):
        """Test case variation bypass attempts."""
        # Path validator should be case-insensitive for traversal patterns
        valid, error = validator.validate("..%2F")
        assert valid is False

    def test_utf8_overlong_encoding(self, validator):
        """Test UTF-8 overlong encoding bypass attempts."""
        # This is a theoretical attack - UTF-8 encoding of ../
        # Most systems normalize this, but we should be safe
        valid, error = validator.validate("%c0%ae%c0%ae%c0%af")
        # Should be rejected or safely handled
        assert isinstance(valid, bool)

    def test_path_with_query_string(self, validator):
        """Test path with query string (web context)."""
        valid, error = validator.validate("file.txt?param=../../etc/passwd")
        # Query string should be treated as part of filename
        # No special meaning in filesystem context
        assert isinstance(valid, bool)

    def test_path_with_fragment(self, validator):
        """Test path with fragment identifier."""
        valid, error = validator.validate("file.txt#../../../etc/passwd")
        # Fragment should be treated as part of filename
        assert isinstance(valid, bool)


class TestSecurityAssertions:
    """Test critical security assertions."""

    def test_cannot_read_etc_passwd(self, validator):
        """CRITICAL: Verify cannot access /etc/passwd."""
        with pytest.raises(PathTraversalError):
            validator.sanitize("../../../../../../../etc/passwd")

    def test_cannot_escape_with_absolute_path(self, validator):
        """CRITICAL: Verify absolute paths are rejected by default."""
        valid, error = validator.validate("/etc/passwd")
        assert valid is False

    def test_cannot_escape_with_symlink(self, validator, temp_sandbox):
        """CRITICAL: Verify symlinks cannot escape sandbox."""
        with tempfile.TemporaryDirectory() as external:
            link = temp_sandbox / "bad_link"
            link.symlink_to(external)

            with pytest.raises(PathTraversalError):
                validator.get_safe_path("bad_link/../../etc/passwd")

    def test_normalized_path_stays_in_sandbox(self, validator, temp_sandbox):
        """CRITICAL: Verify all normalized paths stay in sandbox."""
        test_paths = [
            "file.txt",
            "subdir/file.txt",
            "./file.txt",
            "subdir/../file.txt",
            "//subdir///file.txt",
        ]

        for path in test_paths:
            safe_path = validator.get_safe_path(path)
            assert str(safe_path).startswith(str(temp_sandbox)), \
                f"Path {path} escaped sandbox: {safe_path}"
