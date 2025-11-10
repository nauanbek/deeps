"""
Elasticsearch tool wrapper for LangChain.

Provides log search and correlation with:
- Query DSL support
- Index pattern whitelisting
- Time-range filtering
- Trace correlation
- Result limiting (max 10,000 documents)
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from elasticsearch import AsyncElasticsearch, Elasticsearch
from langchain_core.tools import BaseTool, tool
from loguru import logger

from .base import BaseLangChainTool


class ElasticsearchTool(BaseLangChainTool):
    """
    Elasticsearch log search tool wrapper.

    Configuration schema:
    {
        "host": str,                    # Elasticsearch host
        "port": int,                    # Elasticsearch port (default: 9200)
        "api_key": str,                 # API key (encrypted)
        "use_ssl": bool,                # Use HTTPS (default: true)
        "verify_certs": bool,           # Verify SSL certificates (default: true)
        "index_patterns": List[str],    # Allowed index patterns (e.g., ["logs-*", "metrics-*"])
        "max_results": int,             # Max results per query (default: 1000, max: 10000)
        "timeout": int,                 # Query timeout in seconds (default: 60)
    }
    """

    def get_tool_type(self) -> str:
        """
        Get the tool type identifier.

        Returns:
            str: Tool type "elasticsearch"
        """
        return "elasticsearch"

    def get_encrypted_fields(self) -> List[str]:
        """
        Get list of fields that should be encrypted in storage.

        API keys are automatically encrypted using Fernet
        encryption before being stored in the database.

        Returns:
            List[str]: Field names requiring encryption (["api_key"])
        """
        return ["api_key"]

    def get_required_fields(self) -> List[str]:
        """
        Get list of required configuration fields.

        These fields must be present in the configuration dict
        for the tool to function properly. Validation will fail
        if any required field is missing.

        Returns:
            List[str]: Required field names for Elasticsearch connection
        """
        return ["host", "api_key", "index_patterns"]

    async def validate_config(self) -> None:
        """Validate Elasticsearch configuration."""
        self.validate_required_fields()

        # Validate port
        port = self.config.get("port", 9200)
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError(f"Invalid port: {port}. Must be between 1 and 65535")

        # Validate index_patterns
        index_patterns = self.config.get("index_patterns", [])
        if not isinstance(index_patterns, list) or len(index_patterns) == 0:
            raise ValueError("index_patterns must be a non-empty list")

        # Validate max_results
        max_results = self.config.get("max_results", 1000)
        if not isinstance(max_results, int) or max_results < 1 or max_results > 10000:
            raise ValueError(f"Invalid max_results: {max_results}. Must be between 1 and 10000")

        # Validate timeout
        timeout = self.config.get("timeout", 60)
        if not isinstance(timeout, int) or timeout < 1 or timeout > 300:
            raise ValueError(f"Invalid timeout: {timeout}. Must be between 1 and 300")

    async def create_tools(self) -> List[BaseTool]:
        """
        Create Elasticsearch tools.

        Returns:
            List of tools:
            - query_elasticsearch: Query logs with Elasticsearch DSL
            - correlate_logs: Correlate logs by trace ID or request ID
        """
        await self.validate_config()
        decrypted_config = self.decrypt_config()

        # Create tools with config closure
        tools = [
            self._create_query_tool(decrypted_config),
            self._create_correlate_tool(decrypted_config),
        ]

        logger.info(f"Created {len(tools)} Elasticsearch tools")
        return tools

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test Elasticsearch connection.

        Returns:
            Test result dictionary with success status and details
        """
        try:
            await self.validate_config()
            decrypted_config = self.decrypt_config()

            # Create Elasticsearch client
            es = self._create_client(decrypted_config)

            # Test connection with cluster health
            health = es.cluster.health()

            # Get cluster info
            info = es.info()

            return {
                "success": True,
                "message": "Connection successful",
                "details": {
                    "cluster_name": health.get("cluster_name"),
                    "status": health.get("status"),
                    "number_of_nodes": health.get("number_of_nodes"),
                    "version": info.get("version", {}).get("number"),
                }
            }

        except Exception as e:
            logger.error(f"Elasticsearch connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
            }

    def _create_client(self, config: Dict[str, Any]) -> Elasticsearch:
        """
        Create Elasticsearch client from configuration.

        Args:
            config: Decrypted configuration dictionary

        Returns:
            Elasticsearch client instance
        """
        host = config["host"]
        port = config.get("port", 9200)
        api_key = config["api_key"]
        use_ssl = config.get("use_ssl", True)
        verify_certs = config.get("verify_certs", True)

        # Build connection URL
        scheme = "https" if use_ssl else "http"
        url = f"{scheme}://{host}:{port}"

        # Create client
        es = Elasticsearch(
            [url],
            api_key=api_key,
            verify_certs=verify_certs,
            request_timeout=30,
        )

        return es

    def _create_query_tool(self, config: Dict[str, Any]) -> BaseTool:
        """
        Create query_elasticsearch tool.

        Args:
            config: Decrypted configuration

        Returns:
            LangChain tool for querying Elasticsearch
        """
        es = self._create_client(config)
        index_patterns = config.get("index_patterns", [])
        max_results = config.get("max_results", 1000)

        @tool
        def query_elasticsearch(
            query: str,
            index_pattern: Optional[str] = None,
            time_range_hours: int = 24,
            fields: Optional[List[str]] = None
        ) -> str:
            """
            Query Elasticsearch logs with Query DSL.

            Args:
                query: Search query (supports Query DSL or simple text)
                index_pattern: Index pattern to search (must be in whitelist)
                time_range_hours: Time range in hours (default: 24)
                fields: Fields to return (default: all)

            Returns:
                Search results as formatted string

            Example:
                query_elasticsearch(
                    query="error AND status:500",
                    index_pattern="logs-*",
                    time_range_hours=1
                )
            """
            try:
                # Validate index pattern
                if index_pattern and index_pattern not in index_patterns:
                    return f"Error: index_pattern '{index_pattern}' not in whitelist: {index_patterns}"

                # Use first pattern if not specified
                target_index = index_pattern or index_patterns[0]

                # Build query
                query_body = {
                    "query": {
                        "bool": {
                            "must": [
                                {"query_string": {"query": query}}
                            ],
                            "filter": [
                                {
                                    "range": {
                                        "@timestamp": {
                                            "gte": f"now-{time_range_hours}h",
                                            "lte": "now"
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "size": max_results,
                    "sort": [{"@timestamp": {"order": "desc"}}]
                }

                # Add fields filter if specified
                if fields:
                    query_body["_source"] = fields

                # Execute search
                response = es.search(index=target_index, body=query_body)

                # Format results
                hits = response["hits"]["hits"]
                total = response["hits"]["total"]["value"]

                if total == 0:
                    return "No results found"

                # Format as readable string
                results = [f"Found {total} results (showing {len(hits)}):\n"]

                for i, hit in enumerate(hits, 1):
                    source = hit["_source"]
                    timestamp = source.get("@timestamp", "N/A")
                    message = source.get("message", str(source))

                    results.append(f"{i}. [{timestamp}] {message}")

                return "\n".join(results)

            except Exception as e:
                logger.error(f"Elasticsearch query failed: {e}")
                return f"Query failed: {str(e)}"

        return query_elasticsearch

    def _create_correlate_tool(self, config: Dict[str, Any]) -> BaseTool:
        """
        Create correlate_logs tool.

        Args:
            config: Decrypted configuration

        Returns:
            LangChain tool for correlating logs by trace/request ID
        """
        es = self._create_client(config)
        index_patterns = config.get("index_patterns", [])
        max_results = config.get("max_results", 1000)

        @tool
        def correlate_logs(
            trace_id: Optional[str] = None,
            request_id: Optional[str] = None,
            index_pattern: Optional[str] = None,
            time_range_hours: int = 24
        ) -> str:
            """
            Correlate logs by trace ID or request ID.

            Useful for tracking a request across multiple services.

            Args:
                trace_id: Trace ID to correlate (e.g., from OpenTelemetry)
                request_id: Request ID to correlate
                index_pattern: Index pattern to search
                time_range_hours: Time range in hours (default: 24)

            Returns:
                Correlated log entries as formatted string

            Example:
                correlate_logs(trace_id="abc123", time_range_hours=1)
            """
            try:
                if not trace_id and not request_id:
                    return "Error: Either trace_id or request_id must be provided"

                # Validate index pattern
                if index_pattern and index_pattern not in index_patterns:
                    return f"Error: index_pattern '{index_pattern}' not in whitelist: {index_patterns}"

                target_index = index_pattern or index_patterns[0]

                # Build correlation query
                must_conditions = []

                if trace_id:
                    must_conditions.append({
                        "term": {"trace_id": trace_id}
                    })

                if request_id:
                    must_conditions.append({
                        "term": {"request_id": request_id}
                    })

                query_body = {
                    "query": {
                        "bool": {
                            "must": must_conditions,
                            "filter": [
                                {
                                    "range": {
                                        "@timestamp": {
                                            "gte": f"now-{time_range_hours}h",
                                            "lte": "now"
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "size": max_results,
                    "sort": [{"@timestamp": {"order": "asc"}}]  # Chronological order
                }

                # Execute search
                response = es.search(index=target_index, body=query_body)

                # Format results
                hits = response["hits"]["hits"]
                total = response["hits"]["total"]["value"]

                if total == 0:
                    return f"No logs found for trace_id={trace_id}, request_id={request_id}"

                # Format as timeline
                results = [f"Found {total} correlated log entries (showing {len(hits)}):\n"]

                for i, hit in enumerate(hits, 1):
                    source = hit["_source"]
                    timestamp = source.get("@timestamp", "N/A")
                    service = source.get("service", {}).get("name", "unknown")
                    level = source.get("level", "INFO")
                    message = source.get("message", str(source))

                    results.append(f"{i}. [{timestamp}] [{service}] [{level}] {message}")

                return "\n".join(results)

            except Exception as e:
                logger.error(f"Log correlation failed: {e}")
                return f"Correlation failed: {str(e)}"

        return correlate_logs
