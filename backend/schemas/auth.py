from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    access_token: str
    semestre: str = ""


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
    senha_temporaria: Optional[bool] = None

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
    token: str = ""


class LocalLoginRequest(BaseModel):
    email: str
    senha: str


class ConviteRequest(BaseModel):
    email: str
    nome: str
    tipo_perfil: str = "psicopedagogo"


class ConviteResponse(BaseModel):
    email: str
    senha_temporaria: str
    tipo_perfil: str
    usuario_id: int


class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str

# --- New schemas for Professor Dashboard ---

class SolicitarApoioRequest(BaseModel):
    motivo: str = Field(..., min_length=5)

class ObservacaoRequest(BaseModel):
    disciplina_id: int
    texto: str

class ObservacaoResponse(BaseModel):
    id: int
    aluno_id: int
    disciplina_id: int
    professor_id: int
    disciplina_sigla: str = ""
    professor_nome: str = ""
    texto: str
    criado_em: datetime

    model_config = {"from_attributes": True}
