from datetime import datetime, timezone

from sqlalchemy import Integer, ForeignKey, DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class AcomodacaoObservacao(Base):
    __tablename__ = "acomodacao_observacoes"
    __table_args__ = (
        UniqueConstraint("aluno_id", "disciplina_id", "professor_id", name="uq_acomodacao_obs"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    aluno_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("alunos.id", ondelete="CASCADE"), nullable=False
    )
    disciplina_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("disciplinas.id", ondelete="CASCADE"), nullable=False
    )
    professor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(timezone.utc),
        server_default="now()",
    )

    aluno = relationship("Aluno", backref="observacoes_acomodacao")
    disciplina = relationship("Disciplina")
    professor = relationship("Usuario")

    @property
    def disciplina_sigla(self) -> str:
        return self.disciplina.sigla if self.disciplina else ""

    @property
    def professor_nome(self) -> str:
        # Assuming Usuario has 'nome' or 'nome_usual'; fallback to empty
        return getattr(self.professor, "nome", getattr(self.professor, "nome_usual", ""))

    def __repr__(self):
        return f"<AcomodacaoObservacao(id={self.id}, aluno_id={self.aluno_id})>"
