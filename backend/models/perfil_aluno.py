import enum
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class NivelAtencao(enum.Enum):
    alto = "alto"
    medio = "medio"
    baixo = "baixo"


class PreferenciaAprendizado(enum.Enum):
    visual = "visual"
    auditivo = "auditivo"
    cinestesico = "cinestesico"
    leitura_escrita = "leitura_escrita"
    misto = "misto"


class PerfilAluno(Base):
    __tablename__ = "perfis_aluno"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    aluno_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("alunos.id", ondelete="CASCADE"), nullable=False
    )
    nivel_atencao: Mapped[Optional[NivelAtencao]] = mapped_column(
        Enum(NivelAtencao), nullable=True
    )
    dificuldade_leitura: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    preferencia: Mapped[Optional[PreferenciaAprendizado]] = mapped_column(
        Enum(PreferenciaAprendizado), nullable=True
    )
    interesses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    diagnostico: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    aluno = relationship("Aluno", back_populates="perfil")

    def __repr__(self):
        return f"<PerfilAluno(id={self.id}, aluno_id={self.aluno_id})>"
