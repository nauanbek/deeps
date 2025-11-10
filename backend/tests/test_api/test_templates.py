"""
Comprehensive tests for Template API endpoints.

Tests all REST API endpoints for template management including:
- Creating templates
- Listing templates with pagination and filtering
- Getting template by ID
- Updating templates
- Deleting templates (soft and hard)
- Special operations (categories, featured, popular, search)
- Import/export functionality
- Creating agents from templates
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.template import Template
from models.tool import Tool
from models.user import User


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for API operations."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_here",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_tool(db_session: AsyncSession, test_user: User) -> Tool:
    """Create a sample tool for template tool_ids."""
    tool = Tool(
        name="test_tool",
        description="A test tool",
        tool_type="builtin",
        configuration={"api_key": "test"},
        schema_definition={"type": "object"},
        created_by_id=test_user.id,
        is_active=True,
    )
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)
    return tool


@pytest.fixture
async def sample_template(db_session: AsyncSession, test_user: User, sample_tool: Tool) -> Template:
    """Create a sample template for testing."""
    template = Template(
        name="Test Template",
        description="A test template for API testing",
        category="research",
        tags=["test", "research"],
        config_template={
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "system_prompt": "You are a helpful assistant.",
            "temperature": 0.7,
            "max_tokens": 4096,
            "planning_enabled": True,
            "filesystem_enabled": False,
            "tool_ids": [sample_tool.id],
            "additional_config": {"max_iterations": 10},
        },
        is_public=True,
        is_featured=False,
        use_count=0,
        created_by_id=test_user.id,
        is_active=True,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


# ============================================================================
# POST /api/v1/templates - Create Template
# ============================================================================


def test_create_template_endpoint_success(client: TestClient, test_user: User, sample_tool: Tool):
    """Test successful template creation via API."""
    template_data = {
        "name": "New Template",
        "description": "A new template for testing",
        "category": "research",
        "tags": ["test", "new"],
        "config_template": {
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "system_prompt": "You are a research assistant.",
            "temperature": 0.7,
            "max_tokens": 4096,
            "planning_enabled": True,
            "filesystem_enabled": True,
            "tool_ids": [sample_tool.id],
            "additional_config": {"max_iterations": 15},
        },
        "is_public": True,
        "is_featured": False,
    }

    response = client.post("/api/v1/templates/", json=template_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == template_data["name"]
    assert data["description"] == template_data["description"]
    assert data["category"] == template_data["category"]
    assert data["tags"] == template_data["tags"]
    assert data["is_public"] == template_data["is_public"]
    assert data["is_featured"] == template_data["is_featured"]
    assert data["use_count"] == 0
    assert data["id"] is not None
    assert data["created_at"] is not None


def test_create_template_endpoint_duplicate_name(client: TestClient, sample_template: Template):
    """Test template creation fails with duplicate name."""
    template_data = {
        "name": sample_template.name,  # Duplicate name
        "description": "Different description",
        "category": "coding",
        "tags": ["test"],
        "config_template": {
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "system_prompt": "Test",
            "temperature": 0.7,
            "max_tokens": 4096,
            "planning_enabled": False,
            "filesystem_enabled": False,
            "tool_ids": [],
            "additional_config": {},
        },
        "is_public": True,
        "is_featured": False,
    }

    response = client.post("/api/v1/templates/", json=template_data)

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_create_template_endpoint_invalid_tool_ids(client: TestClient):
    """Test template creation fails with invalid tool IDs."""
    template_data = {
        "name": "Invalid Template",
        "description": "Template with invalid tool IDs",
        "category": "research",
        "tags": ["test"],
        "config_template": {
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "system_prompt": "Test",
            "temperature": 0.7,
            "max_tokens": 4096,
            "planning_enabled": False,
            "filesystem_enabled": False,
            "tool_ids": [99999],  # Non-existent tool
            "additional_config": {},
        },
        "is_public": True,
        "is_featured": False,
    }

    response = client.post("/api/v1/templates/", json=template_data)

    assert response.status_code == 400
    assert "99999" in response.json()["detail"]


# ============================================================================
# GET /api/v1/templates - List Templates
# ============================================================================


def test_list_templates_endpoint_success(client: TestClient, sample_template: Template):
    """Test successful template listing via API."""
    response = client.get("/api/v1/templates/")

    assert response.status_code == 200
    data = response.json()
    assert "templates" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "has_next" in data
    assert len(data["templates"]) > 0


def test_list_templates_endpoint_pagination(client: TestClient, test_user: User, sample_tool: Tool):
    """Test template listing pagination."""
    # Create multiple templates
    for i in range(5):
        template = Template(
            name=f"Template {i}",
            description=f"Description {i}",
            category="research",
            tags=["test"],
            config_template={
                "model_provider": "anthropic",
                "model_name": "claude-3-5-sonnet-20241022",
                "system_prompt": "Test",
                "temperature": 0.7,
                "max_tokens": 4096,
                "planning_enabled": False,
                "filesystem_enabled": False,
                "tool_ids": [],
                "additional_config": {},
            },
            is_public=True,
            is_featured=False,
            created_by_id=test_user.id,
            is_active=True,
        )

    response = client.get("/api/v1/templates/?skip=0&limit=3")

    assert response.status_code == 200
    data = response.json()
    assert len(data["templates"]) <= 3
    assert data["page_size"] == 3


def test_list_templates_endpoint_filter_by_category(client: TestClient, test_user: User, sample_tool: Tool):
    """Test template listing filtered by category."""
    response = client.get("/api/v1/templates/?category=research")

    assert response.status_code == 200
    data = response.json()
    # All returned templates should be in research category
    for template in data["templates"]:
        assert template["category"] == "research"


async def test_list_templates_endpoint_search(client: TestClient, test_user: User, sample_tool: Tool, db_session: AsyncSession):
    """Test template search functionality."""
    # Create a template with searchable content
    template = Template(
        name="Python Developer Assistant",
        description="Specialized in Python development",
        category="coding",
        tags=["python", "coding"],
        config_template={
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "system_prompt": "Test",
            "temperature": 0.7,
            "max_tokens": 4096,
            "planning_enabled": False,
            "filesystem_enabled": False,
            "tool_ids": [],
            "additional_config": {},
        },
        is_public=True,
        is_featured=False,
        created_by_id=test_user.id,
        is_active=True,
    )
    db_session.add(template)
    await db_session.commit()

    response = client.get("/api/v1/templates/?search=python")

    assert response.status_code == 200
    data = response.json()
    # At least one result containing "python"
    assert data["total"] >= 1


# ============================================================================
# GET /api/v1/templates/{template_id} - Get Template
# ============================================================================


def test_get_template_endpoint_success(client: TestClient, sample_template: Template):
    """Test successful template retrieval via API."""
    response = client.get(f"/api/v1/templates/{sample_template.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_template.id
    assert data["name"] == sample_template.name


def test_get_template_endpoint_not_found(client: TestClient):
    """Test template retrieval fails with invalid ID."""
    response = client.get("/api/v1/templates/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ============================================================================
# PUT /api/v1/templates/{template_id} - Update Template
# ============================================================================


def test_update_template_endpoint_success(client: TestClient, sample_template: Template):
    """Test successful template update via API."""
    update_data = {
        "name": "Updated Template Name",
        "description": "Updated description",
    }

    response = client.put(f"/api/v1/templates/{sample_template.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]


def test_update_template_endpoint_not_found(client: TestClient):
    """Test template update fails with invalid ID."""
    update_data = {"name": "Updated Name"}

    response = client.put("/api/v1/templates/99999", json=update_data)

    assert response.status_code == 404


# ============================================================================
# DELETE /api/v1/templates/{template_id} - Delete Template
# ============================================================================


def test_delete_template_endpoint_soft(client: TestClient, sample_template: Template):
    """Test soft delete of template via API."""
    response = client.delete(f"/api/v1/templates/{sample_template.id}")

    assert response.status_code == 204

    # Verify template is soft deleted
    get_response = client.get(f"/api/v1/templates/{sample_template.id}")
    assert get_response.status_code == 404


def test_delete_template_endpoint_not_found(client: TestClient):
    """Test template deletion fails with invalid ID."""
    response = client.delete("/api/v1/templates/99999")

    assert response.status_code == 404


# ============================================================================
# GET /api/v1/templates/categories - Get Categories
# ============================================================================


def test_get_categories_endpoint(client: TestClient, sample_template: Template):
    """Test getting categories via API."""
    response = client.get("/api/v1/templates/categories")

    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "total" in data
    assert isinstance(data["categories"], list)


# ============================================================================
# GET /api/v1/templates/featured - Get Featured Templates
# ============================================================================


def test_get_featured_templates_endpoint(client: TestClient, test_user: User, sample_tool: Tool):
    """Test getting featured templates via API."""
    # Create a featured template
    template = Template(
        name="Featured Template",
        description="A featured template",
        category="research",
        tags=["featured"],
        config_template={
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "system_prompt": "Test",
            "temperature": 0.7,
            "max_tokens": 4096,
            "planning_enabled": False,
            "filesystem_enabled": False,
            "tool_ids": [],
            "additional_config": {},
        },
        is_public=True,
        is_featured=True,  # Featured
        created_by_id=test_user.id,
        is_active=True,
    )

    response = client.get("/api/v1/templates/featured")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # All returned templates should be featured
    for template in data:
        assert template["is_featured"] is True


# ============================================================================
# GET /api/v1/templates/popular - Get Popular Templates
# ============================================================================


def test_get_popular_templates_endpoint(client: TestClient, sample_template: Template):
    """Test getting popular templates via API."""
    response = client.get("/api/v1/templates/popular")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ============================================================================
# POST /api/v1/templates/{template_id}/use - Increment Use Count
# ============================================================================


def test_increment_use_count_endpoint(client: TestClient, sample_template: Template):
    """Test incrementing template use count via API."""
    initial_use_count = sample_template.use_count

    response = client.post(f"/api/v1/templates/{sample_template.id}/use")

    assert response.status_code == 200
    data = response.json()
    assert data["use_count"] == initial_use_count + 1


# ============================================================================
# POST /api/v1/templates/{template_id}/create-agent - Create Agent from Template
# ============================================================================


def test_create_agent_from_template_endpoint_success(client: TestClient, sample_template: Template):
    """Test creating agent from template via API."""
    agent_data = {
        "template_id": sample_template.id,
        "name": "Agent from Template",
        "description": "Custom agent description",
        "config_overrides": {},
    }

    response = client.post(f"/api/v1/templates/{sample_template.id}/create-agent", json=agent_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == agent_data["name"]
    assert data["description"] == agent_data["description"]
    assert data["model_provider"] == sample_template.config_template["model_provider"]


def test_create_agent_from_template_endpoint_with_overrides(client: TestClient, sample_template: Template):
    """Test creating agent from template with config overrides."""
    agent_data = {
        "template_id": sample_template.id,
        "name": "Custom Agent",
        "description": "Custom description",
        "config_overrides": {
            "temperature": 0.9,
            "max_tokens": 2048,
        },
    }

    response = client.post(f"/api/v1/templates/{sample_template.id}/create-agent", json=agent_data)

    assert response.status_code == 201
    data = response.json()
    assert data["temperature"] == 0.9
    assert data["max_tokens"] == 2048


def test_create_agent_from_template_endpoint_template_id_mismatch(client: TestClient, sample_template: Template):
    """Test agent creation fails when template_id in path doesn't match body."""
    agent_data = {
        "template_id": 999,  # Different from path
        "name": "Agent",
        "description": "Description",
        "config_overrides": {},
    }

    response = client.post(f"/api/v1/templates/{sample_template.id}/create-agent", json=agent_data)

    assert response.status_code == 400
    assert "does not match" in response.json()["detail"]


# ============================================================================
# POST /api/v1/templates/import - Import Template
# ============================================================================


def test_import_template_endpoint_success(client: TestClient, sample_tool: Tool):
    """Test template import via API."""
    import_data = {
        "name": "Imported Template",
        "description": "This template was imported",
        "category": "research",
        "tags": ["imported", "test"],
        "config_template": {
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "system_prompt": "Test",
            "temperature": 0.7,
            "max_tokens": 4096,
            "planning_enabled": False,
            "filesystem_enabled": False,
            "tool_ids": [sample_tool.id],
            "additional_config": {},
        },
        "is_public": True,
        "is_featured": False,
    }

    response = client.post("/api/v1/templates/import", json=import_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == import_data["name"]
    assert data["description"] == import_data["description"]


# ============================================================================
# GET /api/v1/templates/{template_id}/export - Export Template
# ============================================================================


def test_export_template_endpoint_success(client: TestClient, sample_template: Template):
    """Test template export via API."""
    response = client.get(f"/api/v1/templates/{sample_template.id}/export")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_template.name
    assert data["description"] == sample_template.description
    assert data["category"] == sample_template.category
    assert "metadata" in data
    assert "use_count" in data["metadata"]


def test_export_template_endpoint_not_found(client: TestClient):
    """Test template export fails with invalid ID."""
    response = client.get("/api/v1/templates/99999/export")

    assert response.status_code == 404
