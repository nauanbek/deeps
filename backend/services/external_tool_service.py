"""
External Tool Service.

Business logic for external tool configuration management,
connection testing, and tool instantiation.
"""

from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.encryption import get_encryptor
from core.metrics_external_tools import (
    record_connection_test,
    record_marketplace_action,
    update_tool_config_gauges,
)
from langchain_tools import (
    ElasticsearchTool,
    HTTPClientTool,
    PostgreSQLTool,
)
from models.external_tool import ExternalToolConfig, ToolExecutionLog
from schemas.external_tool import (
    ExternalToolConfigCreate,
    ExternalToolConfigUpdate,
    ToolCatalogItem,
    ToolUsageStats,
)


class ExternalToolService:
    """Service for managing external tool configurations."""

    # Tool type to class mapping
    TOOL_CLASSES = {
        "postgresql": PostgreSQLTool,
        "elasticsearch": ElasticsearchTool,
        "http": HTTPClientTool,
        # gitlab will be added in Week 2
    }

    async def create_tool_config(
        self,
        db: AsyncSession,
        user_id: int,
        data: ExternalToolConfigCreate,
    ) -> ExternalToolConfig:
        """
        Create new external tool configuration.

        Args:
            db: Database session
            user_id: User ID
            data: Tool configuration data

        Returns:
            Created tool configuration

        Raises:
            ValueError: If tool_name already exists or configuration invalid
        """
        # Check if tool_name already exists for this user
        stmt = select(ExternalToolConfig).where(
            and_(
                ExternalToolConfig.user_id == user_id,
                ExternalToolConfig.tool_name == data.tool_name,
            )
        )
        result = await db.execute(stmt)
        existing_tool = result.scalar_one_or_none()

        if existing_tool:
            raise ValueError(f"Tool '{data.tool_name}' already exists")

        # Encrypt sensitive fields in configuration
        encrypted_config = await self._encrypt_configuration(
            data.tool_type, data.configuration
        )

        # Create tool config
        tool_config = ExternalToolConfig(
            user_id=user_id,
            tool_name=data.tool_name,
            tool_type=data.tool_type,
            provider=data.provider,
            configuration=encrypted_config,
            is_active=True,
            test_status="not_tested",
        )

        db.add(tool_config)
        await db.commit()
        await db.refresh(tool_config)

        logger.info(
            f"Created external tool config: {tool_config.tool_name} "
            f"(type={tool_config.tool_type}, user_id={user_id})"
        )

        # Update metrics
        await self._update_metrics_for_user(db, user_id, data.tool_type)

        # Record marketplace action
        record_marketplace_action("configure", data.tool_type)

        return tool_config

    async def list_tool_configs(
        self,
        db: AsyncSession,
        user_id: int,
        tool_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ExternalToolConfig]:
        """
        List user's external tool configurations.

        Args:
            db: Database session
            user_id: User ID
            tool_type: Filter by tool type
            is_active: Filter by active status
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of tool configurations
        """
        # Build query
        conditions = [ExternalToolConfig.user_id == user_id]

        if tool_type:
            conditions.append(ExternalToolConfig.tool_type == tool_type)

        if is_active is not None:
            conditions.append(ExternalToolConfig.is_active == is_active)

        stmt = (
            select(ExternalToolConfig)
            .where(and_(*conditions))
            .order_by(ExternalToolConfig.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(stmt)
        tool_configs = result.scalars().all()

        return list(tool_configs)

    async def count_tool_configs(
        self,
        db: AsyncSession,
        user_id: int,
        tool_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """
        Count user's external tool configurations.

        Args:
            db: Database session
            user_id: User ID
            tool_type: Filter by tool type
            is_active: Filter by active status

        Returns:
            Total count
        """
        conditions = [ExternalToolConfig.user_id == user_id]

        if tool_type:
            conditions.append(ExternalToolConfig.tool_type == tool_type)

        if is_active is not None:
            conditions.append(ExternalToolConfig.is_active == is_active)

        stmt = select(func.count()).select_from(ExternalToolConfig).where(and_(*conditions))

        result = await db.execute(stmt)
        total = result.scalar_one()

        return total

    async def get_tool_config(
        self, db: AsyncSession, user_id: int, tool_id: int
    ) -> Optional[ExternalToolConfig]:
        """
        Get external tool configuration by ID.

        Args:
            db: Database session
            user_id: User ID (for authorization)
            tool_id: Tool configuration ID

        Returns:
            Tool configuration or None if not found
        """
        stmt = select(ExternalToolConfig).where(
            and_(
                ExternalToolConfig.id == tool_id,
                ExternalToolConfig.user_id == user_id,
            )
        )

        result = await db.execute(stmt)
        tool_config = result.scalar_one_or_none()

        return tool_config

    async def update_tool_config(
        self,
        db: AsyncSession,
        user_id: int,
        tool_id: int,
        data: ExternalToolConfigUpdate,
    ) -> Optional[ExternalToolConfig]:
        """
        Update external tool configuration.

        Args:
            db: Database session
            user_id: User ID
            tool_id: Tool configuration ID
            data: Update data

        Returns:
            Updated tool configuration or None if not found

        Raises:
            ValueError: If tool_name conflict or invalid configuration
        """
        # Get existing config
        tool_config = await self.get_tool_config(db, user_id, tool_id)
        if not tool_config:
            return None

        # Check tool_name conflict if changing name
        if data.tool_name and data.tool_name != tool_config.tool_name:
            stmt = select(ExternalToolConfig).where(
                and_(
                    ExternalToolConfig.user_id == user_id,
                    ExternalToolConfig.tool_name == data.tool_name,
                    ExternalToolConfig.id != tool_id,
                )
            )
            result = await db.execute(stmt)
            existing_tool = result.scalar_one_or_none()

            if existing_tool:
                raise ValueError(f"Tool '{data.tool_name}' already exists")

            tool_config.tool_name = data.tool_name

        # Update configuration if provided
        if data.configuration is not None:
            encrypted_config = await self._encrypt_configuration(
                tool_config.tool_type, data.configuration
            )
            tool_config.configuration = encrypted_config
            # Reset test status when config changes
            tool_config.test_status = "not_tested"
            tool_config.last_tested_at = None
            tool_config.test_error_message = None

        # Update is_active if provided
        if data.is_active is not None:
            tool_config.is_active = data.is_active

        tool_config.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(tool_config)

        logger.info(f"Updated external tool config: {tool_config.tool_name} (id={tool_id})")

        return tool_config

    async def delete_tool_config(
        self, db: AsyncSession, user_id: int, tool_id: int
    ) -> bool:
        """
        Delete external tool configuration.

        Args:
            db: Database session
            user_id: User ID
            tool_id: Tool configuration ID

        Returns:
            True if deleted, False if not found
        """
        tool_config = await self.get_tool_config(db, user_id, tool_id)
        if not tool_config:
            return False

        await db.delete(tool_config)
        await db.commit()

        logger.info(f"Deleted external tool config: {tool_config.tool_name} (id={tool_id})")

        return True

    async def test_connection(
        self,
        db: AsyncSession,
        user_id: int,
        tool_id: int,
        override_config: Optional[Dict] = None,
    ) -> Dict:
        """
        Test connection to external tool.

        Args:
            db: Database session
            user_id: User ID
            tool_id: Tool configuration ID
            override_config: Optional config override for testing before save

        Returns:
            Test result dictionary with success status

        Raises:
            ValueError: If tool not found or unsupported type
        """
        tool_config = await self.get_tool_config(db, user_id, tool_id)
        if not tool_config:
            raise ValueError("Tool configuration not found")

        # Use override config if provided, otherwise use stored config
        config = override_config if override_config else tool_config.configuration

        # Decrypt configuration
        tool_class = self.TOOL_CLASSES.get(tool_config.tool_type)
        if not tool_class:
            raise ValueError(f"Unsupported tool type: {tool_config.tool_type}")

        # Create tool instance and test
        tool = tool_class(config)
        result = await tool.test_connection()

        # Update test status in database if not using override
        if not override_config:
            tool_config.last_tested_at = datetime.utcnow()
            tool_config.test_status = "success" if result["success"] else "failed"
            tool_config.test_error_message = None if result["success"] else result.get("message")

            await db.commit()

        # Record metrics
        record_connection_test(tool_config.tool_type, result["success"])
        record_marketplace_action("test", tool_config.tool_type)

        return result

    async def get_tool_catalog(self) -> List[ToolCatalogItem]:
        """
        Get catalog of available tools for marketplace.

        Returns:
            List of tool catalog items
        """
        catalog = [
            ToolCatalogItem(
                tool_type="postgresql",
                provider="langchain",
                name="PostgreSQL Database",
                description="Query PostgreSQL databases with read-only access, automatic timeouts, and row limits",
                category="database",
                icon="database",
                required_fields=["host", "database", "username", "password"],
                optional_fields=["port", "ssl_mode", "pool_size", "timeout", "row_limit"],
                example_configuration={
                    "host": "localhost",
                    "port": 5432,
                    "database": "mydb",
                    "username": "readonly_user",
                    "password": "***ENCRYPTED***",
                    "ssl_mode": "require",
                    "read_only": True,
                    "timeout": 30,
                    "row_limit": 1000,
                },
            ),
            ToolCatalogItem(
                tool_type="elasticsearch",
                provider="langchain",
                name="Elasticsearch Logs",
                description="Search and correlate logs in Elasticsearch with Query DSL support",
                category="logs",
                icon="search",
                required_fields=["host", "api_key", "index_patterns"],
                optional_fields=["port", "use_ssl", "verify_certs", "max_results", "timeout"],
                example_configuration={
                    "host": "elasticsearch.example.com",
                    "port": 9200,
                    "api_key": "***ENCRYPTED***",
                    "index_patterns": ["logs-*", "metrics-*"],
                    "use_ssl": True,
                    "max_results": 1000,
                },
            ),
            ToolCatalogItem(
                tool_type="http",
                provider="langchain",
                name="HTTP API Client",
                description="Make HTTP GET/POST requests to external APIs with domain whitelisting",
                category="http",
                icon="globe",
                required_fields=["allowed_domains"],
                optional_fields=["base_url", "auth_type", "bearer_token", "api_key", "timeout"],
                example_configuration={
                    "base_url": "https://api.example.com",
                    "auth_type": "bearer",
                    "bearer_token": "***ENCRYPTED***",
                    "allowed_domains": ["api.example.com"],
                    "timeout": 30,
                },
            ),
            # GitLab will be added in Week 2
        ]

        # Record catalog view (without user_id since it's just catalog metadata)
        record_marketplace_action("view_catalog", "all")

        return catalog

    async def get_tool_usage_analytics(
        self,
        db: AsyncSession,
        user_id: int,
        days: int = 30,
    ) -> Dict:
        """
        Get tool usage analytics for user.

        Args:
            db: Database session
            user_id: User ID
            days: Number of days to analyze (default: 30)

        Returns:
            Analytics dictionary with statistics
        """
        # Get tool configs count
        total_tools_stmt = select(func.count()).select_from(ExternalToolConfig).where(
            ExternalToolConfig.user_id == user_id
        )
        total_tools_result = await db.execute(total_tools_stmt)
        total_tools = total_tools_result.scalar_one()

        active_tools_stmt = select(func.count()).select_from(ExternalToolConfig).where(
            and_(
                ExternalToolConfig.user_id == user_id,
                ExternalToolConfig.is_active == True,
            )
        )
        active_tools_result = await db.execute(active_tools_stmt)
        active_tools = active_tools_result.scalar_one()

        # Get execution statistics per tool
        from sqlalchemy import case

        stmt = (
            select(
                ToolExecutionLog.tool_name,
                ToolExecutionLog.tool_type,
                func.count().label("total_executions"),
                func.sum(
                    case((ToolExecutionLog.success == True, 1), else_=0)
                ).label("successful_executions"),
                func.sum(
                    case((ToolExecutionLog.success == False, 1), else_=0)
                ).label("failed_executions"),
                func.avg(ToolExecutionLog.duration_ms).label("avg_duration_ms"),
                func.max(ToolExecutionLog.created_at).label("last_execution_at"),
            )
            .where(
                and_(
                    ToolExecutionLog.user_id == user_id,
                    ToolExecutionLog.created_at >= func.now() - func.cast(f"{days} days", type_=func.text("interval")),
                )
            )
            .group_by(ToolExecutionLog.tool_name, ToolExecutionLog.tool_type)
        )

        result = await db.execute(stmt)
        rows = result.all()

        # Build tool stats
        tool_stats = []
        total_executions = 0

        for row in rows:
            successful = row.successful_executions or 0
            failed = row.failed_executions or 0
            total = row.total_executions or 0
            total_executions += total

            success_rate = successful / total if total > 0 else 0.0

            tool_stats.append(
                ToolUsageStats(
                    tool_name=row.tool_name,
                    tool_type=row.tool_type,
                    total_executions=total,
                    successful_executions=successful,
                    failed_executions=failed,
                    success_rate=success_rate,
                    avg_duration_ms=float(row.avg_duration_ms or 0),
                    last_execution_at=row.last_execution_at,
                )
            )

        # Calculate overall success rate
        if total_executions > 0:
            successful_total = sum(stat.successful_executions for stat in tool_stats)
            overall_success_rate = successful_total / total_executions
        else:
            overall_success_rate = 0.0

        return {
            "total_tools": total_tools,
            "active_tools": active_tools,
            "total_executions": total_executions,
            "success_rate": overall_success_rate,
            "tools": tool_stats,
            "time_range": f"last_{days}_days",
        }

    async def _encrypt_configuration(
        self, tool_type: str, configuration: Dict
    ) -> Dict:
        """
        Encrypt sensitive fields in tool configuration.

        Args:
            tool_type: Tool type
            configuration: Configuration dictionary

        Returns:
            Configuration with encrypted sensitive fields
        """
        tool_class = self.TOOL_CLASSES.get(tool_type)
        if not tool_class:
            raise ValueError(f"Unsupported tool type: {tool_type}")

        # Get encrypted fields for this tool type
        tool_instance = tool_class(configuration)
        encrypted_fields = tool_instance.get_encrypted_fields()

        # Encrypt sensitive fields
        encryptor = get_encryptor()
        encrypted_config = encryptor.encrypt_dict_fields(configuration, encrypted_fields)

        return encrypted_config

    async def _update_metrics_for_user(
        self, db: AsyncSession, user_id: int, tool_type: str
    ) -> None:
        """
        Update Prometheus metrics for user's tool configurations.

        Args:
            db: Database session
            user_id: User ID
            tool_type: Tool type
        """
        # Count active configs
        active_stmt = select(func.count()).select_from(ExternalToolConfig).where(
            and_(
                ExternalToolConfig.user_id == user_id,
                ExternalToolConfig.tool_type == tool_type,
                ExternalToolConfig.is_active == True,
            )
        )
        active_result = await db.execute(active_stmt)
        active_count = active_result.scalar_one()

        # Count total configs
        total_stmt = select(func.count()).select_from(ExternalToolConfig).where(
            and_(
                ExternalToolConfig.user_id == user_id,
                ExternalToolConfig.tool_type == tool_type,
            )
        )
        total_result = await db.execute(total_stmt)
        total_count = total_result.scalar_one()

        # Update metrics
        update_tool_config_gauges(tool_type, active_count, total_count, user_id)


# Global service instance
external_tool_service = ExternalToolService()
