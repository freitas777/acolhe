from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from backend.models.usuario import TipoPerfil


class UsuarioCreate(BaseModel):
    suap_id: str
    nome: str
    email: str
    tipo_perfil: TipoPerfil = TipoPerfil.professor


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    tipo_perfil: Optional[TipoPerfil] = None


class UsuarioResponse(BaseModel):
    id: int
    suap_id: str
    nome: str
    email: str
    tipo_perfil: TipoPerfil
    criado_em: datetime

    model_config = {"from_attributes": True}
