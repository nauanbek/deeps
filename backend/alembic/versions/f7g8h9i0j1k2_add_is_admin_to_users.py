"""add is_admin to users

Revision ID: f7g8h9i0j1k2
Revises: e1f2g3h4i5j6
Create Date: 2025-11-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f7g8h9i0j1k2'
down_revision: Union[str, None] = 'e1f2g3h4i5j6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))

    # Create index for is_admin column
    op.create_index(op.f('ix_users_is_admin'), 'users', ['is_admin'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('ix_users_is_admin'), table_name='users')

    # Drop is_admin column from users table
    op.drop_column('users', 'is_admin')
