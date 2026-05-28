from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.conta_local import ContaLocal
from backend.repositories.base import BaseRepository


class ContaLocalRepository(BaseRepository[ContaLocal]):
    def __init__(self, db: Session):
        super().__init__(ContaLocal, db)

    def get_by_email(self, email: str) -> ContaLocal | None:
        return self.db.query(ContaLocal).filter(ContaLocal.email == email).first()

    def get_by_usuario_id(self, usuario_id: int) -> ContaLocal | None:
        return self.db.query(ContaLocal).filter(ContaLocal.usuario_id == usuario_id).first()
