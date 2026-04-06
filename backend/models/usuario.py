import enum
from datetime import datetime

from sqlalchemy import Enum, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class TipoPerfil(enum.Enum):
    professor = "professor"
    psicopedagogo = "psicopedagogo"
    admin = "admin"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    suap_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo_perfil: Mapped[TipoPerfil] = mapped_column(
        Enum(TipoPerfil), nullable=False, default=TipoPerfil.professor
    )
    criado_em: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow
    )

    conteudos = relationship("ConteudoGerado", back_populates="usuario")

    def __repr__(self):
        return f"<Usuario(id={self.id}, nome={self.nome}, tipo={self.tipo_perfil.value})>"
