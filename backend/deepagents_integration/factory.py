"""
Agent Factory for creating deepagents instances from database configurations.

This module provides the AgentFactory class which creates fully configured
deepagents instances from database Agent models, handling model provider
selection, feature configuration, and tool/subagent setup.
"""

import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

# Add mock deepagents to path for development/testing
mock_path = Path(__file__).parent.parent / "deepagents_mock"
if mock_path.exists() and str(mock_path) not in sys.path:
    sys.path.insert(0, str(mock_path.parent))

try:
    from deepagents import create_deep_agent
    from deepagents.backends import BackendProtocol
    from deepagents.middleware.subagents import SubAgent
except ImportError:
    # Fallback to mock if deepagents not installed
    from deepagents_mock import create_deep_agent
    from deepagents_mock.backends import BackendProtocol
    from deepagents_mock.middleware.subagents import SubAgent

from langchain.tools import BaseTool
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.agent import Agent as AgentModel

from .backends import backend_manager
from .store import store_manager


class AgentFactory:
    """
    Factory for creating deepagents instances from database configurations.

    Responsibilities:
    - Create LLM instances based on model provider (Anthropic, OpenAI, etc.)
    - Configure deepagents with planning and filesystem features
    - Attach tools and subagents to agents
    - Validate API keys and configurations

    Usage:
        factory = AgentFactory()
        agent = await factory.create_agent(agent_config, tools=tools)
    """

    def __init__(self):
        """
        Initialize the agent factory with model provider mappings.
        """
        self.model_providers: dict[str, Callable] = {
            "anthropic": self._create_anthropic_model,
            "openai": self._create_openai_model,
        }

    def _create_anthropic_model(
        self, model_name: str, temperature: float, max_tokens: int
    ) -> ChatAnthropic:
        """
        Create an Anthropic ChatAnthropic model instance.

        Args:
            model_name: Name of the Claude model (e.g., claude-3-5-sonnet-20241022)
            temperature: Temperature setting (0.0-1.0)
            max_tokens: Maximum tokens for completion

        Returns:
            ChatAnthropic: Configured Anthropic model instance

        Raises:
            ValueError: If ANTHROPIC_API_KEY is not configured
        """
        api_key = settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        return ChatAnthropic(
            api_key=api_key,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _create_openai_model(
        self, model_name: str, temperature: float, max_tokens: int
    ) -> ChatOpenAI:
        """
        Create an OpenAI ChatOpenAI model instance.

        Args:
            model_name: Name of the GPT model (e.g., gpt-4)
            temperature: Temperature setting (0.0-1.0)
            max_tokens: Maximum tokens for completion

        Returns:
            ChatOpenAI: Configured OpenAI model instance

        Raises:
            ValueError: If OPENAI_API_KEY is not configured
        """
        api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")

        return ChatOpenAI(
            api_key=api_key,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _validate_model_provider(self, provider: str) -> None:
        """
        Validate that the model provider is supported.

        Args:
            provider: Model provider name (e.g., "anthropic", "openai")

        Raises:
            ValueError: If provider is not supported
        """
        if provider not in self.model_providers:
            raise ValueError(
                f"Unsupported model provider: {provider}. "
                f"Supported providers: {', '.join(self.model_providers.keys())}"
            )

    def _create_llm(self, agent_config: AgentModel) -> Any:
        """
        Create LLM instance based on agent configuration.

        Args:
            agent_config: Agent model with LLM configuration

        Returns:
            LLM instance (ChatAnthropic, ChatOpenAI, etc.)

        Raises:
            ValueError: If model provider is invalid or API key missing
        """
        self._validate_model_provider(agent_config.model_provider)

        llm_creator = self.model_providers[agent_config.model_provider]
        return llm_creator(
            agent_config.model_name,
            agent_config.temperature,
            agent_config.max_tokens or 4096,  # Default to 4096 if not specified
        )

    def _prepare_tools_and_subagents(
        self,
        tools: Optional[list[BaseTool]],
        subagents: Optional[list[SubAgent]]
    ) -> tuple[list[BaseTool], list[SubAgent]]:
        """
        Prepare tools and subagents lists, ensuring they're not None.

        Args:
            tools: Optional list of tools
            subagents: Optional list of subagents

        Returns:
            Tuple of (tools_list, subagents_list) with empty lists as defaults
        """
        return tools or [], subagents or []

    async def _load_backend_config(
        self,
        agent_config: AgentModel,
        db_session: Optional[AsyncSession],
        runtime: Optional[Any]
    ) -> Optional[BackendProtocol]:
        """
        Load and create backend from agent configuration.

        Args:
            agent_config: Agent model with potential backend config
            db_session: Database session for loading configs
            runtime: Runtime instance for backend creation

        Returns:
            BackendProtocol instance or None if not configured
        """
        if not db_session or not hasattr(agent_config, "backend_config"):
            return None

        if not agent_config.backend_config:
            return None

        backend_config = agent_config.backend_config

        # Get or create store if needed for StoreBackend
        store = None
        if hasattr(agent_config, "memory_namespace") and agent_config.memory_namespace:
            namespace = agent_config.memory_namespace.namespace
            store = await store_manager.get_store(
                namespace=namespace,
                store_type=agent_config.memory_namespace.store_type,
                db_session=db_session
            )

        # Create backend from configuration
        return backend_manager.create_backend(
            config={
                "type": backend_config.backend_type,
                **backend_config.config
            },
            runtime=runtime,
            store=store
        )

    def _load_interrupt_config(
        self,
        agent_config: AgentModel,
        db_session: Optional[AsyncSession]
    ) -> tuple[Optional[Dict[str, Any]], Optional[Any]]:
        """
        Load HITL interrupt configuration and create checkpointer.

        Args:
            agent_config: Agent model with potential interrupt configs
            db_session: Database session for loading configs

        Returns:
            Tuple of (interrupt_on dict, checkpointer) or (None, None)
        """
        if not db_session or not hasattr(agent_config, "interrupt_configs"):
            return None, None

        if not agent_config.interrupt_configs:
            return None, None

        # Build interrupt_on dictionary from configs
        interrupt_on = {}
        for interrupt_config in agent_config.interrupt_configs:
            interrupt_on[interrupt_config.tool_name] = {
                "allowed_decisions": interrupt_config.allowed_decisions,
                **interrupt_config.config
            }

        # Create checkpointer for HITL support
        # Note: Using MemorySaver for now, can be replaced with PostgresSaver
        checkpointer = MemorySaver()

        return interrupt_on, checkpointer

    async def create_agent(
        self,
        agent_config: AgentModel,
        tools: Optional[list[BaseTool]] = None,
        subagents: Optional[list[SubAgent]] = None,
        db_session: Optional[AsyncSession] = None,
        runtime: Optional[Any] = None,
    ) -> Any:
        """
        Create a DeepAgent instance from database configuration.

        This method orchestrates the creation of a fully configured deepagents
        instance, including:
        - LLM selection based on model provider
        - Middleware configuration (planning, filesystem)
        - Backend storage configuration (StateBackend, FilesystemBackend, StoreBackend, CompositeBackend)
        - Tool attachment
        - Subagent configuration
        - HITL (Human-in-the-Loop) interrupt configuration
        - Checkpointer for HITL support

        Args:
            agent_config: Agent model from database with configuration
            tools: Optional list of LangChain tools to provide to the agent
            subagents: Optional list of SubAgent configurations for delegation
            db_session: Optional database session for loading advanced configs
            runtime: Optional runtime instance for backend creation

        Returns:
            CompiledStateGraph: Configured deepagents instance ready for execution

        Raises:
            ValueError: If model provider is invalid or API key is missing
            ValueError: If tool configuration is invalid
            ValueError: If backend configuration is invalid

        Example:
            agent_config = await db.get(Agent, agent_id)
            tools = [search_tool, calculator_tool]
            agent = await factory.create_agent(
                agent_config,
                tools=tools,
                db_session=session,
                runtime=runtime
            )
        """
        # Step 1: Create LLM instance
        llm = self._create_llm(agent_config)

        # Step 2: Prepare tools and subagents
        agent_tools, agent_subagents = self._prepare_tools_and_subagents(tools, subagents)

        # Step 3: Load advanced configurations (backend, HITL)
        backend = await self._load_backend_config(agent_config, db_session, runtime)
        interrupt_on, checkpointer = self._load_interrupt_config(agent_config, db_session)

        # Step 4: Create DeepAgent using create_deep_agent
        # Note: By default, create_deep_agent includes:
        #   - write_todos tool (planning) - ALWAYS enabled
        #   - 6 file editing tools (filesystem) - ALWAYS enabled
        #   - subagent delegation tool - enabled when subagents provided
        #
        # The planning_enabled and filesystem_enabled flags in our database
        # are informational for the UI. deepagents agents always have these
        # capabilities built-in.
        #
        # Advanced features (if configured):
        #   - backend: Custom storage backend (State/Filesystem/Store/Composite)
        #   - interrupt_on: HITL approval gates for specific tools
        #   - checkpointer: Required for HITL, enables state persistence
        agent = create_deep_agent(
            model=llm,
            tools=agent_tools,
            system_prompt=agent_config.system_prompt or "",
            subagents=agent_subagents if agent_subagents else None,
            backend=backend,  # Advanced: Custom backend (optional)
            interrupt_on=interrupt_on,  # Advanced: HITL configuration (optional)
            checkpointer=checkpointer,  # Advanced: State persistence (required for HITL)
        )

        return agent

    def get_supported_providers(self) -> list[str]:
        """
        Get list of supported model providers.

        Returns:
            list[str]: List of supported provider names
        """
        return list(self.model_providers.keys())

    def register_provider(
        self, provider_name: str, creator_func: Callable[[str, float, int], Any]
    ):
        """
        Register a custom model provider.

        Args:
            provider_name: Name of the provider (e.g., "google", "cohere")
            creator_func: Function that creates model instance
                         Signature: (model_name, temperature, max_tokens) -> LLM
        """
        self.model_providers[provider_name] = creator_func


# Singleton instance for convenience
agent_factory = AgentFactory()
