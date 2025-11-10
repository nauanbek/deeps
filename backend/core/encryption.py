"""
Credential encryption utilities using Fernet (AES 128 CBC).

Provides encryption/decryption for sensitive data like database passwords,
API keys, and access tokens stored in external_tool_configs.

Security Features:
- Fernet symmetric encryption (AES 128 in CBC mode with HMAC)
- Key management via environment variable
- Safe error handling (no credential exposure in exceptions)
"""

import os
from typing import Any, Dict

from cryptography.fernet import Fernet, InvalidToken
from loguru import logger


class CredentialEncryption:
    """
    Handles encryption and decryption of credentials using Fernet.

    The encryption key must be provided via CREDENTIAL_ENCRYPTION_KEY
    environment variable.

    Usage:
        encryptor = CredentialEncryption()
        encrypted = encryptor.encrypt("my-secret-password")
        decrypted = encryptor.decrypt(encrypted)  # "my-secret-password"
    """

    def __init__(self):
        """
        Initialize the encryptor with the encryption key from environment.

        Raises:
            ValueError: If CREDENTIAL_ENCRYPTION_KEY is not set
        """
        key = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
        if not key:
            raise ValueError(
                "CREDENTIAL_ENCRYPTION_KEY environment variable not set. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

        try:
            self.fernet = Fernet(key.encode())
        except Exception as e:
            raise ValueError(
                f"Invalid CREDENTIAL_ENCRYPTION_KEY format. Must be a valid Fernet key. Error: {e}"
            )

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt

        Returns:
            Encrypted string (base64 encoded)

        Raises:
            ValueError: If encryption fails
        """
        if not plaintext:
            return ""

        try:
            encrypted_bytes = self.fernet.encrypt(plaintext.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {type(e).__name__}")
            raise ValueError("Failed to encrypt credential")

    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            encrypted: The encrypted string (base64 encoded)

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If decryption fails (invalid key or corrupted data)
        """
        if not encrypted:
            return ""

        try:
            decrypted_bytes = self.fernet.decrypt(encrypted.encode())
            return decrypted_bytes.decode()
        except InvalidToken:
            logger.error("Decryption failed: Invalid token or wrong encryption key")
            raise ValueError("Failed to decrypt credential (invalid token or key)")
        except Exception as e:
            logger.error(f"Decryption failed: {type(e).__name__}")
            raise ValueError("Failed to decrypt credential")

    def encrypt_dict_fields(
        self, data: Dict[str, Any], fields_to_encrypt: list[str]
    ) -> Dict[str, Any]:
        """
        Encrypt specific fields in a dictionary.

        Useful for encrypting only sensitive fields in configuration objects.

        Args:
            data: Dictionary containing configuration data
            fields_to_encrypt: List of field names to encrypt

        Returns:
            New dictionary with encrypted fields

        Example:
            config = {"host": "localhost", "password": "secret123"}
            encrypted_config = encryptor.encrypt_dict_fields(config, ["password"])
            # Returns: {"host": "localhost", "password": "***ENCRYPTED***"}
        """
        encrypted_data = data.copy()

        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field]:
                try:
                    encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
                except Exception as e:
                    logger.error(f"Failed to encrypt field '{field}': {e}")
                    # Continue with other fields, don't fail entire operation
                    encrypted_data[field] = "***ENCRYPTION_FAILED***"

        return encrypted_data

    def decrypt_dict_fields(
        self, data: Dict[str, Any], fields_to_decrypt: list[str]
    ) -> Dict[str, Any]:
        """
        Decrypt specific fields in a dictionary.

        Args:
            data: Dictionary containing encrypted configuration data
            fields_to_decrypt: List of field names to decrypt

        Returns:
            New dictionary with decrypted fields

        Raises:
            ValueError: If decryption fails for any field
        """
        decrypted_data = data.copy()

        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field]:
                # Skip if already decrypted or special markers
                if decrypted_data[field] in ["***ENCRYPTED***", "***ENCRYPTION_FAILED***"]:
                    continue

                try:
                    decrypted_data[field] = self.decrypt(str(decrypted_data[field]))
                except Exception as e:
                    logger.error(f"Failed to decrypt field '{field}'")
                    raise ValueError(f"Failed to decrypt field '{field}'")

        return decrypted_data


class CredentialSanitizer:
    """
    Sanitizes sensitive data from logs, error messages, and API responses.

    Prevents credential exposure in logs and error messages by replacing
    sensitive values with safe placeholders.
    """

    # Fields that should always be sanitized
    SENSITIVE_FIELDS = [
        "password",
        "api_key",
        "access_token",
        "secret",
        "token",
        "key",
        "credential",
        "bearer_token",
        "auth_token",
        "private_key",
        "encryption_key",
    ]

    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize sensitive fields in a dictionary for safe logging.

        Args:
            data: Dictionary that may contain sensitive data

        Returns:
            New dictionary with sensitive fields replaced by '***SANITIZED***'

        Example:
            config = {"host": "localhost", "password": "secret123", "port": 5432}
            sanitized = CredentialSanitizer.sanitize_dict(config)
            # Returns: {"host": "localhost", "password": "***SANITIZED***", "port": 5432}
        """
        sanitized = {}

        for key, value in data.items():
            # Check if key contains sensitive field name
            if any(sensitive in key.lower() for sensitive in cls.SENSITIVE_FIELDS):
                sanitized[key] = "***SANITIZED***"
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                # Sanitize lists of dictionaries
                sanitized[key] = [
                    cls.sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    @classmethod
    def sanitize_string(cls, text: str) -> str:
        """
        Sanitize potentially sensitive strings for logging.

        Detects patterns that look like credentials (e.g., long random strings)
        and replaces them with safe placeholders.

        Args:
            text: String that may contain sensitive data

        Returns:
            Sanitized string with credentials replaced

        Example:
            message = "Connection failed for user@localhost with password='abc123xyz'"
            sanitized = CredentialSanitizer.sanitize_string(message)
            # Returns: "Connection failed for user@localhost with password='***SANITIZED***'"
        """
        import re

        # Pattern for password='..' or password="..."
        text = re.sub(
            r"(password|token|key|secret)\s*=\s*['\"]([^'\"]+)['\"]",
            r"\1='***SANITIZED***'",
            text,
            flags=re.IGNORECASE,
        )

        # Pattern for Bearer tokens
        text = re.sub(
            r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
            "Bearer ***SANITIZED***",
            text,
        )

        # Pattern for API keys (often look like: sk-..., glpat-..., etc.)
        text = re.sub(
            r"\b(sk-|glpat-|ghp_|gho_)[A-Za-z0-9_-]{20,}\b",
            "***SANITIZED***",
            text,
        )

        return text


# Global encryptor instance (lazy initialization)
_encryptor: CredentialEncryption | None = None


def get_encryptor() -> CredentialEncryption:
    """
    Get the global CredentialEncryption instance.

    Lazily initializes the encryptor on first use.

    Returns:
        CredentialEncryption instance

    Raises:
        ValueError: If CREDENTIAL_ENCRYPTION_KEY is not set
    """
    global _encryptor
    if _encryptor is None:
        _encryptor = CredentialEncryption()
    return _encryptor
