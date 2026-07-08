"""Add iteracoes de conteudo (versao, conteudo_pai_id)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('conteudos_gerados', sa.Column('versao', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('conteudos_gerados', sa.Column('conteudo_pai_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_conteudos_gerados_pai',
        'conteudos_gerados', 'conteudos_gerados',
        ['conteudo_pai_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_conteudos_gerados_conteudo_pai_id', 'conteudos_gerados', ['conteudo_pai_id'])


def downgrade() -> None:
    op.drop_index('ix_conteudos_gerados_conteudo_pai_id', 'conteudos_gerados')
    op.drop_constraint('fk_conteudos_gerados_pai', 'conteudos_gerados', type_='foreignkey')
    op.drop_column('conteudos_gerados', 'conteudo_pai_id')
    op.drop_column('conteudos_gerados', 'versao')
