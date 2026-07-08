from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.audit_log import AuditLog
from backend.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session):
        super().__init__(AuditLog, db)

    def listar_por_aluno(
        self, aluno_id: int, *, skip: int = 0, limit: int = 50
    ) -> Sequence[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.aluno_id == aluno_id)
            .order_by(AuditLog.criado_em.desc())
            .offset(skip)
            .limit(limit)
        )
        return self.db.execute(stmt).unique().scalars().all()

    def listar_filtrado(
        self,
        *,
        aluno_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
        recurso_tipo: Optional[str] = None,
        acao: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.criado_em.desc())
        if aluno_id is not None:
            stmt = stmt.where(AuditLog.aluno_id == aluno_id)
        if usuario_id is not None:
            stmt = stmt.where(AuditLog.usuario_id == usuario_id)
        if recurso_tipo is not None:
            stmt = stmt.where(AuditLog.recurso_tipo == recurso_tipo)
        if acao is not None:
            stmt = stmt.where(AuditLog.acao == acao)
        stmt = stmt.offset(skip).limit(limit)
        return self.db.execute(stmt).unique().scalars().all()
