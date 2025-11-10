"""
Tests for Tool service layer.

Tests all CRUD operations, filtering, search, and error handling.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.tool import Tool
from schemas.tool import ToolCreate, ToolUpdate
from services.tool_service import tool_service


# ============================================================================
# Create Tool Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_tool_success(db_session: AsyncSession, test_user_id: int):
    """Test creating a tool successfully."""
    tool_data = ToolCreate(
        name="calculator",
        description="Performs calculations",
        tool_type="builtin",
        schema_definition={
            "input": {"expression": "string"},
            "output": {"result": "number"},
        },
    )

    tool = await tool_service.create_tool(db_session, tool_data, created_by_id=test_user_id)

    assert tool.id is not None
    assert tool.name == "calculator"
    assert tool.description == "Performs calculations"
    assert tool.tool_type == "builtin"
    assert tool.is_active is True
    assert tool.created_by_id == test_user_id
    assert tool.schema_definition == {
        "input": {"expression": "string"},
        "output": {"result": "number"},
    }
    assert tool.configuration == {}


@pytest.mark.asyncio
async def test_create_tool_with_configuration(db_session: AsyncSession, test_user_id: int):
    """Test creating a tool with configuration."""
    tool_data = ToolCreate(
        name="api_tool",
        description="API integration tool",
        tool_type="custom",
        configuration={"api_key": "test-key", "timeout": 30},
        schema_definition={"input": {}, "output": {}},
    )

    tool = await tool_service.create_tool(db_session, tool_data, created_by_id=test_user_id)

    assert tool.configuration == {"api_key": "test-key", "timeout": 30}
    assert tool.tool_type == "custom"


@pytest.mark.asyncio
async def test_create_duplicate_tool_fails(db_session: AsyncSession, test_user_id: int):
    """Test that duplicate tool names are rejected."""
    tool_data = ToolCreate(
        name="test_tool",
        description="Test tool",
        tool_type="custom",
    )

    # Create first tool
    await tool_service.create_tool(db_session, tool_data, created_by_id=test_user_id)

    # Attempt to create duplicate should fail
    with pytest.raises(ValueError, match="already exists"):
        await tool_service.create_tool(db_session, tool_data, created_by_id=test_user_id)


@pytest.mark.asyncio
async def test_create_tool_minimal_fields(db_session: AsyncSession, test_user_id: int):
    """Test creating a tool with minimal required fields."""
    tool_data = ToolCreate(
        name="minimal_tool",
        tool_type="builtin",
    )

    tool = await tool_service.create_tool(db_session, tool_data, created_by_id=test_user_id)

    assert tool.name == "minimal_tool"
    assert tool.description is None
    assert tool.configuration == {}
    assert tool.schema_definition == {}


# ============================================================================
# Get Tool Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_tool_success(db_session: AsyncSession, test_user_id: int):
    """Test retrieving a tool by ID."""
    # Create a tool
    tool_data = ToolCreate(name="get_test", tool_type="builtin")
    created_tool = await tool_service.create_tool(
        db_session, tool_data, created_by_id=test_user_id
    )

    # Retrieve it
    tool = await tool_service.get_tool(db_session, created_tool.id)

    assert tool is not None
    assert tool.id == created_tool.id
    assert tool.name == "get_test"


@pytest.mark.asyncio
async def test_get_tool_not_found(db_session: AsyncSession):
    """Test retrieving a non-existent tool."""
    tool = await tool_service.get_tool(db_session, 99999)
    assert tool is None


# ============================================================================
# List Tools Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_tools_empty(db_session: AsyncSession):
    """Test listing tools when database is empty."""
    tools = await tool_service.list_tools(db_session)
    assert tools == []


@pytest.mark.asyncio
async def test_list_tools_all(db_session: AsyncSession, test_user_id: int):
    """Test listing all tools."""
    # Create multiple tools
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="tool1", tool_type="builtin"),
        created_by_id=test_user_id,
    )
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="tool2", tool_type="custom"),
        created_by_id=test_user_id,
    )
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="tool3", tool_type="langgraph"),
        created_by_id=test_user_id,
    )

    tools = await tool_service.list_tools(db_session)

    assert len(tools) == 3
    # Verify all tools are present (order may vary in SQLite)
    tool_names = {t.name for t in tools}
    assert tool_names == {"tool1", "tool2", "tool3"}


@pytest.mark.asyncio
async def test_list_tools_filter_by_type(db_session: AsyncSession, test_user_id: int):
    """Test filtering tools by type."""
    # Create tools of different types
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="builtin1", tool_type="builtin"),
        created_by_id=test_user_id,
    )
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="builtin2", tool_type="builtin"),
        created_by_id=test_user_id,
    )
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="custom1", tool_type="custom"),
        created_by_id=test_user_id,
    )

    # Filter by builtin
    builtin_tools = await tool_service.list_tools(db_session, tool_type="builtin")
    assert len(builtin_tools) == 2
    assert all(t.tool_type == "builtin" for t in builtin_tools)

    # Filter by custom
    custom_tools = await tool_service.list_tools(db_session, tool_type="custom")
    assert len(custom_tools) == 1
    assert custom_tools[0].tool_type == "custom"


@pytest.mark.asyncio
async def test_list_tools_search(db_session: AsyncSession, test_user_id: int):
    """Test searching tools by name and description."""
    # Create tools with different names and descriptions
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="calculator", description="Math operations", tool_type="builtin"),
        created_by_id=test_user_id,
    )
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="web_search", description="Search the web", tool_type="custom"),
        created_by_id=test_user_id,
    )
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="file_reader", description="Read files", tool_type="builtin"),
        created_by_id=test_user_id,
    )

    # Search by name
    calc_tools = await tool_service.list_tools(db_session, search="calc")
    assert len(calc_tools) == 1
    assert calc_tools[0].name == "calculator"

    # Search by description
    search_tools = await tool_service.list_tools(db_session, search="search")
    assert len(search_tools) == 1
    assert search_tools[0].name == "web_search"

    # Case-insensitive search
    file_tools = await tool_service.list_tools(db_session, search="FILE")
    assert len(file_tools) == 1
    assert file_tools[0].name == "file_reader"


@pytest.mark.asyncio
async def test_list_tools_filter_by_active(db_session: AsyncSession, test_user_id: int):
    """Test filtering tools by active status."""
    # Create active and inactive tools
    tool1 = await tool_service.create_tool(
        db_session,
        ToolCreate(name="active_tool", tool_type="builtin"),
        created_by_id=test_user_id,
    )
    tool2 = await tool_service.create_tool(
        db_session,
        ToolCreate(name="inactive_tool", tool_type="builtin"),
        created_by_id=test_user_id,
    )

    # Deactivate tool2
    tool2.is_active = False
    await db_session.commit()

    # Filter active tools
    active_tools = await tool_service.list_tools(db_session, is_active=True)
    assert len(active_tools) == 1
    assert active_tools[0].name == "active_tool"

    # Filter inactive tools
    inactive_tools = await tool_service.list_tools(db_session, is_active=False)
    assert len(inactive_tools) == 1
    assert inactive_tools[0].name == "inactive_tool"


@pytest.mark.asyncio
async def test_list_tools_pagination(db_session: AsyncSession, test_user_id: int):
    """Test pagination with skip and limit."""
    # Create 5 tools
    for i in range(5):
        await tool_service.create_tool(
            db_session,
            ToolCreate(name=f"tool_{i}", tool_type="builtin"),
            created_by_id=test_user_id,
        )

    # First page (2 items)
    page1 = await tool_service.list_tools(db_session, skip=0, limit=2)
    assert len(page1) == 2

    # Second page (2 items)
    page2 = await tool_service.list_tools(db_session, skip=2, limit=2)
    assert len(page2) == 2

    # Third page (1 item)
    page3 = await tool_service.list_tools(db_session, skip=4, limit=2)
    assert len(page3) == 1

    # Verify no overlap
    page1_ids = {t.id for t in page1}
    page2_ids = {t.id for t in page2}
    assert len(page1_ids.intersection(page2_ids)) == 0


@pytest.mark.asyncio
async def test_list_tools_combined_filters(db_session: AsyncSession, test_user_id: int):
    """Test combining multiple filters."""
    # Create various tools
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="calc_builtin", description="Calculator", tool_type="builtin"),
        created_by_id=test_user_id,
    )
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="search_custom", description="Search tool", tool_type="custom"),
        created_by_id=test_user_id,
    )
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="parser_builtin", description="Parse data", tool_type="builtin"),
        created_by_id=test_user_id,
    )

    # Combine type and search filters
    results = await tool_service.list_tools(
        db_session, tool_type="builtin", search="calc"
    )
    assert len(results) == 1
    assert results[0].name == "calc_builtin"


# ============================================================================
# Update Tool Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_tool_success(db_session: AsyncSession, test_user_id: int):
    """Test updating a tool."""
    # Create a tool
    tool = await tool_service.create_tool(
        db_session,
        ToolCreate(name="original_name", description="Original", tool_type="builtin"),
        created_by_id=test_user_id,
    )

    # Update it
    update_data = ToolUpdate(
        name="updated_name",
        description="Updated description",
        configuration={"new_config": "value"},
    )
    updated_tool = await tool_service.update_tool(db_session, tool.id, update_data)

    assert updated_tool.name == "updated_name"
    assert updated_tool.description == "Updated description"
    assert updated_tool.configuration == {"new_config": "value"}
    assert updated_tool.tool_type == "builtin"  # Unchanged


@pytest.mark.asyncio
async def test_update_tool_partial(db_session: AsyncSession, test_user_id: int):
    """Test partial update of a tool."""
    # Create a tool
    tool = await tool_service.create_tool(
        db_session,
        ToolCreate(
            name="tool_name",
            description="Description",
            tool_type="custom",
            configuration={"key": "value"},
        ),
        created_by_id=test_user_id,
    )

    # Update only description
    update_data = ToolUpdate(description="New description only")
    updated_tool = await tool_service.update_tool(db_session, tool.id, update_data)

    assert updated_tool.name == "tool_name"  # Unchanged
    assert updated_tool.description == "New description only"
    assert updated_tool.tool_type == "custom"  # Unchanged
    assert updated_tool.configuration == {"key": "value"}  # Unchanged


@pytest.mark.asyncio
async def test_update_tool_not_found(db_session: AsyncSession):
    """Test updating a non-existent tool."""
    update_data = ToolUpdate(name="new_name")

    with pytest.raises(ValueError, match="not found"):
        await tool_service.update_tool(db_session, 99999, update_data)


@pytest.mark.asyncio
async def test_update_tool_deactivate(db_session: AsyncSession, test_user_id: int):
    """Test deactivating a tool via update."""
    # Create a tool
    tool = await tool_service.create_tool(
        db_session,
        ToolCreate(name="active_tool", tool_type="builtin"),
        created_by_id=test_user_id,
    )
    assert tool.is_active is True

    # Deactivate it
    update_data = ToolUpdate(is_active=False)
    updated_tool = await tool_service.update_tool(db_session, tool.id, update_data)

    assert updated_tool.is_active is False


# ============================================================================
# Delete Tool Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_tool_soft(db_session: AsyncSession, test_user_id: int):
    """Test soft deleting a tool (default behavior)."""
    # Create a tool
    tool = await tool_service.create_tool(
        db_session,
        ToolCreate(name="delete_test", tool_type="builtin"),
        created_by_id=test_user_id,
    )

    # Soft delete
    result = await tool_service.delete_tool(db_session, tool.id, hard_delete=False)
    assert result is True

    # Tool should still exist but be inactive
    deleted_tool = await tool_service.get_tool(db_session, tool.id)
    assert deleted_tool is not None
    assert deleted_tool.is_active is False


@pytest.mark.asyncio
async def test_delete_tool_hard(db_session: AsyncSession, test_user_id: int):
    """Test hard deleting a tool (permanent deletion)."""
    # Create a tool
    tool = await tool_service.create_tool(
        db_session,
        ToolCreate(name="hard_delete_test", tool_type="builtin"),
        created_by_id=test_user_id,
    )

    # Hard delete
    result = await tool_service.delete_tool(db_session, tool.id, hard_delete=True)
    assert result is True

    # Tool should not exist
    deleted_tool = await tool_service.get_tool(db_session, tool.id)
    assert deleted_tool is None


@pytest.mark.asyncio
async def test_delete_tool_not_found(db_session: AsyncSession):
    """Test deleting a non-existent tool."""
    result = await tool_service.delete_tool(db_session, 99999)
    assert result is False


# ============================================================================
# Get Tool Categories Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_tool_categories_empty(db_session: AsyncSession):
    """Test getting categories when no tools exist."""
    categories = await tool_service.get_tool_categories(db_session)
    assert categories == []


@pytest.mark.asyncio
async def test_get_tool_categories(db_session: AsyncSession, test_user_id: int):
    """Test getting unique tool categories."""
    # Create tools of different types
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="builtin1", tool_type="builtin"),
        created_by_id=test_user_id,
    )
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="builtin2", tool_type="builtin"),
        created_by_id=test_user_id,
    )
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="custom1", tool_type="custom"),
        created_by_id=test_user_id,
    )
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="langgraph1", tool_type="langgraph"),
        created_by_id=test_user_id,
    )

    categories = await tool_service.get_tool_categories(db_session)

    # Should have 3 unique categories
    assert len(categories) == 3
    assert set(categories) == {"builtin", "custom", "langgraph"}


# ============================================================================
# Count Tools Tests
# ============================================================================


@pytest.mark.asyncio
async def test_count_tools_all(db_session: AsyncSession, test_user_id: int):
    """Test counting all tools."""
    # Create tools
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="tool1", tool_type="builtin"),
        created_by_id=test_user_id,
    )
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="tool2", tool_type="custom"),
        created_by_id=test_user_id,
    )

    count = await tool_service.count_tools(db_session)
    assert count == 2


@pytest.mark.asyncio
async def test_count_tools_with_filters(db_session: AsyncSession, test_user_id: int):
    """Test counting tools with filters."""
    # Create tools
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="calc", description="Calculator", tool_type="builtin"),
        created_by_id=test_user_id,
    )
    await tool_service.create_tool(
        db_session,
        ToolCreate(name="search", description="Search", tool_type="custom"),
        created_by_id=test_user_id,
    )

    # Count by type
    builtin_count = await tool_service.count_tools(db_session, tool_type="builtin")
    assert builtin_count == 1

    # Count by search
    calc_count = await tool_service.count_tools(db_session, search="calc")
    assert calc_count == 1
