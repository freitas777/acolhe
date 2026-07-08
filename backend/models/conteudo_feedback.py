from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class ConteudoFeedback(Base):
    """Feedback de professor sobre conteúdo gerado por IA."""

    __tablename__ = "conteudo_feedback"

    __table_args__ = (
        UniqueConstraint("conteudo_id", "professor_id", "disciplina_id", name="uq_conteudo_feedback"),
        Index("ix_conteudo_feedback_conteudo_id", "conteudo_id"),
        Index("ix_conteudo_feedback_professor_id", "professor_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conteudo_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conteudos_gerados.id", ondelete="CASCADE"),
        nullable=False,
    )
    professor_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    disciplina_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("disciplinas.id", ondelete="CASCADE"),
        nullable=True,
    )
    avaliacao: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
    )
    utilidade_percebida: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    comentario: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        server_default="now()",
        nullable=False,
    )

    # Relacionamentos (unidirecionais para evitar circular dependency)
    conteudo: Mapped["ConteudoGerado"] = relationship(
        "ConteudoGerado",
    )
    professor: Mapped[Optional["Usuario"]] = relationship(
        "Usuario",
    )
    disciplina: Mapped["Disciplina"] = relationship(
        "Disciplina",
    )

    def __repr__(self) -> str:
        return f"<ConteudoFeedback(id={self.id}, conteudo_id={self.conteudo_id}, avaliacao={self.avaliacao})>"