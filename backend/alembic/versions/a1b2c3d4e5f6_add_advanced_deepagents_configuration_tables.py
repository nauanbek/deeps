"""add_advanced_deepagents_configuration_tables

Revision ID: a1b2c3d4e5f6
Revises: 54b1fdcbedae
Create Date: 2025-11-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '54b1fdcbedae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agent_backend_configs table
    op.create_table(
        'agent_backend_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('backend_type', sa.String(length=50), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', name='uq_backend_config_agent')
    )
    op.create_index(op.f('ix_agent_backend_configs_id'), 'agent_backend_configs', ['id'], unique=False)
    op.create_index('idx_backend_configs_agent', 'agent_backend_configs', ['agent_id'], unique=False)
    op.create_index('idx_backend_configs_type', 'agent_backend_configs', ['backend_type'], unique=False)

    # Create agent_memory_namespaces table
    op.create_table(
        'agent_memory_namespaces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('namespace', sa.String(length=255), nullable=False),
        sa.Column('store_type', sa.String(length=50), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', name='uq_memory_namespace_agent'),
        sa.UniqueConstraint('namespace', name='uq_memory_namespace_unique')
    )
    op.create_index(op.f('ix_agent_memory_namespaces_id'), 'agent_memory_namespaces', ['id'], unique=False)
    op.create_index('idx_memory_namespaces_agent', 'agent_memory_namespaces', ['agent_id'], unique=False)
    op.create_index('idx_memory_namespaces_namespace', 'agent_memory_namespaces', ['namespace'], unique=False)
    op.create_index('idx_memory_namespaces_store_type', 'agent_memory_namespaces', ['store_type'], unique=False)

    # Create agent_memory_files table
    op.create_table(
        'agent_memory_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('namespace', sa.String(length=255), nullable=False),
        sa.Column('key', sa.String(length=1024), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('namespace', 'key', name='uq_namespace_key')
    )
    op.create_index(op.f('ix_agent_memory_files_id'), 'agent_memory_files', ['id'], unique=False)
    op.create_index('idx_memory_files_namespace', 'agent_memory_files', ['namespace'], unique=False)
    op.create_index('idx_memory_files_namespace_key', 'agent_memory_files', ['namespace', 'key'], unique=False)
    op.create_index('idx_memory_files_updated', 'agent_memory_files', ['updated_at'], unique=False)

    # Create agent_interrupt_configs table
    op.create_table(
        'agent_interrupt_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(length=255), nullable=False),
        sa.Column('allowed_decisions', sa.JSON(), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', 'tool_name', name='uq_agent_tool_interrupt')
    )
    op.create_index(op.f('ix_agent_interrupt_configs_id'), 'agent_interrupt_configs', ['id'], unique=False)
    op.create_index('idx_interrupt_configs_agent', 'agent_interrupt_configs', ['agent_id'], unique=False)
    op.create_index('idx_interrupt_configs_tool', 'agent_interrupt_configs', ['tool_name'], unique=False)
    op.create_index('idx_interrupt_configs_agent_tool', 'agent_interrupt_configs', ['agent_id', 'tool_name'], unique=False)

    # Create execution_approvals table
    op.create_table(
        'execution_approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(length=255), nullable=False),
        sa.Column('tool_args', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('decision_data', sa.JSON(), nullable=False),
        sa.Column('decided_by_id', sa.Integer(), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['decided_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['execution_id'], ['executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_execution_approvals_id'), 'execution_approvals', ['id'], unique=False)
    op.create_index(op.f('ix_execution_approvals_created_at'), 'execution_approvals', ['created_at'], unique=False)
    op.create_index(op.f('ix_execution_approvals_status'), 'execution_approvals', ['status'], unique=False)
    op.create_index('idx_approvals_execution', 'execution_approvals', ['execution_id'], unique=False)
    op.create_index('idx_approvals_execution_status', 'execution_approvals', ['execution_id', 'status'], unique=False)
    op.create_index('idx_approvals_pending', 'execution_approvals', ['status', 'created_at'], unique=False)
    op.create_index('idx_approvals_tool', 'execution_approvals', ['tool_name'], unique=False)


def downgrade() -> None:
    # Drop execution_approvals table
    op.drop_index('idx_approvals_tool', table_name='execution_approvals')
    op.drop_index('idx_approvals_pending', table_name='execution_approvals')
    op.drop_index('idx_approvals_execution_status', table_name='execution_approvals')
    op.drop_index('idx_approvals_execution', table_name='execution_approvals')
    op.drop_index(op.f('ix_execution_approvals_status'), table_name='execution_approvals')
    op.drop_index(op.f('ix_execution_approvals_created_at'), table_name='execution_approvals')
    op.drop_index(op.f('ix_execution_approvals_id'), table_name='execution_approvals')
    op.drop_table('execution_approvals')

    # Drop agent_interrupt_configs table
    op.drop_index('idx_interrupt_configs_agent_tool', table_name='agent_interrupt_configs')
    op.drop_index('idx_interrupt_configs_tool', table_name='agent_interrupt_configs')
    op.drop_index('idx_interrupt_configs_agent', table_name='agent_interrupt_configs')
    op.drop_index(op.f('ix_agent_interrupt_configs_id'), table_name='agent_interrupt_configs')
    op.drop_table('agent_interrupt_configs')

    # Drop agent_memory_files table
    op.drop_index('idx_memory_files_updated', table_name='agent_memory_files')
    op.drop_index('idx_memory_files_namespace_key', table_name='agent_memory_files')
    op.drop_index('idx_memory_files_namespace', table_name='agent_memory_files')
    op.drop_index(op.f('ix_agent_memory_files_id'), table_name='agent_memory_files')
    op.drop_table('agent_memory_files')

    # Drop agent_memory_namespaces table
    op.drop_index('idx_memory_namespaces_store_type', table_name='agent_memory_namespaces')
    op.drop_index('idx_memory_namespaces_namespace', table_name='agent_memory_namespaces')
    op.drop_index('idx_memory_namespaces_agent', table_name='agent_memory_namespaces')
    op.drop_index(op.f('ix_agent_memory_namespaces_id'), table_name='agent_memory_namespaces')
    op.drop_table('agent_memory_namespaces')

    # Drop agent_backend_configs table
    op.drop_index('idx_backend_configs_type', table_name='agent_backend_configs')
    op.drop_index('idx_backend_configs_agent', table_name='agent_backend_configs')
    op.drop_index(op.f('ix_agent_backend_configs_id'), table_name='agent_backend_configs')
    op.drop_table('agent_backend_configs')
