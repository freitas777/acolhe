"""Make disciplina_id nullable in conteudo_feedback

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'cf0000000002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('conteudo_feedback', 'disciplina_id', existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    # Set NULL values to a default before making NOT NULL
    op.execute("UPDATE conteudo_feedback SET disciplina_id = 1 WHERE disciplina_id IS NULL")
    op.alter_column('conteudo_feedback', 'disciplina_id', existing_type=sa.Integer(), nullable=False)
