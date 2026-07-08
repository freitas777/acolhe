from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from backend.repositories.audit_log import AuditLogRepository

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditLogRepository(db)

    def registrar(
        self,
        *,
        usuario_id: Optional[int],
        acao: str,
        recurso_tipo: str,
        recurso_id: int,
        aluno_id: Optional[int] = None,
        detalhes: Optional[str] = None,
        ip_origem: Optional[str] = None,
    ) -> None:
        try:
            self.repo.create({
                "usuario_id": usuario_id,
                "acao": acao,
                "recurso_tipo": recurso_tipo,
                "recurso_id": recurso_id,
                "aluno_id": aluno_id,
                "detalhes": detalhes,
                "ip_origem": ip_origem,
            })
        except Exception:
            logger.exception(
                "Falha ao registrar auditoria: usuario_id=%s acao=%s recurso=%s/%s",
                usuario_id,
                acao,
                recurso_tipo,
                recurso_id,
            )
