"""
HTTP Client tool wrapper for LangChain.

Provides HTTP API requests with:
- Domain whitelisting
- Bearer token authentication
- GET/POST support
- Request timeout (30 seconds)
- Response size limit (10MB)
"""

from typing import Any, Dict, List, Optional

import requests
from langchain_core.tools import BaseTool, tool
from loguru import logger

from .base import BaseLangChainTool
from .wrappers import DomainWhitelistWrapper


class HTTPClientTool(BaseLangChainTool):
    """
    HTTP Client tool wrapper.

    Configuration schema:
    {
        "base_url": str,                # Base URL for API (optional)
        "auth_type": str,               # Authentication type: none, bearer, api_key
        "bearer_token": str,            # Bearer token (encrypted, if auth_type=bearer)
        "api_key": str,                 # API key (encrypted, if auth_type=api_key)
        "api_key_header": str,          # Header name for API key (default: X-API-Key)
        "allowed_domains": List[str],   # Whitelisted domains
        "timeout": int,                 # Request timeout in seconds (default: 30)
        "max_response_size": int,       # Max response size in bytes (default: 10MB)
        "custom_headers": Dict[str, str],  # Custom headers to include in requests
    }
    """

    def get_tool_type(self) -> str:
        """
        Get the tool type identifier.

        Returns:
            str: Tool type "http"
        """
        return "http"

    def get_encrypted_fields(self) -> List[str]:
        """
        Get list of fields that should be encrypted in storage.

        Bearer tokens and API keys are automatically encrypted using
        Fernet encryption before being stored in the database.

        Returns:
            List[str]: Field names requiring encryption (["bearer_token", "api_key"])
        """
        return ["bearer_token", "api_key"]

    def get_required_fields(self) -> List[str]:
        """
        Get list of required configuration fields.

        These fields must be present in the configuration dict
        for the tool to function properly. Validation will fail
        if any required field is missing.

        Returns:
            List[str]: Required field names for HTTP client configuration
        """
        return ["allowed_domains"]

    async def validate_config(self) -> None:
        """Validate HTTP client configuration."""
        self.validate_required_fields()

        # Validate allowed_domains
        allowed_domains = self.config.get("allowed_domains", [])
        if not isinstance(allowed_domains, list) or len(allowed_domains) == 0:
            raise ValueError("allowed_domains must be a non-empty list")

        # Validate auth_type
        auth_type = self.config.get("auth_type", "none")
        valid_auth_types = ["none", "bearer", "api_key"]
        if auth_type not in valid_auth_types:
            raise ValueError(
                f"Invalid auth_type: {auth_type}. Must be one of: {', '.join(valid_auth_types)}"
            )

        # Validate auth credentials based on type
        if auth_type == "bearer" and "bearer_token" not in self.config:
            raise ValueError("bearer_token required when auth_type=bearer")

        if auth_type == "api_key" and "api_key" not in self.config:
            raise ValueError("api_key required when auth_type=api_key")

        # Validate timeout
        timeout = self.config.get("timeout", 30)
        if not isinstance(timeout, int) or timeout < 1 or timeout > 120:
            raise ValueError(f"Invalid timeout: {timeout}. Must be between 1 and 120")

        # Validate max_response_size
        max_size = self.config.get("max_response_size", 10 * 1024 * 1024)  # 10MB
        if not isinstance(max_size, int) or max_size < 1024 or max_size > 100 * 1024 * 1024:
            raise ValueError(
                f"Invalid max_response_size: {max_size}. Must be between 1KB and 100MB"
            )

    async def create_tools(self) -> List[BaseTool]:
        """
        Create HTTP client tools.

        Returns:
            List of tools: http_get, http_post
        """
        await self.validate_config()
        decrypted_config = self.decrypt_config()

        # Create tools
        tools = [
            self._create_get_tool(decrypted_config),
            self._create_post_tool(decrypted_config),
        ]

        # Wrap with domain whitelist
        allowed_domains = self.config.get("allowed_domains", [])
        wrapped_tools = [
            DomainWhitelistWrapper(tool, allowed_domains) for tool in tools
        ]

        logger.info(f"Created {len(wrapped_tools)} HTTP client tools")
        return wrapped_tools

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test HTTP connection to base_url or first allowed domain.

        Returns:
            Test result dictionary with success status and details
        """
        try:
            await self.validate_config()
            decrypted_config = self.decrypt_config()

            # Determine test URL
            base_url = decrypted_config.get("base_url")
            if base_url:
                test_url = base_url
            else:
                # Use first allowed domain
                allowed_domains = decrypted_config["allowed_domains"]
                test_url = f"https://{allowed_domains[0]}"

            # Build headers
            headers = self._build_headers(decrypted_config)

            # Send test GET request
            timeout = decrypted_config.get("timeout", 30)
            response = requests.get(
                test_url,
                headers=headers,
                timeout=min(timeout, 10),  # Max 10s for test
                allow_redirects=True,
            )

            return {
                "success": True,
                "message": "Connection successful",
                "details": {
                    "url": test_url,
                    "status_code": response.status_code,
                    "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                }
            }

        except requests.RequestException as e:
            logger.error(f"HTTP connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
            }
        except Exception as e:
            logger.error(f"HTTP test failed: {e}")
            return {
                "success": False,
                "message": f"Test failed: {str(e)}",
            }

    def _build_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Build HTTP headers from configuration.

        Args:
            config: Decrypted configuration

        Returns:
            Headers dictionary
        """
        headers = {}

        # Add authentication headers
        auth_type = config.get("auth_type", "none")

        if auth_type == "bearer":
            bearer_token = config.get("bearer_token", "")
            headers["Authorization"] = f"Bearer {bearer_token}"

        elif auth_type == "api_key":
            api_key = config.get("api_key", "")
            api_key_header = config.get("api_key_header", "X-API-Key")
            headers[api_key_header] = api_key

        # Add custom headers
        custom_headers = config.get("custom_headers", {})
        if isinstance(custom_headers, dict):
            headers.update(custom_headers)

        # Add user agent
        headers.setdefault("User-Agent", "DeepAgents-Platform/1.0")

        return headers

    def _create_get_tool(self, config: Dict[str, Any]) -> BaseTool:
        """
        Create http_get tool.

        Args:
            config: Decrypted configuration

        Returns:
            LangChain tool for GET requests
        """
        headers = self._build_headers(config)
        timeout = config.get("timeout", 30)
        max_size = config.get("max_response_size", 10 * 1024 * 1024)

        @tool
        def http_get(
            url: str,
            params: Optional[Dict[str, str]] = None,
            additional_headers: Optional[Dict[str, str]] = None
        ) -> str:
            """
            Send HTTP GET request.

            Args:
                url: Full URL to request
                params: Query parameters (optional)
                additional_headers: Additional headers to include (optional)

            Returns:
                Response body as string

            Example:
                http_get("https://api.example.com/users", params={"limit": "10"})
            """
            try:
                # Merge headers
                request_headers = headers.copy()
                if additional_headers:
                    request_headers.update(additional_headers)

                # Send request
                response = requests.get(
                    url,
                    params=params,
                    headers=request_headers,
                    timeout=timeout,
                    stream=True,  # Stream to check content length
                )

                # Check content length
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > max_size:
                    return f"Error: Response too large ({content_length} bytes, max {max_size})"

                # Read response with size limit
                content = b""
                for chunk in response.iter_content(chunk_size=8192):
                    content += chunk
                    if len(content) > max_size:
                        return f"Error: Response exceeds size limit ({max_size} bytes)"

                response.raise_for_status()

                # Return response
                result = [
                    f"Status: {response.status_code}",
                    f"Response:\n{content.decode('utf-8', errors='replace')}"
                ]

                return "\n".join(result)

            except requests.RequestException as e:
                logger.error(f"HTTP GET failed: {e}")
                return f"Request failed: {str(e)}"

        return http_get

    def _create_post_tool(self, config: Dict[str, Any]) -> BaseTool:
        """
        Create http_post tool.

        Args:
            config: Decrypted configuration

        Returns:
            LangChain tool for POST requests
        """
        headers = self._build_headers(config)
        timeout = config.get("timeout", 30)
        max_size = config.get("max_response_size", 10 * 1024 * 1024)

        @tool
        def http_post(
            url: str,
            json_body: Optional[Dict[str, Any]] = None,
            form_data: Optional[Dict[str, str]] = None,
            additional_headers: Optional[Dict[str, str]] = None
        ) -> str:
            """
            Send HTTP POST request.

            Args:
                url: Full URL to request
                json_body: JSON body (optional, mutually exclusive with form_data)
                form_data: Form data (optional, mutually exclusive with json_body)
                additional_headers: Additional headers to include (optional)

            Returns:
                Response body as string

            Example:
                http_post(
                    "https://api.example.com/users",
                    json_body={"name": "Alice", "email": "alice@example.com"}
                )
            """
            try:
                # Validate input
                if json_body and form_data:
                    return "Error: Cannot specify both json_body and form_data"

                # Merge headers
                request_headers = headers.copy()
                if additional_headers:
                    request_headers.update(additional_headers)

                # Send request
                if json_body:
                    request_headers.setdefault("Content-Type", "application/json")
                    response = requests.post(
                        url,
                        json=json_body,
                        headers=request_headers,
                        timeout=timeout,
                        stream=True,
                    )
                elif form_data:
                    request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
                    response = requests.post(
                        url,
                        data=form_data,
                        headers=request_headers,
                        timeout=timeout,
                        stream=True,
                    )
                else:
                    # Empty body
                    response = requests.post(
                        url,
                        headers=request_headers,
                        timeout=timeout,
                        stream=True,
                    )

                # Check content length
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > max_size:
                    return f"Error: Response too large ({content_length} bytes, max {max_size})"

                # Read response with size limit
                content = b""
                for chunk in response.iter_content(chunk_size=8192):
                    content += chunk
                    if len(content) > max_size:
                        return f"Error: Response exceeds size limit ({max_size} bytes)"

                response.raise_for_status()

                # Return response
                result = [
                    f"Status: {response.status_code}",
                    f"Response:\n{content.decode('utf-8', errors='replace')}"
                ]

                return "\n".join(result)

            except requests.RequestException as e:
                logger.error(f"HTTP POST failed: {e}")
                return f"Request failed: {str(e)}"

        return http_post
