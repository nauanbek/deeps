"""
Password validation and strength checking utility.

Implements comprehensive password complexity requirements:
- Minimum length (8 characters)
- Must contain uppercase letters
- Must contain lowercase letters
- Must contain digits
- Must contain special characters (optional but recommended)
- Prevents common passwords
- Calculates password strength score
"""

import re
from enum import Enum
from typing import List, Tuple


class PasswordStrength(str, Enum):
    """Password strength levels."""
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class PasswordValidator:
    """
    Validates password complexity and calculates strength.

    Requirements (configurable):
    - Minimum 8 characters (can be increased)
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - Optional: At least 1 special character
    - Not in common password list
    """

    # Common weak passwords (subset - in production, use a larger list)
    COMMON_PASSWORDS = {
        "password", "12345678", "qwerty", "abc123", "password123",
        "admin", "letmein", "welcome", "monkey", "1234567890",
        "password1", "qwerty123", "admin123", "welcome123", "test123",
        "root", "toor", "pass", "Password1", "Password123"
    }

    # Special characters
    SPECIAL_CHARS = r"!@#$%^&*()_+-=[]{}|;:,.<>?/~`"

    def __init__(
        self,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = False,  # Optional for basic security
        check_common: bool = True,
    ):
        """
        Initialize password validator with custom requirements.

        Args:
            min_length: Minimum password length (default: 8)
            require_uppercase: Require at least one uppercase letter
            require_lowercase: Require at least one lowercase letter
            require_digit: Require at least one digit
            require_special: Require at least one special character
            check_common: Check against common password list
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
        self.check_common = check_common

    def validate(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password against all requirements.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
            - is_valid: True if password meets all requirements
            - list_of_errors: List of error messages (empty if valid)
        """
        errors = []

        # Check length
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")

        # Check uppercase
        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        # Check lowercase
        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        # Check digit
        if self.require_digit and not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")

        # Check special character
        if self.require_special and not re.search(rf"[{re.escape(self.SPECIAL_CHARS)}]", password):
            errors.append("Password must contain at least one special character")

        # Check common passwords (case-insensitive)
        if self.check_common and password.lower() in self.COMMON_PASSWORDS:
            errors.append("Password is too common. Please choose a more unique password")

        return len(errors) == 0, errors

    def calculate_strength(self, password: str) -> Tuple[PasswordStrength, int]:
        """
        Calculate password strength score.

        Scoring:
        - Length: +1 per character (max 20)
        - Uppercase: +10
        - Lowercase: +10
        - Digit: +10
        - Special char: +15
        - Length > 12: +10
        - Length > 16: +10
        - Mixed case + digits + special: +15 bonus

        Score ranges:
        - 0-29: Very Weak
        - 30-49: Weak
        - 50-69: Medium
        - 70-89: Strong
        - 90+: Very Strong

        Args:
            password: Password to evaluate

        Returns:
            Tuple of (PasswordStrength enum, numeric score)
        """
        score = 0

        # Length score (1 point per char, max 20)
        score += min(len(password), 20)

        # Character variety bonuses
        has_upper = bool(re.search(r"[A-Z]", password))
        has_lower = bool(re.search(r"[a-z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = bool(re.search(rf"[{re.escape(self.SPECIAL_CHARS)}]", password))

        if has_upper:
            score += 10
        if has_lower:
            score += 10
        if has_digit:
            score += 10
        if has_special:
            score += 15

        # Length bonuses
        if len(password) > 12:
            score += 10
        if len(password) > 16:
            score += 10

        # Complexity bonus (all character types present)
        if has_upper and has_lower and has_digit and has_special:
            score += 15

        # Penalize common passwords
        if password.lower() in self.COMMON_PASSWORDS:
            score = max(0, score - 30)

        # Penalize repetitive characters
        if self._has_repetitive_chars(password):
            score = max(0, score - 10)

        # Determine strength level
        if score < 30:
            strength = PasswordStrength.VERY_WEAK
        elif score < 50:
            strength = PasswordStrength.WEAK
        elif score < 70:
            strength = PasswordStrength.MEDIUM
        elif score < 90:
            strength = PasswordStrength.STRONG
        else:
            strength = PasswordStrength.VERY_STRONG

        return strength, score

    def _has_repetitive_chars(self, password: str, threshold: int = 3) -> bool:
        """
        Check if password has repetitive character sequences.

        Args:
            password: Password to check
            threshold: Number of consecutive repeated chars to flag

        Returns:
            True if repetitive pattern found
        """
        for i in range(len(password) - threshold + 1):
            if password[i] == password[i + 1] == password[i + threshold - 1]:
                return True
        return False

    def get_suggestions(self, password: str) -> List[str]:
        """
        Get suggestions for improving password strength.

        Args:
            password: Password to evaluate

        Returns:
            List of improvement suggestions
        """
        suggestions = []
        strength, score = self.calculate_strength(password)

        # Only suggest if not very strong
        if strength == PasswordStrength.VERY_STRONG:
            return ["Password is very strong!"]

        # Check what's missing
        if len(password) < 12:
            suggestions.append("Use at least 12 characters for better security")

        if not re.search(r"[A-Z]", password):
            suggestions.append("Add uppercase letters")

        if not re.search(r"[a-z]", password):
            suggestions.append("Add lowercase letters")

        if not re.search(r"\d", password):
            suggestions.append("Add numbers")

        if not re.search(rf"[{re.escape(self.SPECIAL_CHARS)}]", password):
            suggestions.append("Add special characters (!@#$%^&*)")

        if password.lower() in self.COMMON_PASSWORDS:
            suggestions.append("Avoid common passwords")

        if self._has_repetitive_chars(password):
            suggestions.append("Avoid repeating characters")

        return suggestions


# Default validator instance
default_validator = PasswordValidator(
    min_length=8,
    require_uppercase=True,
    require_lowercase=True,
    require_digit=True,
    require_special=False,  # Optional for user-friendliness
    check_common=True,
)


def validate_password(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password using default requirements.

    Requirements:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - Not a common password

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, list_of_errors)

    Example:
        >>> valid, errors = validate_password("WeakPass")
        >>> print(valid)  # False
        >>> print(errors)  # ['Password must contain at least one digit']
    """
    return default_validator.validate(password)


def calculate_password_strength(password: str) -> dict:
    """
    Calculate password strength and return detailed results.

    Args:
        password: Password to evaluate

    Returns:
        Dictionary with strength, score, and suggestions

    Example:
        >>> result = calculate_password_strength("MyP@ssw0rd!")
        >>> print(result)
        {
            "strength": "strong",
            "score": 75,
            "suggestions": ["Use at least 12 characters for better security"]
        }
    """
    strength, score = default_validator.calculate_strength(password)
    suggestions = default_validator.get_suggestions(password)

    return {
        "strength": strength.value,
        "score": score,
        "suggestions": suggestions,
    }
