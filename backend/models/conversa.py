import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Conversa(Base):
    __tablename__ = "conversas"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    titulo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="Nova conversa",
    )
    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    aluno_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("alunos.id", ondelete="SET NULL"),
        nullable=True,
    )
    criada_em: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    mensagens = relationship(
        "Mensagem",
        back_populates="conversa",
        cascade="all, delete-orphan",
        order_by="Mensagem.criada_em",
    )
    aluno = relationship("Aluno")

    def __repr__(self) -> str:
        return f"<Conversa(id={self.id}, titulo={self.titulo!r})>"