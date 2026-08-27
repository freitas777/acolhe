from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import AuthData, get_current_usuario
from backend.schemas.notificacao import NotificacaoResponse, NotificacaoCountResponse
from backend.services.notificacao_service import NotificacaoService

router = APIRouter(prefix="/notificacoes", tags=["Notificacoes"])


def _destino_params(auth_data: AuthData):
    tipo_perfil = auth_data.usuario.tipo_perfil
    if tipo_perfil in ("psicopedagogo", "servidor", "admin"):
        destino_tipo = "napne"
        destino_id = None
    else:
        destino_tipo = "usuario"
        destino_id = auth_data.usuario.id
    campus = auth_data.usuario.campus
    usuario_id = auth_data.usuario.id
    return destino_tipo, destino_id, campus, usuario_id


@router.get("/", response_model=list[NotificacaoResponse])
def listar_notificacoes(
    skip: int = 0,
    limit: int = 20,
    auth_data: AuthData = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    destino_tipo, destino_id, campus, usuario_id = _destino_params(auth_data)
    service = NotificacaoService(db)
    notificacoes = service.listar(
        destino_tipo=destino_tipo,
        destino_id=destino_id,
        campus=campus,
        usuario_id=usuario_id,
        skip=skip,
        limit=min(limit, 50),
    )
    result = []
    for n in notificacoes:
        resp = NotificacaoResponse.model_validate(n)
        resp.lida = service.esta_lida(n.id, usuario_id)
        if n.aluno:
            resp.aluno_nome = n.aluno.nome
        result.append(resp)
    return result


@router.get("/count", response_model=NotificacaoCountResponse)
def contar_nao_lidas(
    auth_data: AuthData = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    destino_tipo, destino_id, campus, usuario_id = _destino_params(auth_data)
    service = NotificacaoService(db)
    count = service.contar_nao_lidas(
        destino_tipo=destino_tipo,
        destino_id=destino_id,
        campus=campus,
        usuario_id=usuario_id,
    )
    return NotificacaoCountResponse(nao_lidas=count)


@router.put("/ler-todas", response_model=NotificacaoCountResponse)
def marcar_todas_como_lidas(
    auth_data: AuthData = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    destino_tipo, destino_id, campus, usuario_id = _destino_params(auth_data)
    service = NotificacaoService(db)
    service.marcar_todas_como_lidas(
        destino_tipo=destino_tipo,
        destino_id=destino_id,
        campus=campus,
        usuario_id=usuario_id,
    )
    count = service.contar_nao_lidas(
        destino_tipo=destino_tipo,
        destino_id=destino_id,
        campus=campus,
        usuario_id=usuario_id,
    )
    return NotificacaoCountResponse(nao_lidas=count)


@router.delete("/{notificacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_notificacao(
    notificacao_id: int,
    auth_data: AuthData = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    destino_tipo, destino_id, campus, usuario_id = _destino_params(auth_data)
    service = NotificacaoService(db)
    ok = service.excluir(notificacao_id, usuario_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificacao nao encontrada.",
        )


@router.put("/{notificacao_id}/ler", response_model=NotificacaoResponse)
def marcar_como_lida(
    notificacao_id: int,
    auth_data: AuthData = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    destino_tipo, destino_id, campus, usuario_id = _destino_params(auth_data)
    service = NotificacaoService(db)
    ok = service.marcar_como_lida(notificacao_id, usuario_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificacao nao encontrada.",
        )
    n = service.repo.get_by_id(notificacao_id)
    resp = NotificacaoResponse.model_validate(n)
    resp.lida = True
    if n.aluno:
        resp.aluno_nome = n.aluno.nome
    return resp
