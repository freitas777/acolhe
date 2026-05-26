"""adiciona indexes para colunas frequentemente consultadas

Revision ID: f1a2b3c4d5e6
Revises: e8f1a2b3c4d5
Create Date: 2026-05-26 10:40:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e8f1a2b3c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_alunos_status_acompanhamento", "alunos", ["status_acompanhamento"])
    op.create_index("ix_pendencias_validacao_status", "pendencias_validacao", ["status"])
    op.create_index("ix_pendencias_validacao_aluno_id", "pendencias_validacao", ["aluno_id"])
    op.create_index("ix_diario_alunos_disciplina_id", "diario_alunos", ["disciplina_id"])
    op.create_index("ix_diario_alunos_aluno_id", "diario_alunos", ["aluno_id"])
    op.create_index("ix_disciplinas_usuario_id", "disciplinas", ["usuario_id"])
    op.create_index("ix_conversas_usuario_id", "conversas", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_conversas_usuario_id", table_name="conversas")
    op.drop_index("ix_disciplinas_usuario_id", table_name="disciplinas")
    op.drop_index("ix_diario_alunos_aluno_id", table_name="diario_alunos")
    op.drop_index("ix_diario_alunos_disciplina_id", table_name="diario_alunos")
    op.drop_index("ix_pendencias_validacao_aluno_id", table_name="pendencias_validacao")
    op.drop_index("ix_pendencias_validacao_status", table_name="pendencias_validacao")
    op.drop_index("ix_alunos_status_acompanhamento", table_name="alunos")
