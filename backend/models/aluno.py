from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Aluno(Base):
    __tablename__ = "alunos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    matricula: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)
    suap_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)
    curso: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    campus: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    foto_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    cpf: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
    status_acompanhamento: Mapped[str] = mapped_column(
        String(50), nullable=False, default="aguardando_indicacao"
    )
    data_importacao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    perfil = relationship(
        "PerfilAluno",
        back_populates="aluno",
        uselist=False,
        cascade="all, delete-orphan"
    )

    conteudos = relationship("ConteudoGerado", back_populates="aluno")
    diarios = relationship("DiarioAluno", back_populates="aluno", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Aluno(id={self.id}, nome={self.nome})>"
