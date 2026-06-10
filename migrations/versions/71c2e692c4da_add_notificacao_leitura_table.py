"""add notificacao_leitura table

Revision ID: 71c2e692c4da
Revises: fae763a825b7
Create Date: 2026-06-10 08:50:34.262880

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71c2e692c4da'
down_revision: Union[str, None] = 'fae763a825b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('notificacao_leitura',
    sa.Column('notificacao_id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('lida_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['notificacao_id'], ['notificacoes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('notificacao_id', 'usuario_id')
    )


def downgrade() -> None:
    op.drop_table('notificacao_leitura')
