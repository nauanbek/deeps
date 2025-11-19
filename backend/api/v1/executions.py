"""
Execution API endpoints for agent execution management.

Provides REST endpoints for:
- Creating executions
- Starting executions (non-streaming)
- Getting execution details
- Listing executions with filters
- Cancelling executions
- Retrieving execution traces

Also provides WebSocket endpoint for:
- Real-time execution trace streaming
"""

from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user
from core.security import decode_access_token
from models.user import User
from schemas.execution import ExecutionCreate, ExecutionResponse, TraceResponse
from services.auth_service import AuthService
from services.execution_service import execution_service

router = APIRouter(prefix="/executions", tags=["executions"])


# ============================================================================
# Helper Functions - Authorization
# ============================================================================


async def get_agent_or_403(
    agent_id: int,
    user_id: int,
    db: AsyncSession,
) -> "Agent":
    """
    Get agent and verify ownership, raise 403 if not owner.

    Args:
        agent_id: Agent ID to fetch
        user_id: Current user ID (from JWT token)
        db: Database session

    Returns:
        Agent: The agent if user is the owner

    Raises:
        404: Agent not found
        403: User doesn't own this agent (access denied)
    """
    from models.agent import Agent
    from sqlalchemy import select

    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found",
        )

    # Critical security check: Verify ownership
    if agent.created_by_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this agent",
        )

    return agent


async def get_execution_or_403(
    execution_id: int,
    user_id: int,
    db: AsyncSession,
) -> "Execution":
    """
    Get execution and verify ownership, raise 403 if not owner.

    Args:
        execution_id: Execution ID to fetch
        user_id: Current user ID (from JWT token)
        db: Database session

    Returns:
        Execution: The execution if user is the owner

    Raises:
        404: Execution not found
        403: User doesn't own this execution (access denied)
    """
    from models.execution import Execution
    from sqlalchemy import select

    stmt = select(Execution).where(Execution.id == execution_id)
    result = await db.execute(stmt)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution with id {execution_id} not found",
        )

    # Critical security check: Verify ownership
    if execution.created_by_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this execution",
        )

    return execution


@router.post("/", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
async def create_execution(
    execution_data: ExecutionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ExecutionResponse:
    """
    Create a new execution.

    Creates an execution record in pending status.
    Use the /start endpoint or WebSocket to begin execution.

    Args:
        execution_data: Execution creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created execution

    Raises:
        HTTPException: 403 if user doesn't own the agent
        HTTPException: 404 if agent not found
    """
    try:
        # Verify user owns the agent before creating execution
        await get_agent_or_403(execution_data.agent_id, current_user.id, db)

        execution = await execution_service.create_execution(
            db=db,
            agent_id=execution_data.agent_id,
            prompt=execution_data.prompt,
            created_by_id=current_user.id,
        )
        return execution
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{execution_id}/start")
async def start_execution(
    execution_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Start an execution (non-streaming).

    This endpoint starts execution and waits for completion.
    For real-time streaming, use the WebSocket endpoint instead.

    Args:
        execution_id: ID of execution to start
        current_user: Current authenticated user
        db: Database session

    Returns:
        Execution completion summary

    Raises:
        HTTPException: 403 if user doesn't own the execution
        HTTPException: 404 if execution not found
        HTTPException: 400 if execution cannot be started
    """
    try:
        # Verify user owns the execution before starting
        await get_execution_or_403(execution_id, current_user.id, db)

        # Collect all traces (non-streaming)
        traces = []
        async for trace in execution_service.start_execution(db, execution_id):
            traces.append(trace)

        return {"status": "completed", "trace_count": len(traces)}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ExecutionResponse:
    """
    Get execution by ID.

    Args:
        execution_id: Execution ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Execution details

    Raises:
        HTTPException: 403 if user doesn't own the execution
        HTTPException: 404 if not found
    """
    # Verify ownership before returning execution
    execution = await get_execution_or_403(execution_id, current_user.id, db)
    return execution


@router.get("/", response_model=List[ExecutionResponse])
async def list_executions(
    agent_id: Optional[int] = Query(None, description="Filter by agent ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ExecutionResponse]:
    """
    List executions with optional filters.

    Only returns executions owned by the current user.

    Args:
        agent_id: Filter by agent ID (optional)
        status: Filter by status (pending, running, completed, failed, cancelled)
        skip: Pagination offset
        limit: Pagination limit
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of executions owned by the current user

    Raises:
        HTTPException: 403 if agent_id specified but user doesn't own it
    """
    # If agent_id filter is specified, verify user owns that agent
    if agent_id is not None:
        await get_agent_or_403(agent_id, current_user.id, db)

    # List executions - need to filter by user_id
    # Note: execution_service.list_executions should filter by created_by_id
    executions = await execution_service.list_executions(
        db=db,
        agent_id=agent_id,
        status=status,
        skip=skip,
        limit=limit,
        user_id=current_user.id,  # Filter by current user
    )
    return executions


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Cancel a running execution.

    Args:
        execution_id: Execution ID to cancel
        current_user: Current authenticated user
        db: Database session

    Returns:
        Cancellation confirmation

    Raises:
        HTTPException: 403 if user doesn't own the execution
        HTTPException: 404 if execution not found
        HTTPException: 400 if execution not running
    """
    # Verify user owns the execution before cancelling
    await get_execution_or_403(execution_id, current_user.id, db)

    success = await execution_service.cancel_execution(db, execution_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Execution not found or not running",
        )
    return {"status": "cancelled"}


@router.get("/{execution_id}/traces", response_model=List[TraceResponse])
async def get_execution_traces(
    execution_id: int,
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(1000, ge=1, le=10000, description="Pagination limit"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[TraceResponse]:
    """
    Get traces for an execution.

    Returns ordered list of trace events for post-execution analysis.

    Args:
        execution_id: Execution ID
        skip: Pagination offset
        limit: Pagination limit
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of traces ordered by sequence number

    Raises:
        HTTPException: 403 if user doesn't own the execution
        HTTPException: 404 if execution not found
    """
    # Verify user owns the execution before returning traces
    await get_execution_or_403(execution_id, current_user.id, db)

    traces = await execution_service.get_execution_traces(
        db=db, execution_id=execution_id, skip=skip, limit=limit
    )
    return traces


@router.websocket("/{execution_id}/stream")
async def stream_execution(websocket: WebSocket, execution_id: int):
    """
    WebSocket endpoint for streaming execution traces in real-time.

    Connect to ws://host/api/v1/executions/{execution_id}/stream
    to receive trace events as they occur during execution.

    Authentication Protocol:
    1. Client connects to WebSocket
    2. Server accepts connection
    3. Client sends authentication message: {"type": "auth", "token": "Bearer <JWT>"}
    4. Server validates token and responds with {"type": "auth", "status": "success"}
       or {"type": "auth", "status": "error", "message": "..."} and closes connection
    5. Server starts execution and streams trace events as JSON
    6. Server sends {"event_type": "execution_complete"} on completion
    7. Server closes connection

    Error handling:
    - Sends {"event_type": "error", "content": {"error": "..."}} on errors
    - Closes connection on client disconnect or auth failure

    Args:
        websocket: WebSocket connection
        execution_id: Execution ID to stream
    """
    await websocket.accept()

    try:
        # Wait for authentication message
        auth_message = await websocket.receive_json()

        # Validate auth message format
        if not isinstance(auth_message, dict) or auth_message.get("type") != "auth":
            await websocket.send_json({
                "type": "auth",
                "status": "error",
                "message": "First message must be authentication message with type='auth'"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        token = auth_message.get("token", "")

        # Extract token from "Bearer <token>" format
        if token.startswith("Bearer "):
            token = token[7:]
        elif not token:
            await websocket.send_json({
                "type": "auth",
                "status": "error",
                "message": "Token is required"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Validate JWT token
        token_data = decode_access_token(token)
        if token_data is None:
            await websocket.send_json({
                "type": "auth",
                "status": "error",
                "message": "Invalid or expired token"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Get user from token
        username = token_data.get("sub")
        if not username:
            await websocket.send_json({
                "type": "auth",
                "status": "error",
                "message": "Invalid token payload"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Get database session and validate user
        async for db in get_db():
            try:
                user = await AuthService.get_user_by_username(db, username=username)
                if not user or not user.is_active:
                    await websocket.send_json({
                        "type": "auth",
                        "status": "error",
                        "message": "User not found or inactive"
                    })
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return

                # Authentication successful
                await websocket.send_json({
                    "type": "auth",
                    "status": "success"
                })

                # Verify user owns the execution before starting
                try:
                    await get_execution_or_403(execution_id, user.id, db)
                except HTTPException as e:
                    await websocket.send_json({
                        "event_type": "error",
                        "content": {"error": f"Access denied: {e.detail}"}
                    })
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return

                # Start execution and stream traces
                async for trace in execution_service.start_execution(db, execution_id):
                    # Send trace to WebSocket client
                    await websocket.send_json(trace)

                # Send completion message
                await websocket.send_json({"event_type": "execution_complete"})

            except ValueError as e:
                # Send error to client
                await websocket.send_json(
                    {"event_type": "error", "content": {"error": str(e)}}
                )
            finally:
                break  # Exit the async for db loop

    except WebSocketDisconnect:
        # Client disconnected, nothing to do
        pass
    except Exception as e:
        # Send error to client if still connected
        try:
            await websocket.send_json(
                {"event_type": "error", "content": {"error": str(e)}}
            )
        except:
            pass
    finally:
        # Ensure connection is closed
        try:
            await websocket.close()
        except:
            pass
