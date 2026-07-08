"""Add conteudo_feedback table

Revision ID: cf0000000001
Revises: b1c2d3e4f5a6
Create Date: 2026-07-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'cf0000000001'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'conteudo_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conteudo_id', sa.Integer(), nullable=False),
        sa.Column('professor_id', sa.Integer(), nullable=True),
        sa.Column('disciplina_id', sa.Integer(), nullable=False),
        sa.Column('avaliacao', sa.String(length=12), nullable=False),
        sa.Column('comentario', sa.String(length=1000), nullable=True),
        sa.Column('criado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conteudo_id'], ['conteudos_gerados.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['professor_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['disciplina_id'], ['disciplinas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conteudo_id', 'professor_id', 'disciplina_id', name='uq_conteudo_feedback'),
    )
    op.create_index('ix_conteudo_feedback_conteudo_id', 'conteudo_feedback', ['conteudo_id'])
    op.create_index('ix_conteudo_feedback_professor_id', 'conteudo_feedback', ['professor_id'])


def downgrade() -> None:
    op.drop_index('ix_conteudo_feedback_professor_id', 'conteudo_feedback')
    op.drop_index('ix_conteudo_feedback_conteudo_id', 'conteudo_feedback')
    op.drop_table('conteudo_feedback')
