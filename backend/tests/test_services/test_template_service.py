"""
Comprehensive tests for Template Service layer.

Tests all business logic for template CRUD operations, including:
- Template creation with validation
- Template retrieval by ID and name
- Template listing with filtering
- Template updates
- Template deletion (soft and hard)
- Search functionality
- Import/export
- Agent creation from templates
- Usage tracking
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent
from models.template import Template
from models.tool import Tool
from models.user import User
from schemas.template import (
    AgentFromTemplateCreate,
    ConfigTemplate,
    TemplateCategory,
    TemplateCreate,
    TemplateImport,
    TemplateUpdate,
)
from services.template_service import (
    DuplicateTemplateNameError,
    TemplateNotFoundError,
    TemplateService,
    TemplateValidationError,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for template ownership."""
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
async def test_tool(db_session: AsyncSession, test_user: User) -> Tool:
    """Create a test tool for template tool_ids."""
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
def sample_config_template(test_tool: Tool) -> ConfigTemplate:
    """Create sample config template."""
    return ConfigTemplate(
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        system_prompt="You are a helpful assistant.",
        temperature=0.7,
        max_tokens=4096,
        planning_enabled=True,
        filesystem_enabled=False,
        tool_ids=[test_tool.id],
        additional_config={"max_iterations": 10},
    )


@pytest.fixture
def sample_template_data(sample_config_template: ConfigTemplate) -> TemplateCreate:
    """Create sample template data for testing."""
    return TemplateCreate(
        name="Test Template",
        description="A test template for unit testing",
        category=TemplateCategory.RESEARCH,
        tags=["test", "research", "sample"],
        config_template=sample_config_template,
        is_public=True,
        is_featured=False,
    )


@pytest.fixture
def template_service() -> TemplateService:
    """Create an instance of TemplateService."""
    return TemplateService()


# ============================================================================
# Create Template Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_template_success(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_template_data: TemplateCreate,
):
    """Test successful template creation."""
    template = await template_service.create_template(
        db=db_session,
        template_data=sample_template_data,
        created_by_id=test_user.id,
    )

    assert template.id is not None
    assert template.name == sample_template_data.name
    assert template.description == sample_template_data.description
    assert template.category == sample_template_data.category.value
    assert template.tags == sample_template_data.tags
    assert template.config_template == sample_template_data.config_template.model_dump()
    assert template.is_public == sample_template_data.is_public
    assert template.is_featured == sample_template_data.is_featured
    assert template.use_count == 0
    assert template.created_by_id == test_user.id
    assert template.is_active is True
    assert template.created_at is not None


@pytest.mark.asyncio
async def test_create_template_duplicate_name(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_template_data: TemplateCreate,
):
    """Test template creation fails with duplicate name."""
    # Create first template
    await template_service.create_template(
        db=db_session,
        template_data=sample_template_data,
        created_by_id=test_user.id,
    )

    # Try to create another with same name
    with pytest.raises(DuplicateTemplateNameError):
        await template_service.create_template(
            db=db_session,
            template_data=sample_template_data,
            created_by_id=test_user.id,
        )


@pytest.mark.asyncio
async def test_create_template_invalid_tool_ids(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_template_data: TemplateCreate,
):
    """Test template creation fails with invalid tool IDs."""
    # Add non-existent tool ID
    sample_template_data.config_template.tool_ids = [99999]

    with pytest.raises(TemplateValidationError) as exc_info:
        await template_service.create_template(
            db=db_session,
            template_data=sample_template_data,
            created_by_id=test_user.id,
        )

    assert "99999" in str(exc_info.value)


# ============================================================================
# Get Template Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_template_success(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_template_data: TemplateCreate,
):
    """Test successful template retrieval."""
    created_template = await template_service.create_template(
        db=db_session,
        template_data=sample_template_data,
        created_by_id=test_user.id,
    )

    retrieved_template = await template_service.get_template(
        db=db_session,
        template_id=created_template.id,
    )

    assert retrieved_template.id == created_template.id
    assert retrieved_template.name == created_template.name


@pytest.mark.asyncio
async def test_get_template_not_found(
    db_session: AsyncSession,
    template_service: TemplateService,
):
    """Test template retrieval fails with invalid ID."""
    with pytest.raises(TemplateNotFoundError):
        await template_service.get_template(
            db=db_session,
            template_id=99999,
        )


@pytest.mark.asyncio
async def test_get_template_by_name_success(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_template_data: TemplateCreate,
):
    """Test successful template retrieval by name."""
    created_template = await template_service.create_template(
        db=db_session,
        template_data=sample_template_data,
        created_by_id=test_user.id,
    )

    retrieved_template = await template_service.get_template_by_name(
        db=db_session,
        name=created_template.name,
    )

    assert retrieved_template is not None
    assert retrieved_template.id == created_template.id


# ============================================================================
# List Templates Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_templates_pagination(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_config_template: ConfigTemplate,
):
    """Test template listing with pagination."""
    # Create multiple templates
    for i in range(5):
        template_data = TemplateCreate(
            name=f"Template {i}",
            description=f"Description {i}",
            category=TemplateCategory.RESEARCH,
            tags=["test"],
            config_template=sample_config_template,
            is_public=True,
            is_featured=False,
        )
        await template_service.create_template(
            db=db_session,
            template_data=template_data,
            created_by_id=test_user.id,
        )

    # Test pagination
    templates, total = await template_service.list_templates(
        db=db_session,
        skip=0,
        limit=3,
    )

    assert len(templates) == 3
    assert total == 5


@pytest.mark.asyncio
async def test_list_templates_filter_by_category(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_config_template: ConfigTemplate,
):
    """Test template listing filtered by category."""
    # Create templates in different categories
    categories = [TemplateCategory.RESEARCH, TemplateCategory.CODING, TemplateCategory.RESEARCH]

    for i, category in enumerate(categories):
        template_data = TemplateCreate(
            name=f"Template {i}",
            description=f"Description {i}",
            category=category,
            tags=["test"],
            config_template=sample_config_template,
            is_public=True,
            is_featured=False,
        )
        await template_service.create_template(
            db=db_session,
            template_data=template_data,
            created_by_id=test_user.id,
        )

    # Filter by research category
    templates, total = await template_service.list_templates(
        db=db_session,
        category=TemplateCategory.RESEARCH.value,
    )

    assert total == 2
    assert all(t.category == TemplateCategory.RESEARCH.value for t in templates)


@pytest.mark.asyncio
async def test_list_templates_search(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_config_template: ConfigTemplate,
):
    """Test template search functionality."""
    # Create templates with searchable content
    template_data1 = TemplateCreate(
        name="Python Developer",
        description="For Python development",
        category=TemplateCategory.CODING,
        tags=["python"],
        config_template=sample_config_template,
        is_public=True,
        is_featured=False,
    )

    template_data2 = TemplateCreate(
        name="Research Assistant",
        description="For research tasks",
        category=TemplateCategory.RESEARCH,
        tags=["research"],
        config_template=sample_config_template,
        is_public=True,
        is_featured=False,
    )

    await template_service.create_template(db=db_session, template_data=template_data1, created_by_id=test_user.id)
    await template_service.create_template(db=db_session, template_data=template_data2, created_by_id=test_user.id)

    # Search for "python"
    templates, total = await template_service.list_templates(
        db=db_session,
        search="python",
    )

    assert total == 1
    assert templates[0].name == "Python Developer"


# ============================================================================
# Update Template Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_template_success(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_template_data: TemplateCreate,
):
    """Test successful template update."""
    template = await template_service.create_template(
        db=db_session,
        template_data=sample_template_data,
        created_by_id=test_user.id,
    )

    update_data = TemplateUpdate(
        name="Updated Template",
        description="Updated description",
    )

    updated_template = await template_service.update_template(
        db=db_session,
        template_id=template.id,
        template_update=update_data,
    )

    assert updated_template.name == "Updated Template"
    assert updated_template.description == "Updated description"
    assert updated_template.category == template.category  # Unchanged


@pytest.mark.asyncio
async def test_update_template_duplicate_name(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_config_template: ConfigTemplate,
):
    """Test template update fails with duplicate name."""
    # Create two templates
    template1_data = TemplateCreate(
        name="Template 1",
        description="Description 1",
        category=TemplateCategory.RESEARCH,
        tags=["test"],
        config_template=sample_config_template,
        is_public=True,
        is_featured=False,
    )

    template2_data = TemplateCreate(
        name="Template 2",
        description="Description 2",
        category=TemplateCategory.CODING,
        tags=["test"],
        config_template=sample_config_template,
        is_public=True,
        is_featured=False,
    )

    template1 = await template_service.create_template(db=db_session, template_data=template1_data, created_by_id=test_user.id)
    template2 = await template_service.create_template(db=db_session, template_data=template2_data, created_by_id=test_user.id)

    # Try to update template2 with template1's name
    update_data = TemplateUpdate(name="Template 1")

    with pytest.raises(DuplicateTemplateNameError):
        await template_service.update_template(
            db=db_session,
            template_id=template2.id,
            template_update=update_data,
        )


# ============================================================================
# Delete Template Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_template_soft(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_template_data: TemplateCreate,
):
    """Test soft delete of template."""
    template = await template_service.create_template(
        db=db_session,
        template_data=sample_template_data,
        created_by_id=test_user.id,
    )

    await template_service.delete_template(
        db=db_session,
        template_id=template.id,
        hard_delete=False,
    )

    # Should not be found without include_inactive
    with pytest.raises(TemplateNotFoundError):
        await template_service.get_template(db=db_session, template_id=template.id)

    # Should be found with include_inactive
    deleted_template = await template_service.get_template(
        db=db_session,
        template_id=template.id,
        include_inactive=True,
    )
    assert deleted_template.is_active is False


@pytest.mark.asyncio
async def test_delete_template_hard(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_template_data: TemplateCreate,
):
    """Test hard delete of template."""
    template = await template_service.create_template(
        db=db_session,
        template_data=sample_template_data,
        created_by_id=test_user.id,
    )

    await template_service.delete_template(
        db=db_session,
        template_id=template.id,
        hard_delete=True,
    )

    # Should not be found even with include_inactive
    with pytest.raises(TemplateNotFoundError):
        await template_service.get_template(
            db=db_session,
            template_id=template.id,
            include_inactive=True,
        )


# ============================================================================
# Special Operations Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_categories(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_config_template: ConfigTemplate,
):
    """Test getting distinct categories."""
    categories = [TemplateCategory.RESEARCH, TemplateCategory.CODING, TemplateCategory.TESTING]

    for category in categories:
        template_data = TemplateCreate(
            name=f"Template {category.value}",
            description="Description",
            category=category,
            tags=["test"],
            config_template=sample_config_template,
            is_public=True,
            is_featured=False,
        )
        await template_service.create_template(db=db_session, template_data=template_data, created_by_id=test_user.id)

    result = await template_service.get_categories(db=db_session)

    assert len(result) == 3
    assert sorted(result) == sorted([c.value for c in categories])


@pytest.mark.asyncio
async def test_get_featured_templates(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_config_template: ConfigTemplate,
):
    """Test getting featured templates."""
    # Create some featured and non-featured templates
    for i in range(5):
        template_data = TemplateCreate(
            name=f"Template {i}",
            description="Description",
            category=TemplateCategory.RESEARCH,
            tags=["test"],
            config_template=sample_config_template,
            is_public=True,
            is_featured=(i < 2),  # Only first 2 are featured
        )
        await template_service.create_template(db=db_session, template_data=template_data, created_by_id=test_user.id)

    featured = await template_service.get_featured_templates(db=db_session, limit=10)

    assert len(featured) == 2
    assert all(t.is_featured for t in featured)


@pytest.mark.asyncio
async def test_increment_use_count(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_template_data: TemplateCreate,
):
    """Test incrementing template use count."""
    template = await template_service.create_template(
        db=db_session,
        template_data=sample_template_data,
        created_by_id=test_user.id,
    )

    assert template.use_count == 0

    # Increment twice
    await template_service.increment_use_count(db=db_session, template_id=template.id)
    await template_service.increment_use_count(db=db_session, template_id=template.id)

    updated = await template_service.get_template(db=db_session, template_id=template.id)
    assert updated.use_count == 2


@pytest.mark.asyncio
async def test_search_templates(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_config_template: ConfigTemplate,
):
    """Test template search functionality."""
    # Create templates with different content
    templates_data = [
        ("Python Expert", "Advanced Python development", ["python", "coding"]),
        ("Data Scientist", "Data analysis with Python", ["python", "data"]),
        ("DevOps Engineer", "Infrastructure automation", ["devops", "automation"]),
    ]

    for name, desc, tags in templates_data:
        template_data = TemplateCreate(
            name=name,
            description=desc,
            category=TemplateCategory.CODING,
            tags=tags,
            config_template=sample_config_template,
            is_public=True,
            is_featured=False,
        )
        await template_service.create_template(db=db_session, template_data=template_data, created_by_id=test_user.id)

    # Search for "python"
    results = await template_service.search_templates(db=db_session, query_text="python", limit=10)

    assert len(results) == 2
    assert all("python" in t.name.lower() or "python" in t.description.lower() or "python" in str(t.tags).lower() for t in results)


@pytest.mark.asyncio
async def test_import_template(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_config_template: ConfigTemplate,
):
    """Test template import functionality."""
    import_data = TemplateImport(
        name="Imported Template",
        description="This template was imported",
        category=TemplateCategory.RESEARCH,
        tags=["imported", "test"],
        config_template=sample_config_template,
        is_public=True,
        is_featured=False,
    )

    template = await template_service.import_template(
        db=db_session,
        template_data=import_data,
        created_by_id=test_user.id,
    )

    assert template.name == import_data.name
    assert template.description == import_data.description


@pytest.mark.asyncio
async def test_export_template(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_template_data: TemplateCreate,
):
    """Test template export functionality."""
    template = await template_service.create_template(
        db=db_session,
        template_data=sample_template_data,
        created_by_id=test_user.id,
    )

    export_data = await template_service.export_template(
        db=db_session,
        template_id=template.id,
    )

    assert export_data.name == template.name
    assert export_data.description == template.description
    assert export_data.category == template.category
    assert export_data.config_template == template.config_template
    assert "use_count" in export_data.metadata


# ============================================================================
# Agent Creation from Template Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_agent_from_template(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_template_data: TemplateCreate,
):
    """Test creating an agent from a template."""
    template = await template_service.create_template(
        db=db_session,
        template_data=sample_template_data,
        created_by_id=test_user.id,
    )

    agent_data = AgentFromTemplateCreate(
        template_id=template.id,
        name="My Agent from Template",
        description="Custom description",
        config_overrides={},
    )

    agent = await template_service.create_agent_from_template(
        db=db_session,
        agent_data=agent_data,
        user_id=test_user.id,
    )

    assert agent.name == "My Agent from Template"
    assert agent.description == "Custom description"
    assert agent.model_provider == template.config_template["model_provider"]
    assert agent.model_name == template.config_template["model_name"]
    assert agent.created_by_id == test_user.id

    # Verify use count was incremented
    updated_template = await template_service.get_template(db=db_session, template_id=template.id)
    assert updated_template.use_count == 1


@pytest.mark.asyncio
async def test_create_agent_from_template_with_overrides(
    db_session: AsyncSession,
    template_service: TemplateService,
    test_user: User,
    sample_template_data: TemplateCreate,
):
    """Test creating an agent from a template with config overrides."""
    template = await template_service.create_template(
        db=db_session,
        template_data=sample_template_data,
        created_by_id=test_user.id,
    )

    agent_data = AgentFromTemplateCreate(
        template_id=template.id,
        name="Custom Agent",
        description="Custom description",
        config_overrides={
            "temperature": 0.9,
            "max_tokens": 2048,
        },
    )

    agent = await template_service.create_agent_from_template(
        db=db_session,
        agent_data=agent_data,
        user_id=test_user.id,
    )

    assert agent.temperature == 0.9
    assert agent.max_tokens == 2048
    # Other fields should come from template
    assert agent.model_provider == template.config_template["model_provider"]
