from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from backend.schemas.perfil_aluno import PerfilAlunoResponse


class AlunoCreate(BaseModel):
    nome: str
    matricula: Optional[str] = None
    suap_id: Optional[str] = None
    curso: Optional[str] = None
    campus: Optional[str] = None
    foto_url: Optional[str] = None
    email: Optional[str] = None
    cpf: Optional[str] = None
    status_acompanhamento: str = "aguardando_indicacao"
    observacoes: Optional[str] = None


class AlunoUpdate(BaseModel):
    nome: Optional[str] = None
    observacoes: Optional[str] = None


class AlunoResponse(BaseModel):
    id: int
    nome: str
    matricula: Optional[str] = None
    suap_id: Optional[str] = None
    curso: Optional[str] = None
    campus: Optional[str] = None
    foto_url: Optional[str] = None
    email: Optional[str] = None
    cpf: Optional[str] = None
    status_acompanhamento: str = "aguardando_indicacao"
    data_importacao: Optional[datetime] = None
    observacoes: Optional[str] = None
    criado_em: datetime
    perfil: Optional[PerfilAlunoResponse] = None

    model_config = {"from_attributes": True}


class AlunoSUAPSearchResult(BaseModel):
    matricula: str
    nome: str
    curso: Optional[str] = None
    campus: Optional[str] = None
    foto_url: Optional[str] = None
    status_acompanhamento: Optional[str] = None
    ja_importado: bool = False
    aluno_id: Optional[int] = None


class ImportarAlunoRequest(BaseModel):
    matricula: str
