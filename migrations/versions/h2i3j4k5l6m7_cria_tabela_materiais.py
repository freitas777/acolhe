"""cria tabela materiais

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-07-06 13:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'h2i3j4k5l6m7'
down_revision: Union[str, None] = 'g1h2i3j4k5l6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "materiais",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("disciplina_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("nome_original", sa.String(300), nullable=False),
        sa.Column("nome_arquivo", sa.String(100), nullable=False),
        sa.Column("tipo_arquivo", sa.String(50), nullable=False),
        sa.Column("tamanho", sa.BigInteger(), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["disciplina_id"],
            ["disciplinas.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome_arquivo"),
    )
    op.create_index("ix_materiais_disciplina_id", "materiais", ["disciplina_id"])


def downgrade() -> None:
    op.drop_index("ix_materiais_disciplina_id", table_name="materiais")
    op.drop_table("materiais")
