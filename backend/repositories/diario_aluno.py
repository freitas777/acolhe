from __future__ import annotations

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from backend.models.diario_aluno import DiarioAluno
from backend.models.disciplina import Disciplina
from backend.repositories.base import BaseRepository


class DiarioAlunoRepository(BaseRepository[DiarioAluno]):
    def __init__(self, db: Session):
        super().__init__(DiarioAluno, db)

    def listar_por_disciplina(self, disciplina_id: int) -> list[DiarioAluno]:
        return (
            self.db.query(DiarioAluno)
            .filter(DiarioAluno.disciplina_id == disciplina_id)
            .all()
        )

    def get_by_disciplina_aluno(self, disciplina_id: int, aluno_id: int) -> DiarioAluno | None:
        return (
            self.db.query(DiarioAluno)
            .filter(DiarioAluno.disciplina_id == disciplina_id, DiarioAluno.aluno_id == aluno_id)
            .first()
        )

    def deletar_por_disciplina(self, disciplina_id: int) -> int:
        result = (
            self.db.query(DiarioAluno)
            .filter(DiarioAluno.disciplina_id == disciplina_id)
            .delete()
        )
        self.db.commit()
        return result

    def contar_por_disciplina(self, disciplina_id: int) -> int:
        return (
            self.db.query(DiarioAluno)
            .filter(DiarioAluno.disciplina_id == disciplina_id)
            .count()
        )

    def verificar_professor_aluno(self, professor_id: int, aluno_id: int) -> bool:
        stmt = (
            select(exists())
            .select_from(DiarioAluno)
            .join(Disciplina, DiarioAluno.disciplina_id == Disciplina.id)
            .where(
                Disciplina.usuario_id == professor_id,
                DiarioAluno.aluno_id == aluno_id,
            )
        )
        return self.db.execute(stmt).scalar()
