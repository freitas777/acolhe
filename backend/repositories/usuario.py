from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from backend.models.usuario import Usuario, TipoPerfil
from backend.repositories.base import BaseRepository


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, db: Session):
        super().__init__(Usuario, db)

    def get_by_suap_id(self, suap_id: str) -> Usuario | None:
        return self.db.query(Usuario).filter(Usuario.suap_id == suap_id).first()

    def filter_by_profile(self, profile: TipoPerfil) -> list[Usuario]:
        return (
            self.db.query(Usuario)
            .filter(Usuario.tipo_perfil == profile)
            .all()
        )
