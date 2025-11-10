"""
Tests for AgentFactory - deepagents agent creation from database configurations.

Following TDD: Write tests first, then implement the factory.
"""

import os
from unittest.mock import AsyncMock, Mock, patch

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from deepagents_integration.factory import AgentFactory
from models.agent import Agent as AgentModel


@pytest.fixture
def agent_factory():
    """Create an AgentFactory instance for testing."""
    return AgentFactory()


@pytest.fixture
def basic_agent_config():
    """Create a basic agent configuration for testing."""
    return AgentModel(
        id=1,
        name="Test Agent",
        description="A test agent",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=4096,
        system_prompt="You are a helpful assistant.",
        planning_enabled=False,
        filesystem_enabled=False,
        additional_config={},
        created_by_id=1,
        is_active=True,
    )


@pytest.fixture
def agent_with_features():
    """Create an agent configuration with planning and filesystem enabled."""
    return AgentModel(
        id=2,
        name="Advanced Agent",
        description="An agent with all features",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.5,
        max_tokens=8192,
        system_prompt="You are an advanced planning agent.",
        planning_enabled=True,
        filesystem_enabled=True,
        additional_config={},
        created_by_id=1,
        is_active=True,
    )


@pytest.fixture
def openai_agent_config():
    """Create an OpenAI agent configuration."""
    return AgentModel(
        id=3,
        name="GPT Agent",
        description="An OpenAI GPT-4 agent",
        model_provider="openai",
        model_name="gpt-4",
        temperature=0.8,
        max_tokens=2048,
        system_prompt="You are a creative assistant.",
        planning_enabled=False,
        filesystem_enabled=False,
        additional_config={},
        created_by_id=1,
        is_active=True,
    )


# Basic Agent Creation Tests


@pytest.mark.asyncio
async def test_create_basic_agent_from_config(agent_factory, basic_agent_config):
    """Test creating a basic agent from database configuration."""
    # Set API key for test
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(basic_agent_config)

        assert agent is not None
        assert hasattr(agent, "ainvoke")  # Has async invoke method
        assert hasattr(agent, "astream")  # Has async stream method


@pytest.mark.asyncio
async def test_create_agent_with_planning_enabled(agent_factory, agent_with_features):
    """Test creating an agent with planning enabled."""
    config = agent_with_features
    config.planning_enabled = True
    config.filesystem_enabled = False

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(config)

        assert agent is not None
        # Agent should have planning capabilities
        # Note: deepagents handles this internally


@pytest.mark.asyncio
async def test_create_agent_with_filesystem_enabled(agent_factory, agent_with_features):
    """Test creating an agent with filesystem middleware enabled."""
    config = agent_with_features
    config.planning_enabled = False
    config.filesystem_enabled = True

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(config)

        assert agent is not None


@pytest.mark.asyncio
async def test_create_agent_with_both_features(agent_factory, agent_with_features):
    """Test creating an agent with both planning and filesystem enabled."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(agent_with_features)

        assert agent is not None


# Model Configuration Tests


@pytest.mark.asyncio
async def test_create_agent_anthropic_claude(agent_factory, basic_agent_config):
    """Test creating an agent with Anthropic Claude model."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.ChatAnthropic") as mock_anthropic:
            mock_llm = Mock()
            mock_anthropic.return_value = mock_llm

            agent = await agent_factory.create_agent(basic_agent_config)

            # Verify ChatAnthropic was called with correct parameters
            mock_anthropic.assert_called_once()
            call_kwargs = mock_anthropic.call_args.kwargs
            assert call_kwargs["api_key"] == "test-key"
            assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
            assert call_kwargs["temperature"] == 0.7
            assert call_kwargs["max_tokens"] == 4096


@pytest.mark.asyncio
async def test_create_agent_openai_gpt4(agent_factory, openai_agent_config):
    """Test creating an agent with OpenAI GPT-4 model."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.ChatOpenAI") as mock_openai:
            mock_llm = Mock()
            mock_openai.return_value = mock_llm

            agent = await agent_factory.create_agent(openai_agent_config)

            # Verify ChatOpenAI was called with correct parameters
            mock_openai.assert_called_once()
            call_kwargs = mock_openai.call_args.kwargs
            assert call_kwargs["api_key"] == "test-key"
            assert call_kwargs["model"] == "gpt-4"
            assert call_kwargs["temperature"] == 0.8
            assert call_kwargs["max_tokens"] == 2048


@pytest.mark.asyncio
async def test_create_agent_with_custom_temperature(agent_factory, basic_agent_config):
    """Test creating an agent with custom temperature setting."""
    basic_agent_config.temperature = 0.3

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.ChatAnthropic") as mock_anthropic:
            mock_llm = Mock()
            mock_anthropic.return_value = mock_llm

            await agent_factory.create_agent(basic_agent_config)

            call_kwargs = mock_anthropic.call_args.kwargs
            assert call_kwargs["temperature"] == 0.3


@pytest.mark.asyncio
async def test_create_agent_with_max_tokens(agent_factory, basic_agent_config):
    """Test creating an agent with specific max_tokens setting."""
    basic_agent_config.max_tokens = 16000

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.ChatAnthropic") as mock_anthropic:
            mock_llm = Mock()
            mock_anthropic.return_value = mock_llm

            await agent_factory.create_agent(basic_agent_config)

            call_kwargs = mock_anthropic.call_args.kwargs
            assert call_kwargs["max_tokens"] == 16000


# Tool Integration Tests


@pytest.mark.asyncio
async def test_create_agent_with_tools(agent_factory, basic_agent_config):
    """Test creating an agent with custom tools."""
    # Create mock tools
    mock_tool1 = Mock(name="search_tool")
    mock_tool2 = Mock(name="calculator_tool")
    tools = [mock_tool1, mock_tool2]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.create_deep_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_create.return_value = mock_agent

            agent = await agent_factory.create_agent(basic_agent_config, tools=tools)

            # Verify tools were passed to deepagents
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["tools"] == tools


@pytest.mark.asyncio
async def test_create_agent_with_custom_tool_config(agent_factory, basic_agent_config):
    """Test creating an agent with tools and custom configuration."""
    mock_tool = Mock(name="custom_tool")
    tools = [mock_tool]

    basic_agent_config.additional_config = {
        "tool_timeout": 30,
        "max_tool_iterations": 5,
    }

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.create_deep_agent") as mock_create:
            mock_agent = Mock()
            mock_create.return_value = mock_agent

            agent = await agent_factory.create_agent(basic_agent_config, tools=tools)

            assert agent is not None
            # Verify tools were passed
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["tools"] == tools


# Subagent Configuration Tests


@pytest.mark.asyncio
async def test_create_agent_with_subagents(agent_factory, basic_agent_config):
    """Test creating an agent with subagent configurations."""
    from deepagents.middleware.subagents import SubAgent

    # Create mock subagent
    mock_subagent = Mock(spec=SubAgent)
    subagents = [mock_subagent]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.create_deep_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_create.return_value = mock_agent

            agent = await agent_factory.create_agent(
                basic_agent_config, subagents=subagents
            )

            # Verify subagents were passed
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["subagents"] == subagents


@pytest.mark.asyncio
async def test_subagent_delegation_config(agent_factory, basic_agent_config):
    """Test that subagent delegation is properly configured."""
    from deepagents.middleware.subagents import SubAgent

    # Create multiple subagents
    subagent1 = Mock(spec=SubAgent)
    subagent1.name = "research_agent"
    subagent2 = Mock(spec=SubAgent)
    subagent2.name = "coding_agent"

    subagents = [subagent1, subagent2]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.create_deep_agent") as mock_create:
            mock_agent = Mock()
            mock_create.return_value = mock_agent

            agent = await agent_factory.create_agent(
                basic_agent_config, subagents=subagents
            )

            assert agent is not None
            # Verify subagents were passed
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["subagents"] == subagents


# Error Handling Tests


@pytest.mark.asyncio
async def test_create_agent_invalid_model_provider(agent_factory, basic_agent_config):
    """Test error handling for invalid model provider."""
    basic_agent_config.model_provider = "invalid_provider"

    with pytest.raises(ValueError, match="Unsupported model provider"):
        await agent_factory.create_agent(basic_agent_config)


@pytest.mark.asyncio
async def test_create_agent_missing_anthropic_api_key(agent_factory, basic_agent_config):
    """Test error handling when Anthropic API key is missing."""
    # Ensure ANTHROPIC_API_KEY is not set
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=True):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not configured"):
            await agent_factory.create_agent(basic_agent_config)


@pytest.mark.asyncio
async def test_create_agent_missing_openai_api_key(agent_factory, openai_agent_config):
    """Test error handling when OpenAI API key is missing."""
    # Ensure OPENAI_API_KEY is not set
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
        with pytest.raises(ValueError, match="OPENAI_API_KEY not configured"):
            await agent_factory.create_agent(openai_agent_config)


@pytest.mark.asyncio
async def test_create_agent_invalid_tool_reference(agent_factory, basic_agent_config):
    """Test error handling for invalid tool references."""
    # Pass None as a tool (invalid)
    invalid_tools = [None, Mock(name="valid_tool")]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        # This should handle gracefully or raise appropriate error
        with patch("deepagents_integration.factory.create_deep_agent") as mock_create:
            mock_create.side_effect = ValueError("Invalid tool configuration")

            with pytest.raises(ValueError, match="Invalid tool configuration"):
                await agent_factory.create_agent(basic_agent_config, tools=invalid_tools)


# Model Provider Registration Tests


def test_agent_factory_has_model_providers(agent_factory):
    """Test that AgentFactory has registered model providers."""
    assert "anthropic" in agent_factory.model_providers
    assert "openai" in agent_factory.model_providers


def test_anthropic_model_creator(agent_factory):
    """Test the Anthropic model creator method."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.ChatAnthropic") as mock_anthropic:
            mock_llm = Mock()
            mock_anthropic.return_value = mock_llm

            llm = agent_factory._create_anthropic_model(
                "claude-3-5-sonnet-20241022", 0.7, 4096
            )

            assert llm == mock_llm
            mock_anthropic.assert_called_once()


def test_openai_model_creator(agent_factory):
    """Test the OpenAI model creator method."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.ChatOpenAI") as mock_openai:
            mock_llm = Mock()
            mock_openai.return_value = mock_llm

            llm = agent_factory._create_openai_model("gpt-4", 0.8, 2048)

            assert llm == mock_llm
            mock_openai.assert_called_once()


# System Prompt Tests


@pytest.mark.asyncio
async def test_create_agent_with_system_prompt(agent_factory, basic_agent_config):
    """Test that system prompt is properly passed to agent."""
    custom_prompt = "You are a specialized coding assistant with expertise in Python."
    basic_agent_config.system_prompt = custom_prompt

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.create_deep_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_create.return_value = mock_agent

            await agent_factory.create_agent(basic_agent_config)

            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["system_prompt"] == custom_prompt


@pytest.mark.asyncio
async def test_create_agent_without_system_prompt(agent_factory, basic_agent_config):
    """Test creating an agent without a system prompt."""
    basic_agent_config.system_prompt = None

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(basic_agent_config)

        assert agent is not None
