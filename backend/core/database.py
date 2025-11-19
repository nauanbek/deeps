"""
Database configuration and session management for async SQLAlchemy.

Provides:
- AsyncEngine for async database operations
- AsyncSession factory for dependency injection
- Base declarative class for all models
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

# Database URL loaded from settings (environment variables)
# Format: postgresql+asyncpg://user:password@host:port/database?sslmode=require
DATABASE_URL = settings.DATABASE_URL

# SSL/TLS configuration for PostgreSQL (production security requirement)
# For production: Use DATABASE_URL with ?sslmode=require parameter
# Example: postgresql+asyncpg://user:password@host:port/db?sslmode=require
connect_args = {}
if settings.ENVIRONMENT == "production" and "postgresql" in DATABASE_URL.lower():
    # In production with PostgreSQL, SSL should be enforced
    # The sslmode parameter should be in the connection string
    if "sslmode" not in DATABASE_URL.lower():
        # Log warning if SSL is not configured in production
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            "Production PostgreSQL connection without SSL! "
            "Add '?sslmode=require' to DATABASE_URL for security."
        )

# Create async engine with connection pooling
# Increased pool size for production concurrency (Problem #12)
engine = create_async_engine(
    DATABASE_URL,
    echo=(settings.ENVIRONMENT == "development"),  # Logging only in development
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=20,  # Increased from 10 for concurrent load
    max_overflow=40,  # Increased from 20 for burst traffic
    pool_recycle=3600,  # Recycle connections after 1 hour to prevent stale connections
    connect_args=connect_args,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: Database session for use in FastAPI endpoints

    Example:
        @app.get("/agents")
        async def list_agents(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.

    This should be called on application startup.
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
