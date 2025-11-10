"""add_external_tools_integration

Revision ID: e1f2g3h4i5j6
Revises: a1b2c3d4e5f6
Create Date: 2025-11-09 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e1f2g3h4i5j6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create external_tool_configs table
    op.create_table(
        'external_tool_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(length=255), nullable=False),
        sa.Column('tool_type', sa.String(length=50), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('configuration', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_tested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('test_status', sa.String(length=50), nullable=True),
        sa.Column('test_error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for external_tool_configs
    op.create_index(op.f('ix_external_tool_configs_id'), 'external_tool_configs', ['id'], unique=False)
    op.create_index(op.f('ix_external_tool_configs_user_id'), 'external_tool_configs', ['user_id'], unique=False)
    op.create_index(op.f('ix_external_tool_configs_tool_name'), 'external_tool_configs', ['tool_name'], unique=False)
    op.create_index(op.f('ix_external_tool_configs_tool_type'), 'external_tool_configs', ['tool_type'], unique=False)
    op.create_index(op.f('ix_external_tool_configs_is_active'), 'external_tool_configs', ['is_active'], unique=False)
    op.create_index(op.f('ix_external_tool_configs_created_at'), 'external_tool_configs', ['created_at'], unique=False)
    op.create_index('idx_external_tool_configs_user_active', 'external_tool_configs', ['user_id', 'is_active'], unique=False)
    op.create_index('idx_external_tool_configs_user_tool_name', 'external_tool_configs', ['user_id', 'tool_name'], unique=True)
    op.create_index('idx_external_tool_configs_tool_type', 'external_tool_configs', ['tool_type'], unique=False)
    op.create_index('idx_external_tool_configs_provider', 'external_tool_configs', ['provider'], unique=False)

    # Create tool_execution_logs table
    op.create_table(
        'tool_execution_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('execution_id', sa.Integer(), nullable=True),
        sa.Column('tool_config_id', sa.Integer(), nullable=True),
        sa.Column('tool_name', sa.String(length=255), nullable=False),
        sa.Column('tool_type', sa.String(length=50), nullable=False),
        sa.Column('tool_provider', sa.String(length=50), nullable=False),
        sa.Column('input_params', sa.JSON(), nullable=False),
        sa.Column('output_summary', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['execution_id'], ['executions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tool_config_id'], ['external_tool_configs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for tool_execution_logs
    op.create_index(op.f('ix_tool_execution_logs_id'), 'tool_execution_logs', ['id'], unique=False)
    op.create_index(op.f('ix_tool_execution_logs_user_id'), 'tool_execution_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_tool_execution_logs_agent_id'), 'tool_execution_logs', ['agent_id'], unique=False)
    op.create_index(op.f('ix_tool_execution_logs_execution_id'), 'tool_execution_logs', ['execution_id'], unique=False)
    op.create_index(op.f('ix_tool_execution_logs_tool_config_id'), 'tool_execution_logs', ['tool_config_id'], unique=False)
    op.create_index(op.f('ix_tool_execution_logs_tool_name'), 'tool_execution_logs', ['tool_name'], unique=False)
    op.create_index(op.f('ix_tool_execution_logs_tool_type'), 'tool_execution_logs', ['tool_type'], unique=False)
    op.create_index(op.f('ix_tool_execution_logs_success'), 'tool_execution_logs', ['success'], unique=False)
    op.create_index(op.f('ix_tool_execution_logs_created_at'), 'tool_execution_logs', ['created_at'], unique=False)
    op.create_index('idx_tool_execution_logs_user_created', 'tool_execution_logs', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_tool_execution_logs_agent_created', 'tool_execution_logs', ['agent_id', 'created_at'], unique=False)
    op.create_index('idx_tool_execution_logs_execution', 'tool_execution_logs', ['execution_id'], unique=False)
    op.create_index('idx_tool_execution_logs_tool_name_success', 'tool_execution_logs', ['tool_name', 'success'], unique=False)
    op.create_index('idx_tool_execution_logs_tool_type_created', 'tool_execution_logs', ['tool_type', 'created_at'], unique=False)

    # Add langchain_tool_ids column to agents table
    op.add_column('agents', sa.Column('langchain_tool_ids', postgresql.ARRAY(sa.Integer()), nullable=True))


def downgrade() -> None:
    # Remove langchain_tool_ids column from agents table
    op.drop_column('agents', 'langchain_tool_ids')

    # Drop tool_execution_logs indexes
    op.drop_index('idx_tool_execution_logs_tool_type_created', table_name='tool_execution_logs')
    op.drop_index('idx_tool_execution_logs_tool_name_success', table_name='tool_execution_logs')
    op.drop_index('idx_tool_execution_logs_execution', table_name='tool_execution_logs')
    op.drop_index('idx_tool_execution_logs_agent_created', table_name='tool_execution_logs')
    op.drop_index('idx_tool_execution_logs_user_created', table_name='tool_execution_logs')
    op.drop_index(op.f('ix_tool_execution_logs_created_at'), table_name='tool_execution_logs')
    op.drop_index(op.f('ix_tool_execution_logs_success'), table_name='tool_execution_logs')
    op.drop_index(op.f('ix_tool_execution_logs_tool_type'), table_name='tool_execution_logs')
    op.drop_index(op.f('ix_tool_execution_logs_tool_name'), table_name='tool_execution_logs')
    op.drop_index(op.f('ix_tool_execution_logs_tool_config_id'), table_name='tool_execution_logs')
    op.drop_index(op.f('ix_tool_execution_logs_execution_id'), table_name='tool_execution_logs')
    op.drop_index(op.f('ix_tool_execution_logs_agent_id'), table_name='tool_execution_logs')
    op.drop_index(op.f('ix_tool_execution_logs_user_id'), table_name='tool_execution_logs')
    op.drop_index(op.f('ix_tool_execution_logs_id'), table_name='tool_execution_logs')

    # Drop tool_execution_logs table
    op.drop_table('tool_execution_logs')

    # Drop external_tool_configs indexes
    op.drop_index('idx_external_tool_configs_provider', table_name='external_tool_configs')
    op.drop_index('idx_external_tool_configs_tool_type', table_name='external_tool_configs')
    op.drop_index('idx_external_tool_configs_user_tool_name', table_name='external_tool_configs')
    op.drop_index('idx_external_tool_configs_user_active', table_name='external_tool_configs')
    op.drop_index(op.f('ix_external_tool_configs_created_at'), table_name='external_tool_configs')
    op.drop_index(op.f('ix_external_tool_configs_is_active'), table_name='external_tool_configs')
    op.drop_index(op.f('ix_external_tool_configs_tool_type'), table_name='external_tool_configs')
    op.drop_index(op.f('ix_external_tool_configs_tool_name'), table_name='external_tool_configs')
    op.drop_index(op.f('ix_external_tool_configs_user_id'), table_name='external_tool_configs')
    op.drop_index(op.f('ix_external_tool_configs_id'), table_name='external_tool_configs')

    # Drop external_tool_configs table
    op.drop_table('external_tool_configs')
