from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import AuthData, require_napne
from backend.models.audit_log import AuditLog
from backend.repositories.audit_log import AuditLogRepository
from backend.schemas.audit_log import AuditLogResponse

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("/alunos/{aluno_id}", response_model=list[AuditLogResponse])
async def logs_aluno(
    aluno_id: int,
    skip: int = 0,
    limit: int = 50,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    repo = AuditLogRepository(db)
    logs = repo.listar_por_aluno(aluno_id, skip=skip, limit=limit)
    result = []
    for log in logs:
        resp = AuditLogResponse.model_validate(log)
        if log.usuario:
            resp.usuario_nome = log.usuario.nome
        result.append(resp)
    return result
