from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from backend.models.material import Material
from backend.repositories.base import BaseRepository


class MaterialRepository(BaseRepository[Material]):
    def __init__(self, db: Session):
        super().__init__(Material, db)

    def listar_por_disciplina(self, disciplina_id: int) -> list[Material]:
        return (
            self.db.query(Material)
            .filter(Material.disciplina_id == disciplina_id)
            .order_by(Material.criado_em.desc())
            .all()
        )

    def obter_com_relacionamentos(self, material_id: int) -> Material | None:
        return (
            self.db.query(Material)
            .options(selectinload(Material.disciplina))
            .options(selectinload(Material.usuario))
            .filter(Material.id == material_id)
            .first()
        )
