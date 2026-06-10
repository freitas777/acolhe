from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, ForeignKey, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class DiarioAluno(Base):
    __tablename__ = "diario_alunos"
    __table_args__ = (UniqueConstraint("disciplina_id", "aluno_id", name="uq_diario_aluno"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    disciplina_id: Mapped[int] = mapped_column(Integer, ForeignKey("disciplinas.id", ondelete="CASCADE"), nullable=False)
    aluno_id: Mapped[int] = mapped_column(Integer, ForeignKey("alunos.id", ondelete="CASCADE"), nullable=False)
    aluno_nome: Mapped[str] = mapped_column(String(200), nullable=False)
    aluno_matricula: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now(timezone.utc))

    disciplina = relationship("Disciplina", back_populates="alunos_assistidos")
    aluno = relationship("Aluno", back_populates="diarios")

    def __repr__(self):
        return f"<DiarioAluno(disciplina_id={self.disciplina_id}, aluno_id={self.aluno_id})>"
