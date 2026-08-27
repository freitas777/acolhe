from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel

TipoPerfilStr = Literal["aluno", "professor", "psicopedagogo", "servidor", "admin"]


class UsuarioCreate(BaseModel):
    suap_id: str
    nome: str
    email: str
    matricula: Optional[str] = None
    campus: Optional[str] = None
    tipo_vinculo: Optional[str] = None
    tipo_perfil: TipoPerfilStr = "aluno"


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    matricula: Optional[str] = None
    campus: Optional[str] = None
    tipo_vinculo: Optional[str] = None
    tipo_perfil: Optional[TipoPerfilStr] = None


class UsuarioResponse(BaseModel):
    id: int
    suap_id: str
    nome: str
    email: str
    matricula: Optional[str] = None
    campus: Optional[str] = None
    tipo_vinculo: Optional[str] = None
    tipo_perfil: str
    criado_em: datetime

    model_config = {"from_attributes": True}
