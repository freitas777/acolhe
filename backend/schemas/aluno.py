from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from backend.schemas.perfil_aluno import PerfilAlunoResponse


class AlunoCreate(BaseModel):
    nome: str
    observacoes: Optional[str] = None


class AlunoUpdate(BaseModel):
    nome: Optional[str] = None
    observacoes: Optional[str] = None


class AlunoResponse(BaseModel):
    id: int
    nome: str
    observacoes: Optional[str] = None
    criado_em: datetime
    perfil: Optional[PerfilAlunoResponse] = None

    model_config = {"from_attributes": True}
