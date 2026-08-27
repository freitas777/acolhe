from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NotificacaoResponse(BaseModel):
    id: int
    tipo: str
    titulo: str
    mensagem: Optional[str] = None
    aluno_id: Optional[int] = None
    aluno_nome: Optional[str] = None
    destino_tipo: str
    destino_id: Optional[int] = None
    lida: bool = False
    criada_em: datetime

    model_config = {"from_attributes": True, "populate_by_name": True, "by_alias": False}


class NotificacaoCountResponse(BaseModel):
    nao_lidas: int
