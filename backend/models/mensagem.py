import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Mensagem(Base):
    __tablename__ = "mensagens"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    conversa_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    papel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    conteudo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    criada_em: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    conversa = relationship("Conversa", back_populates="mensagens")

    def __repr__(self) -> str:
        return f"<Mensagem(id={self.id}, papel={self.papel!r})>"
