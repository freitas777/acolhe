"""initial_tables

Revision ID: 16b9683e89a2
Revises:
Create Date: 2026-04-06 09:26:42.831789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16b9683e89a2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    sa.Enum('professor', 'psicopedagogo', 'admin', name='tipoperfil').create(op.get_bind())
    sa.Enum('alto', 'medio', 'baixo', name='nivelatencao').create(op.get_bind())
    sa.Enum('visual', 'auditivo', 'cinestesico', 'leitura_escrita', 'misto', name='preferenciaaprendizado').create(op.get_bind())

    # Tabela: usuarios
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('suap_id', sa.String(50), unique=True, nullable=False),
        sa.Column('nome', sa.String(200), nullable=False),
        sa.Column('email', sa.String(200), nullable=False),
        sa.Column('tipo_perfil', sa.Enum('professor', 'psicopedagogo', 'admin', name='tipoperfil'), nullable=False, server_default='professor'),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Tabela: alunos
    op.create_table(
        'alunos',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('nome', sa.String(200), nullable=False),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Tabela: perfis_aluno
    op.create_table(
        'perfis_aluno',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('aluno_id', sa.Integer(), sa.ForeignKey('alunos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nivel_atencao', sa.Enum('alto', 'medio', 'baixo', name='nivelatencao'), nullable=True),
        sa.Column('dificuldade_leitura', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('preferencia', sa.Enum('visual', 'auditivo', 'cinestesico', 'leitura_escrita', 'misto', name='preferenciaaprendizado'), nullable=True),
        sa.Column('interesses', sa.Text(), nullable=True),
        sa.Column('diagnostico', sa.String(200), nullable=True),
    )

    # Tabela: conteudos_gerados
    op.create_table(
        'conteudos_gerados',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('aluno_id', sa.Integer(), sa.ForeignKey('alunos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('usuario_id', sa.Integer(), sa.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True),
        sa.Column('tema', sa.String(300), nullable=False),
        sa.Column('prompt_utilizado', sa.Text(), nullable=False),
        sa.Column('conteudo', sa.Text(), nullable=False),
        sa.Column('modelo_ia', sa.String(100), nullable=False),
        sa.Column('gerado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Indices
    op.create_index('ix_perfis_aluno_aluno_id', 'perfis_aluno', ['aluno_id'])
    op.create_index('ix_conteudos_gerados_aluno_id', 'conteudos_gerados', ['aluno_id'])
    op.create_index('ix_conteudos_gerados_usuario_id', 'conteudos_gerados', ['usuario_id'])


def downgrade() -> None:
    op.drop_index('ix_conteudos_gerados_usuario_id', 'conteudos_gerados')
    op.drop_index('ix_conteudos_gerados_aluno_id', 'conteudos_gerados')
    op.drop_index('ix_perfis_aluno_aluno_id', 'perfis_aluno')

    op.drop_table('conteudos_gerados')
    op.drop_table('perfis_aluno')
    op.drop_table('alunos')
    op.drop_table('usuarios')

    sa.Enum(name='preferenciaaprendizado').drop(op.get_bind())
    sa.Enum(name='nivelatencao').drop(op.get_bind())
    sa.Enum(name='tipoperfil').drop(op.get_bind())
