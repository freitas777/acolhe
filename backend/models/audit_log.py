from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    acao: Mapped[str] = mapped_column(String(30), nullable=False)
    recurso_tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    recurso_id: Mapped[int] = mapped_column(Integer, nullable=False)
    aluno_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("alunos.id", ondelete="SET NULL"), nullable=True
    )
    detalhes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_origem: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default="now()"
    )

    usuario = relationship("Usuario", lazy="selectin")
    aluno = relationship("Aluno", lazy="selectin")

    __table_args__ = (
        Index("ix_audit_logs_aluno_id", "aluno_id"),
        Index("ix_audit_logs_recurso", "recurso_tipo", "recurso_id"),
        Index("ix_audit_logs_usuario", "usuario_id"),
        Index("ix_audit_logs_criado_em", "criado_em"),
    )
