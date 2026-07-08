"""adiciona disciplina_id em conversas

Revision ID: g1h2i3j4k5l6
Revises: 91710d0a9f13
Create Date: 2026-07-05 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'g1h2i3j4k5l6'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Verifica se a coluna já existe
    result = conn.execute(
        sa.text("SELECT column_name FROM information_schema.columns WHERE table_name='conversas' AND column_name='disciplina_id'")
    )
    if not result.scalar():
        op.add_column(
            "conversas",
            sa.Column("disciplina_id", sa.Integer(), nullable=True),
        )
    # Verifica se a FK já existe
    result = conn.execute(
        sa.text("SELECT constraint_name FROM information_schema.table_constraints WHERE table_name='conversas' AND constraint_name='fk_conversas_disciplina_id'")
    )
    if not result.scalar():
        op.create_foreign_key(
            "fk_conversas_disciplina_id",
            "conversas",
            "disciplinas",
            ["disciplina_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    op.drop_constraint("fk_conversas_disciplina_id", "conversas", type_="foreignkey")
    op.drop_column("conversas", "disciplina_id")
