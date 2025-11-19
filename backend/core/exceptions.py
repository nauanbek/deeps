"""
Custom exception classes for better error handling.

Provides domain-specific exceptions with detailed error information
for agents, tools, executions, and external integrations.
"""

from typing import Any, Optional


# ============================================================================
# Base Exception Classes
# ============================================================================


class DeepAgentsException(Exception):
    """
    Base exception for all DeepAgents platform errors.

    All custom exceptions should inherit from this class for consistent
    error handling and logging.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        """
        Initialize exception with message and optional metadata.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code (e.g., "AGENT_NOT_FOUND")
            details: Additional context for debugging
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


# ============================================================================
# Resource Not Found Exceptions
# ============================================================================


class ResourceNotFoundException(DeepAgentsException):
    """Base exception for resource not found errors."""

    def __init__(self, resource_type: str, resource_id: Any):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(
            message=message,
            error_code=f"{resource_type.upper()}_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class AgentNotFoundException(ResourceNotFoundException):
    """Agent not found in database."""

    def __init__(self, agent_id: int):
        super().__init__("Agent", agent_id)


class ToolNotFoundException(ResourceNotFoundException):
    """Tool not found in database."""

    def __init__(self, tool_id: int):
        super().__init__("Tool", tool_id)


class ExecutionNotFoundException(ResourceNotFoundException):
    """Execution not found in database."""

    def __init__(self, execution_id: int):
        super().__init__("Execution", execution_id)


class TemplateNotFoundException(ResourceNotFoundException):
    """Template not found in database."""

    def __init__(self, template_id: int):
        super().__init__("Template", template_id)


class UserNotFoundException(ResourceNotFoundException):
    """User not found in database."""

    def __init__(self, user_id: int):
        super().__init__("User", user_id)


class ExternalToolNotFoundException(ResourceNotFoundException):
    """External tool configuration not found in database."""

    def __init__(self, tool_id: int):
        super().__init__("ExternalTool", tool_id)


# ============================================================================
# Authorization Exceptions
# ============================================================================


class AuthorizationException(DeepAgentsException):
    """Base exception for authorization errors."""
    pass


class UnauthorizedAccessException(AuthorizationException):
    """User does not have permission to access resource."""

    def __init__(self, resource_type: str, resource_id: Any, user_id: int):
        message = f"User {user_id} is not authorized to access {resource_type} {resource_id}"
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED_ACCESS",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "user_id": user_id
            }
        )


class InsufficientPermissionsException(AuthorizationException):
    """User does not have required permissions."""

    def __init__(self, required_permission: str, user_id: int):
        message = f"User {user_id} lacks required permission: {required_permission}"
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_PERMISSIONS",
            details={"required_permission": required_permission, "user_id": user_id}
        )


# ============================================================================
# Validation Exceptions
# ============================================================================


class ValidationException(DeepAgentsException):
    """Base exception for validation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


class InvalidConfigurationException(ValidationException):
    """Configuration is invalid or malformed."""

    def __init__(self, config_type: str, reason: str):
        message = f"Invalid {config_type} configuration: {reason}"
        super().__init__(message)
        self.details["config_type"] = config_type
        self.details["reason"] = reason


class InvalidParameterException(ValidationException):
    """Parameter value is invalid."""

    def __init__(self, param_name: str, param_value: Any, reason: str):
        message = f"Invalid parameter '{param_name}': {reason}"
        super().__init__(message, field=param_name)
        self.details["param_value"] = str(param_value)
        self.details["reason"] = reason


# ============================================================================
# Agent Execution Exceptions
# ============================================================================


class AgentExecutionException(DeepAgentsException):
    """Base exception for agent execution errors."""
    pass


class AgentNotConfiguredException(AgentExecutionException):
    """Agent is not properly configured for execution."""

    def __init__(self, agent_id: int, missing_config: str):
        message = f"Agent {agent_id} missing required configuration: {missing_config}"
        super().__init__(
            message=message,
            error_code="AGENT_NOT_CONFIGURED",
            details={"agent_id": agent_id, "missing_config": missing_config}
        )


class AgentExecutionTimeoutException(AgentExecutionException):
    """Agent execution exceeded timeout."""

    def __init__(self, execution_id: int, timeout_seconds: int):
        message = f"Execution {execution_id} timed out after {timeout_seconds}s"
        super().__init__(
            message=message,
            error_code="EXECUTION_TIMEOUT",
            details={"execution_id": execution_id, "timeout_seconds": timeout_seconds}
        )


class AgentExecutionFailedException(AgentExecutionException):
    """Agent execution failed with error."""

    def __init__(self, execution_id: int, error_message: str):
        message = f"Execution {execution_id} failed: {error_message}"
        super().__init__(
            message=message,
            error_code="EXECUTION_FAILED",
            details={"execution_id": execution_id, "error_message": error_message}
        )


class ToolExecutionException(AgentExecutionException):
    """Tool execution failed."""

    def __init__(self, tool_name: str, error_message: str):
        message = f"Tool '{tool_name}' execution failed: {error_message}"
        super().__init__(
            message=message,
            error_code="TOOL_EXECUTION_FAILED",
            details={"tool_name": tool_name, "error_message": error_message}
        )


# ============================================================================
# External Tool Exceptions
# ============================================================================


class ExternalToolException(DeepAgentsException):
    """Base exception for external tool errors."""
    pass


class ExternalToolConnectionException(ExternalToolException):
    """Failed to connect to external tool."""

    def __init__(self, tool_type: str, tool_name: str, reason: str):
        message = f"Failed to connect to {tool_type} '{tool_name}': {reason}"
        super().__init__(
            message=message,
            error_code="EXTERNAL_TOOL_CONNECTION_FAILED",
            details={"tool_type": tool_type, "tool_name": tool_name, "reason": reason}
        )


class ExternalToolAuthenticationException(ExternalToolException):
    """Failed to authenticate with external tool."""

    def __init__(self, tool_type: str, tool_name: str):
        message = f"Authentication failed for {tool_type} '{tool_name}'"
        super().__init__(
            message=message,
            error_code="EXTERNAL_TOOL_AUTH_FAILED",
            details={"tool_type": tool_type, "tool_name": tool_name}
        )


class ExternalToolRateLimitException(ExternalToolException):
    """External tool rate limit exceeded."""

    def __init__(self, tool_type: str, retry_after: Optional[int] = None):
        message = f"Rate limit exceeded for {tool_type}"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        super().__init__(
            message=message,
            error_code="EXTERNAL_TOOL_RATE_LIMIT",
            details={"tool_type": tool_type, "retry_after": retry_after}
        )


# ============================================================================
# Database Exceptions
# ============================================================================


class DatabaseException(DeepAgentsException):
    """Base exception for database errors."""
    pass


class DatabaseConnectionException(DatabaseException):
    """Failed to connect to database."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Database connection failed: {reason}",
            error_code="DATABASE_CONNECTION_FAILED",
            details={"reason": reason}
        )


class DatabaseOperationException(DatabaseException):
    """Database operation failed."""

    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Database {operation} failed: {reason}",
            error_code="DATABASE_OPERATION_FAILED",
            details={"operation": operation, "reason": reason}
        )


# ============================================================================
# Rate Limiting Exceptions
# ============================================================================


class RateLimitExceededException(DeepAgentsException):
    """API rate limit exceeded."""

    def __init__(
        self,
        identifier: str,
        limit: int,
        window: int,
        retry_after: int
    ):
        message = f"Rate limit exceeded for {identifier}: {limit} requests per {window}s"
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details={
                "identifier": identifier,
                "limit": limit,
                "window": window,
                "retry_after": retry_after
            }
        )


# ============================================================================
# Cache Exceptions
# ============================================================================


class CacheException(DeepAgentsException):
    """Base exception for cache errors."""
    pass


class CacheConnectionException(CacheException):
    """Failed to connect to cache (Redis)."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Cache connection failed: {reason}",
            error_code="CACHE_CONNECTION_FAILED",
            details={"reason": reason}
        )


# ============================================================================
# Authentication Exceptions
# ============================================================================


class AuthenticationException(DeepAgentsException):
    """Base exception for authentication errors."""
    pass


class InvalidCredentialsException(AuthenticationException):
    """Invalid username or password."""

    def __init__(self):
        super().__init__(
            message="Invalid username or password",
            error_code="INVALID_CREDENTIALS"
        )


class InvalidTokenException(AuthenticationException):
    """JWT token is invalid or expired."""

    def __init__(self, reason: str = "Invalid or expired token"):
        super().__init__(
            message=reason,
            error_code="INVALID_TOKEN",
            details={"reason": reason}
        )


class UserInactiveException(AuthenticationException):
    """User account is inactive."""

    def __init__(self, user_id: int):
        super().__init__(
            message=f"User {user_id} account is inactive",
            error_code="USER_INACTIVE",
            details={"user_id": user_id}
        )


# ============================================================================
# Encryption Exceptions
# ============================================================================


class EncryptionException(DeepAgentsException):
    """Base exception for encryption/decryption errors."""
    pass


class EncryptionFailedException(EncryptionException):
    """Failed to encrypt data."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Encryption failed: {reason}",
            error_code="ENCRYPTION_FAILED",
            details={"reason": reason}
        )


class DecryptionFailedException(EncryptionException):
    """Failed to decrypt data."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Decryption failed: {reason}",
            error_code="DECRYPTION_FAILED",
            details={"reason": reason}
        )


# ============================================================================
# deepagents Integration Exceptions
# ============================================================================


class DeepAgentsIntegrationException(DeepAgentsException):
    """Base exception for deepagents framework integration errors."""
    pass


class AgentFactoryException(DeepAgentsIntegrationException):
    """Failed to create agent from configuration."""

    def __init__(self, agent_id: int, reason: str):
        super().__init__(
            message=f"Failed to create agent {agent_id}: {reason}",
            error_code="AGENT_FACTORY_FAILED",
            details={"agent_id": agent_id, "reason": reason}
        )


class BackendConfigurationException(DeepAgentsIntegrationException):
    """Invalid backend configuration."""

    def __init__(self, backend_type: str, reason: str):
        super().__init__(
            message=f"Invalid {backend_type} backend configuration: {reason}",
            error_code="BACKEND_CONFIG_INVALID",
            details={"backend_type": backend_type, "reason": reason}
        )
