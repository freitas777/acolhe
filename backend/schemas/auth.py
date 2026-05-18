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
    setor: Optional[str] = None
    aprovado_napne: bool = False
    criado_em: datetime

    model_config = {"from_attributes": True}


class DisciplinaResponse(BaseModel):
    id: int
    suap_id: int
    diario_id: Optional[int] = None
    descricao: str
    sigla: Optional[str] = None
    codigo_turma: Optional[str] = None
    situacao: Optional[str] = None
    professor: Optional[str] = None
    semestre: str
    usuario_id: int
    criada_em: datetime
    qtd_alunos_assistidos: int = 0

    model_config = {"from_attributes": True}


class AlunoAssistidoResponse(BaseModel):
    id: int
    aluno_id: int
    aluno_nome: str
    aluno_matricula: Optional[str] = None
    disciplina_id: int
    criado_em: datetime

    model_config = {"from_attributes": True}


class PendenciaResponse(BaseModel):
    id: int
    aluno_id: int
    aluno_nome: Optional[str] = None
    aluno_matricula: Optional[str] = None
    indicado_por_id: Optional[int] = None
    indicado_por_nome: Optional[str] = None
    motivo: Optional[str] = None
    status: str
    criado_em: datetime
    validado_em: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PendenciaCreateRequest(BaseModel):
    aluno_id: int
    motivo: Optional[str] = None


class PendenciaValidacaoRequest(BaseModel):
    acao: str


class AtualizarPerfilRequest(BaseModel):
    tipo_perfil: str


class AlunoResumoResponse(BaseModel):
    id: int
    nome: str
    matricula: Optional[str] = None
    curso: Optional[str] = None
    campus: Optional[str] = None
    status_acompanhamento: Optional[str] = None
    diagnostico: Optional[str] = None
    criado_em: datetime

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    usuario: UsuarioSUAPResponse
    tipo_perfil: str = "aluno"
    disciplinas: List[DisciplinaResponse] = []
