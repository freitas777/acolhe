"""add audit_logs

Revision ID: a3b4c5d6e7f8
Revises: 746c64112447
Create Date: 2026-06-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, None] = '746c64112447'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('usuario_id', sa.Integer(), sa.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True),
        sa.Column('acao', sa.String(30), nullable=False),
        sa.Column('recurso_tipo', sa.String(50), nullable=False),
        sa.Column('recurso_id', sa.Integer(), nullable=False),
        sa.Column('aluno_id', sa.Integer(), sa.ForeignKey('alunos.id', ondelete='SET NULL'), nullable=True),
        sa.Column('detalhes', sa.Text(), nullable=True),
        sa.Column('ip_origem', sa.String(45), nullable=True),
        sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_aluno_id', 'audit_logs', ['aluno_id'])
    op.create_index('ix_audit_logs_recurso', 'audit_logs', ['recurso_tipo', 'recurso_id'])
    op.create_index('ix_audit_logs_usuario', 'audit_logs', ['usuario_id'])
    op.create_index('ix_audit_logs_criado_em', 'audit_logs', ['criado_em'])


def downgrade() -> None:
    op.drop_index('ix_audit_logs_criado_em', table_name='audit_logs')
    op.drop_index('ix_audit_logs_usuario', table_name='audit_logs')
    op.drop_index('ix_audit_logs_recurso', table_name='audit_logs')
    op.drop_index('ix_audit_logs_aluno_id', table_name='audit_logs')
    op.drop_table('audit_logs')
