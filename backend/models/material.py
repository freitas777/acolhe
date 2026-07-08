from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Material(Base):
    __tablename__ = "materiais"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    disciplina_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("disciplinas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    nome_original: Mapped[str] = mapped_column(String(300), nullable=False)
    nome_arquivo: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    tipo_arquivo: Mapped[str] = mapped_column(String(50), nullable=False)
    tamanho: Mapped[int] = mapped_column(BigInteger, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    disciplina = relationship("Disciplina")
    usuario = relationship("Usuario")

    def __repr__(self) -> str:
        return f"<Material(id={self.id}, nome={self.nome_original!r})>"
