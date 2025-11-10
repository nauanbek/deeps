#!/usr/bin/env python3
"""
Database initialization script.

Creates all tables and optionally seeds initial data.
For production, use Alembic migrations instead.
"""

import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal, init_db
from models import Agent, Execution, Tool, Trace, User


async def create_tables() -> None:
    """Create all database tables."""
    print("Creating database tables...")
    try:
        await init_db()
        print("✓ All tables created successfully")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        sys.exit(1)


async def seed_data() -> None:
    """Seed initial data for development/testing.

    WARNING: This creates a user with a default password (admin123).
    This is for DEVELOPMENT ONLY. Never use this in production.
    Change the password immediately after first login.
    """
    print("\nSeeding initial data...")
    print("⚠️  WARNING: Creating default credentials for DEVELOPMENT ONLY")
    print("⚠️  Change password immediately after first login!")

    async with AsyncSessionLocal() as session:
        try:
            # Check if user already exists
            from sqlalchemy import select

            result = await session.execute(select(User).where(User.username == "admin"))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print("✓ Admin user already exists, skipping seed")
                return

            # Create admin user
            from passlib.context import CryptContext

            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=pwd_context.hash("admin123"),  # SECURITY: For dev only! Change immediately!
                is_active=True,
            )
            session.add(admin_user)
            await session.flush()  # Get user ID

            # Create sample agent
            sample_agent = Agent(
                name="Sample Claude Agent",
                description="A sample agent using Claude 3.5 Sonnet for testing",
                model_provider="anthropic",
                model_name="claude-3-5-sonnet-20241022",
                temperature=0.7,
                max_tokens=4096,
                system_prompt="You are a helpful AI assistant.",
                planning_enabled=True,
                filesystem_enabled=False,
                created_by_id=admin_user.id,
                is_active=True,
            )
            session.add(sample_agent)

            # Create sample tools
            search_tool = Tool(
                name="web_search",
                description="Search the web for information",
                tool_type="builtin",
                configuration={
                    "api_provider": "tavily",
                    "max_results": 5,
                },
                schema_definition={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                    },
                    "required": ["query"],
                },
                created_by_id=admin_user.id,
                is_active=True,
            )
            session.add(search_tool)

            code_tool = Tool(
                name="python_repl",
                description="Execute Python code in a REPL",
                tool_type="builtin",
                configuration={
                    "timeout": 30,
                    "max_output_length": 10000,
                },
                schema_definition={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python code to execute"},
                    },
                    "required": ["code"],
                },
                created_by_id=admin_user.id,
                is_active=True,
            )
            session.add(code_tool)

            await session.commit()

            print("✓ Seeded initial data:")
            print(f"  - User: {admin_user.username} (password: admin123)")
            print(f"  - Agent: {sample_agent.name}")
            print(f"  - Tools: {search_tool.name}, {code_tool.name}")
            print("\n⚠️  SECURITY WARNING: Default password 'admin123' is INSECURE!")
            print("⚠️  Change it immediately at first login or via the API")

        except Exception as e:
            await session.rollback()
            print(f"✗ Error seeding data: {e}")
            raise


async def main() -> None:
    """Main initialization function."""
    print("=" * 60)
    print("DeepAgents Control Platform - Database Initialization")
    print("=" * 60)

    # Create tables
    await create_tables()

    # Ask if user wants to seed data
    if len(sys.argv) > 1 and sys.argv[1] == "--seed":
        await seed_data()
    else:
        print("\nTo seed initial data, run: python init_db.py --seed")

    print("\n" + "=" * 60)
    print("Database initialization complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
