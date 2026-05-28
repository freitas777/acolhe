"""adiciona coluna senha_temporaria em contas_locais

Revision ID: b5dd2dfa4a6d
Revises: 19af06df1d82
Create Date: 2026-05-27 16:52:54.431563

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b5dd2dfa4a6d'
down_revision: Union[str, None] = '19af06df1d82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('contas_locais', sa.Column('senha_temporaria', sa.Boolean(), nullable=True))
    op.execute("UPDATE contas_locais SET senha_temporaria = TRUE")
    op.alter_column('contas_locais', 'senha_temporaria', nullable=False)


def downgrade() -> None:
    op.drop_column('contas_locais', 'senha_temporaria')
