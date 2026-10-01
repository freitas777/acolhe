from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class AnexoConversa(Base):
    __tablename__ = "anexos_conversa"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversa_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("conversas.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    nome_original: Mapped[str] = mapped_column(String(300), nullable=False)
    nome_arquivo: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    tipo_arquivo: Mapped[str] = mapped_column(String(100), nullable=False)
    tamanho: Mapped[int] = mapped_column(BigInteger, nullable=False)
    conteudo_texto: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    conversa = relationship("Conversa")
    usuario = relationship("Usuario")

    def __repr__(self) -> str:
        return f"<AnexoConversa(id={self.id}, nome={self.nome_original!r})>"