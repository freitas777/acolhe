"""cria tabelas conversa e mensagem

Revision ID: a1b2c3d4e5f6
Revises: 6f2c5e53a895
Create Date: 2026-05-06 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "6f2c5e53a895"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("titulo", sa.String(255), nullable=False, server_default="Nova conversa"),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column(
            "criada_em",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "mensagens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversa_id", sa.String(36), nullable=False),
        sa.Column("papel", sa.String(20), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column(
            "criada_em",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["conversa_id"], ["conversas.id"], ondelete="CASCADE"),
    )

    op.create_index("ix_mensagens_conversa_id", "mensagens", ["conversa_id"])


def downgrade() -> None:
    op.drop_index("ix_mensagens_conversa_id", table_name="mensagens")
    op.drop_table("mensagens")
    op.drop_table("conversas")
