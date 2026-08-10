"""add atualizada_em to conversas

Revision ID: j4k5l6m7n8o9
Revises: i3j4k5l6m7n8
Create Date: 2026-08-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

revision = 'j4k5l6m7n8o9'
down_revision = 'bb3a39107762'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('conversas', sa.Column('atualizada_em', sa.DateTime(), nullable=False, server_default=func.now()))
    op.create_index('ix_conversas_atualizada_em', 'conversas', ['atualizada_em'])


def downgrade() -> None:
    op.drop_index('ix_conversas_atualizada_em', table_name='conversas')
    op.drop_column('conversas', 'atualizada_em')
