from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy.orm import Session

from backend.models.anexo_conversa import AnexoConversa
from backend.repositories.base import BaseRepository


class AnexoConversaRepository(BaseRepository[AnexoConversa]):
    def __init__(self, db: Session):
        super().__init__(AnexoConversa, db)

    def listar_por_conversa(self, conversa_id: str) -> list[AnexoConversa]:
        return (
            self.db.query(AnexoConversa)
            .filter(AnexoConversa.conversa_id == conversa_id)
            .order_by(AnexoConversa.criado_em.asc())
            .all()
        )

    def vincular_a_conversa(
        self, conversa_id: str, anexo_ids: list[int], usuario_id: int
    ) -> int:
        vinculados = 0
        for anexo_id in anexo_ids:
            anexo = self.db.get(AnexoConversa, anexo_id)
            if not anexo or anexo.conversa_id:
                continue
            if anexo.usuario_id != usuario_id:
                continue
            anexo.conversa_id = conversa_id
            vinculados += 1
        self.db.commit()
        return vinculados

    def deletar(self, anexo_id: int) -> Optional[str]:
        anexo = self.db.get(AnexoConversa, anexo_id)
        if not anexo:
            return None
        nome_arquivo = anexo.nome_arquivo
        self.db.delete(anexo)
        self.db.commit()
        return nome_arquivo