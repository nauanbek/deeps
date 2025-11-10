"""update_subagent_model_for_agent_references

Revision ID: db69f2686c4d
Revises: b82b7b0c49b9
Create Date: 2025-11-08 12:43:26.654507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db69f2686c4d'
down_revision: Union[str, None] = 'b82b7b0c49b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Update subagents table to support agent-to-agent references.

    Changes:
    - Rename parent_agent_id to agent_id (parent agent)
    - Add subagent_id (references agents table)
    - Remove name and description columns (get from referenced agent)
    - Replace agent_config JSONB with delegation_prompt TEXT and priority INTEGER
    """
    # Drop existing indexes
    op.drop_index('idx_subagents_parent_name', table_name='subagents')
    op.drop_index('idx_subagents_parent', table_name='subagents')

    # Rename parent_agent_id to agent_id
    op.alter_column('subagents', 'parent_agent_id', new_column_name='agent_id')

    # Add new columns
    op.add_column('subagents', sa.Column('subagent_id', sa.Integer(), nullable=True))
    op.add_column('subagents', sa.Column('delegation_prompt', sa.Text(), nullable=True))
    op.add_column('subagents', sa.Column('priority', sa.Integer(), nullable=False, server_default='0'))

    # Create foreign key for subagent_id
    op.create_foreign_key(
        'fk_subagents_subagent_id_agents',
        'subagents',
        'agents',
        ['subagent_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Drop old columns
    op.drop_column('subagents', 'name')
    op.drop_column('subagents', 'description')
    op.drop_column('subagents', 'agent_config')

    # Make subagent_id NOT NULL after migration
    op.alter_column('subagents', 'subagent_id', nullable=False)

    # Create new indexes
    op.create_index('idx_subagents_agent_id', 'subagents', ['agent_id'])
    op.create_index('idx_subagents_subagent_id', 'subagents', ['subagent_id'])
    op.create_index('idx_subagents_agent_subagent', 'subagents', ['agent_id', 'subagent_id'], unique=True)
    op.create_index('idx_subagents_priority', 'subagents', ['agent_id', 'priority'])


def downgrade() -> None:
    """
    Rollback subagents table to original schema.
    """
    # Drop new indexes
    op.drop_index('idx_subagents_priority', table_name='subagents')
    op.drop_index('idx_subagents_agent_subagent', table_name='subagents')
    op.drop_index('idx_subagents_subagent_id', table_name='subagents')
    op.drop_index('idx_subagents_agent_id', table_name='subagents')

    # Add back old columns
    op.add_column('subagents', sa.Column('agent_config', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('subagents', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('subagents', sa.Column('name', sa.String(255), nullable=False, server_default='unnamed'))

    # Drop new columns and foreign key
    op.drop_constraint('fk_subagents_subagent_id_agents', 'subagents', type_='foreignkey')
    op.drop_column('subagents', 'priority')
    op.drop_column('subagents', 'delegation_prompt')
    op.drop_column('subagents', 'subagent_id')

    # Rename agent_id back to parent_agent_id
    op.alter_column('subagents', 'agent_id', new_column_name='parent_agent_id')

    # Recreate original indexes
    op.create_index('idx_subagents_parent', 'subagents', ['parent_agent_id'])
    op.create_index('idx_subagents_parent_name', 'subagents', ['parent_agent_id', 'name'])
