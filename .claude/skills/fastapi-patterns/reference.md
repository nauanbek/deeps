# FastAPI Patterns Reference

Comprehensive reference for production-ready FastAPI development.

## Table of Contents

- [Application Structure](#application-structure)
- [Router Configuration](#router-configuration)
- [Dependency Injection](#dependency-injection)
- [Service Layer](#service-layer)
- [Error Handling](#error-handling)
- [Authentication & Authorization](#authentication--authorization)
- [Database Integration](#database-integration)
- [WebSocket](#websocket)
- [Background Tasks](#background-tasks)
- [Testing](#testing)

## Application Structure

### Recommended Directory Layout

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py          # Shared dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── agents.py    # Agent routes
│   │       ├── tools.py     # Tool routes
│   │       └── auth.py      # Auth routes
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Settings management
│   │   ├── security.py      # Security utilities
│   │   └── database.py      # Database connection
│   ├── middleware/          # Custom middleware
│   │   ├── __init__.py
│   │   ├── rate_limit.py    # Rate limiting
│   │   ├── logging.py       # Request logging
│   │   └── correlation_id.py
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py          # Base model
│   │   ├── user.py
│   │   └── agent.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── base.py          # Base schemas
│   │   ├── user.py
│   │   └── agent.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── agent_service.py
│   │   └── auth_service.py
│   ├── exceptions.py        # Custom exceptions
│   └── utils/               # Helper functions
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── unit/                # Unit tests
│   │   ├── __init__.py
│   │   ├── test_services.py
│   │   └── test_schemas.py
│   └── integration/         # Integration tests
│       ├── __init__.py
│       ├── test_agents_api.py
│       └── test_auth_api.py
├── alembic/                 # Database migrations
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
├── .env                     # Environment variables (gitignored)
├── .env.example             # Example environment variables
├── .gitignore
├── pyproject.toml           # Project configuration
├── requirements.txt         # Production dependencies
└── requirements-dev.txt     # Development dependencies
```

### Main Application Setup

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.database import engine
from app.api.v1 import agents, tools, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup: Initialize resources
    # Database connection, cache, etc.
    print("Starting up...")
    yield
    # Shutdown: Cleanup resources
    # Close connections, cleanup, etc.
    await engine.dispose()
    print("Shutting down...")

def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Include routers
    app.include_router(
        auth.router,
        prefix="/api/v1/auth",
        tags=["authentication"]
    )
    app.include_router(
        agents.router,
        prefix="/api/v1/agents",
        tags=["agents"]
    )
    app.include_router(
        tools.router,
        prefix="/api/v1/tools",
        tags=["tools"]
    )
    
    return app

app = create_application()
```

## Response Model Patterns

### Modern Response Models

**Using response_model_exclude_none:**
```python
from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar

class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: str | None = None  # None values excluded in response
    model_name: str
    config: dict | None = None

# Exclude None values from response
@router.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    response_model_exclude_none=True,  # Don't include null fields
)
async def get_agent(agent_id: int, db: DatabaseDep):
    agent = await db.get(Agent, agent_id)
    return agent  # description=None won't be in JSON response
```

### Generic Pagination Response

```python
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    \"\"\"Generic pagination response.\"\"\"
    
    items: list[T]
    total: int = Field(..., description=\"Total number of items\")
    page: int = Field(..., ge=1, description=\"Current page number\")
    page_size: int = Field(..., ge=1, le=100, description=\"Items per page\")
    pages: int = Field(..., description=\"Total number of pages\")
    
    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> 'PaginatedResponse[T]':
        \"\"\"Create paginated response with calculated pages.\"\"\"
        pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

# Usage
@router.get(\"/agents\", response_model=PaginatedResponse[AgentResponse])
async def list_agents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: DatabaseDep,
):
    offset = (page - 1) * page_size
    
    # Get items
    stmt = select(Agent).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    # Get total count
    total_stmt = select(func.count()).select_from(Agent)
    total_result = await db.execute(total_stmt)
    total = total_result.scalar_one()
    
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
```

### Union Response Types for Different Status Codes

```python
from typing import Union
from pydantic import BaseModel, Field

class SuccessResponse(BaseModel):
    success: bool = True
    data: dict
    message: str | None = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: dict
    timestamp: str

# Multiple response models
@router.post(
    \"/agents\",
    response_model=Union[AgentResponse, ErrorResponse],
    responses={
        201: {\"model\": AgentResponse, \"description\": \"Agent created successfully\"},
        400: {\"model\": ErrorResponse, \"description\": \"Validation error\"},
        409: {\"model\": ErrorResponse, \"description\": \"Agent already exists\"},
    },
    status_code=201,
)
async def create_agent(agent: AgentCreate, db: DatabaseDep):
    # Implementation
    pass
```

### Response Model with Aliases

```python
from pydantic import BaseModel, Field, ConfigDict

class AgentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,  # Allow both field name and alias
    )
    
    id: int
    name: str
    model_name: str = Field(..., serialization_alias=\"model\")  # JSON key: \"model\"
    created_at: str = Field(..., serialization_alias=\"createdAt\")  # camelCase
    updated_at: str = Field(..., serialization_alias=\"updatedAt\")

# Use with response_model_by_alias
@router.get(
    \"/agents/{agent_id}\",
    response_model=AgentResponse,
    response_model_by_alias=True,  # Use aliases in response
)
async def get_agent(agent_id: int, db: DatabaseDep):
    agent = await db.get(Agent, agent_id)
    return agent
    # Response: {\"id\": 1, \"name\": \"...\", \"model\": \"...\", \"createdAt\": \"...\"}
```

### Base Response Classes

```python
from datetime import datetime
from typing import Generic, TypeVar, Any
from pydantic import BaseModel, Field

T = TypeVar('T')

class BaseResponse(BaseModel):
    \"\"\"Base response with metadata.\"\"\"
    success: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str | None = None

class DataResponse(BaseResponse, Generic[T]):
    \"\"\"Response with typed data payload.\"\"\"
    data: T

class ListResponse(BaseResponse, Generic[T]):
    \"\"\"Response with list of items and pagination.\"\"\"
    data: list[T]
    pagination: dict[str, Any] = Field(
        default_factory=lambda: {
            \"page\": 1,
            \"page_size\": 20,
            \"total\": 0,
            \"pages\": 0,
        }
    )

# Usage
@router.get(\"/agents/{agent_id}\", response_model=DataResponse[AgentResponse])
async def get_agent(agent_id: int, db: DatabaseDep):
    agent = await db.get(Agent, agent_id)
    return DataResponse(data=agent)

@router.get(\"/agents\", response_model=ListResponse[AgentResponse])
async def list_agents(page: int = 1, page_size: int = 20, db: DatabaseDep):
    # Get data
    offset = (page - 1) * page_size
    stmt = select(Agent).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    # Get count
    total = await db.scalar(select(func.count()).select_from(Agent))
    
    return ListResponse(
        data=items,
        pagination={
            \"page\": page,
            \"page_size\": page_size,
            \"total\": total,
            \"pages\": (total + page_size - 1) // page_size,
        }
    )
```

### Response Model Exclude/Include Fields

```python
class AgentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    system_prompt: str
    api_key: str | None = None  # Sensitive field
    internal_notes: str | None = None  # Internal field

# Exclude sensitive fields
@router.get(
    \"/agents/{agent_id}\",
    response_model=AgentDetailResponse,
    response_model_exclude={\"api_key\", \"internal_notes\"},  # Don't expose
)
async def get_agent_public(agent_id: int, db: DatabaseDep):
    agent = await db.get(Agent, agent_id)
    return agent

# Include only specific fields
@router.get(
    \"/agents/{agent_id}/summary\",
    response_model=AgentDetailResponse,
    response_model_include={\"id\", \"name\"},  # Only these fields
)
async def get_agent_summary(agent_id: int, db: DatabaseDep):
    agent = await db.get(Agent, agent_id)
    return agent
```

## Router Configuration

### Router Template

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    ResourceListResponse
)
from app.services.resource_service import ResourceService

router = APIRouter()

@router.post(
    "",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new resource",
    description="Create a new resource with the provided data."
)
async def create_resource(
    resource: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceResponse:
    """Create new resource."""
    service = ResourceService(db)
    return await service.create(resource, current_user.id)

@router.get(
    "",
    response_model=ResourceListResponse,
    summary="List resources",
    description="Retrieve paginated list of resources."
)
async def list_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceListResponse:
    """List resources with pagination."""
    service = ResourceService(db)
    items = await service.list(current_user.id, skip, limit)
    total = await service.count(current_user.id)
    
    return ResourceListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )

@router.get(
    "/{resource_id}",
    response_model=ResourceResponse,
    summary="Get resource by ID"
)
async def get_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceResponse:
    """Retrieve specific resource."""
    service = ResourceService(db)
    resource = await service.get(resource_id, current_user.id)
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    return resource

@router.patch(
    "/{resource_id}",
    response_model=ResourceResponse,
    summary="Update resource"
)
async def update_resource(
    resource_id: int,
    resource: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceResponse:
    """Update existing resource."""
    service = ResourceService(db)
    updated = await service.update(resource_id, resource, current_user.id)
    
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    return updated

@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete resource"
)
async def delete_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Soft delete resource."""
    service = ResourceService(db)
    deleted = await service.delete(resource_id, current_user.id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
```

## Dependency Injection

### Common Dependencies

```python
# app/api/deps.py
from typing import AsyncGenerator, Annotated
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.user import User
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
bearer_scheme = HTTPBearer()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.
    
    Yields:
        AsyncSession: SQLAlchemy async session
    
    Note:
        Automatically commits on success, rolls back on exception.
        Session is closed by async context manager.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        token: JWT access token
        db: Database session
    
    Returns:
        User: Authenticated user instance
    
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure user has admin privileges."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def pagination_params(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return"),
) -> dict[str, int]:
    """Common pagination parameters."""
    return {"skip": skip, "limit": limit}

# Type aliases for cleaner dependency injection (Python 3.10+)
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
SuperUserDep = Annotated[User, Depends(get_current_superuser)]
PaginationDep = Annotated[dict, Depends(pagination_params)]
```

### Using Type Aliases in Endpoints

**Before (Repetitive):**
```python
@router.get("/items")
async def get_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    pass
```

**After (Clean with Annotated):**
```python
@router.get("/items")
async def get_items(
    db: DatabaseDep,
    current_user: CurrentUserDep,
    pagination: PaginationDep,
):
    items = await get_paginated_items(db, **pagination)
    return items
```

## Service Layer

### Base Service Pattern

```python
# app/services/base_service.py
from typing import Generic, TypeVar, Type, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import DeclarativeMeta

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base service with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
    
    async def get(self, id: int) -> Optional[ModelType]:
        """Get single record by ID."""
        return await self.db.get(self.model, id)
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[ModelType]:
        """Get multiple records with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def count(self) -> int:
        """Count total records."""
        stmt = select(func.count()).select_from(self.model)
        result = await self.db.execute(stmt)
        return result.scalar_one()
    
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create new record."""
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(
        self,
        id: int,
        obj_in: UpdateSchemaType
    ) -> Optional[ModelType]:
        """Update existing record."""
        db_obj = await self.get(id)
        if not db_obj:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: int) -> bool:
        """Delete record (hard delete)."""
        db_obj = await self.get(id)
        if not db_obj:
            return False
        
        await self.db.delete(db_obj)
        await self.db.flush()
        return True
    
    async def soft_delete(self, id: int) -> bool:
        """Soft delete record."""
        db_obj = await self.get(id)
        if not db_obj:
            return False
        
        db_obj.deleted_at = datetime.utcnow()
        await self.db.flush()
        return True
```

### Specific Service Implementation

```python
# app/services/agent_service.py
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate
from app.services.base_service import BaseService

class AgentService(BaseService[Agent, AgentCreate, AgentUpdate]):
    """Service for agent-specific business logic."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Agent, db)
    
    async def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Agent]:
        """Get agents owned by specific user."""
        stmt = (
            select(Agent)
            .where(
                Agent.user_id == user_id,
                Agent.deleted_at.is_(None)
            )
            .offset(skip)
            .limit(limit)
            .order_by(Agent.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def count_by_user(self, user_id: int) -> int:
        """Count agents for user."""
        stmt = (
            select(func.count())
            .select_from(Agent)
            .where(
                Agent.user_id == user_id,
                Agent.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()
    
    async def get_with_permission_check(
        self,
        agent_id: int,
        user_id: int
    ) -> Optional[Agent]:
        """Get agent with ownership verification."""
        stmt = select(Agent).where(
            Agent.id == agent_id,
            Agent.user_id == user_id,
            Agent.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_with_defaults(
        self,
        agent_in: AgentCreate,
        user_id: int
    ) -> Agent:
        """Create agent with default values."""
        agent_data = agent_in.model_dump()
        agent_data["user_id"] = user_id
        agent_data["created_at"] = datetime.utcnow()
        agent_data["is_active"] = True
        
        agent = Agent(**agent_data)
        self.db.add(agent)
        await self.db.flush()
        await self.db.refresh(agent)
        
        return agent
    
    async def search(
        self,
        user_id: int,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[Agent]:
        """Search agents by name or description."""
        stmt = (
            select(Agent)
            .where(
                Agent.user_id == user_id,
                Agent.deleted_at.is_(None),
                (Agent.name.ilike(f"%{query}%") | 
                 Agent.description.ilike(f"%{query}%"))
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
```

## Error Handling

### Pydantic V2 Validators

**Field Validators:**
```python
from pydantic import BaseModel, field_validator, model_validator
from typing import Any

class AgentCreate(BaseModel):
    name: str
    model_name: str
    system_prompt: str
    max_tokens: int = 1000
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate agent name."""
        if len(v) < 3:
            raise ValueError('Name must be at least 3 characters')
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Name can only contain alphanumeric characters, hyphens, and underscores')
        return v.lower()
    
    @field_validator('max_tokens')
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Validate token limit."""
        if v < 100 or v > 100000:
            raise ValueError('max_tokens must be between 100 and 100000')
        return v
    
    @model_validator(mode='after')
    def validate_model(self) -> 'AgentCreate':
        """Cross-field validation."""
        # Validate model supports requested token count
        if 'gpt-3.5' in self.model_name and self.max_tokens > 4096:
            raise ValueError('GPT-3.5 models support max 4096 tokens')
        
        # Validate system prompt length
        if len(self.system_prompt) > self.max_tokens:
            raise ValueError('System prompt exceeds max_tokens limit')
        
        return self
```

**Multiple Field Validation:**
```python
class UserCreate(BaseModel):
    email: str
    password: str
    password_confirm: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.lower().strip()
        if not '@' in v or not '.' in v.split('@')[1]:
            raise ValueError('Invalid email format')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
    
    @model_validator(mode='after')
    def validate_passwords_match(self) -> 'UserCreate':
        if self.password != self.password_confirm:
            raise ValueError('Passwords do not match')
        return self
```

### Custom Exceptions

```python
# app/exceptions.py
from typing import Any
import logging

logger = logging.getLogger(__name__)

class AppException(Exception):
    """Base application exception with structured error details."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
        error_code: str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)
        
        # Structured logging
        logger.error(
            f"{self.error_code}: {self.message}",
            extra={
                "error_code": self.error_code,
                "status_code": self.status_code,
                "details": self.details,
            }
        )

class NotFoundException(AppException):
    """Resource not found exception."""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            details={"resource": resource, "id": str(identifier)},
            error_code="RESOURCE_NOT_FOUND"
        )

class ValidationException(AppException):
    """Validation error exception."""
    
    def __init__(self, field: str, message: str, value: Any = None):
        super().__init__(
            message="Validation error",
            status_code=422,
            details={"field": field, "message": message, "value": value},
            error_code="VALIDATION_ERROR"
        )

class UnauthorizedException(AppException):
    """Unauthorized access exception."""
    
    def __init__(self, message: str = "Unauthorized", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=401,
            details=details or {},
            error_code="UNAUTHORIZED"
        )

class ForbiddenException(AppException):
    """Forbidden access exception."""
    
    def __init__(self, message: str = "Forbidden", resource: str | None = None):
        super().__init__(
            message=message,
            status_code=403,
            details={"resource": resource} if resource else {},
            error_code="FORBIDDEN"
        )

class RateLimitException(AppException):
    """Rate limit exceeded exception."""
    
    def __init__(self, retry_after: int):
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            details={"retry_after": retry_after},
            error_code="RATE_LIMIT_EXCEEDED"
        )
```

### Exception Handlers with Structured Responses

```python
# app/main.py
import logging
import traceback
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, DBAPIError
import structlog

from app.exceptions import AppException

# Structured logging setup
logger = structlog.get_logger()

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions with structured error response."""
    
    # Structured logging
    logger.error(
        "Application error",
        error_code=exc.error_code,
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method,
        details=exc.details,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path),
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with detailed field information."""
    
    # Extract and format validation errors
    errors = []
    for error in exc.errors():
        field_path = '.'.join(str(loc) for loc in error['loc'])
        errors.append({
            "field": field_path,
            "message": error['msg'],
            "type": error['type'],
            "input": error.get('input'),
        })
    
    logger.warning(
        "Validation error",
        path=request.url.path,
        method=request.method,
        errors=errors,
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": {"fields": errors},
            },
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path),
        }
    )

@app.exception_handler(IntegrityError)
async def integrity_exception_handler(
    request: Request,
    exc: IntegrityError
) -> JSONResponse:
    """Handle database integrity errors."""
    
    # Parse constraint violation
    error_detail = str(exc.orig)
    constraint_type = "unique" if "unique" in error_detail.lower() else "constraint"
    
    logger.error(
        "Database integrity error",
        path=request.url.path,
        constraint_type=constraint_type,
        detail=error_detail,
    )
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "error": {
                "code": "INTEGRITY_ERROR",
                "message": f"Database {constraint_type} violation",
                "details": {"constraint": constraint_type},
            },
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path),
        }
    )

@app.exception_handler(DBAPIError)
async def database_exception_handler(
    request: Request,
    exc: DBAPIError
) -> JSONResponse:
    """Handle database connection errors."""
    
    logger.critical(
        "Database error",
        path=request.url.path,
        error=str(exc),
    )
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "Database service unavailable",
                "details": {},
            },
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path),
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected errors with full logging."""
    
    # Log with full traceback
    logger.critical(
        "Unexpected error",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        traceback=traceback.format_exc(),
    )
    
    # Don't expose internal error details in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            },
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path),
        }
    )
```

### Using HTTPException with Structured Detail

```python
from fastapi import HTTPException

# Simple error
raise HTTPException(status_code=404, detail="User not found")

# Structured error with dict detail
raise HTTPException(
    status_code=400,
    detail={
        "code": "INVALID_INPUT",
        "message": "Email already exists",
        "field": "email",
        "value": user_email,
    }
)

# With headers
raise HTTPException(
    status_code=401,
    detail={"code": "TOKEN_EXPIRED", "message": "Access token has expired"},
    headers={"WWW-Authenticate": "Bearer"},
)
```

## Authentication & Authorization

### Modern Password Hashing with Passlib

```python
# app/core/security.py
from datetime import datetime, timedelta
from typing import Any
from jose import jwt, JWTError
from passlib.context import CryptContext
import secrets

from app.core.config import settings

# Use bcrypt (not deprecated)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Adjust for security/performance
)

def create_access_token(
    subject: int | str,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None
) -> str:
    """Create JWT access token with optional additional claims."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.utcnow(),
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(subject: int | str) -> str:
    """Create JWT refresh token with longer expiry."""
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(32),  # Unique token ID
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password with bcrypt."""
    return pwd_context.hash(password)

def decode_token(token: str, token_type: str = "access") -> dict[str, Any]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            raise JWTError(f"Invalid token type. Expected {token_type}")
        
        return payload
    except JWTError:
        return {}
```

### Refresh Token Pattern

```python
# app/api/v1/auth.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import DatabaseDep, CurrentUserDep
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.config import settings

router = APIRouter()

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/token/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: DatabaseDep,
):
    """Exchange refresh token for new access token."""
    
    # Decode refresh token
    payload = decode_token(request.refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_REFRESH_TOKEN", "message": "Invalid refresh token"},
        )
    
    user_id = payload.get("sub")
    jti = payload.get("jti")
    
    # TODO: Check if refresh token is revoked (store jti in Redis/DB)
    # is_revoked = await check_token_revoked(jti)
    # if is_revoked:
    #     raise HTTPException(status_code=401, detail="Token revoked")
    
    # Create new tokens
    access_token = create_access_token(subject=user_id)
    new_refresh_token = create_refresh_token(subject=user_id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )
```

### API Key Authentication

```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Annotated

from app.core.config import settings
from app.models.user import User

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_user_from_api_key(
    api_key: Annotated[str | None, Security(api_key_header)],
    db: DatabaseDep,
) -> User:
    """Authenticate user via API key."""
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"X-API-Key": "Required"},
        )
    
    # Hash API key for comparison
    from app.core.security import get_password_hash
    
    # Query user by API key hash
    stmt = select(User).where(
        User.api_key_hash == api_key,  # In production, hash the key
        User.is_active == True
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    return user

# Type alias
APIKeyUser = Annotated[User, Security(get_user_from_api_key)]

# Usage in endpoints
@router.get("/protected")
async def protected_endpoint(user: APIKeyUser):
    return {"user_id": user.id}
```

### Rate Limiting

```python
# app/middleware/rate_limit.py
import time
from collections import defaultdict
from typing import Callable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

from app.core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""
    
    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.rate_limit = 100  # requests per minute
        self.window = 60  # seconds
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Get client identifier (IP or user ID)
        client_id = request.client.host
        
        # Check if authenticated user
        if hasattr(request.state, "user"):
            client_id = f"user:{request.state.user.id}"
        
        # Rate limit key
        key = f"rate_limit:{client_id}:{int(time.time() / self.window)}"
        
        # Increment counter
        current = await self.redis.incr(key)
        
        if current == 1:
            await self.redis.expire(key, self.window)
        
        # Check limit
        if current > self.rate_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests",
                    "retry_after": self.window,
                },
                headers={"Retry-After": str(self.window)},
            )
        
        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.rate_limit - current))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.window)
        
        return response

# Add to app
from app.core.database import redis_client
app.add_middleware(RateLimitMiddleware, redis_client=redis_client)
```

### CORS Configuration

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

# Explicit CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://app.example.com",
        "https://staging.example.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=600,  # Cache preflight for 10 minutes
)

# For development only - allow all origins
if settings.ENVIRONMENT == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

## SQLAlchemy 2.0 Patterns

### Modern Query Patterns

**Use select() instead of query():**
```python
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload, selectinload

# ❌ OLD (SQLAlchemy 1.x)
users = session.query(User).filter(User.is_active == True).all()

# ✅ NEW (SQLAlchemy 2.0)
stmt = select(User).where(User.is_active == True)
result = await session.execute(stmt)
users = result.scalars().all()

# Use scalar_one_or_none() instead of first()
stmt = select(User).where(User.id == user_id)
result = await session.execute(stmt)
user = result.scalar_one_or_none()  # Returns None if not found

# Or scalar_one() if you expect exactly one result
user = result.scalar_one()  # Raises if not found or multiple found
```

### Eager Loading with joinedload() and selectinload()

```python
from sqlalchemy.orm import joinedload, selectinload

# joinedload - Single query with JOIN
@router.get("/agents/{agent_id}")
async def get_agent_with_tools(
    agent_id: int,
    db: DatabaseDep,
):
    """Load agent with tools in single query."""
    stmt = (
        select(Agent)
        .where(Agent.id == agent_id)
        .options(joinedload(Agent.tools))  # Eager load tools
    )
    result = await db.execute(stmt)
    agent = result.unique().scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent

# selectinload - Separate query (better for one-to-many)
@router.get("/users/{user_id}/agents")
async def get_user_with_agents(
    user_id: int,
    db: DatabaseDep,
):
    """Load user with all agents."""
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.agents))  # Separate query for agents
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    return user

# Multiple levels of eager loading
stmt = (
    select(Agent)
    .options(
        selectinload(Agent.tools),
        selectinload(Agent.executions).selectinload(Execution.traces)
    )
)
```

### Count Queries with func.count()

```python
from sqlalchemy import func, select

# Count all rows
stmt = select(func.count()).select_from(Agent)
result = await db.execute(stmt)
total = result.scalar_one()

# Count with filter
stmt = (
    select(func.count())
    .select_from(Agent)
    .where(Agent.user_id == user_id, Agent.is_active == True)
)
result = await db.execute(stmt)
active_count = result.scalar_one()

# Count with GROUP BY
stmt = (
    select(
        Agent.model_name,
        func.count(Agent.id).label("count")
    )
    .group_by(Agent.model_name)
)
result = await db.execute(stmt)
counts = result.all()  # [("gpt-4", 10), ("claude", 5)]

# Efficient exists check
from sqlalchemy import exists

stmt = select(exists().where(Agent.name == "test-agent"))
result = await db.execute(stmt)
agent_exists = result.scalar()
```

### Advanced Query Patterns

```python
from sqlalchemy import and_, or_, case
from datetime import datetime, timedelta

# Complex WHERE clauses
stmt = select(Agent).where(
    and_(
        Agent.user_id == user_id,
        or_(
            Agent.name.ilike(f"%{query}%"),
            Agent.description.ilike(f"%{query}%")
        ),
        Agent.deleted_at.is_(None)
    )
)

# Subqueries
subquery = (
    select(Execution.agent_id)
    .where(Execution.status == "failed")
    .subquery()
)

stmt = select(Agent).where(Agent.id.in_(subquery))

# Window functions
from sqlalchemy import over

stmt = select(
    Agent.id,
    Agent.name,
    func.row_number().over(
        partition_by=Agent.user_id,
        order_by=Agent.created_at.desc()
    ).label("row_num")
)

# CASE statements
stmt = select(
    Agent.id,
    case(
        (Agent.is_active == True, "active"),
        (Agent.deleted_at.isnot(None), "deleted"),
        else_="inactive"
    ).label("status")
)
```

## Database Integration

### Async Database Configuration

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Close database connections."""
    await engine.dispose()
```

## WebSocket

### Connection Manager

```python
# app/core/websocket.py
from typing import Dict, Set, Any
from contextlib import asynccontextmanager
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections with automatic cleanup."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str) -> None:
        """Connect client to room."""
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        
        self.active_connections[room_id].add(websocket)
        logger.info(f"Client connected to room {room_id}. Total: {len(self.active_connections[room_id])}")
    
    def disconnect(self, websocket: WebSocket, room_id: str) -> None:
        """Disconnect client from room."""
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
            
            logger.info(f"Client disconnected from room {room_id}")
    
    @asynccontextmanager
    async def connection(self, websocket: WebSocket, room_id: str):
        """Context manager for automatic connection cleanup."""
        await self.connect(websocket, room_id)
        try:
            yield
        finally:
            self.disconnect(websocket, room_id)
    
    async def send_personal_message(
        self,
        message: dict[str, Any],
        websocket: WebSocket
    ) -> None:
        """Send message to specific client with error handling."""
        try:
            if websocket.client_state.value == 1:  # WebSocketState.CONNECTED
                await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def broadcast_to_room(
        self,
        message: dict[str, Any],
        room_id: str,
        exclude: WebSocket | None = None
    ) -> None:
        """Broadcast message to all clients in room."""
        if room_id not in self.active_connections:
            return
        
        # Create list to avoid modification during iteration
        connections = list(self.active_connections[room_id])
        
        for connection in connections:
            if connection != exclude:
                await self.send_personal_message(message, connection)
    
    async def broadcast_all(self, message: dict[str, Any]) -> None:
        """Broadcast to all connected clients."""
        for room_id, connections in self.active_connections.items():
            for connection in list(connections):
                await self.send_personal_message(message, connection)
    
    def get_room_size(self, room_id: str) -> int:
        """Get number of connections in room."""
        return len(self.active_connections.get(room_id, set()))
    
    def is_connected(self, room_id: str) -> bool:
        """Check if room has active connections."""
        return room_id in self.active_connections and len(self.active_connections[room_id]) > 0
```

### WebSocket Endpoint Example

```python
from fastapi import WebSocket, WebSocketDisconnect

manager = ConnectionManager()

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """WebSocket endpoint with automatic cleanup."""
    async with manager.connection(websocket, room_id):
        try:
            while True:
                # Receive and process messages
                data = await websocket.receive_json()
                
                # Broadcast to room
                await manager.broadcast_to_room(
                    message={
                        "type": "message",
                        "content": data.get("content"),
                        "room": room_id
                    },
                    room_id=room_id,
                    exclude=websocket
                )
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected from room {room_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
```

## Async/Await Best Practices

### When to Use Async

**✅ Use async/await for I/O-bound operations:**
- Database queries
- HTTP requests
- File operations
- External API calls
- WebSocket communication

**❌ DO NOT use async for CPU-bound operations:**
- Heavy calculations
- Data processing
- Image manipulation
- Cryptographic operations

```python
# ✅ GOOD: I/O-bound operation
async def fetch_user(db: AsyncSession, user_id: int) -> User:
    """Async for database I/O."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# ❌ BAD: CPU-bound operation blocking event loop
async def process_data(data: list[int]) -> list[int]:
    """Don't use async for CPU-intensive work."""
    # This blocks the event loop!
    return [x ** 2 for x in range(10_000_000)]

# ✅ GOOD: CPU-bound in thread pool
import asyncio
from concurrent.futures import ProcessPoolExecutor

async def process_data_correctly(data: list[int]) -> list[int]:
    """Use ProcessPoolExecutor for CPU-intensive work."""
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, cpu_intensive_task, data)
    return result

def cpu_intensive_task(data: list[int]) -> list[int]:
    return [x ** 2 for x in data]
```

### Parallel Operations with asyncio.gather()

```python
import asyncio

async def fetch_multiple_resources(db: AsyncSession, ids: list[int]):
    """Fetch multiple resources concurrently."""
    # Execute all queries in parallel
    tasks = [fetch_user(db, user_id) for user_id in ids]
    users = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    return [user for user in users if not isinstance(user, Exception)]

async def parallel_api_calls():
    """Make multiple external API calls in parallel."""
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get("https://api1.example.com/data"),
            client.get("https://api2.example.com/data"),
            client.get("https://api3.example.com/data"),
        ]
        responses = await asyncio.gather(*tasks)
    
    return [r.json() for r in responses]

# With timeout
async def fetch_with_timeout(url: str, timeout: float = 5.0):
    """Fetch with timeout to prevent hanging."""
    async with httpx.AsyncClient() as client:
        try:
            return await asyncio.wait_for(
                client.get(url),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Request timeout")
```

### Common Async Pitfalls

```python
# ❌ WRONG: Forgetting await
async def wrong_example(db: AsyncSession):
    user = db.execute(select(User))  # Returns coroutine, not result!
    return user

# ✅ CORRECT: Always await async operations
async def correct_example(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()

# ❌ WRONG: Blocking operation in async function
async def blocking_file_read():
    with open("large_file.txt") as f:  # Blocks event loop!
        return f.read()

# ✅ CORRECT: Use async file operations
async def async_file_read():
    async with aiofiles.open("large_file.txt") as f:
        return await f.read()

# ❌ WRONG: Sequential when could be parallel
async def slow_sequential():
    user1 = await fetch_user(db, 1)
    user2 = await fetch_user(db, 2)
    user3 = await fetch_user(db, 3)
    return [user1, user2, user3]

# ✅ CORRECT: Parallel execution
async def fast_parallel():
    users = await asyncio.gather(
        fetch_user(db, 1),
        fetch_user(db, 2),
        fetch_user(db, 3),
    )
    return users
```

## Background Tasks

### Background Task Patterns with Type Hints

```python
from typing import Callable
from fastapi import BackgroundTasks
import asyncio
import logging

logger = logging.getLogger(__name__)

async def send_email_task(
    email: str,
    subject: str,
    body: str,
    *,
    retry_count: int = 0,
) -> None:
    """Background task to send email (I/O-bound).
    
    Args:
        email: Recipient email address
        subject: Email subject
        body: Email body content
        retry_count: Number of retry attempts
    
    Note:
        This runs in the request context and must complete quickly.
        For long-running tasks, use asyncio.create_task() instead.
    """
    try:
        # Simulate email sending
        await asyncio.sleep(1)
        logger.info(f"Email sent to {email}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        if retry_count < 3:
            # Retry with backoff
            await asyncio.sleep(2 ** retry_count)
            await send_email_task(email, subject, body, retry_count=retry_count + 1)

@router.post("/users")
async def create_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db: DatabaseDep,
):
    """Create user and send welcome email in background."""
    service = UserService(db)
    created_user = await service.create(user)
    
    # Add background task (runs in request context)
    background_tasks.add_task(
        send_email_task,
        created_user.email,
        "Welcome!",
        f"Welcome {created_user.name}"
    )
    
    return created_user
```

### Passing DB Session to Background Tasks

**❌ WRONG - Don't pass db session directly:**
```python
# DON'T DO THIS - session will be closed!
async def process_data(db: AsyncSession, user_id: int):
    # Session is already closed when this runs
    user = await db.get(User, user_id)  # ERROR!

background_tasks.add_task(process_data, db, user.id)
```

**✅ CORRECT - Create new session or pass data:**
```python
from app.core.database import async_session_maker

async def process_data_with_new_session(user_id: int) -> None:
    """Background task with its own DB session."""
    async with async_session_maker() as session:
        try:
            user = await session.get(User, user_id)
            # Process user data
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Background task failed: {e}")

# Pass only the ID, not the session
background_tasks.add_task(process_data_with_new_session, user.id)
```

### Long-Running Tasks with asyncio.create_task()

**⚠️ Important Limitations:**
- `BackgroundTasks` runs in request context (must complete quickly)
- For long-running tasks, use `asyncio.create_task()`
- For distributed tasks, use Celery/RQ

```python
import asyncio
from typing import Any

async def long_running_analysis(
    agent_id: int,
    data: dict[str, Any],
) -> None:
    """Long-running background task (not tied to request).
    
    Note:
        This task runs independently and won't block the response.
        Use for tasks that may take minutes/hours.
    """
    async with async_session_maker() as session:
        try:
            # Long processing
            for i in range(100):
                await asyncio.sleep(1)
                # Update progress
                logger.info(f"Processing {i}%")
            
            # Save results
            await session.execute(
                update(Agent)
                .where(Agent.id == agent_id)
                .values(analysis_complete=True)
            )
            await session.commit()
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            await session.rollback()

@router.post("/agents/{agent_id}/analyze")
async def start_analysis(
    agent_id: int,
    data: dict[str, Any],
    db: DatabaseDep,
):
    """Start long-running analysis in background."""
    
    # Verify agent exists
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Start background task (fire and forget)
    asyncio.create_task(long_running_analysis(agent_id, data))
    
    return {
        "status": "started",
        "agent_id": agent_id,
        "message": "Analysis started in background"
    }
```

### Background Task Best Practices

```python
from typing import TypeVar, Callable
import functools

T = TypeVar('T')

def background_task_with_error_handling(
    func: Callable[..., T]
) -> Callable[..., T]:
    """Decorator for background tasks with error handling."""
    
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Background task {func.__name__} failed",
                exc_info=True,
                extra={"args": args, "kwargs": kwargs}
            )
            # Optionally: Send alert, store in dead letter queue, etc.
    
    return wrapper

@background_task_with_error_handling
async def safe_background_task(user_id: int) -> None:
    """Task with automatic error handling."""
    # Your code here
    pass
```

## Testing

### Modern Test Configuration

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User

# Use separate test database
TEST_DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/test_db"

# Test engine with NullPool for better isolation
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # No connection pooling in tests
)

test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Database session with transaction rollback.
    
    Each test gets a fresh database state.
    Changes are rolled back after test completion.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session with savepoint
    async with test_session_maker() as session:
        async with session.begin():
            yield session
            # Rollback after test
            await session.rollback()
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def async_client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client with database dependency override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Use ASGITransport for async support
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user."""
    from app.core.security import get_password_hash
    
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user

@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    """Authentication headers for test user."""
    from app.core.security import create_access_token
    
    access_token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="session")
def anyio_backend():
    """Backend for anyio (used by pytest-asyncio)."""
    return "asyncio"
```

### Unit Tests with Mocking

```python
# tests/unit/test_services.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import Response

from app.services.agent_service import AgentService
from app.models.agent import Agent

@pytest.mark.asyncio
async def test_create_agent():
    """Test agent creation service."""
    # Mock database session
    mock_db = AsyncMock()
    
    service = AgentService(mock_db)
    
    # Create test data
    from app.schemas.agent import AgentCreate
    agent_data = AgentCreate(
        name="test-agent",
        model_name="gpt-4",
        system_prompt="Test prompt",
    )
    
    # Execute
    agent = await service.create(agent_data, user_id=1)
    
    # Verify database operations
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_external_api_call():
    """Mock external API calls."""
    from app.services.openai_service import OpenAIService
    
    # Mock httpx.AsyncClient
    with patch('httpx.AsyncClient.post') as mock_post:
        # Setup mock response
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response
        
        # Execute
        service = OpenAIService(api_key="test-key")
        result = await service.complete("Test prompt")
        
        # Verify
        assert result == "Test response"
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_redis_operations():
    """Mock Redis operations."""
    from app.services.cache_service import CacheService
    
    # Mock Redis client
    mock_redis = AsyncMock()
    mock_redis.get.return_value = b'{"data": "cached"}'
    
    service = CacheService(mock_redis)
    
    # Execute
    result = await service.get_cached_data("key")
    
    # Verify
    assert result == {"data": "cached"}
    mock_redis.get.assert_called_once_with("key")
```

### Integration Tests

```python
# tests/integration/test_agents_api.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent

@pytest.mark.asyncio
async def test_create_agent_endpoint(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
):
    """Test POST /agents endpoint."""
    response = await async_client.post(
        "/api/v1/agents",
        json={
            "name": "test-agent",
            "model_name": "gpt-4",
            "system_prompt": "You are a helpful assistant",
        },
        headers=auth_headers,
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-agent"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_agents_pagination(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    """Test agent list with pagination."""
    # Create test agents
    for i in range(25):
        agent = Agent(
            name=f"agent-{i}",
            model_name="gpt-4",
            system_prompt="Test",
            user_id=1,
        )
        db_session.add(agent)
    await db_session.commit()
    
    # Test pagination
    response = await async_client.get(
        "/api/v1/agents?page=1&page_size=10",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 25
    assert data["pages"] == 3

@pytest.mark.asyncio
async def test_unauthorized_access(async_client: AsyncClient):
    """Test authentication required."""
    response = await async_client.get("/api/v1/agents")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_not_found(async_client: AsyncClient, auth_headers: dict):
    """Test 404 error handling."""
    response = await async_client.get(
        "/api/v1/agents/99999",
        headers=auth_headers,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
```

### Parametrized Tests

```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name,expected_valid",
    [
        ("valid-name", True),
        ("valid_name", True),
        ("ab", False),  # Too short
        ("invalid name!", False),  # Special chars
        ("", False),  # Empty
    ],
)
async def test_agent_name_validation(
    async_client: AsyncClient,
    auth_headers: dict,
    name: str,
    expected_valid: bool,
):
    """Test agent name validation."""
    response = await async_client.post(
        "/api/v1/agents",
        json={
            "name": name,
            "model_name": "gpt-4",
            "system_prompt": "Test",
        },
        headers=auth_headers,
    )
    
    if expected_valid:
        assert response.status_code == 201
    else:
        assert response.status_code == 422
```

### Test Factories with Faker

```python
# tests/factories.py
from faker import Faker
from app.models.agent import Agent
from app.models.user import User

fake = Faker()

class UserFactory:
    @staticmethod
    def create(**kwargs) -> User:
        """Create user with fake data."""
        defaults = {
            "email": fake.email(),
            "hashed_password": "hashed_password",
            "full_name": fake.name(),
            "is_active": True,
        }
        defaults.update(kwargs)
        return User(**defaults)

class AgentFactory:
    @staticmethod
    def create(**kwargs) -> Agent:
        """Create agent with fake data."""
        defaults = {
            "name": fake.slug(),
            "model_name": "gpt-4",
            "system_prompt": fake.text(),
            "user_id": 1,
        }
        defaults.update(kwargs)
        return Agent(**defaults)

# Usage in tests
@pytest.mark.asyncio
async def test_with_factory(db_session: AsyncSession):
    user = UserFactory.create(email="specific@example.com")
    db_session.add(user)
    await db_session.commit()
    
    agent = AgentFactory.create(user_id=user.id)
    db_session.add(agent)
    await db_session.commit()
    
    assert agent.user_id == user.id
```
# Logging and Deployment Patterns

## Structured Logging with Structlog

### Structlog Configuration

```python
# app/core/logging.py
import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

def add_app_context(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Add application context to log entries."""
    event_dict["app"] = "deepagents-api"
    event_dict["environment"] = settings.ENVIRONMENT
    return event_dict

def setup_logging() -> None:
    """Configure structured logging with structlog."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            add_app_context,
            structlog.processors.JSONRenderer() if settings.ENVIRONMENT == "production"
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Call on app startup
setup_logging()
logger = structlog.get_logger()
```

### Request Logging Middleware with Correlation ID

```python
# app/middleware/logging.py
import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = structlog.get_logger()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests with correlation ID."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        
        # Bind correlation ID to structlog context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None,
        )
        
        # Log request
        start_time = time.time()
        logger.info(
            "request_started",
            user_agent=request.headers.get("user-agent"),
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            # Log response
            duration = time.time() - start_time
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_seconds=f"{duration:.3f}",
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "request_failed",
                error=str(e),
                duration_seconds=f"{duration:.3f}",
                exc_info=True,
            )
            raise

# Add to app
from app.middleware.logging import RequestLoggingMiddleware
app.add_middleware(RequestLoggingMiddleware)
```

### SQL Query Logging in Development

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine
import logging

# Enable SQL query logging in development
if settings.ENVIRONMENT == "development":
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",  # Log all SQL
    echo_pool=settings.ENVIRONMENT == "development",  # Log connection pool
)
```

### Sentry Integration

```python
# app/core/sentry.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from app.core.config import settings

def setup_sentry() -> None:
    """Configure Sentry for error tracking."""
    
    if settings.SENTRY_DSN and settings.ENVIRONMENT != "development":
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            profiles_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            before_send=filter_sensitive_data,
        )

def filter_sensitive_data(event, hint):
    """Remove sensitive data from Sentry events."""
    # Remove sensitive headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        for sensitive_header in ["authorization", "cookie", "x-api-key"]:
            if sensitive_header in headers:
                headers[sensitive_header] = "[Filtered]"
    
    return event

# Call on app startup
setup_sentry()
```

### OpenTelemetry Integration

```python
# app/core/telemetry.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import settings

def setup_telemetry(app) -> None:
    """Configure OpenTelemetry for distributed tracing."""
    
    if settings.OTLP_ENDPOINT:
        # Create resource
        resource = Resource(attributes={
            "service.name": "deepagents-api",
            "service.version": settings.VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        })
        
        # Configure tracer
        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=settings.OTLP_ENDPOINT)
        )
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        # Instrument SQLAlchemy
        from app.core.database import engine
        SQLAlchemyInstrumentor().instrument(
            engine=engine.sync_engine,
        )

# Call in lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_telemetry(app)
    yield
    # Cleanup
```

## Deployment Patterns

### Uvicorn + Gunicorn Configuration

**Production server with multiple workers:**

```python
# gunicorn_conf.py
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000  # Restart workers after N requests (prevent memory leaks)
max_requests_jitter = 100
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "deepagents-api"

# Server mechanics
daemon = False
pidfile = None
umask = 0
tmp_upload_dir = None

# Graceful timeout
graceful_timeout = 30

# Run command:
# gunicorn app.main:app -c gunicorn_conf.py
```

### Environment-Based Settings with Pydantic

```python
# app/core/config.py
from typing import Literal
from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings with environment-based configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = Field(default=False)
    
    # API
    PROJECT_NAME: str = "DeepAgents API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: PostgresDsn
    
    # CORS
    ALLOWED_ORIGINS: list[str] = Field(default_factory=list)
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Sentry
    SENTRY_DSN: str | None = None
    
    # OpenTelemetry
    OTLP_ENDPOINT: str | None = None
    
    # Feature flags
    ENABLE_DOCS: bool = Field(default=True)
    
    @field_validator("ENABLE_DOCS", mode="before")
    @classmethod
    def disable_docs_in_production(cls, v, info):
        # Automatically disable docs in production
        if info.data.get("ENVIRONMENT") == "production":
            return False
        return v

settings = Settings()
```

### Health Check Endpoints

```python
# app/api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.api.deps import get_db
from app.core.database import engine

router = APIRouter()

@router.get("/health", tags=["health"])
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }

@router.get("/health/ready", tags=["health"])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check with dependencies."""
    
    health_status = {
        "status": "ready",
        "checks": {
            "database": "unknown",
            "redis": "unknown",
        }
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "not_ready"
    
    # Check Redis
    try:
        from app.core.database import redis_client
        await redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "not_ready"
    
    return health_status

@router.get("/health/live", tags=["health"])
async def liveness_check():
    """Liveness check for Kubernetes."""
    return {"status": "alive"}
```

### Docker Multi-Stage Build

```dockerfile
# Dockerfile
# Stage 1: Build dependencies
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Add local binaries to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run with gunicorn
CMD ["gunicorn", "app.main:app", "-c", "gunicorn_conf.py"]
```

### Docker Compose for Development

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app/app  # Hot reload in development
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  
  db:
    image: postgres:17.6-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7.4.6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Conditional API Documentation

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode")
    yield
    # Shutdown
    print("Shutting down...")

def create_application() -> FastAPI:
    """Create FastAPI application with environment-based configuration."""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
        # Disable docs in production
        docs_url="/docs" if settings.ENABLE_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_DOCS else None,
        openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
    )
    
    return app

app = create_application()
```

### .env.example

```bash
# .env.example
# Copy this file to .env and fill in your values

# Environment
ENVIRONMENT=development
DEBUG=true

# Security
SECRET_KEY=your-secret-key-min-32-characters-long-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/deepagents

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS - comma separated
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Sentry (optional)
SENTRY_DSN=

# OpenTelemetry (optional)
OTLP_ENDPOINT=

# Feature Flags
ENABLE_DOCS=true

# Server
PORT=8000
WEB_CONCURRENCY=4
LOG_LEVEL=info
```
