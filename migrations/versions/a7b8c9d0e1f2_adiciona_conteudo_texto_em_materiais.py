"""adiciona_conteudo_texto_em_materiais

Revision ID: a7b8c9d0e1f2
Revises: c299aa25e88e
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'c299aa25e88e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('materiais', sa.Column('conteudo_texto', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('materiais', 'conteudo_texto')