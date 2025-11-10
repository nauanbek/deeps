"""
Base class for LangChain tool wrappers.

Provides common functionality for all external tool integrations:
- Configuration validation
- Credential encryption/decryption
- Connection testing
- Tool instantiation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from langchain_core.tools import BaseTool
from loguru import logger

from core.encryption import get_encryptor


class BaseLangChainTool(ABC):
    """
    Abstract base class for LangChain tool wrappers.

    All tool wrappers (PostgreSQL, GitLab, Elasticsearch, HTTP)
    must inherit from this class and implement the required methods.

    Attributes:
        tool_type: Type identifier (e.g., "postgresql", "gitlab")
        config: Tool configuration dictionary (with encrypted credentials)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the tool wrapper with configuration.

        Args:
            config: Tool configuration dictionary
                    (credentials should be encrypted)
        """
        self.config = config
        self.tool_type = self.get_tool_type()
        self.encryptor = get_encryptor()

    @abstractmethod
    def get_tool_type(self) -> str:
        """
        Get the tool type identifier.

        Returns:
            Tool type string (e.g., "postgresql", "gitlab")
        """
        pass

    @abstractmethod
    def get_encrypted_fields(self) -> List[str]:
        """
        Get list of configuration fields that should be encrypted.

        Returns:
            List of field names that contain sensitive data

        Example:
            ["password", "api_key", "access_token"]
        """
        pass

    @abstractmethod
    async def validate_config(self) -> None:
        """
        Validate the tool configuration.

        Raises:
            ValueError: If configuration is invalid or missing required fields
        """
        pass

    @abstractmethod
    async def create_tools(self) -> List[BaseTool]:
        """
        Create LangChain tools from configuration.

        This is the main method that instantiates LangChain tools
        based on the decrypted configuration.

        Returns:
            List of LangChain BaseTool instances

        Raises:
            ValueError: If tool creation fails
        """
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the external service.

        Returns:
            Dictionary with test results:
            {
                "success": bool,
                "message": str,
                "details": dict (optional)
            }
        """
        pass

    def decrypt_config(self) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in the configuration.

        Returns:
            Configuration dictionary with decrypted credentials
        """
        try:
            encrypted_fields = self.get_encrypted_fields()
            decrypted_config = self.encryptor.decrypt_dict_fields(
                self.config, encrypted_fields
            )
            return decrypted_config
        except Exception as e:
            logger.error(f"Failed to decrypt config for {self.tool_type}: {e}")
            raise ValueError(f"Failed to decrypt credentials: {e}")

    def get_required_fields(self) -> List[str]:
        """
        Get list of required configuration fields.

        Override this method to specify required fields for validation.

        Returns:
            List of required field names
        """
        return []

    def validate_required_fields(self) -> None:
        """
        Validate that all required fields are present in config.

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = self.get_required_fields()
        missing_fields = [
            field for field in required_fields if field not in self.config
        ]

        if missing_fields:
            raise ValueError(
                f"Missing required fields for {self.tool_type}: {', '.join(missing_fields)}"
            )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(tool_type='{self.tool_type}')>"
