from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MaterialResponse(BaseModel):
    id: int
    disciplina_id: int
    usuario_id: int
    nome_original: str
    tipo_arquivo: str
    tamanho: int
    descricao: Optional[str] = None
    categoria: str = "outro"
    criado_em: datetime
    usuario_nome: Optional[str] = None

    model_config = {"from_attributes": True}


class MaterialUploadResponse(BaseModel):
    id: int
    nome_original: str
    tipo_arquivo: str
    tamanho: int
    criado_em: datetime

    model_config = {"from_attributes": True}
