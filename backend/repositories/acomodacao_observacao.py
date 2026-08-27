from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.acomodacao_observacao import AcomodacaoObservacao
from backend.repositories.base import BaseRepository


class AcomodacaoObservacaoRepository(BaseRepository[AcomodacaoObservacao]):
    def __init__(self, db: Session):
        super().__init__(AcomodacaoObservacao, db)

    def listar_por_aluno(self, aluno_id: int) -> list[AcomodacaoObservacao]:
        return (
            self.db.query(AcomodacaoObservacao)
            .filter(AcomodacaoObservacao.aluno_id == aluno_id)
            .order_by(AcomodacaoObservacao.criado_em.desc())
            .all()
        )

    def get_by_aluno_disciplina_professor(
        self, aluno_id: int, disciplina_id: int, professor_id: int
    ) -> AcomodacaoObservacao | None:
        return (
            self.db.query(AcomodacaoObservacao)
            .filter(
                AcomodacaoObservacao.aluno_id == aluno_id,
                AcomodacaoObservacao.disciplina_id == disciplina_id,
                AcomodacaoObservacao.professor_id == professor_id,
            )
            .first()
        )

    def criar_ou_atualizar(
        self, aluno_id: int, disciplina_id: int, professor_id: int, texto: str
    ) -> AcomodacaoObservacao:
        existing = self.get_by_aluno_disciplina_professor(aluno_id, disciplina_id, professor_id)
        if existing is not None:
            existing.texto = texto
            self.db.commit()
            self.db.refresh(existing)
            return existing
        obs = AcomodacaoObservacao(
            aluno_id=aluno_id,
            disciplina_id=disciplina_id,
            professor_id=professor_id,
            texto=texto,
        )
        self.db.add(obs)
        self.db.commit()
        self.db.refresh(obs)
        return obs
