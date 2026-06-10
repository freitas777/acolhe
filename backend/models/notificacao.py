from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Notificacao(Base):
    __tablename__ = "notificacoes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    mensagem: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remetente_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    aluno_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("alunos.id", ondelete="SET NULL"), nullable=True
    )
    destino_tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    destino_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criada_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    remetente = relationship("Usuario", foreign_keys=[remetente_id])
    aluno = relationship("Aluno")
    leituras = relationship(
        "NotificacaoLeitura", back_populates="notificacao", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Notificacao(id={self.id}, tipo={self.tipo!r}, destino_tipo={self.destino_tipo!r})>"


class NotificacaoLeitura(Base):
    __tablename__ = "notificacao_leitura"

    notificacao_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("notificacoes.id", ondelete="CASCADE"), primary_key=True
    )
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    lida_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    excluida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    notificacao = relationship("Notificacao", back_populates="leituras")
    usuario = relationship("Usuario")

    def __repr__(self) -> str:
        return f"<NotificacaoLeitura(notificacao_id={self.notificacao_id}, usuario_id={self.usuario_id})>"
