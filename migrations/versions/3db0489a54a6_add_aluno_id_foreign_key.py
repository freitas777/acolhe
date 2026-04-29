"""add aluno_id foreign key

Revision ID: 3db0489a54a6
Revises: 16b9683e89a2
Create Date: 2026-04-28 21:38:21.396152
"""
from alembic import op
import sqlalchemy as sa

revision = '3db0489a54a6'
down_revision = '16b9683e89a2'
branch_labels = None
depends_on = None

def upgrade():
    op.create_foreign_key(
        'fk_perfis_aluno_aluno_id',
        'perfis_aluno',
        'alunos',
        ['aluno_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.create_unique_constraint(
        'uq_perfis_aluno_aluno_id',
        'perfis_aluno',
        ['aluno_id']
    )

    op.alter_column('perfis_aluno', 'aluno_id', nullable=False)
    op.create_unique_constraint('uq_perfis_aluno_aluno_id', 'perfis_aluno', ['aluno_id'])

def downgrade():
    op.drop_constraint('uq_perfis_aluno_aluno_id', 'perfis_aluno', type_='unique')
    op.drop_constraint('fk_perfis_aluno_aluno_id', 'perfis_aluno', type_='foreignkey')
    op.drop_column('perfis_aluno', 'aluno_id')