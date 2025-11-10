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
        db: Database session

    Returns:
        Created execution

    Raises:
        HTTPException: 404 if agent not found
    """
    try:
        execution = await execution_service.create_execution(
            db=db,
            agent_id=execution_data.agent_id,
            prompt=execution_data.prompt,
            created_by_id=1,  # Hardcoded for single-user MVP
        )
        return execution
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
        db: Database session

    Returns:
        Execution completion summary

    Raises:
        HTTPException: 400 if execution cannot be started
    """
    try:
        # Collect all traces (non-streaming)
        traces = []
        async for trace in execution_service.start_execution(db, execution_id):
            traces.append(trace)

        return {"status": "completed", "trace_count": len(traces)}
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
        db: Database session

    Returns:
        Execution details

    Raises:
        HTTPException: 404 if not found
    """
    execution = await execution_service.get_execution(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found"
        )
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

    Args:
        agent_id: Filter by agent ID
        status: Filter by status (pending, running, completed, failed, cancelled)
        skip: Pagination offset
        limit: Pagination limit
        db: Database session

    Returns:
        List of executions
    """
    executions = await execution_service.list_executions(
        db=db, agent_id=agent_id, status=status, skip=skip, limit=limit
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
        db: Database session

    Returns:
        Cancellation confirmation

    Raises:
        HTTPException: 400 if execution not running or not found
    """
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
        db: Database session

    Returns:
        List of traces ordered by sequence number
    """
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
