from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class ConteudoGerado(Base):
    __tablename__ = "conteudos_gerados"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    aluno_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("alunos.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    tema: Mapped[str] = mapped_column(String(300), nullable=False)
    prompt_utilizado: Mapped[str] = mapped_column(Text, nullable=False)
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    modelo_ia: Mapped[str] = mapped_column(String(100), nullable=False)
    gerado_em: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow
    )

    aluno = relationship("Aluno", back_populates="conteudos")
    usuario = relationship("Usuario", back_populates="conteudos")

    def __repr__(self):
        return f"<ConteudoGerado(id={self.id}, tema={self.tema})>"
