from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import AuthData, get_current_usuario
from backend.schemas.conteudo_gerado import ConteudoGeradoResponse
from backend.schemas.perfil_aluno import PerfilAlunoResponse
from backend.schemas.portal import MeuPerfilResponse, PerfilAlunoSelfUpdate
from backend.services.portal_service import PortalService

router = APIRouter(prefix="/portal", tags=["Portal do Aluno"])


def _service(db: Session = Depends(get_db)) -> PortalService:
    return PortalService(db)


@router.get("/meu-perfil", response_model=MeuPerfilResponse)
def get_meu_perfil(
    auth_data: AuthData = Depends(get_current_usuario),
    service: PortalService = Depends(_service),
):
    aluno = service.obter_meu_perfil(auth_data.usuario.suap_id)
    if not aluno:
        return MeuPerfilResponse(aluno=None, existe=False)
    return MeuPerfilResponse(aluno=aluno, existe=True)


@router.put("/meu-perfil", response_model=PerfilAlunoResponse)
def update_meu_perfil(
    data: PerfilAlunoSelfUpdate,
    auth_data: AuthData = Depends(get_current_usuario),
    service: PortalService = Depends(_service),
):
    try:
        perfil = service.atualizar_meu_perfil(
            auth_data.usuario.suap_id, data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    return perfil


@router.get("/meus-conteudos", response_model=list[ConteudoGeradoResponse])
def get_meus_conteudos(
    auth_data: AuthData = Depends(get_current_usuario),
    service: PortalService = Depends(_service),
):
    return service.listar_meus_conteudos(auth_data.usuario.suap_id)


@router.get("/meus-conteudos/{conteudo_id}", response_model=ConteudoGeradoResponse)
def get_meu_conteudo(
    conteudo_id: int,
    auth_data: AuthData = Depends(get_current_usuario),
    service: PortalService = Depends(_service),
):
    conteudo = service.obter_conteudo(auth_data.usuario.suap_id, conteudo_id)
    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conteudo nao encontrado ou nao pertence a este aluno.",
        )
    return conteudo
