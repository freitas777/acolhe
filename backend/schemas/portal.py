from typing import Optional

from pydantic import BaseModel

from backend.models.perfil_aluno import PreferenciaAprendizado
from backend.schemas.aluno import AlunoResponse


class PerfilAlunoSelfUpdate(BaseModel):
    interesses: Optional[str] = None
    preferencia: Optional[PreferenciaAprendizado] = None


class MeuPerfilResponse(BaseModel):
    aluno: Optional[AlunoResponse] = None
    existe: bool = False

    model_config = {"from_attributes": True}
