# FastAPI Patterns Examples

Practical examples for implementing production-ready FastAPI applications.

## Table of Contents

- [Complete CRUD API](#complete-crud-api)
- [Authentication System](#authentication-system)
- [File Upload](#file-upload)
- [WebSocket Chat](#websocket-chat)
- [Background Tasks](#background-tasks)
- [Testing](#testing)

## Complete CRUD API

### Agent Management API

**Models:**
```python
# app/models/agent.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=True)
    model_name = Column(String(128), nullable=False)
    system_prompt = Column(Text, nullable=False)
    config = Column(JSON, nullable=True, default=dict)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="agents")
    executions = relationship("Execution", back_populates="agent", cascade="all, delete-orphan")
```

**Schemas:**
```python
# app/schemas/agent.py
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class AgentBase(BaseModel):
    name: str = Field(min_length=3, max_length=64)
    description: str | None = None
    model_name: str
    system_prompt: str = Field(min_length=10)
    config: dict = Field(default_factory=dict)

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    name: str | None = Field(None, min_length=3, max_length=64)
    description: str | None = None
    model_name: str | None = None
    system_prompt: str | None = Field(None, min_length=10)
    config: dict | None = None
    is_active: bool | None = None

class AgentResponse(AgentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

class AgentListResponse(BaseModel):
    items: list[AgentResponse]
    total: int
    skip: int
    limit: int
```

**Service:**
```python
# app/services/agent_service.py
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate

class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, data: AgentCreate, user_id: int) -> Agent:
        agent = Agent(**data.model_dump(), user_id=user_id)
        self.db.add(agent)
        await self.db.flush()
        await self.db.refresh(agent)
        return agent
    
    async def get(self, agent_id: int, user_id: int) -> Agent | None:
        stmt = select(Agent).where(
            Agent.id == agent_id,
            Agent.user_id == user_id,
            Agent.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list(self, user_id: int, skip: int, limit: int) -> list[Agent]:
        stmt = (
            select(Agent)
            .where(Agent.user_id == user_id, Agent.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Agent.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def count(self, user_id: int) -> int:
        stmt = select(func.count()).select_from(Agent).where(
            Agent.user_id == user_id,
            Agent.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()
    
    async def update(self, agent_id: int, data: AgentUpdate, user_id: int) -> Agent | None:
        agent = await self.get(agent_id, user_id)
        if not agent:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)
        
        agent.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(agent)
        return agent
    
    async def delete(self, agent_id: int, user_id: int) -> bool:
        agent = await self.get(agent_id, user_id)
        if not agent:
            return False
        
        agent.deleted_at = datetime.utcnow()
        await self.db.flush()
        return True
```

**Router:**
```python
# app/api/v1/agents.py
from fastapi import APIRouter, HTTPException, status, Query

from app.api.deps import DatabaseDep, CurrentUserDep
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentListResponse
from app.services.agent_service import AgentService

router = APIRouter()

@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent: AgentCreate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
):
    service = AgentService(db)
    return await service.create(agent, current_user.id)

@router.get("", response_model=AgentListResponse)
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: DatabaseDep,
    current_user: CurrentUserDep,
):
    service = AgentService(db)
    items = await service.list(current_user.id, skip, limit)
    total = await service.count(current_user.id)
    return AgentListResponse(items=items, total=total, skip=skip, limit=limit)

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    db: DatabaseDep,
    current_user: CurrentUserDep,
):
    service = AgentService(db)
    agent = await service.get(agent_id, current_user.id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent: AgentUpdate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
):
    service = AgentService(db)
    updated = await service.update(agent_id, agent, current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Agent not found")
    return updated

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    db: DatabaseDep,
    current_user: CurrentUserDep,
):
    service = AgentService(db)
    deleted = await service.delete(agent_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
```

## Authentication System

**JWT Auth Implementation:**
```python
# app/api/v1/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DatabaseDep
from app.core.security import create_access_token, verify_password
from app.core.config import settings
from app.schemas.auth import Token, UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: DatabaseDep,
):
    service = AuthService(db)
    
    # Check if user exists
    existing = await service.get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = await service.create_user(user_data)
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: DatabaseDep,
):
    service = AuthService(db)
    user = await service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: CurrentUserDep,
):
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=current_user.id,
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
```

**Auth Service:**
```python
# app/services/auth_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import UserCreate
from app.core.security import get_password_hash, verify_password

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)
    
    async def create_user(self, user_data: UserCreate) -> User:
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def authenticate_user(self, email: str, password: str) -> User | None:
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
```

## File Upload

**File Upload Endpoint:**
```python
# app/api/v1/uploads.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pathlib import Path
import aiofiles
import uuid

router = APIRouter()

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: CurrentUserDep,
):
    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {MAX_FILE_SIZE} bytes"
        )
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    return {
        "filename": unique_filename,
        "original_filename": file.filename,
        "size": len(content),
        "path": str(file_path)
    }

@router.post("/upload-multiple")
async def upload_multiple_files(
    files: list[UploadFile] = File(...),
    current_user: CurrentUserDep,
):
    uploaded_files = []
    
    for file in files:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            continue  # Skip large files
        
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        uploaded_files.append({
            "filename": unique_filename,
            "original_filename": file.filename,
            "size": len(content)
        })
    
    return {"uploaded_files": uploaded_files}
```

## WebSocket Chat

**Chat WebSocket:**
```python
# app/api/v1/chat.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.websocket import ConnectionManager
from app.api.deps import get_current_user_ws

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/chat/{room_id}")
async def chat_websocket(
    websocket: WebSocket,
    room_id: str,
):
    await manager.connect(websocket, room_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            # Broadcast to room
            await manager.broadcast_to_room(
                message={
                    "type": "message",
                    "content": data["content"],
                    "user": data.get("user", "Anonymous")
                },
                room_id=room_id,
                exclude=websocket
            )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast_to_room(
            message={
                "type": "system",
                "content": "User left the chat"
            },
            room_id=room_id
        )
```

## Background Tasks

**Email Notification:**
```python
# app/api/v1/notifications.py
from fastapi import APIRouter, BackgroundTasks, Depends

router = APIRouter()

async def send_welcome_email(email: str, name: str):
    """Send welcome email (background task)."""
    # Email sending logic
    await asyncio.sleep(2)  # Simulate delay
    print(f"Welcome email sent to {email}")

@router.post("/welcome")
async def send_welcome(
    email: str,
    name: str,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(send_welcome_email, email, name)
    return {"message": "Welcome email will be sent"}
```

## Testing

**Test Examples:**
```python
# tests/test_agents.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_agent(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/v1/agents",
        json={
            "name": "Test Agent",
            "model_name": "claude-sonnet-4-5",
            "system_prompt": "You are a test agent"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Agent"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_agents(async_client: AsyncClient, auth_headers):
    response = await async_client.get(
        "/api/v1/agents",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
```
