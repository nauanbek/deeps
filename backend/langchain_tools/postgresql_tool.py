"""
PostgreSQL tool wrapper for LangChain.

Provides safe database query access with:
- Read-only enforcement (SELECT, EXPLAIN only)
- Query timeout (30 seconds)
- Row limit (1000 rows)
- Connection pooling
"""

import asyncio
import re
from typing import Any, Dict, List

from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.tools import BaseTool
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool, QueuePool

from .base import BaseLangChainTool
from .wrappers import RowLimitWrapper, TimeoutWrapper


class PostgreSQLTool(BaseLangChainTool):
    """
    PostgreSQL database tool wrapper.

    Configuration schema:
    {
        "host": str,              # Database host
        "port": int,              # Database port (default: 5432)
        "database": str,          # Database name
        "username": str,          # Database username
        "password": str,          # Database password (encrypted)
        "ssl_mode": str,          # SSL mode: disable, require, verify-full (default: require)
        "pool_size": int,         # Connection pool size (default: 5, max: 20)
        "timeout": int,           # Query timeout in seconds (default: 30, max: 60)
        "row_limit": int,         # Max rows per query (default: 1000, max: 10000)
        "read_only": bool,        # Enforce read-only (default: true)
    }
    """

    # SQL keywords that indicate write operations
    WRITE_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
        "TRUNCATE", "GRANT", "REVOKE", "COMMIT", "ROLLBACK"
    ]

    def get_tool_type(self) -> str:
        """
        Get the tool type identifier.

        Returns:
            str: Tool type "postgresql"
        """
        return "postgresql"

    def get_encrypted_fields(self) -> List[str]:
        """
        Get list of fields that should be encrypted in storage.

        Password credentials are automatically encrypted using Fernet
        encryption before being stored in the database.

        Returns:
            List[str]: Field names requiring encryption (["password"])
        """
        return ["password"]

    def get_required_fields(self) -> List[str]:
        """
        Get list of required configuration fields.

        These fields must be present in the configuration dict
        for the tool to function properly. Validation will fail
        if any required field is missing.

        Returns:
            List[str]: Required field names for PostgreSQL connection
        """
        return ["host", "database", "username", "password"]

    async def validate_config(self) -> None:
        """Validate PostgreSQL configuration."""
        self.validate_required_fields()

        # Validate port
        port = self.config.get("port", 5432)
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError(f"Invalid port: {port}. Must be between 1 and 65535")

        # Validate pool_size
        pool_size = self.config.get("pool_size", 5)
        if not isinstance(pool_size, int) or pool_size < 1 or pool_size > 20:
            raise ValueError(f"Invalid pool_size: {pool_size}. Must be between 1 and 20")

        # Validate timeout
        timeout = self.config.get("timeout", 30)
        if not isinstance(timeout, int) or timeout < 1 or timeout > 60:
            raise ValueError(f"Invalid timeout: {timeout}. Must be between 1 and 60")

        # Validate row_limit
        row_limit = self.config.get("row_limit", 1000)
        if not isinstance(row_limit, int) or row_limit < 1 or row_limit > 10000:
            raise ValueError(f"Invalid row_limit: {row_limit}. Must be between 1 and 10000")

        # Validate SSL mode
        ssl_mode = self.config.get("ssl_mode", "require")
        valid_ssl_modes = ["disable", "require", "verify-ca", "verify-full"]
        if ssl_mode not in valid_ssl_modes:
            raise ValueError(
                f"Invalid ssl_mode: {ssl_mode}. Must be one of: {', '.join(valid_ssl_modes)}"
            )

    async def create_tools(self) -> List[BaseTool]:
        """
        Create PostgreSQL tools using SQLDatabaseToolkit.

        Returns:
            List of tools: sql_db_query, sql_db_schema, sql_db_list_tables
        """
        await self.validate_config()
        decrypted_config = self.decrypt_config()

        # Build connection URL
        connection_url = self._build_connection_url(decrypted_config)

        # Create SQLAlchemy engine with connection pooling
        pool_size = self.config.get("pool_size", 5)
        engine = create_engine(
            connection_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections every hour
            echo=False,
        )

        # Create SQLDatabase wrapper
        try:
            db = SQLDatabase(engine)
        except Exception as e:
            logger.error(f"Failed to create SQLDatabase: {e}")
            raise ValueError(f"Failed to connect to database: {e}")

        # Create toolkit
        toolkit = SQLDatabaseToolkit(db=db, llm=None)  # No LLM needed for tools
        tools = toolkit.get_tools()

        # Apply wrappers to query tool
        wrapped_tools = []
        timeout = self.config.get("timeout", 30)
        row_limit = self.config.get("row_limit", 1000)
        read_only = self.config.get("read_only", True)

        for tool in tools:
            # Apply wrappers to sql_db_query tool only
            if tool.name == "sql_db_query":
                # Wrap with timeout
                tool = TimeoutWrapper(tool, timeout_seconds=timeout)

                # Wrap with row limit
                tool = RowLimitWrapper(tool, max_rows=row_limit)

                # Apply read-only validation
                if read_only:
                    tool = self._wrap_with_read_only_check(tool)

            wrapped_tools.append(tool)

        logger.info(f"Created {len(wrapped_tools)} PostgreSQL tools")
        return wrapped_tools

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test PostgreSQL connection.

        Returns:
            Test result dictionary with success status and details
        """
        try:
            await self.validate_config()
            decrypted_config = self.decrypt_config()
            connection_url = self._build_connection_url(decrypted_config)

            # Create test engine (no pooling for test)
            engine = create_engine(
                connection_url,
                poolclass=NullPool,
                connect_args={"connect_timeout": 5},
            )

            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()

                if row and row[0] == 1:
                    # Get database version
                    version_result = conn.execute(text("SELECT version()"))
                    version = version_result.fetchone()[0]

                    return {
                        "success": True,
                        "message": "Connection successful",
                        "details": {
                            "host": self.config["host"],
                            "database": self.config["database"],
                            "version": version,
                        }
                    }
                else:
                    return {
                        "success": False,
                        "message": "Connection test query failed",
                    }

        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
            }

    def _build_connection_url(self, config: Dict[str, Any]) -> str:
        """
        Build PostgreSQL connection URL from configuration.

        Args:
            config: Decrypted configuration dictionary

        Returns:
            SQLAlchemy connection URL string
        """
        host = config["host"]
        port = config.get("port", 5432)
        database = config["database"]
        username = config["username"]
        password = config["password"]
        ssl_mode = config.get("ssl_mode", "require")

        # Build base URL
        url = f"postgresql://{username}:{password}@{host}:{port}/{database}"

        # Add SSL mode
        if ssl_mode != "disable":
            url += f"?sslmode={ssl_mode}"

        return url

    def _wrap_with_read_only_check(self, tool: BaseTool) -> BaseTool:
        """
        Wrap tool with read-only SQL validation.

        Args:
            tool: Original tool

        Returns:
            Wrapped tool that validates queries are read-only
        """
        original_func = tool._run

        def read_only_func(query: str, *args, **kwargs):
            # Normalize query (remove comments, extra whitespace)
            normalized_query = self._normalize_query(query)

            # Check for write keywords
            for keyword in self.WRITE_KEYWORDS:
                if re.search(rf"\b{keyword}\b", normalized_query, re.IGNORECASE):
                    raise ValueError(
                        f"Write operations are not allowed. Detected keyword: {keyword}"
                    )

            # Execute original function
            return original_func(query, *args, **kwargs)

        tool._run = read_only_func
        return tool

    def _normalize_query(self, query: str) -> str:
        """
        Normalize SQL query for validation.

        Removes comments and extra whitespace.

        Args:
            query: Raw SQL query

        Returns:
            Normalized query string
        """
        # Remove single-line comments (-- ...)
        query = re.sub(r"--[^\n]*", "", query)

        # Remove multi-line comments (/* ... */)
        query = re.sub(r"/\*.*?\*/", "", query, flags=re.DOTALL)

        # Remove extra whitespace
        query = " ".join(query.split())

        return query
