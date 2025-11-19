"""
FastAPI application entry point.

Main application setup including:
- CORS middleware
- Exception handlers
- API routers
- Startup/shutdown events
- OpenAPI documentation
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from core.config import settings
from core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Handles:
    - Database connection initialization on startup
    - Cleanup on shutdown
    """
    # Startup
    logger.info("Starting DeepAgents Control Platform API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Version: {settings.VERSION}")

    # Test database connection
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql("SELECT 1")
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.warning("Application starting without database connection")

    yield

    # Shutdown
    logger.info("Shutting down DeepAgents Control Platform API")
    await engine.dispose()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise-grade administrative interface for creating, configuring, and managing AI agents",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware (Problem #15)
from core.rate_limit import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    redis_url=str(settings.REDIS_URL),
    default_limit=60,  # 60 requests per minute
    default_window=60,  # 1 minute window
)

# Add metrics collection middleware
from core.middleware import MetricsMiddleware

app.add_middleware(MetricsMiddleware)


# Exception Handlers


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with consistent error response format.

    Args:
        request: The request that caused the exception
        exc: The HTTP exception

    Returns:
        JSON response with error details
    """
    logger.warning(f"HTTP {exc.status_code} error: {exc.detail} - {request.url}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors with detailed error information.

    Args:
        request: The request that failed validation
        exc: The validation exception

    Returns:
        JSON response with validation error details
    """
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")

    # Convert errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        serializable_error = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": str(error.get("msg", "")),
            "input": str(error.get("input", "")) if error.get("input") is not None else None,
        }
        # Add context if present
        if "ctx" in error:
            serializable_error["ctx"] = {k: str(v) for k, v in error["ctx"].items()}
        errors.append(serializable_error)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
            "body": exc.body,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions with error logging.

    Args:
        request: The request that caused the exception
        exc: The exception

    Returns:
        JSON response with generic error message
    """
    exc_str = str(exc).replace("{", "{{").replace("}", "}}")
    logger.error(f"Unexpected error on {request.url}: {exc_str}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "status_code": 500,
        },
    )


# Health Check Endpoint


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        Health status and version information
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "service": settings.PROJECT_NAME,
    }


# API Routers
from api.v1 import (
    advanced_config,
    agents,
    analytics,
    auth,
    executions,
    external_tools,
    health,
    metrics,
    monitoring,
    templates,
    tools,
    users,
)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(agents.router, prefix=settings.API_V1_STR)
app.include_router(templates.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(executions.router, prefix=settings.API_V1_STR)
app.include_router(external_tools.router, prefix=settings.API_V1_STR)
app.include_router(monitoring.router, prefix=settings.API_V1_STR)
app.include_router(tools.router, prefix=settings.API_V1_STR)
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(metrics.router, prefix=settings.API_V1_STR)
app.include_router(advanced_config.router, prefix=settings.API_V1_STR)


# Root endpoint (optional)
@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """
    Root endpoint with API information.

    Returns:
        Welcome message and API documentation link
    """
    return {
        "message": "DeepAgents Control Platform API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    # Run with uvicorn when executed directly
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
