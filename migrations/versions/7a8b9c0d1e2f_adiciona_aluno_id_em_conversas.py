"""adiciona aluno_id em conversas

Revision ID: 7a8b9c0d1e2f
Revises: b5dd2dfa4a6d
Create Date: 2026-05-28 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, None] = 'b5dd2dfa4a6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversas",
        sa.Column("aluno_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_conversas_aluno_id",
        "conversas",
        "alunos",
        ["aluno_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_conversas_aluno_id", "conversas", type_="foreignkey")
    op.drop_column("conversas", "aluno_id")
