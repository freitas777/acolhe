from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class LoginRequest(BaseModel):
    access_token: str
    semestre: str = "2026.1"


class UsuarioSUAPResponse(BaseModel):
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


class DisciplinaResponse(BaseModel):
    id: int
    suap_id: int
    descricao: str
    sigla: Optional[str] = None
    situacao: Optional[str] = None
    professor: Optional[str] = None
    semestre: str
    usuario_id: int
    criada_em: datetime

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    usuario: UsuarioSUAPResponse
    disciplinas: List[DisciplinaResponse] = []
