import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Enum, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class TipoPerfil(enum.Enum):
    aluno = "aluno"
    professor = "professor"
    psicopedagogo = "psicopedagogo"
    servidor = "servidor"
    admin = "admin"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    suap_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    matricula: Mapped[str] = mapped_column(String(50), nullable=True)
    campus: Mapped[str] = mapped_column(String(200), nullable=True)
    tipo_vinculo: Mapped[str] = mapped_column(String(100), nullable=True)
    tipo_perfil: Mapped[str] = mapped_column(
        String(50), nullable=False, default="aluno"
    )
    setor: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    aprovado_napne: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    conta_local = relationship("ContaLocal", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    conteudos = relationship("ConteudoGerado", back_populates="usuario")
    disciplinas = relationship("Disciplina", back_populates="usuario", cascade="all, delete-orphan")
    pendencias_validadas = relationship("PendenciaValidacao", back_populates="validado_por", foreign_keys="PendenciaValidacao.validado_por_id")

    def __repr__(self):
        return f"<Usuario(id={self.id}, nome={self.nome}, tipo={self.tipo_perfil})>"
