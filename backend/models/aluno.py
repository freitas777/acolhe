from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Aluno(Base):
    __tablename__ = "alunos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow
    )

    perfil = relationship(
        "PerfilAluno", back_populates="aluno", uselist=False, cascade="all, delete-orphan"
    )
    conteudos = relationship("ConteudoGerado", back_populates="aluno")

    def __repr__(self):
        return f"<Aluno(id={self.id}, nome={self.nome})>"
