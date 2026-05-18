from fastapi import APIRouter, Depends, HTTPException, status

from backend.dependencies import AuthData, get_current_usuario, require_napne
from backend.services.auth_service import AuthService
from backend.schemas.auth import (
    PendenciaResponse,
    PendenciaCreateRequest,
    PendenciaValidacaoRequest,
    AtualizarPerfilRequest,
    AlunoResumoResponse,
    UsuarioSUAPResponse,
)
from backend.models.aluno import Aluno

router = APIRouter(prefix="/equipe", tags=["Equipe NAPNE"])


@router.get("/pendencias", response_model=list[PendenciaResponse])
async def listar_pendencias(
    auth_data: AuthData = Depends(get_current_usuario),
    auth_service: AuthService = Depends(),
):
    pendencias = auth_service.obter_pendencias()
    result = []
    for p in pendencias:
        resp = PendenciaResponse(
            id=p.id,
            aluno_id=p.aluno_id,
            aluno_nome=p.aluno.nome if p.aluno else None,
            aluno_matricula=p.aluno.matricula if p.aluno else None,
            indicado_por_id=p.indicado_por_id,
            indicado_por_nome=p.indicado_por.nome if p.indicado_por else None,
            motivo=p.motivo,
            status=p.status,
            criado_em=p.criado_em,
            validado_em=p.validado_em,
        )
        result.append(resp)
    return result


@router.post("/pendencias", response_model=PendenciaResponse, status_code=status.HTTP_201_CREATED)
async def criar_pendencia(
    request: PendenciaCreateRequest,
    auth_data: AuthData = Depends(require_napne),
    auth_service: AuthService = Depends(),
):
    if request.motivo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Motivo é obrigatório")
    pendencia = auth_service.criar_pendencia(request.aluno_id, auth_data.usuario.id, request.motivo)
    return PendenciaResponse(
        id=pendencia.id,
        aluno_id=pendencia.aluno_id,
        aluno_nome=pendencia.aluno.nome if pendencia.aluno else None,
        aluno_matricula=pendencia.aluno.matricula if pendencia.aluno else None,
        indicado_por_id=pendencia.indicado_por_id,
        indicado_por_nome=pendencia.indicado_por.nome if pendencia.indicado_por else None,
        motivo=pendencia.motivo,
        status=pendencia.status,
        criado_em=pendencia.criado_em,
        validado_em=pendencia.validado_em,
    )


@router.put("/pendencias/{pendencia_id}", response_model=PendenciaResponse)
async def validar_pendencia(
    pendencia_id: int,
    request: PendenciaValidacaoRequest,
    auth_data: AuthData = Depends(require_napne),
    auth_service: AuthService = Depends(),
):
    if request.acao not in ("validado", "rejeitado"):
        raise HTTPException(status_code=400, detail="Ação deve ser 'validado' ou 'rejeitado'")
    pendencia = auth_service.validar_pendencia(pendencia_id, auth_data.usuario.id, request.acao)
    return PendenciaResponse(
        id=pendencia.id,
        aluno_id=pendencia.aluno_id,
        aluno_nome=pendencia.aluno.nome if pendencia.aluno else None,
        aluno_matricula=pendencia.aluno.matricula if pendencia.aluno else None,
        indicado_por_id=pendencia.indicado_por_id,
        indicado_por_nome=pendencia.indicado_por.nome if pendencia.indicado_por else None,
        motivo=pendencia.motivo,
        status=pendencia.status,
        criado_em=pendencia.criado_em,
        validado_em=pendencia.validado_em,
    )


@router.get("/alunos-ativos", response_model=list[AlunoResumoResponse])
async def listar_alunos_ativos(
    auth_data: AuthData = Depends(get_current_usuario),
    auth_service: AuthService = Depends(),
):
    alunos = auth_service.obter_alunos_ativos()
    result = []
    for a in alunos:
        result.append(AlunoResumoResponse(
            id=a.id,
            nome=a.nome,
            matricula=a.matricula,
            curso=a.curso,
            campus=a.campus,
            status_acompanhamento=a.status_acompanhamento,
            diagnostico=a.perfil.diagnostico if a.perfil else None,
            criado_em=a.criado_em,
        ))
    return result


@router.get("/alunos-busca", response_model=list[AlunoResumoResponse])
async def buscar_alunos(
    q: str = "",
    auth_data: AuthData = Depends(get_current_usuario),
    auth_service: AuthService = Depends(),
):
    if not q or len(q) < 2:
        return []
    alunos = auth_service.buscar_alunos(q)
    result = []
    for a in alunos:
        result.append(AlunoResumoResponse(
            id=a.id,
            nome=a.nome,
            matricula=a.matricula,
            curso=a.curso,
            campus=a.campus,
            status_acompanhamento=a.status_acompanhamento,
            diagnostico=a.perfil.diagnostico if a.perfil else None,
            criado_em=a.criado_em,
        ))
    return result


@router.put("/usuarios/{usuario_id}/perfil", response_model=UsuarioSUAPResponse)
async def atualizar_perfil(
    usuario_id: int,
    request: AtualizarPerfilRequest,
    auth_data: AuthData = Depends(get_current_usuario),
    auth_service: AuthService = Depends(),
):
    if auth_data.usuario.tipo_perfil not in ("psicopedagogo", "admin"):
        raise HTTPException(status_code=403, detail="Apenas psicopedagogos ou admins podem alterar perfis")
    if request.tipo_perfil not in ("aluno", "professor", "psicopedagogo", "admin", "servidor"):
        raise HTTPException(status_code=400, detail="Perfil inválido")
    usuario = auth_service.atualizar_perfil_usuario(usuario_id, request.tipo_perfil)
    return UsuarioSUAPResponse.model_validate(usuario)
