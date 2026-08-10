from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class TokenRevogado(Base):
    __tablename__ = "tokens_revogados"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    usuario_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    revogado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    expira_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self):
        return f"<TokenRevogado(jti={self.jti}, usuario_id={self.usuario_id})>"
