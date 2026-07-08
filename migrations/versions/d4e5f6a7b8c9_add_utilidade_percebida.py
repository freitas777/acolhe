"""Add utilidade_percebida field to conteudo_feedback

Revision ID: cf0000000002
Revises: cf0000000001
Create Date: 2026-07-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'cf0000000002'
down_revision = 'cf0000000001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('conteudo_feedback', sa.Column('utilidade_percebida', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('conteudo_feedback', 'utilidade_percebida')
