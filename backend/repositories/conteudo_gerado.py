from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.conteudo_gerado import ConteudoGerado
from backend.repositories.base import BaseRepository


class ConteudoGeradoRepository(BaseRepository[ConteudoGerado]):
    def __init__(self, db: Session):
        super().__init__(ConteudoGerado, db)

    def list_by_aluno(self, aluno_id: int) -> list[ConteudoGerado]:
        return (
            self.db.query(ConteudoGerado)
            .filter(ConteudoGerado.aluno_id == aluno_id)
            .all()
        )
