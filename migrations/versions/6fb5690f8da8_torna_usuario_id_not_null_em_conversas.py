"""torna usuario_id not null em conversas

Revision ID: 6fb5690f8da8
Revises: 7a8b9c0d1e2f
Create Date: 2026-06-02 09:02:27.434545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6fb5690f8da8'
down_revision: Union[str, None] = '7a8b9c0d1e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "conversas",
        "usuario_id",
        existing_type=sa.Integer(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "conversas",
        "usuario_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
