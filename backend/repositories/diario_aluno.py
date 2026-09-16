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

    def listar_disciplinas_por_aluno(
        self, aluno_id: int, semestre: str | None = None, excluir_usuario_id: int | None = None
    ) -> list[Disciplina]:
        query = (
            self.db.query(Disciplina)
            .join(DiarioAluno, DiarioAluno.disciplina_id == Disciplina.id)
            .filter(DiarioAluno.aluno_id == aluno_id)
            .order_by(Disciplina.id.asc())
        )
        if semestre:
            query = query.filter(Disciplina.semestre == semestre)
        if excluir_usuario_id is not None:
            query = query.filter(Disciplina.usuario_id != excluir_usuario_id)
        return query.all()

    def verificar_professor_aluno(self, professor_id: int, aluno_id: int) -> bool:
        stmt = (
            select(exists(
                select(1)
                .select_from(DiarioAluno)
                .join(Disciplina, DiarioAluno.disciplina_id == Disciplina.id)
                .where(
                    Disciplina.usuario_id == professor_id,
                    DiarioAluno.aluno_id == aluno_id,
                )
            ))
        )
        return self.db.execute(stmt).scalar()
