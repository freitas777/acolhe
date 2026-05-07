from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Disciplina(Base):
    __tablename__ = "disciplinas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    suap_id: Mapped[int] = mapped_column(Integer, nullable=False)
    descricao: Mapped[str] = mapped_column(String(300), nullable=False)
    sigla: Mapped[str] = mapped_column(String(50), nullable=True)
    situacao: Mapped[str] = mapped_column(String(100), nullable=True)
    professor: Mapped[str] = mapped_column(String(200), nullable=True)
    semestre: Mapped[str] = mapped_column(String(10), nullable=False)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False)
    criada_em: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow
    )

    usuario = relationship("Usuario", back_populates="disciplinas")

    def __repr__(self):
        return f"<Disciplina(id={self.id}, sigla={self.sigla}, semestre={self.semestre})>"
