"""cria_tabela_anexos_conversa

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-09-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('anexos_conversa',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('conversa_id', sa.String(length=36), nullable=True),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('nome_original', sa.String(length=300), nullable=False),
    sa.Column('nome_arquivo', sa.String(length=100), nullable=False),
    sa.Column('tipo_arquivo', sa.String(length=100), nullable=False),
    sa.Column('tamanho', sa.BigInteger(), nullable=False),
    sa.Column('conteudo_texto', sa.Text(), nullable=True),
    sa.Column('criado_em', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['conversa_id'], ['conversas.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nome_arquivo')
    )
    op.create_index('ix_anexos_conversa_conversa_id', 'anexos_conversa', ['conversa_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_anexos_conversa_conversa_id', table_name='anexos_conversa')
    op.drop_table('anexos_conversa')