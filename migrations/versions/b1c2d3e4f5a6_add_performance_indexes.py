"""Add performance indexes

Revision ID: b1c2d3e4f5a6
Revises: a3b4c5d6e7f8
Create Date: 2026-07-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5a6'
down_revision = 'a3b4c5d6e7f8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Index em alunos.campus (filtrado no painel/portal)
    op.create_index('ix_alunos_campus', 'alunos', ['campus'])
    
    # Index em usuarios.campus e usuarios.tipo_perfil (filtrado em equipe/tipo)
    op.create_index('ix_usuarios_campus', 'usuarios', ['campus'])
    op.create_index('ix_usuarios_tipo_perfil', 'usuarios', ['tipo_perfil'])
    
    # Index em notificacoes (destino_tipo, destino_id, criada_em)
    # Index composto para filtragem + ordena��o
    op.create_index('ix_notificacoes_destino', 'notificacoes', ['destino_tipo', 'destino_id'])
    op.create_index('ix_notificacoes_criada_em', 'notificacoes', ['criada_em'])
    
    # Index em disciplinas.semestre (filtrado por semestre vigente)
    op.create_index('ix_disciplinas_semestre', 'disciplinas', ['semestre'])
    
    # Index em conteudos_gerados.aluno_id (filtrado por aluno)
    op.create_index('ix_conteudos_gerados_aluno_id', 'conteudos_gerados', ['aluno_id'])


def downgrade() -> None:
    op.drop_index('ix_conteudos_gerados_aluno_id', 'conteudos_gerados')
    op.drop_index('ix_disciplinas_semestre', 'disciplinas')
    op.drop_index('ix_notificacoes_criada_em', 'notificacoes')
    op.drop_index('ix_notificacoes_destino', 'notificacoes')
    op.drop_index('ix_usuarios_tipo_perfil', 'usuarios')
    op.drop_index('ix_usuarios_campus', 'usuarios')
    op.drop_index('ix_alunos_campus', 'alunos')
