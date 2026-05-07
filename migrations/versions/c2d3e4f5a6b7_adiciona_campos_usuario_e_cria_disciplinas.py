"""adiciona campos ao usuario e cria tabela disciplinas

Revision ID: c2d3e4f5a6b7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-06 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("matricula", sa.String(50), nullable=True))
    op.add_column("usuarios", sa.Column("campus", sa.String(200), nullable=True))
    op.add_column("usuarios", sa.Column("tipo_vinculo", sa.String(100), nullable=True))

    op.execute("ALTER TABLE usuarios ALTER COLUMN tipo_perfil DROP DEFAULT")
    op.execute("ALTER TABLE usuarios ALTER COLUMN tipo_perfil TYPE VARCHAR(50) USING tipo_perfil::text")
    op.execute("ALTER TABLE usuarios ALTER COLUMN tipo_perfil SET DEFAULT 'aluno'")
    op.execute("ALTER TABLE usuarios ALTER COLUMN tipo_perfil SET NOT NULL")

    op.create_table(
        "disciplinas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("suap_id", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.String(300), nullable=False),
        sa.Column("sigla", sa.String(50), nullable=True),
        sa.Column("situacao", sa.String(100), nullable=True),
        sa.Column("professor", sa.String(200), nullable=True),
        sa.Column("semestre", sa.String(10), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("criada_em", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("disciplinas")

    op.execute("ALTER TABLE usuarios ALTER COLUMN tipo_perfil DROP DEFAULT")
    op.execute("ALTER TABLE usuarios ALTER COLUMN tipo_perfil SET DEFAULT 'professor'")

    op.drop_column("usuarios", "tipo_vinculo")
    op.drop_column("usuarios", "campus")
    op.drop_column("usuarios", "matricula")
