from __future__ import annotations

import logging
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from backend.models.notificacao import Notificacao
from backend.repositories.notificacao import NotificacaoRepository

logger = logging.getLogger(__name__)


class NotificacaoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificacaoRepository(db)

    def listar(
        self,
        *,
        destino_tipo: str,
        destino_id: Optional[int] = None,
        campus: Optional[str] = None,
        usuario_id: int = 0,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Notificacao]:
        return self.repo.listar_por_destino(
            destino_tipo=destino_tipo,
            destino_id=destino_id,
            campus=campus,
            usuario_id=usuario_id,
            skip=skip,
            limit=limit,
        )

    def contar_nao_lidas(
        self,
        *,
        destino_tipo: str,
        destino_id: Optional[int] = None,
        campus: Optional[str] = None,
        usuario_id: int = 0,
    ) -> int:
        return self.repo.contar_nao_lidas(
            destino_tipo=destino_tipo,
            destino_id=destino_id,
            campus=campus,
            usuario_id=usuario_id,
        )

    def marcar_como_lida(self, notificacao_id: int, usuario_id: int) -> bool:
        return self.repo.marcar_como_lida(notificacao_id, usuario_id)

    def marcar_todas_como_lidas(
        self,
        *,
        destino_tipo: str,
        destino_id: Optional[int] = None,
        campus: Optional[str] = None,
        usuario_id: int = 0,
    ) -> int:
        return self.repo.marcar_todas_como_lidas(
            destino_tipo=destino_tipo,
            destino_id=destino_id,
            campus=campus,
            usuario_id=usuario_id,
        )

    def esta_lida(self, notificacao_id: int, usuario_id: int) -> bool:
        return self.repo.esta_lida(notificacao_id, usuario_id)

    def excluir(self, notificacao_id: int, usuario_id: int) -> bool:
        return self.repo.excluir(notificacao_id, usuario_id)

    def criar_notificacao(
        self,
        *,
        tipo: str,
        titulo: str,
        mensagem: Optional[str] = None,
        remetente_id: Optional[int] = None,
        aluno_id: Optional[int] = None,
        destino_tipo: str,
        destino_id: Optional[int] = None,
    ) -> Notificacao:
        notificacao = self.repo.create({
            "tipo": tipo,
            "titulo": titulo,
            "mensagem": mensagem,
            "remetente_id": remetente_id,
            "aluno_id": aluno_id,
            "destino_tipo": destino_tipo,
            "destino_id": destino_id,
        })
        logger.info(
            "Notificacao criada: tipo=%s destino=%s/%s aluno_id=%s",
            tipo, destino_tipo, destino_id, aluno_id,
        )
        return notificacao
