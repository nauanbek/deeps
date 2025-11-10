"""Initial schema for DeepAgents Control Platform

Revision ID: 001
Revises:
Create Date: 2025-11-08

Creates all tables for the DeepAgents Control Platform:
- users: User authentication and authorization
- agents: AI agent configuration
- tools: Tool registry
- agent_tools: Many-to-many agent-tool association
- subagents: Hierarchical subagent configuration
- executions: Agent execution tracking
- traces: Granular execution event logging

All tables include proper indexes, constraints, and audit trails.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create all tables and indexes for the DeepAgents Control Platform.

    Table creation order respects foreign key dependencies:
    1. users (no dependencies)
    2. agents (depends on users)
    3. tools (depends on users)
    4. agent_tools (depends on agents and tools)
    5. subagents (depends on agents)
    6. executions (depends on agents and users)
    7. traces (depends on executions)
    """

    # =========================================================================
    # 1. USERS TABLE
    # =========================================================================
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
    )

    # Users indexes
    op.create_index('idx_users_active', 'users', ['is_active'])
    op.create_index('idx_users_username_active', 'users', ['username', 'is_active'])
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # =========================================================================
    # 2. AGENTS TABLE
    # =========================================================================
    op.create_table(
        'agents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model_provider', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=255), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False, server_default=sa.text('0.7')),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('planning_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('filesystem_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('additional_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Agents indexes
    op.create_index('idx_agents_created_by_active', 'agents', ['created_by_id', 'is_active'])
    op.create_index('idx_agents_provider_model', 'agents', ['model_provider', 'model_name'])
    op.create_index('idx_agents_features', 'agents', ['planning_enabled', 'filesystem_enabled'])
    op.create_index('idx_agents_created_at', 'agents', ['created_at'])
    op.create_index(op.f('ix_agents_id'), 'agents', ['id'], unique=False)
    op.create_index(op.f('ix_agents_name'), 'agents', ['name'], unique=False)
    op.create_index(op.f('ix_agents_model_provider'), 'agents', ['model_provider'], unique=False)
    op.create_index(op.f('ix_agents_planning_enabled'), 'agents', ['planning_enabled'], unique=False)
    op.create_index(op.f('ix_agents_filesystem_enabled'), 'agents', ['filesystem_enabled'], unique=False)
    op.create_index(op.f('ix_agents_created_by_id'), 'agents', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_agents_is_active'), 'agents', ['is_active'], unique=False)

    # =========================================================================
    # 3. TOOLS TABLE
    # =========================================================================
    op.create_table(
        'tools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tool_type', sa.String(length=50), nullable=False),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('schema_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Tools indexes
    op.create_index('idx_tools_type_active', 'tools', ['tool_type', 'is_active'])
    op.create_index('idx_tools_name_type', 'tools', ['name', 'tool_type'])
    op.create_index('idx_tools_created_by', 'tools', ['created_by_id', 'created_at'])
    op.create_index(op.f('ix_tools_id'), 'tools', ['id'], unique=False)
    op.create_index(op.f('ix_tools_name'), 'tools', ['name'], unique=False)
    op.create_index(op.f('ix_tools_tool_type'), 'tools', ['tool_type'], unique=False)
    op.create_index(op.f('ix_tools_created_by_id'), 'tools', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_tools_is_active'), 'tools', ['is_active'], unique=False)

    # =========================================================================
    # 4. AGENT_TOOLS TABLE (Many-to-Many Association)
    # =========================================================================
    op.create_table(
        'agent_tools',
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sa.Integer(), nullable=False),
        sa.Column('configuration_override', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('agent_id', 'tool_id'),
    )

    # Agent_tools indexes
    op.create_index('idx_agent_tools_agent', 'agent_tools', ['agent_id'])
    op.create_index('idx_agent_tools_tool', 'agent_tools', ['tool_id'])

    # =========================================================================
    # 5. SUBAGENTS TABLE
    # =========================================================================
    op.create_table(
        'subagents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_agent_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('agent_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Subagents indexes
    op.create_index('idx_subagents_parent', 'subagents', ['parent_agent_id'])
    op.create_index('idx_subagents_parent_name', 'subagents', ['parent_agent_id', 'name'])
    op.create_index(op.f('ix_subagents_id'), 'subagents', ['id'], unique=False)
    op.create_index(op.f('ix_subagents_parent_agent_id'), 'subagents', ['parent_agent_id'], unique=False)

    # =========================================================================
    # 6. EXECUTIONS TABLE
    # =========================================================================
    op.create_table(
        'executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('input_prompt', sa.Text(), nullable=False),
        sa.Column('execution_params', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('status', sa.String(length=50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('estimated_cost', sa.DECIMAL(precision=10, scale=6), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.Column('output', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Executions indexes
    op.create_index('idx_executions_agent_status', 'executions', ['agent_id', 'status'])
    op.create_index('idx_executions_user_created', 'executions', ['created_by_id', 'created_at'])
    op.create_index('idx_executions_status_started', 'executions', ['status', 'started_at'])
    op.create_index('idx_executions_agent_started', 'executions', ['agent_id', 'started_at'])
    op.create_index('idx_executions_cost', 'executions', ['estimated_cost'])
    op.create_index(op.f('ix_executions_id'), 'executions', ['id'], unique=False)
    op.create_index(op.f('ix_executions_agent_id'), 'executions', ['agent_id'], unique=False)
    op.create_index(op.f('ix_executions_created_by_id'), 'executions', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_executions_status'), 'executions', ['status'], unique=False)
    op.create_index(op.f('ix_executions_started_at'), 'executions', ['started_at'], unique=False)

    # =========================================================================
    # 7. TRACES TABLE
    # =========================================================================
    op.create_table(
        'traces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.Integer(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['execution_id'], ['executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Traces indexes
    op.create_index('idx_traces_execution_sequence', 'traces', ['execution_id', 'sequence_number'])
    op.create_index('idx_traces_execution_timestamp', 'traces', ['execution_id', 'timestamp'])
    op.create_index('idx_traces_execution_type', 'traces', ['execution_id', 'event_type'])
    op.create_index('idx_traces_timestamp', 'traces', ['timestamp'])
    op.create_index(op.f('ix_traces_id'), 'traces', ['id'], unique=False)
    op.create_index(op.f('ix_traces_execution_id'), 'traces', ['execution_id'], unique=False)
    op.create_index(op.f('ix_traces_sequence_number'), 'traces', ['sequence_number'], unique=False)
    op.create_index(op.f('ix_traces_timestamp'), 'traces', ['timestamp'], unique=False)
    op.create_index(op.f('ix_traces_event_type'), 'traces', ['event_type'], unique=False)


def downgrade() -> None:
    """
    Drop all tables in reverse order to respect foreign key dependencies.
    """

    # Drop tables in reverse order
    op.drop_table('traces')
    op.drop_table('executions')
    op.drop_table('subagents')
    op.drop_table('agent_tools')
    op.drop_table('tools')
    op.drop_table('agents')
    op.drop_table('users')
