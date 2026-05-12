"""adiciona setor, aprovado_napne e pendencias_validacao

Revision ID: d4e5f6a7b8c9
Revises: 16f242611856
Create Date: 2026-05-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = '16f242611856'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("setor", sa.String(200), nullable=True))
    op.add_column("usuarios", sa.Column("aprovado_napne", sa.Boolean(), nullable=False, server_default="false"))

    op.create_table(
        "pendencias_validacao",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("aluno_id", sa.Integer(), nullable=False),
        sa.Column("indicado_por_id", sa.Integer(), nullable=True),
        sa.Column("validado_por_id", sa.Integer(), nullable=True),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pendente"),
        sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("validado_em", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["aluno_id"], ["alunos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["indicado_por_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["validado_por_id"], ["usuarios.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("pendencias_validacao")
    op.drop_column("usuarios", "aprovado_napne")
    op.drop_column("usuarios", "setor")
