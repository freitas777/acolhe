"""cria_tabela_contas_locais

Revision ID: 19af06df1d82
Revises: f1a2b3c4d5e6
Create Date: 2026-05-27 15:20:19.269222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19af06df1d82'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('contas_locais',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('senha_hash', sa.String(length=128), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('usuario_id')
    )
    op.create_index(op.f('ix_contas_locais_email'), 'contas_locais', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_contas_locais_email'), table_name='contas_locais')
    op.drop_table('contas_locais')
