"""recreate_conteudo_feedback

Revision ID: bb3a39107762
Revises: ff83d0426b0e
Create Date: 2026-07-30 14:56:48.619301

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb3a39107762'
down_revision: Union[str, None] = 'ff83d0426b0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Recria a tabela conteudo_feedback que foi dropada na migration anterior
    op.create_table('conteudo_feedback',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('conteudo_id', sa.Integer(), nullable=False),
    sa.Column('professor_id', sa.Integer(), nullable=True),
    sa.Column('disciplina_id', sa.Integer(), nullable=True),
    sa.Column('avaliacao', sa.String(length=12), nullable=False),
    sa.Column('utilidade_percebida', sa.Integer(), nullable=True),
    sa.Column('comentario', sa.String(length=1000), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['conteudo_id'], ['conteudos_gerados.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['disciplina_id'], ['disciplinas.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['professor_id'], ['usuarios.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('conteudo_id', 'professor_id', 'disciplina_id', name='uq_conteudo_feedback')
    )
    op.create_index('ix_conteudo_feedback_conteudo_id', 'conteudo_feedback', ['conteudo_id'], unique=False)
    op.create_index('ix_conteudo_feedback_professor_id', 'conteudo_feedback', ['professor_id'], unique=False)
    
    # Restaura indexes críticos dropados na migration anterior
    op.create_index('ix_alunos_campus', 'alunos', ['campus'], unique=False)
    op.create_index('ix_alunos_status_acompanhamento', 'alunos', ['status_acompanhamento'], unique=False)
    op.create_index('ix_conteudos_gerados_aluno_id', 'conteudos_gerados', ['aluno_id'], unique=False)
    op.create_index('ix_conteudos_gerados_conteudo_pai_id', 'conteudos_gerados', ['conteudo_pai_id'], unique=False)
    op.create_index('ix_conversas_usuario_id', 'conversas', ['usuario_id'], unique=False)
    op.create_index('ix_diario_alunos_aluno_id', 'diario_alunos', ['aluno_id'], unique=False)
    op.create_index('ix_diario_alunos_disciplina_id', 'diario_alunos', ['disciplina_id'], unique=False)
    op.create_index('ix_disciplinas_semestre', 'disciplinas', ['semestre'], unique=False)
    op.create_index('ix_materiais_categoria', 'materiais', ['categoria'], unique=False)
    op.create_index('ix_notificacoes_criada_em', 'notificacoes', ['criada_em'], unique=False)
    op.create_index('ix_notificacoes_destino', 'notificacoes', ['destino_tipo', 'destino_id'], unique=False)
    op.create_index('ix_usuarios_campus', 'usuarios', ['campus'], unique=False)
    op.create_index('ix_usuarios_tipo_perfil', 'usuarios', ['tipo_perfil'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_conteudo_feedback_professor_id', table_name='conteudo_feedback')
    op.drop_index('ix_conteudo_feedback_conteudo_id', table_name='conteudo_feedback')
    op.drop_table('conteudo_feedback')
