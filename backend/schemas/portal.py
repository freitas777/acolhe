from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from backend.models.perfil_aluno import PreferenciaAprendizado
from backend.schemas.aluno import AlunoResponse


class PerfilAlunoSelfUpdate(BaseModel):
    interesses: Optional[str] = None
    preferencia: Optional[PreferenciaAprendizado] = None


class MeuPerfilResponse(BaseModel):
    aluno: Optional[AlunoResponse] = None
    existe: bool = False

    model_config = {"from_attributes": True}


class MensagemPortalResponse(BaseModel):
    id: str
    role: str = Field(alias="papel")
    content: str = Field(alias="conteudo")
    created_at: datetime = Field(alias="criada_em")

    model_config = {"from_attributes": True, "populate_by_name": True, "by_alias": False}


class ConteudoPortalResponse(BaseModel):
    id: str
    tipo: str
    titulo: str
    data: datetime
    conteudo: Optional[str] = None
    modelo_ia: Optional[str] = None
    versao: Optional[int] = None
    usuario_tipo: Optional[str] = None
    messages: Optional[list[MensagemPortalResponse]] = None

    model_config = {"from_attributes": True}
