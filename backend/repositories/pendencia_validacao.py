from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from backend.models.pendencia_validacao import PendenciaValidacao
from backend.models.aluno import Aluno
from backend.repositories.base import BaseRepository


class PendenciaValidacaoRepository(BaseRepository[PendenciaValidacao]):
    def __init__(self, db: Session):
        super().__init__(PendenciaValidacao, db)

    def listar_pendentes(self) -> list[PendenciaValidacao]:
        return (
            self.db.query(PendenciaValidacao)
            .filter(PendenciaValidacao.status == "pendente")
            .options(selectinload(PendenciaValidacao.aluno))
            .order_by(PendenciaValidacao.criado_em.desc())
            .all()
        )

    def get_pendente_por_aluno(self, aluno_id: int) -> PendenciaValidacao | None:
        return (
            self.db.query(PendenciaValidacao)
            .filter(PendenciaValidacao.aluno_id == aluno_id, PendenciaValidacao.status == "pendente")
            .first()
        )
