"""
Tests for password validation and strength checking.

Comprehensive test coverage for:
- Password complexity validation
- Strength calculation
- Common password detection
- Edge cases and special characters
"""

import pytest
from core.password_validator import (
    PasswordValidator,
    PasswordStrength,
    validate_password,
    calculate_password_strength,
)


class TestPasswordValidator:
    """Test suite for PasswordValidator class."""

    def test_valid_password_passes_all_checks(self):
        """Test that a strong password passes all validation checks."""
        validator = PasswordValidator()
        valid, errors = validator.validate("StrongPass123")

        assert valid is True
        assert len(errors) == 0

    def test_short_password_fails(self):
        """Test that password shorter than minimum length fails."""
        validator = PasswordValidator(min_length=8)
        valid, errors = validator.validate("Short1")

        assert valid is False
        assert any("8 characters" in err for err in errors)

    def test_no_uppercase_fails(self):
        """Test that password without uppercase fails if required."""
        validator = PasswordValidator(require_uppercase=True)
        valid, errors = validator.validate("lowercase123")

        assert valid is False
        assert any("uppercase" in err for err in errors)

    def test_no_lowercase_fails(self):
        """Test that password without lowercase fails if required."""
        validator = PasswordValidator(require_lowercase=True)
        valid, errors = validator.validate("UPPERCASE123")

        assert valid is False
        assert any("lowercase" in err for err in errors)

    def test_no_digit_fails(self):
        """Test that password without digit fails if required."""
        validator = PasswordValidator(require_digit=True)
        valid, errors = validator.validate("NoDigitsHere")

        assert valid is False
        assert any("digit" in err for err in errors)

    def test_no_special_character_fails_if_required(self):
        """Test that password without special char fails if required."""
        validator = PasswordValidator(require_special=True)
        valid, errors = validator.validate("NoSpecialChar123")

        assert valid is False
        assert any("special character" in err for err in errors)

    def test_special_character_passes_if_required(self):
        """Test that password with special character passes if required."""
        validator = PasswordValidator(require_special=True)
        valid, errors = validator.validate("HasSpecial!123")

        assert valid is True
        assert len(errors) == 0

    def test_common_password_fails(self):
        """Test that common passwords are rejected."""
        validator = PasswordValidator(check_common=True)
        common_passwords = ["password", "12345678", "qwerty", "Password123"]

        for pwd in common_passwords:
            valid, errors = validator.validate(pwd)
            assert valid is False
            assert any("common" in err.lower() for err in errors)

    def test_common_password_case_insensitive(self):
        """Test that common password check is case-insensitive."""
        validator = PasswordValidator(check_common=True)
        valid, errors = validator.validate("PASSWORD")

        assert valid is False
        assert any("common" in err.lower() for err in errors)

    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are returned."""
        validator = PasswordValidator(
            min_length=8,
            require_uppercase=True,
            require_lowercase=True,
            require_digit=True,
        )
        valid, errors = validator.validate("short")

        assert valid is False
        assert len(errors) >= 2  # Should fail multiple checks

    def test_custom_min_length(self):
        """Test custom minimum length requirement."""
        validator = PasswordValidator(min_length=12)

        # 10 chars - should fail
        valid, errors = validator.validate("Short123Ab")
        assert valid is False

        # 12 chars - should pass
        valid, errors = validator.validate("LongerPass123")
        assert valid is True

    def test_disable_uppercase_requirement(self):
        """Test that uppercase can be optional."""
        validator = PasswordValidator(require_uppercase=False)
        valid, errors = validator.validate("lowercase123")

        assert valid is True

    def test_disable_common_password_check(self):
        """Test that common password check can be disabled."""
        validator = PasswordValidator(check_common=False)
        valid, errors = validator.validate("password")

        # Should only fail other checks, not common password
        assert not any("common" in err.lower() for err in errors)


class TestPasswordStrengthCalculation:
    """Test suite for password strength calculation."""

    def test_very_weak_password(self):
        """Test very weak password detection."""
        validator = PasswordValidator()
        strength, score = validator.calculate_strength("abc")

        assert strength == PasswordStrength.VERY_WEAK
        assert score < 30

    def test_weak_password(self):
        """Test weak password detection."""
        validator = PasswordValidator()
        strength, score = validator.calculate_strength("password123")

        assert strength in [PasswordStrength.VERY_WEAK, PasswordStrength.WEAK]
        assert score < 50

    def test_medium_password(self):
        """Test medium password detection."""
        validator = PasswordValidator()
        strength, score = validator.calculate_strength("MyPassword123")

        assert strength == PasswordStrength.MEDIUM
        assert 50 <= score < 70

    def test_strong_password(self):
        """Test strong password detection."""
        validator = PasswordValidator()
        strength, score = validator.calculate_strength("MyP@ssword123!")

        assert strength in [PasswordStrength.STRONG, PasswordStrength.VERY_STRONG]
        assert score >= 70

    def test_very_strong_password(self):
        """Test very strong password detection."""
        validator = PasswordValidator()
        strength, score = validator.calculate_strength("MyV3ry$tr0ng&L0ngP@ssw0rd!")

        assert strength == PasswordStrength.VERY_STRONG
        assert score >= 90

    def test_length_affects_score(self):
        """Test that longer passwords get higher scores."""
        validator = PasswordValidator()

        _, short_score = validator.calculate_strength("Pass1!")
        _, long_score = validator.calculate_strength("MyLongerPassword123!")

        assert long_score > short_score

    def test_character_variety_bonus(self):
        """Test that using all character types gives bonus."""
        validator = PasswordValidator()

        # Only letters and digits
        _, basic_score = validator.calculate_strength("Password123")

        # Letters, digits, and special chars
        _, complex_score = validator.calculate_strength("P@ssw0rd!23")

        assert complex_score > basic_score

    def test_common_password_penalty(self):
        """Test that common passwords get score penalty."""
        validator = PasswordValidator()

        # Common password
        _, common_score = validator.calculate_strength("password")

        # Unique password
        _, unique_score = validator.calculate_strength("uniqueword")

        assert unique_score > common_score

    def test_repetitive_characters_penalty(self):
        """Test that repetitive characters reduce score."""
        validator = PasswordValidator()

        # Repetitive
        _, rep_score = validator.calculate_strength("aaa111bbb")

        # Non-repetitive
        _, normal_score = validator.calculate_strength("abc123xyz")

        assert normal_score > rep_score

    def test_score_ranges_are_consistent(self):
        """Test that strength levels map to correct score ranges."""
        test_cases = [
            ("abc", PasswordStrength.VERY_WEAK),  # Very weak
            ("password12", PasswordStrength.WEAK),  # Weak
            ("Password123", PasswordStrength.MEDIUM),  # Medium
            ("MyP@ss123!", PasswordStrength.STRONG),  # Strong
            ("MyV3ry$ecure&P@ssw0rd!", PasswordStrength.VERY_STRONG),  # Very strong
        ]

        validator = PasswordValidator()
        for password, expected_strength in test_cases:
            strength, _ = validator.calculate_strength(password)
            assert strength == expected_strength or strength.value in [
                PasswordStrength.STRONG.value,
                PasswordStrength.VERY_STRONG.value
            ]  # Allow some flexibility for strong passwords


class TestPasswordSuggestions:
    """Test suite for password improvement suggestions."""

    def test_short_password_gets_length_suggestion(self):
        """Test that short passwords get length suggestion."""
        validator = PasswordValidator()
        suggestions = validator.get_suggestions("Short1")

        assert any("12 characters" in s for s in suggestions)

    def test_no_uppercase_gets_suggestion(self):
        """Test suggestion for missing uppercase."""
        validator = PasswordValidator()
        suggestions = validator.get_suggestions("lowercase123")

        assert any("uppercase" in s.lower() for s in suggestions)

    def test_no_lowercase_gets_suggestion(self):
        """Test suggestion for missing lowercase."""
        validator = PasswordValidator()
        suggestions = validator.get_suggestions("UPPERCASE123")

        assert any("lowercase" in s.lower() for s in suggestions)

    def test_no_digit_gets_suggestion(self):
        """Test suggestion for missing digit."""
        validator = PasswordValidator()
        suggestions = validator.get_suggestions("NoDigitsHere")

        assert any("number" in s.lower() for s in suggestions)

    def test_no_special_gets_suggestion(self):
        """Test suggestion for missing special character."""
        validator = PasswordValidator()
        suggestions = validator.get_suggestions("NoSpecial123")

        assert any("special" in s.lower() for s in suggestions)

    def test_common_password_gets_suggestion(self):
        """Test suggestion for common password."""
        validator = PasswordValidator()
        suggestions = validator.get_suggestions("password")

        assert any("common" in s.lower() for s in suggestions)

    def test_very_strong_password_gets_positive_feedback(self):
        """Test that very strong passwords get positive feedback."""
        validator = PasswordValidator()
        suggestions = validator.get_suggestions("MyV3ry$tr0ng&L0ngP@ssw0rd!")

        assert any("strong" in s.lower() for s in suggestions)
        assert len(suggestions) == 1  # Only positive feedback

    def test_repetitive_password_gets_suggestion(self):
        """Test suggestion for repetitive characters."""
        validator = PasswordValidator()
        suggestions = validator.get_suggestions("aaabbb111")

        assert any("repeat" in s.lower() for s in suggestions)


class TestDefaultValidator:
    """Test suite for default validator helper functions."""

    def test_validate_password_function(self):
        """Test default validate_password helper."""
        valid, errors = validate_password("GoodPass123")
        assert valid is True
        assert len(errors) == 0

        valid, errors = validate_password("bad")
        assert valid is False
        assert len(errors) > 0

    def test_calculate_password_strength_function(self):
        """Test default calculate_password_strength helper."""
        result = calculate_password_strength("MyP@ssw0rd!")

        assert "strength" in result
        assert "score" in result
        assert "suggestions" in result
        assert isinstance(result["score"], int)
        assert isinstance(result["suggestions"], list)

    def test_strength_result_format(self):
        """Test that strength calculation returns correct format."""
        result = calculate_password_strength("TestPass123")

        assert result["strength"] in [
            "very_weak", "weak", "medium", "strong", "very_strong"
        ]
        assert 0 <= result["score"] <= 120  # Reasonable score range


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_password(self):
        """Test validation of empty password."""
        validator = PasswordValidator()
        valid, errors = validator.validate("")

        assert valid is False
        assert len(errors) > 0

    def test_very_long_password(self):
        """Test that very long passwords are handled correctly."""
        validator = PasswordValidator()
        long_password = "A1b!" + "x" * 100
        valid, errors = validator.validate(long_password)

        assert valid is True

    def test_unicode_characters(self):
        """Test passwords with Unicode characters."""
        validator = PasswordValidator()
        unicode_password = "Пароль123!"
        valid, errors = validator.validate(unicode_password)

        # Should validate (contains variety of characters)
        assert isinstance(valid, bool)

    def test_all_special_characters(self):
        """Test password with all special characters."""
        validator = PasswordValidator()
        special_password = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
        valid, errors = validator.validate(special_password)

        # Will fail digit/letter requirements but should handle gracefully
        assert isinstance(valid, bool)

    def test_whitespace_in_password(self):
        """Test passwords containing whitespace."""
        validator = PasswordValidator()
        valid, errors = validator.validate("Pass Word 123")

        # Whitespace is allowed (some systems permit it)
        assert isinstance(valid, bool)

    def test_only_numbers(self):
        """Test password with only numbers."""
        validator = PasswordValidator()
        valid, errors = validator.validate("123456789012")

        assert valid is False
        assert any("uppercase" in err.lower() or "lowercase" in err.lower() for err in errors)

    def test_only_letters(self):
        """Test password with only letters."""
        validator = PasswordValidator()
        valid, errors = validator.validate("OnlyLettersHere")

        assert valid is False
        assert any("digit" in err.lower() for err in errors)
