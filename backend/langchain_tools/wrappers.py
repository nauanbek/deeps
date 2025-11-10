"""
Tool wrappers for security and performance enhancements.

Provides decorators that wrap LangChain tools to add:
- Timeout enforcement
- Row/result limiting
- Domain whitelisting
- Rate limiting
"""

import asyncio
import signal
from functools import wraps
from typing import Any, Callable, List

from langchain_core.tools import BaseTool
from loguru import logger


class TimeoutWrapper(BaseTool):
    """
    Wraps a tool to enforce execution timeout.

    If the tool execution exceeds the timeout, it raises a TimeoutError.

    Args:
        tool: Original LangChain tool
        timeout_seconds: Maximum execution time in seconds
    """

    def __init__(self, tool: BaseTool, timeout_seconds: int = 30):
        self.wrapped_tool = tool
        self.timeout_seconds = timeout_seconds

        # Copy metadata from original tool
        super().__init__(
            name=tool.name,
            description=f"{tool.description} (timeout: {timeout_seconds}s)",
            args_schema=tool.args_schema if hasattr(tool, 'args_schema') else None,
        )

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the tool with timeout enforcement.

        Raises:
            TimeoutError: If execution exceeds timeout
        """
        def timeout_handler(signum, frame):
            raise TimeoutError(
                f"Tool '{self.wrapped_tool.name}' execution exceeded {self.timeout_seconds}s timeout"
            )

        # Set up timeout (Unix-based systems)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout_seconds)

            try:
                result = self.wrapped_tool._run(*args, **kwargs)
                return result
            finally:
                # Cancel alarm
                signal.alarm(0)

        except AttributeError:
            # SIGALRM not available (Windows)
            # Fall back to threading-based timeout
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.wrapped_tool._run, *args, **kwargs)
                try:
                    result = future.result(timeout=self.timeout_seconds)
                    return result
                except concurrent.futures.TimeoutError:
                    raise TimeoutError(
                        f"Tool '{self.wrapped_tool.name}' execution exceeded {self.timeout_seconds}s timeout"
                    )

    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the tool asynchronously with timeout.

        Raises:
            TimeoutError: If execution exceeds timeout
        """
        try:
            result = await asyncio.wait_for(
                self.wrapped_tool._arun(*args, **kwargs),
                timeout=self.timeout_seconds
            )
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Tool '{self.wrapped_tool.name}' execution exceeded {self.timeout_seconds}s timeout"
            )


class RowLimitWrapper(BaseTool):
    """
    Wraps a database query tool to limit the number of returned rows.

    Useful for preventing large result sets that could consume excessive
    memory or bandwidth.

    Args:
        tool: Original LangChain tool
        max_rows: Maximum number of rows to return
    """

    def __init__(self, tool: BaseTool, max_rows: int = 1000):
        self.wrapped_tool = tool
        self.max_rows = max_rows

        # Copy metadata from original tool
        super().__init__(
            name=tool.name,
            description=f"{tool.description} (max rows: {max_rows})",
            args_schema=tool.args_schema if hasattr(tool, 'args_schema') else None,
        )

    def _run(self, query: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute query with LIMIT clause injected.

        Args:
            query: SQL query to execute

        Returns:
            Query result with row limit applied
        """
        # Inject LIMIT clause if not present
        limited_query = self._add_limit_clause(query)

        logger.debug(f"Executing query with row limit: {limited_query}")
        result = self.wrapped_tool._run(limited_query, *args, **kwargs)

        return result

    async def _arun(self, query: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute query asynchronously with LIMIT clause.

        Args:
            query: SQL query to execute

        Returns:
            Query result with row limit applied
        """
        limited_query = self._add_limit_clause(query)
        result = await self.wrapped_tool._arun(limited_query, *args, **kwargs)
        return result

    def _add_limit_clause(self, query: str) -> str:
        """
        Add LIMIT clause to SQL query if not present.

        Args:
            query: Original SQL query

        Returns:
            Query with LIMIT clause
        """
        import re

        # Normalize query
        normalized_query = query.strip()

        # Check if LIMIT already exists
        if re.search(r"\bLIMIT\b", normalized_query, re.IGNORECASE):
            # LIMIT already present, check if it exceeds max_rows
            match = re.search(r"\bLIMIT\s+(\d+)", normalized_query, re.IGNORECASE)
            if match:
                existing_limit = int(match.group(1))
                if existing_limit > self.max_rows:
                    # Replace with max_rows
                    limited_query = re.sub(
                        r"\bLIMIT\s+\d+",
                        f"LIMIT {self.max_rows}",
                        normalized_query,
                        flags=re.IGNORECASE
                    )
                    logger.warning(
                        f"Query LIMIT {existing_limit} exceeds max {self.max_rows}, "
                        f"reducing to {self.max_rows}"
                    )
                    return limited_query
            return normalized_query
        else:
            # Add LIMIT clause
            # Handle queries with/without semicolon
            if normalized_query.endswith(";"):
                limited_query = f"{normalized_query[:-1]} LIMIT {self.max_rows};"
            else:
                limited_query = f"{normalized_query} LIMIT {self.max_rows}"

            return limited_query


class DomainWhitelistWrapper(BaseTool):
    """
    Wraps an HTTP client tool to enforce domain whitelisting.

    Only allows requests to whitelisted domains.

    Args:
        tool: Original LangChain HTTP tool
        allowed_domains: List of allowed domain names
    """

    def __init__(self, tool: BaseTool, allowed_domains: List[str]):
        self.wrapped_tool = tool
        self.allowed_domains = [domain.lower() for domain in allowed_domains]

        # Copy metadata from original tool
        super().__init__(
            name=tool.name,
            description=f"{tool.description} (allowed domains: {', '.join(allowed_domains)})",
            args_schema=tool.args_schema if hasattr(tool, 'args_schema') else None,
        )

    def _run(self, url: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute HTTP request with domain validation.

        Args:
            url: URL to request

        Returns:
            HTTP response

        Raises:
            ValueError: If domain is not whitelisted
        """
        self._validate_domain(url)
        return self.wrapped_tool._run(url, *args, **kwargs)

    async def _arun(self, url: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute HTTP request asynchronously with domain validation.

        Args:
            url: URL to request

        Returns:
            HTTP response

        Raises:
            ValueError: If domain is not whitelisted
        """
        self._validate_domain(url)
        return await self.wrapped_tool._arun(url, *args, **kwargs)

    def _validate_domain(self, url: str) -> None:
        """
        Validate that URL domain is whitelisted.

        Args:
            url: URL to validate

        Raises:
            ValueError: If domain is not whitelisted
        """
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove port if present
            if ":" in domain:
                domain = domain.split(":")[0]

            # Check if domain is whitelisted
            if domain not in self.allowed_domains:
                # Check for subdomain match (e.g., api.example.com matches example.com)
                is_allowed = any(
                    domain.endswith(f".{allowed_domain}")
                    for allowed_domain in self.allowed_domains
                )

                if not is_allowed:
                    raise ValueError(
                        f"Domain '{domain}' is not whitelisted. "
                        f"Allowed domains: {', '.join(self.allowed_domains)}"
                    )

        except Exception as e:
            logger.error(f"Domain validation failed for URL '{url}': {e}")
            raise ValueError(f"Invalid URL or domain not whitelisted: {e}")
