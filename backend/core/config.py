"""
Configuration management using Pydantic Settings.

Loads configuration from environment variables with validation and type safety.
All settings can be overridden via environment variables.
"""

from typing import Any

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be configured via environment variables.
    Use .env file for local development.
    """

    # Application Metadata
    PROJECT_NAME: str = "DeepAgents Control Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///:memory:",
        description="Database connection URL (PostgreSQL for production)",
    )

    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL for caching",
    )

    # Security Configuration
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production-use-strong-random-key",
        description="Secret key for JWT token signing (MUST be changed in production)",
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm for JWT token encoding",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT token expiration time in minutes",
    )

    # CORS Configuration (stored as comma-separated string in env)
    CORS_ORIGINS_STR: str = Field(
        default="http://localhost:3000,http://testserver",
        description="Allowed CORS origins (comma-separated)",
    )

    # External API Keys (Optional)
    ANTHROPIC_API_KEY: str | None = Field(
        default=None,
        description="Anthropic API key for Claude models",
    )
    OPENAI_API_KEY: str | None = Field(
        default=None,
        description="OpenAI API key for GPT models",
    )

    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment name (development, testing, production)",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        frozen=True,  # Make settings immutable
    )

    @computed_field  # type: ignore[misc]
    @property
    def CORS_ORIGINS(self) -> list[str]:
        """
        Parse CORS origins from comma-separated string.

        Returns:
            List of CORS origin strings
        """
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]

    def __repr__(self) -> str:
        """Return string representation with masked secrets."""
        return (
            f"Settings(PROJECT_NAME='{self.PROJECT_NAME}', "
            f"VERSION='{self.VERSION}', "
            f"ENVIRONMENT='{self.ENVIRONMENT}', "
            f"DATABASE_URL='***masked***', "
            f"SECRET_KEY='***masked***')"
        )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance.

    This function allows settings to be used as a FastAPI dependency.

    Returns:
        Settings: The global settings instance
    """
    return settings
