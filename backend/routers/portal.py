from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import AuthData, get_current_usuario
from backend.schemas.conteudo_gerado import ConteudoGeradoResponse
from backend.schemas.perfil_aluno import PerfilAlunoResponse
from backend.schemas.portal import MeuPerfilResponse, PerfilAlunoSelfUpdate
from backend.services.portal_service import PortalService
from backend.services.audit_service import AuditService

router = APIRouter(prefix="/portal", tags=["Portal"])


def _service(db: Session = Depends(get_db)) -> PortalService:
    return PortalService(db)


@router.get("/meu-perfil", response_model=MeuPerfilResponse)
def get_meu_perfil(
    request: Request,
    auth_data: AuthData = Depends(get_current_usuario),
    service: PortalService = Depends(_service),
    db: Session = Depends(get_db),
):
    aluno = service.obter_meu_perfil(auth_data.usuario.suap_id)
    if not aluno:
        return MeuPerfilResponse(aluno=None, existe=False)
    perfil_id = aluno.perfil.id if aluno.perfil else 0
    AuditService(db).registrar(
        usuario_id=auth_data.usuario.id,
        acao="leitura",
        recurso_tipo="perfil_aluno",
        recurso_id=perfil_id,
        aluno_id=aluno.id,
        ip_origem=request.client.host if request.client else None,
    )
    return MeuPerfilResponse(aluno=aluno, existe=True)


@router.put("/meu-perfil", response_model=PerfilAlunoResponse)
def update_meu_perfil(
    data: PerfilAlunoSelfUpdate,
    request: Request,
    auth_data: AuthData = Depends(get_current_usuario),
    service: PortalService = Depends(_service),
    db: Session = Depends(get_db),
):
    try:
        perfil = service.atualizar_meu_perfil(
            auth_data.usuario.suap_id, data
        )
        AuditService(db).registrar(
            usuario_id=auth_data.usuario.id,
            acao="atualizacao",
            recurso_tipo="perfil_aluno",
            recurso_id=perfil.id,
            aluno_id=perfil.aluno_id,
            detalhes="autoatualizacao pelo portal",
            ip_origem=request.client.host if request.client else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    return perfil


@router.get("/meus-conteudos", response_model=list[ConteudoGeradoResponse])
def get_meus_conteudos(
    request: Request,
    auth_data: AuthData = Depends(get_current_usuario),
    service: PortalService = Depends(_service),
    db: Session = Depends(get_db),
):
    conteudos = service.listar_meus_conteudos(auth_data.usuario.suap_id)
    aluno = service.obter_meu_perfil(auth_data.usuario.suap_id)
    aluno_id = aluno.id if aluno else None
    AuditService(db).registrar(
        usuario_id=auth_data.usuario.id,
        acao="leitura",
        recurso_tipo="conteudo_gerado",
        recurso_id=0,
        aluno_id=aluno_id,
        detalhes=f"{len(conteudos)} conteudos listados",
        ip_origem=request.client.host if request.client else None,
    )
    return conteudos


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
