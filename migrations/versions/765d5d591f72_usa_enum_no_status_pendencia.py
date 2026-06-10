"""usa_enum_no_status_pendencia

Revision ID: 765d5d591f72
Revises: 6fb5690f8da8
Create Date: 2026-06-08 11:06:50.299460

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '765d5d591f72'
down_revision: Union[str, None] = '6fb5690f8da8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

status_pendencia = sa.Enum('pendente', 'validado', 'rejeitado', name='statuspendencia')


def upgrade() -> None:
    status_pendencia.create(op.get_bind(), checkfirst=True)
    op.execute(
        "ALTER TABLE pendencias_validacao "
        "ALTER COLUMN status DROP DEFAULT"
    )
    op.execute(
        "ALTER TABLE pendencias_validacao "
        "ALTER COLUMN status TYPE statuspendencia "
        "USING status::statuspendencia"
    )
    op.execute(
        "ALTER TABLE pendencias_validacao "
        "ALTER COLUMN status SET DEFAULT 'pendente'::statuspendencia"
    )


def downgrade() -> None:
    op.alter_column(
        "pendencias_validacao",
        "status",
        existing_type=status_pendencia,
        type_=sa.String(20),
        existing_nullable=False,
    )
    status_pendencia.drop(op.get_bind(), checkfirst=True)
