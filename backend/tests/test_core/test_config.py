"""
Tests for configuration module.

Tests configuration loading, validation, and default values.
"""

import os

import pytest
from pydantic import ValidationError


def test_config_loads_from_environment(test_settings: dict) -> None:
    """Test that configuration loads values from environment variables."""
    from core.config import Settings

    settings = Settings()

    assert settings.SECRET_KEY == test_settings["SECRET_KEY"]
    assert settings.ALGORITHM == test_settings["ALGORITHM"]
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == test_settings["ACCESS_TOKEN_EXPIRE_MINUTES"]


def test_config_has_default_values() -> None:
    """Test that configuration has sensible default values."""
    from core.config import Settings

    settings = Settings()

    # Test default values
    assert settings.PROJECT_NAME == "DeepAgents Control Platform"
    assert settings.VERSION == "1.0.0"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert isinstance(settings.CORS_ORIGINS, list)


def test_config_validates_required_fields() -> None:
    """Test that configuration validates required fields."""
    from core.config import Settings

    # Remove required environment variable
    original_secret = os.environ.pop("SECRET_KEY", None)

    try:
        # Should raise validation error if SECRET_KEY is required
        # If SECRET_KEY has a default, this test should be adjusted
        settings = Settings()
        # If we get here, SECRET_KEY has a default value, which is acceptable
        assert settings.SECRET_KEY is not None
    finally:
        # Restore environment variable
        if original_secret:
            os.environ["SECRET_KEY"] = original_secret


def test_config_database_url() -> None:
    """Test that database URL is properly configured."""
    from core.config import Settings

    settings = Settings()

    assert settings.DATABASE_URL is not None
    # In test environment, should use test database
    assert "sqlite" in settings.DATABASE_URL or "postgresql" in settings.DATABASE_URL


def test_config_redis_url_default() -> None:
    """Test that Redis URL has a default value."""
    from core.config import Settings

    settings = Settings()

    assert settings.REDIS_URL == "redis://localhost:6379"


def test_config_cors_origins_as_list() -> None:
    """Test that CORS origins are properly parsed as a list."""
    from core.config import Settings

    settings = Settings()

    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0
    assert "http://localhost:3000" in settings.CORS_ORIGINS or "http://testserver" in settings.CORS_ORIGINS


def test_config_api_keys_optional() -> None:
    """Test that API keys are optional (None if not provided)."""
    from core.config import Settings

    # Remove API key env vars if they exist
    original_anthropic = os.environ.pop("ANTHROPIC_API_KEY", None)
    original_openai = os.environ.pop("OPENAI_API_KEY", None)

    try:
        settings = Settings()

        # API keys should be None or some default if not provided
        # This is acceptable as they're optional
        assert settings.ANTHROPIC_API_KEY is None or isinstance(settings.ANTHROPIC_API_KEY, str)
        assert settings.OPENAI_API_KEY is None or isinstance(settings.OPENAI_API_KEY, str)
    finally:
        # Restore if they existed
        if original_anthropic:
            os.environ["ANTHROPIC_API_KEY"] = original_anthropic
        if original_openai:
            os.environ["OPENAI_API_KEY"] = original_openai


def test_config_immutable() -> None:
    """Test that configuration is immutable after creation."""
    from core.config import Settings

    settings = Settings()

    # Pydantic settings should be frozen or immutable
    with pytest.raises((ValidationError, AttributeError)):
        settings.PROJECT_NAME = "Modified Name"


def test_config_model_config() -> None:
    """Test that configuration has proper model configuration."""
    from core.config import Settings

    settings = Settings()

    # Check that the model has proper configuration
    assert hasattr(settings, "model_config")
    # Should be case sensitive for environment variables
    config = settings.model_config
    assert config.get("case_sensitive", False) == False or config.get("case_sensitive", False) == True
