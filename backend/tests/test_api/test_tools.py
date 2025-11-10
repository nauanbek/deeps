"""
Tests for Tool API endpoints.

Tests all REST endpoints for tool CRUD operations.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.tool_service import tool_service
from schemas.tool import ToolCreate


# ============================================================================
# Create Tool Endpoint Tests
# ============================================================================


def test_create_tool_success(client: TestClient):
    """Test POST /api/v1/tools/ - successful creation."""
    response = client.post(
        "/api/v1/tools/",
        json={
            "name": "test_tool",
            "description": "A test tool",
            "tool_type": "custom",
            "schema_definition": {"input": {}, "output": {}},
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_tool"
    assert data["description"] == "A test tool"
    assert data["tool_type"] == "custom"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


def test_create_tool_minimal_fields(client: TestClient):
    """Test creating a tool with minimal required fields."""
    response = client.post(
        "/api/v1/tools/",
        json={
            "name": "minimal_tool",
            "tool_type": "builtin",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "minimal_tool"
    assert data["tool_type"] == "builtin"
    assert data["description"] is None


def test_create_tool_with_configuration(client: TestClient):
    """Test creating a tool with configuration."""
    response = client.post(
        "/api/v1/tools/",
        json={
            "name": "configured_tool",
            "tool_type": "custom",
            "configuration": {"api_key": "test-key", "timeout": 30},
            "schema_definition": {"input": {"param": "string"}},
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["configuration"] == {"api_key": "test-key", "timeout": 30}
    assert data["schema_definition"] == {"input": {"param": "string"}}


def test_create_tool_duplicate_name(client: TestClient):
    """Test creating a tool with duplicate name fails."""
    # Create first tool
    client.post(
        "/api/v1/tools/",
        json={"name": "duplicate_tool", "tool_type": "builtin"},
    )

    # Attempt duplicate
    response = client.post(
        "/api/v1/tools/",
        json={"name": "duplicate_tool", "tool_type": "custom"},
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_tool_invalid_data(client: TestClient):
    """Test creating a tool with invalid data."""
    response = client.post(
        "/api/v1/tools/",
        json={
            "name": "",  # Empty name
            "tool_type": "builtin",
        },
    )

    assert response.status_code == 422  # Validation error


def test_create_tool_missing_required_field(client: TestClient):
    """Test creating a tool without required fields."""
    response = client.post(
        "/api/v1/tools/",
        json={
            "name": "incomplete_tool",
            # Missing tool_type
        },
    )

    assert response.status_code == 422


# ============================================================================
# List Tools Endpoint Tests
# ============================================================================


def test_list_tools_empty(client: TestClient):
    """Test GET /api/v1/tools/ - empty list."""
    response = client.get("/api/v1/tools/")

    assert response.status_code == 200
    data = response.json()
    assert data["tools"] == []
    assert data["total"] == 0
    assert data["page"] == 1


def test_list_tools_all(client: TestClient):
    """Test listing all tools."""
    # Create test tools
    client.post("/api/v1/tools/", json={"name": "tool1", "tool_type": "builtin"})
    client.post("/api/v1/tools/", json={"name": "tool2", "tool_type": "custom"})
    client.post("/api/v1/tools/", json={"name": "tool3", "tool_type": "langgraph"})

    response = client.get("/api/v1/tools/")

    assert response.status_code == 200
    data = response.json()
    assert len(data["tools"]) == 3
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 100


def test_list_tools_filter_by_type(client: TestClient):
    """Test filtering tools by type."""
    # Create tools
    client.post("/api/v1/tools/", json={"name": "builtin1", "tool_type": "builtin"})
    client.post("/api/v1/tools/", json={"name": "builtin2", "tool_type": "builtin"})
    client.post("/api/v1/tools/", json={"name": "custom1", "tool_type": "custom"})

    # Filter by builtin
    response = client.get("/api/v1/tools/?tool_type=builtin")

    assert response.status_code == 200
    data = response.json()
    assert len(data["tools"]) == 2
    assert all(t["tool_type"] == "builtin" for t in data["tools"])
    assert data["total"] == 2


def test_list_tools_search(client: TestClient):
    """Test searching tools by name and description."""
    # Create tools
    client.post(
        "/api/v1/tools/",
        json={"name": "calculator", "description": "Math operations", "tool_type": "builtin"},
    )
    client.post(
        "/api/v1/tools/",
        json={"name": "web_search", "description": "Search the web", "tool_type": "custom"},
    )

    # Search by name
    response = client.get("/api/v1/tools/?search=calc")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "calculator"

    # Search by description
    response = client.get("/api/v1/tools/?search=search")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "web_search"


def test_list_tools_filter_by_active(client: TestClient):
    """Test filtering tools by active status."""
    # Create tools
    response1 = client.post("/api/v1/tools/", json={"name": "active", "tool_type": "builtin"})
    tool1_id = response1.json()["id"]

    response2 = client.post("/api/v1/tools/", json={"name": "inactive", "tool_type": "builtin"})
    tool2_id = response2.json()["id"]

    # Deactivate second tool
    client.put(f"/api/v1/tools/{tool2_id}", json={"is_active": False})

    # Filter active tools
    response = client.get("/api/v1/tools/?is_active=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "active"

    # Filter inactive tools
    response = client.get("/api/v1/tools/?is_active=false")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "inactive"


def test_list_tools_pagination(client: TestClient):
    """Test pagination with skip and limit."""
    # Create 5 tools
    for i in range(5):
        client.post("/api/v1/tools/", json={"name": f"tool_{i}", "tool_type": "builtin"})

    # First page
    response = client.get("/api/v1/tools/?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["has_next"] is True

    # Second page
    response = client.get("/api/v1/tools/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools"]) == 2
    assert data["page"] == 2
    assert data["has_next"] is True

    # Last page
    response = client.get("/api/v1/tools/?skip=4&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools"]) == 1
    assert data["has_next"] is False


def test_list_tools_combined_filters(client: TestClient):
    """Test combining multiple filters."""
    # Create tools
    client.post(
        "/api/v1/tools/",
        json={"name": "calc_builtin", "description": "Calculator", "tool_type": "builtin"},
    )
    client.post(
        "/api/v1/tools/",
        json={"name": "search_custom", "description": "Search", "tool_type": "custom"},
    )

    # Combine type and search
    response = client.get("/api/v1/tools/?tool_type=builtin&search=calc")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "calc_builtin"


def test_list_tools_invalid_pagination(client: TestClient):
    """Test invalid pagination parameters."""
    # Negative skip
    response = client.get("/api/v1/tools/?skip=-1")
    assert response.status_code == 422

    # Limit too large
    response = client.get("/api/v1/tools/?limit=10000")
    assert response.status_code == 422

    # Invalid limit
    response = client.get("/api/v1/tools/?limit=0")
    assert response.status_code == 422


# ============================================================================
# Get Tool Categories Endpoint Tests
# ============================================================================


def test_get_tool_categories_empty(client: TestClient):
    """Test GET /api/v1/tools/categories - empty."""
    response = client.get("/api/v1/tools/categories")

    assert response.status_code == 200
    data = response.json()
    assert data["categories"] == []


def test_get_tool_categories(client: TestClient):
    """Test getting tool categories."""
    # Create tools of different types
    client.post("/api/v1/tools/", json={"name": "builtin1", "tool_type": "builtin"})
    client.post("/api/v1/tools/", json={"name": "builtin2", "tool_type": "builtin"})
    client.post("/api/v1/tools/", json={"name": "custom1", "tool_type": "custom"})
    client.post("/api/v1/tools/", json={"name": "langgraph1", "tool_type": "langgraph"})

    response = client.get("/api/v1/tools/categories")

    assert response.status_code == 200
    data = response.json()
    assert len(data["categories"]) == 3
    assert set(data["categories"]) == {"builtin", "custom", "langgraph"}


# ============================================================================
# Get Tool By ID Endpoint Tests
# ============================================================================


def test_get_tool_success(client: TestClient):
    """Test GET /api/v1/tools/{id} - successful retrieval."""
    # Create a tool
    create_response = client.post(
        "/api/v1/tools/",
        json={"name": "get_test", "description": "Test tool", "tool_type": "builtin"},
    )
    tool_id = create_response.json()["id"]

    # Retrieve it
    response = client.get(f"/api/v1/tools/{tool_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tool_id
    assert data["name"] == "get_test"
    assert data["description"] == "Test tool"


def test_get_tool_not_found(client: TestClient):
    """Test getting a non-existent tool."""
    response = client.get("/api/v1/tools/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_tool_invalid_id(client: TestClient):
    """Test getting a tool with invalid ID format."""
    response = client.get("/api/v1/tools/invalid")

    assert response.status_code == 422


# ============================================================================
# Update Tool Endpoint Tests
# ============================================================================


def test_update_tool_success(client: TestClient):
    """Test PUT /api/v1/tools/{id} - successful update."""
    # Create a tool
    create_response = client.post(
        "/api/v1/tools/",
        json={"name": "original", "description": "Original desc", "tool_type": "builtin"},
    )
    tool_id = create_response.json()["id"]

    # Update it
    response = client.put(
        f"/api/v1/tools/{tool_id}",
        json={
            "name": "updated",
            "description": "Updated description",
            "configuration": {"new_config": "value"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated"
    assert data["description"] == "Updated description"
    assert data["configuration"] == {"new_config": "value"}
    assert data["tool_type"] == "builtin"  # Unchanged


def test_update_tool_partial(client: TestClient):
    """Test partial update of a tool."""
    # Create a tool
    create_response = client.post(
        "/api/v1/tools/",
        json={
            "name": "partial_test",
            "description": "Original",
            "tool_type": "custom",
            "configuration": {"key": "value"},
        },
    )
    tool_id = create_response.json()["id"]

    # Update only description
    response = client.put(
        f"/api/v1/tools/{tool_id}",
        json={"description": "New description only"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "partial_test"  # Unchanged
    assert data["description"] == "New description only"
    assert data["tool_type"] == "custom"  # Unchanged
    assert data["configuration"] == {"key": "value"}  # Unchanged


def test_update_tool_deactivate(client: TestClient):
    """Test deactivating a tool via update."""
    # Create a tool
    create_response = client.post(
        "/api/v1/tools/",
        json={"name": "deactivate_test", "tool_type": "builtin"},
    )
    tool_id = create_response.json()["id"]

    # Deactivate
    response = client.put(f"/api/v1/tools/{tool_id}", json={"is_active": False})

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


def test_update_tool_not_found(client: TestClient):
    """Test updating a non-existent tool."""
    response = client.put("/api/v1/tools/99999", json={"name": "new_name"})

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_tool_invalid_data(client: TestClient):
    """Test updating a tool with invalid data."""
    # Create a tool
    create_response = client.post(
        "/api/v1/tools/",
        json={"name": "update_invalid_test", "tool_type": "builtin"},
    )
    tool_id = create_response.json()["id"]

    # Update with invalid name
    response = client.put(f"/api/v1/tools/{tool_id}", json={"name": ""})

    assert response.status_code == 422


# ============================================================================
# Delete Tool Endpoint Tests
# ============================================================================


def test_delete_tool_soft_success(client: TestClient):
    """Test DELETE /api/v1/tools/{id} - soft delete."""
    # Create a tool
    create_response = client.post(
        "/api/v1/tools/",
        json={"name": "delete_test", "tool_type": "builtin"},
    )
    tool_id = create_response.json()["id"]

    # Soft delete (default)
    response = client.delete(f"/api/v1/tools/{tool_id}")

    assert response.status_code == 204

    # Tool should still exist but be inactive
    get_response = client.get(f"/api/v1/tools/{tool_id}")
    assert get_response.status_code == 200
    assert get_response.json()["is_active"] is False


def test_delete_tool_hard_success(client: TestClient):
    """Test DELETE /api/v1/tools/{id} - hard delete."""
    # Create a tool
    create_response = client.post(
        "/api/v1/tools/",
        json={"name": "hard_delete_test", "tool_type": "builtin"},
    )
    tool_id = create_response.json()["id"]

    # Hard delete
    response = client.delete(f"/api/v1/tools/{tool_id}?hard_delete=true")

    assert response.status_code == 204

    # Tool should not exist
    get_response = client.get(f"/api/v1/tools/{tool_id}")
    assert get_response.status_code == 404


def test_delete_tool_not_found(client: TestClient):
    """Test deleting a non-existent tool."""
    response = client.delete("/api/v1/tools/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# ============================================================================
# Integration Tests
# ============================================================================


def test_tool_lifecycle(client: TestClient):
    """Test complete tool lifecycle: create -> update -> list -> delete."""
    # Create
    create_response = client.post(
        "/api/v1/tools/",
        json={
            "name": "lifecycle_tool",
            "description": "Lifecycle test",
            "tool_type": "custom",
            "configuration": {"version": "1.0"},
        },
    )
    assert create_response.status_code == 201
    tool_id = create_response.json()["id"]

    # Update
    update_response = client.put(
        f"/api/v1/tools/{tool_id}",
        json={"configuration": {"version": "2.0"}},
    )
    assert update_response.status_code == 200
    assert update_response.json()["configuration"]["version"] == "2.0"

    # List (should contain our tool)
    list_response = client.get("/api/v1/tools/")
    assert list_response.status_code == 200
    assert any(t["id"] == tool_id for t in list_response.json()["tools"])

    # Delete
    delete_response = client.delete(f"/api/v1/tools/{tool_id}")
    assert delete_response.status_code == 204

    # Verify soft delete
    get_response = client.get(f"/api/v1/tools/{tool_id}")
    assert get_response.status_code == 200
    assert get_response.json()["is_active"] is False


def test_multiple_tools_different_types(client: TestClient):
    """Test creating and managing multiple tools of different types."""
    tools_data = [
        {"name": "builtin_calc", "tool_type": "builtin", "description": "Calculator"},
        {"name": "custom_api", "tool_type": "custom", "description": "API tool"},
        {"name": "langgraph_flow", "tool_type": "langgraph", "description": "Flow tool"},
    ]

    created_ids = []
    for tool_data in tools_data:
        response = client.post("/api/v1/tools/", json=tool_data)
        assert response.status_code == 201
        created_ids.append(response.json()["id"])

    # List all tools
    response = client.get("/api/v1/tools/")
    assert response.status_code == 200
    assert response.json()["total"] == 3

    # Get categories
    response = client.get("/api/v1/tools/categories")
    assert response.status_code == 200
    assert len(response.json()["categories"]) == 3
