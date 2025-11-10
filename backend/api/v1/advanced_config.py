"""
Advanced Configuration API endpoints for agents.

Provides RESTful API endpoints for managing advanced agent configurations:
- Backend storage configuration
- Long-term memory management
- HITL (Human-in-the-Loop) interrupt configuration
- Execution approval management
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user
from deepagents_integration.backends import backend_manager
from deepagents_integration.store import store_manager
from models.advanced_config import (
    AgentBackendConfig,
    AgentInterruptConfig,
    AgentMemoryFile,
    AgentMemoryNamespace,
    ExecutionApproval,
)
from models.agent import Agent
from models.execution import Execution
from models.user import User
from schemas.advanced_config import (
    AgentAdvancedConfigResponse,
    ApprovalDecision,
    ApprovalListResponse,
    ApprovalResponse,
    BackendConfigCreate,
    BackendConfigResponse,
    BackendConfigUpdate,
    InterruptConfigCreate,
    InterruptConfigListResponse,
    InterruptConfigResponse,
    InterruptConfigsInfo,
    InterruptConfigUpdate,
    MemoryFileContentResponse,
    MemoryFileCreate,
    MemoryFileListResponse,
    MemoryFileResponse,
    MemoryFilesInfo,
    MemoryNamespaceCreate,
    MemoryNamespaceResponse,
)

# Create router with prefix and tags
router = APIRouter(prefix="/agents", tags=["advanced-config"])


# ============================================================================
# Helper Functions
# ============================================================================


async def get_agent_or_404(
    agent_id: int,
    db: AsyncSession,
    user_id: int
) -> Agent:
    """Get agent by ID or raise 404."""
    stmt = select(Agent).where(
        Agent.id == agent_id,
        Agent.created_by_id == user_id,
        Agent.is_active == True
    )
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return agent


async def get_execution_or_404(
    execution_id: int,
    db: AsyncSession,
    user_id: int
) -> Execution:
    """Get execution by ID or raise 404."""
    stmt = select(Execution).where(
        Execution.id == execution_id,
        Execution.created_by_id == user_id
    )
    result = await db.execute(stmt)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )

    return execution


# ============================================================================
# Backend Configuration Endpoints
# ============================================================================


@router.post(
    "/{agent_id}/backend",
    response_model=BackendConfigResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_backend_config(
    agent_id: int,
    config_data: BackendConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create backend configuration for an agent.

    Args:
        agent_id: Agent ID
        config_data: Backend configuration data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created backend configuration

    Raises:
        404: Agent not found
        409: Backend config already exists
        400: Invalid configuration
    """
    # Verify agent exists and belongs to user
    agent = await get_agent_or_404(agent_id, db, current_user.id)

    # Check if backend config already exists
    stmt = select(AgentBackendConfig).where(AgentBackendConfig.agent_id == agent_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Backend config already exists for agent {agent_id}"
        )

    # Validate configuration
    is_valid, error = backend_manager.validate_config({
        "type": config_data.backend_type,
        **config_data.config
    })
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid backend configuration: {error}"
        )

    # Create backend config
    backend_config = AgentBackendConfig(
        agent_id=agent_id,
        backend_type=config_data.backend_type,
        config=config_data.config
    )
    db.add(backend_config)
    await db.commit()
    await db.refresh(backend_config)

    return backend_config


@router.get("/{agent_id}/backend", response_model=BackendConfigResponse)
async def get_backend_config(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get backend configuration for an agent."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Get backend config
    stmt = select(AgentBackendConfig).where(AgentBackendConfig.agent_id == agent_id)
    result = await db.execute(stmt)
    backend_config = result.scalar_one_or_none()

    if not backend_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backend config not found for agent {agent_id}"
        )

    return backend_config


@router.put("/{agent_id}/backend", response_model=BackendConfigResponse)
async def update_backend_config(
    agent_id: int,
    config_data: BackendConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update backend configuration for an agent."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Get existing config
    stmt = select(AgentBackendConfig).where(AgentBackendConfig.agent_id == agent_id)
    result = await db.execute(stmt)
    backend_config = result.scalar_one_or_none()

    if not backend_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backend config not found for agent {agent_id}"
        )

    # Update fields
    if config_data.backend_type is not None:
        backend_config.backend_type = config_data.backend_type
    if config_data.config is not None:
        backend_config.config = config_data.config

    # Validate updated configuration
    is_valid, error = backend_manager.validate_config({
        "type": backend_config.backend_type,
        **backend_config.config
    })
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid backend configuration: {error}"
        )

    await db.commit()
    await db.refresh(backend_config)

    return backend_config


@router.delete("/{agent_id}/backend", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backend_config(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete backend configuration for an agent (reverts to default StateBackend)."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Delete backend config
    stmt = delete(AgentBackendConfig).where(AgentBackendConfig.agent_id == agent_id)
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backend config not found for agent {agent_id}"
        )


# ============================================================================
# Memory Namespace Endpoints
# ============================================================================


@router.post(
    "/{agent_id}/memory/namespace",
    response_model=MemoryNamespaceResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_memory_namespace(
    agent_id: int,
    namespace_data: MemoryNamespaceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create memory namespace for an agent."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Check if namespace already exists
    stmt = select(AgentMemoryNamespace).where(
        AgentMemoryNamespace.agent_id == agent_id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Memory namespace already exists for agent {agent_id}"
        )

    # Create namespace
    try:
        namespace = await store_manager.create_namespace(agent_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

    # Get created namespace record
    stmt = select(AgentMemoryNamespace).where(
        AgentMemoryNamespace.agent_id == agent_id
    )
    result = await db.execute(stmt)
    namespace_record = result.scalar_one()

    return namespace_record


@router.get("/{agent_id}/memory/namespace", response_model=MemoryNamespaceResponse)
async def get_memory_namespace(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get memory namespace for an agent."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Get namespace
    stmt = select(AgentMemoryNamespace).where(
        AgentMemoryNamespace.agent_id == agent_id
    )
    result = await db.execute(stmt)
    namespace = result.scalar_one_or_none()

    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory namespace not found for agent {agent_id}"
        )

    return namespace


@router.delete("/{agent_id}/memory/namespace", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory_namespace(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete memory namespace and all its files."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Get namespace
    namespace = await store_manager.get_namespace(agent_id, db)
    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory namespace not found for agent {agent_id}"
        )

    # Delete namespace and files
    await store_manager.delete_namespace(namespace, db)


# ============================================================================
# Memory File Endpoints
# ============================================================================


@router.get("/{agent_id}/memory/files", response_model=MemoryFileListResponse)
async def list_memory_files(
    agent_id: int,
    prefix: Optional[str] = Query(None, description="Filter by key prefix"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all memory files for an agent."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Get namespace
    namespace = await store_manager.get_namespace(agent_id, db)
    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory namespace not found for agent {agent_id}. Create one first."
        )

    # Get files
    stmt = select(AgentMemoryFile).where(AgentMemoryFile.namespace == namespace)
    if prefix:
        stmt = stmt.where(AgentMemoryFile.key.startswith(prefix))

    result = await db.execute(stmt)
    files = result.scalars().all()

    # Calculate totals
    total_size = sum(f.size_bytes for f in files)

    return MemoryFileListResponse(
        namespace=namespace,
        files=[MemoryFileResponse.model_validate(f) for f in files],
        total_files=len(files),
        total_size_bytes=total_size
    )


@router.get("/{agent_id}/memory/files/{file_key:path}", response_model=MemoryFileContentResponse)
async def get_memory_file(
    agent_id: int,
    file_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get memory file content."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Get namespace
    namespace = await store_manager.get_namespace(agent_id, db)
    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory namespace not found for agent {agent_id}"
        )

    # Get file
    stmt = select(AgentMemoryFile).where(
        AgentMemoryFile.namespace == namespace,
        AgentMemoryFile.key == file_key
    )
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{file_key}' not found in memory"
        )

    # Decode from base64 for API response
    import base64
    try:
        decoded_value = base64.b64decode(file_record.value).decode('utf-8')
    except Exception:
        # If decode fails, return as-is (legacy data)
        decoded_value = file_record.value

    return MemoryFileContentResponse(
        key=file_record.key,
        value=decoded_value,
        size_bytes=file_record.size_bytes,
        content_type=file_record.content_type,
        created_at=file_record.created_at,
        updated_at=file_record.updated_at
    )


@router.post(
    "/{agent_id}/memory/files",
    response_model=MemoryFileContentResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_memory_file(
    agent_id: int,
    file_data: MemoryFileCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update memory file."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Get namespace
    namespace = await store_manager.get_namespace(agent_id, db)
    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory namespace not found for agent {agent_id}. Create one first."
        )

    # Get store and save file
    store = await store_manager.get_store(namespace, db_session=db)
    await store.put(file_data.key, file_data.value.encode('utf-8'))

    # Get saved file
    stmt = select(AgentMemoryFile).where(
        AgentMemoryFile.namespace == namespace,
        AgentMemoryFile.key == file_data.key
    )
    result = await db.execute(stmt)
    file_record = result.scalar_one()

    # Decode from base64 for API response
    import base64
    try:
        decoded_value = base64.b64decode(file_record.value).decode('utf-8')
    except Exception:
        # If decode fails, return as-is (legacy data)
        decoded_value = file_record.value

    return MemoryFileContentResponse(
        key=file_record.key,
        value=decoded_value,
        size_bytes=file_record.size_bytes,
        content_type=file_record.content_type,
        created_at=file_record.created_at,
        updated_at=file_record.updated_at
    )


@router.delete("/{agent_id}/memory/files/{file_key:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory_file(
    agent_id: int,
    file_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete memory file."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Get namespace
    namespace = await store_manager.get_namespace(agent_id, db)
    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory namespace not found for agent {agent_id}"
        )

    # Delete file
    store = await store_manager.get_store(namespace, db_session=db)
    deleted = await store.delete(file_key)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{file_key}' not found in memory"
        )


# ============================================================================
# HITL Interrupt Configuration Endpoints
# ============================================================================


@router.post(
    "/{agent_id}/interrupt",
    response_model=InterruptConfigResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_interrupt_config(
    agent_id: int,
    config_data: InterruptConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create HITL interrupt configuration for a tool."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Check if interrupt config already exists for this tool
    stmt = select(AgentInterruptConfig).where(
        AgentInterruptConfig.agent_id == agent_id,
        AgentInterruptConfig.tool_name == config_data.tool_name
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Interrupt config already exists for tool '{config_data.tool_name}'"
        )

    # Create interrupt config
    interrupt_config = AgentInterruptConfig(
        agent_id=agent_id,
        tool_name=config_data.tool_name,
        allowed_decisions=config_data.allowed_decisions,
        config=config_data.config
    )
    db.add(interrupt_config)
    await db.commit()
    await db.refresh(interrupt_config)

    return interrupt_config


@router.get("/{agent_id}/interrupt", response_model=InterruptConfigListResponse)
async def list_interrupt_configs(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all HITL interrupt configurations for an agent."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Get all interrupt configs
    stmt = select(AgentInterruptConfig).where(
        AgentInterruptConfig.agent_id == agent_id
    )
    result = await db.execute(stmt)
    configs = result.scalars().all()

    return InterruptConfigListResponse(
        configs=[InterruptConfigResponse.model_validate(c) for c in configs],
        total=len(configs)
    )


@router.get("/{agent_id}/interrupt/{tool_name}", response_model=InterruptConfigResponse)
async def get_interrupt_config(
    agent_id: int,
    tool_name: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get HITL interrupt configuration for a specific tool."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Get interrupt config
    stmt = select(AgentInterruptConfig).where(
        AgentInterruptConfig.agent_id == agent_id,
        AgentInterruptConfig.tool_name == tool_name
    )
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interrupt config not found for tool '{tool_name}'"
        )

    return config


@router.put("/{agent_id}/interrupt/{tool_name}", response_model=InterruptConfigResponse)
async def update_interrupt_config(
    agent_id: int,
    tool_name: str,
    config_data: InterruptConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update HITL interrupt configuration for a tool."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Get existing config
    stmt = select(AgentInterruptConfig).where(
        AgentInterruptConfig.agent_id == agent_id,
        AgentInterruptConfig.tool_name == tool_name
    )
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interrupt config not found for tool '{tool_name}'"
        )

    # Update fields
    if config_data.allowed_decisions is not None:
        config.allowed_decisions = config_data.allowed_decisions
    if config_data.config is not None:
        config.config = config_data.config

    await db.commit()
    await db.refresh(config)

    return config


@router.delete("/{agent_id}/interrupt/{tool_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interrupt_config(
    agent_id: int,
    tool_name: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete HITL interrupt configuration for a tool."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Delete config
    stmt = delete(AgentInterruptConfig).where(
        AgentInterruptConfig.agent_id == agent_id,
        AgentInterruptConfig.tool_name == tool_name
    )
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interrupt config not found for tool '{tool_name}'"
        )


# ============================================================================
# Execution Approval Endpoints (HITL)
# ============================================================================


@router.get("/executions/{execution_id}/approvals", response_model=ApprovalListResponse)
async def list_execution_approvals(
    execution_id: int,
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all approval requests for an execution."""
    # Verify execution exists
    await get_execution_or_404(execution_id, db, current_user.id)

    # Get approvals
    stmt = select(ExecutionApproval).where(
        ExecutionApproval.execution_id == execution_id
    )
    if status_filter:
        stmt = stmt.where(ExecutionApproval.status == status_filter)

    result = await db.execute(stmt)
    approvals = result.scalars().all()

    # Count pending
    pending_count = sum(1 for a in approvals if a.status == "pending")

    return ApprovalListResponse(
        approvals=[ApprovalResponse.model_validate(a) for a in approvals],
        total=len(approvals),
        pending_count=pending_count
    )


@router.get("/executions/{execution_id}/approvals/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    execution_id: int,
    approval_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific approval request."""
    # Verify execution exists
    await get_execution_or_404(execution_id, db, current_user.id)

    # Get approval
    stmt = select(ExecutionApproval).where(
        ExecutionApproval.id == approval_id,
        ExecutionApproval.execution_id == execution_id
    )
    result = await db.execute(stmt)
    approval = result.scalar_one_or_none()

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval {approval_id} not found"
        )

    return approval


@router.post("/executions/{execution_id}/approvals/{approval_id}/decide", response_model=ApprovalResponse)
async def submit_approval_decision(
    execution_id: int,
    approval_id: int,
    decision_data: ApprovalDecision,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit decision for an approval request."""
    from datetime import datetime

    # Verify execution exists
    await get_execution_or_404(execution_id, db, current_user.id)

    # Get approval
    stmt = select(ExecutionApproval).where(
        ExecutionApproval.id == approval_id,
        ExecutionApproval.execution_id == execution_id
    )
    result = await db.execute(stmt)
    approval = result.scalar_one_or_none()

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval {approval_id} not found"
        )

    # Check if already decided
    if approval.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Approval already decided with status: {approval.status}"
        )

    # Update approval
    approval.status = decision_data.decision
    approval.decided_by_id = current_user.id
    approval.decided_at = datetime.utcnow()

    # Store decision data
    decision_dict = {"decision": decision_data.decision}
    if decision_data.edited_args:
        decision_dict["edited_args"] = decision_data.edited_args
    if decision_data.reason:
        decision_dict["reason"] = decision_data.reason

    approval.decision_data = decision_dict

    await db.commit()
    await db.refresh(approval)

    # TODO: Resume agent execution with decision
    # This would typically involve:
    # 1. Loading the checkpointed state
    # 2. Resuming execution with approved/edited args
    # 3. Streaming results back to client

    return approval


# ============================================================================
# Combined Endpoint
# ============================================================================


@router.get("/{agent_id}/advanced-config", response_model=AgentAdvancedConfigResponse)
async def get_all_advanced_config(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all advanced configurations for an agent in one request."""
    # Verify agent exists
    await get_agent_or_404(agent_id, db, current_user.id)

    # Get backend config
    stmt = select(AgentBackendConfig).where(AgentBackendConfig.agent_id == agent_id)
    result = await db.execute(stmt)
    backend_config = result.scalar_one_or_none()

    # Get memory namespace
    stmt = select(AgentMemoryNamespace).where(AgentMemoryNamespace.agent_id == agent_id)
    result = await db.execute(stmt)
    memory_namespace = result.scalar_one_or_none()

    # Get memory files
    memory_files_list = []
    if memory_namespace:
        stmt = select(AgentMemoryFile).where(AgentMemoryFile.namespace == memory_namespace.namespace)
        result = await db.execute(stmt)
        memory_files_list = result.scalars().all()

    # Get interrupt configs
    stmt = select(AgentInterruptConfig).where(AgentInterruptConfig.agent_id == agent_id)
    result = await db.execute(stmt)
    interrupt_configs = result.scalars().all()

    return AgentAdvancedConfigResponse(
        backend_config=BackendConfigResponse.model_validate(backend_config) if backend_config else None,
        memory_namespace=MemoryNamespaceResponse.model_validate(memory_namespace) if memory_namespace else None,
        memory_files=MemoryFilesInfo(
            total_files=len(memory_files_list),
            files=[MemoryFileResponse.model_validate(f) for f in memory_files_list]
        ),
        interrupt_configs=InterruptConfigsInfo(
            total=len(interrupt_configs),
            configs=[InterruptConfigResponse.model_validate(c) for c in interrupt_configs]
        )
    )
