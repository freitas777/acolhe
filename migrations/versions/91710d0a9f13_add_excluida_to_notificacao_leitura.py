"""add_excluida_to_notificacao_leitura

Revision ID: 91710d0a9f13
Revises: 71c2e692c4da
Create Date: 2026-06-10 09:28:43.593111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '91710d0a9f13'
down_revision: Union[str, None] = '71c2e692c4da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('notificacao_leitura', sa.Column('excluida', sa.Boolean(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('notificacao_leitura', 'excluida')
