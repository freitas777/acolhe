import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class StatusPendencia(enum.Enum):
    pendente = "pendente"
    validado = "validado"
    rejeitado = "rejeitado"


class PendenciaValidacao(Base):
    __tablename__ = "pendencias_validacao"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    aluno_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("alunos.id", ondelete="CASCADE"), nullable=False
    )
    indicado_por_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    validado_por_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    motivo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pendente"
    )
    criado_em: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow
    )
    validado_em: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    aluno = relationship("Aluno", backref="pendencias")
    indicado_por = relationship("Usuario", foreign_keys=[indicado_por_id], backref="pendencias_criadas")
    validado_por = relationship("Usuario", foreign_keys=[validado_por_id], back_populates="pendencias_validadas")

    def __repr__(self):
        return f"<PendenciaValidacao(id={self.id}, aluno_id={self.aluno_id}, status={self.status})>"
