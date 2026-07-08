from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: Optional[int] = None
    acao: str
    recurso_tipo: str
    recurso_id: int
    aluno_id: Optional[int] = None
    detalhes: Optional[str] = None
    ip_origem: Optional[str] = None
    criado_em: datetime

    usuario_nome: Optional[str] = None
