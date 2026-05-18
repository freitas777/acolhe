"""adiciona campos importacao suap ao aluno

Revision ID: e8f1a2b3c4d5
Revises: d4e5f6a7b8c9
Create Date: 2026-05-13 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "e8f1a2b3c4d5"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alunos", sa.Column("curso", sa.String(300), nullable=True))
    op.add_column("alunos", sa.Column("campus", sa.String(200), nullable=True))
    op.add_column("alunos", sa.Column("foto_url", sa.Text(), nullable=True))
    op.add_column("alunos", sa.Column("email", sa.String(200), nullable=True))
    op.add_column("alunos", sa.Column("cpf", sa.String(14), nullable=True))
    op.add_column("alunos", sa.Column("status_acompanhamento", sa.String(50), nullable=False, server_default="aguardando_indicacao"))
    op.add_column("alunos", sa.Column("data_importacao", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("alunos", "data_importacao")
    op.drop_column("alunos", "status_acompanhamento")
    op.drop_column("alunos", "cpf")
    op.drop_column("alunos", "email")
    op.drop_column("alunos", "foto_url")
    op.drop_column("alunos", "campus")
    op.drop_column("alunos", "curso")
