from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from backend.database import get_db
from backend.dependencies import AuthData, get_current_usuario, require_napne, require_psicopedagogo_or_admin
from backend.models.acomodacao_observacao import AcomodacaoObservacao
from backend.models.aluno import Aluno
from backend.models.conteudo_gerado import ConteudoGerado
from backend.models.pendencia_validacao import PendenciaValidacao, StatusPendencia
from backend.services.auth_service import AuthService
from backend.services.audit_service import AuditService
from backend.schemas.auth import (
    PendenciaResponse,
    PendenciaCreateRequest,
    PendenciaValidacaoRequest,
    AtualizarPerfilRequest,
    AlunoResumoResponse,
    UsuarioSUAPResponse,
    ObservacaoResponse,
)
from backend.schemas.perfil_aluno import PerfilAlunoCreate, PerfilAlunoUpdate, PerfilAlunoResponse
from backend.models.aluno import Aluno
from backend.models.usuario import Usuario
from backend.models.perfil_aluno import PerfilAluno
from backend.models.conta_local import ContaLocal

router = APIRouter(prefix="/equipe", tags=["NAPNE"])


@router.get("/membros")
async def listar_membros(
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    membros = db.query(Usuario).filter(
        Usuario.tipo_perfil.in_(["psicopedagogo", "servidor", "admin"])
    ).order_by(Usuario.nome).all()
    result = []
    for m in membros:
        conta = db.query(ContaLocal).filter(ContaLocal.usuario_id == m.id).first()
        result.append({
            "id": m.id,
            "nome": m.nome,
            "email": m.email,
            "tipo_perfil": m.tipo_perfil,
            "aprovado_napne": m.aprovado_napne,
            "tem_conta_local": conta is not None,
            "conta_ativa": conta.ativo if conta else None,
            "senha_temporaria": conta.senha_temporaria if conta else None,
        })
    return result


@router.put("/membros/{usuario_id}/desativar")
async def desativar_membro(
    usuario_id: int,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    if auth_data.usuario.tipo_perfil != "admin":
        raise HTTPException(status_code=403, detail="Apenas admins podem desativar membros.")
    if auth_data.usuario.id == usuario_id:
        raise HTTPException(status_code=400, detail="Voce nao pode desativar sua propria conta.")
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
    conta = db.query(ContaLocal).filter(ContaLocal.usuario_id == usuario_id).first()
    if conta:
        conta.ativo = False
        db.commit()
    return {"detail": "Conta desativada com sucesso."}


@router.get("/pendencias", response_model=list[PendenciaResponse])
async def listar_pendencias(
    skip: int = 0,
    limit: int = 50,
    auth_data: AuthData = Depends(require_napne),
    auth_service: AuthService = Depends(),
):
    pendencias = auth_service.obter_pendencias()
    # Aplicar paginação
    pendencias_paginadas = pendencias[skip : skip + limit]
    result = []
    for p in pendencias_paginadas:
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
    req: Request,
    auth_data: AuthData = Depends(require_napne),
    auth_service: AuthService = Depends(),
    db: Session = Depends(get_db),
):
    if request.acao not in ("validado", "rejeitado"):
        raise HTTPException(status_code=400, detail="Ação deve ser 'validado' ou 'rejeitado'")
    pendencia = auth_service.validar_pendencia(pendencia_id, auth_data.usuario.id, request.acao)
    AuditService(db).registrar(
        usuario_id=auth_data.usuario.id,
        acao="atualizacao",
        recurso_tipo="pendencia",
        recurso_id=pendencia.id,
        aluno_id=pendencia.aluno_id,
        detalhes=f"acao={request.acao}",
        ip_origem=req.client.host if req.client else None,
    )
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
 auth_data: AuthData = Depends(require_napne),
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
 auth_data: AuthData = Depends(require_napne),
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
 auth_data: AuthData = Depends(require_psicopedagogo_or_admin),
 auth_service: AuthService = Depends(),
):
 if request.tipo_perfil not in ("aluno", "professor", "psicopedagogo", "admin", "servidor"):
  raise HTTPException(status_code=400, detail="Perfil invalido")
 usuario = auth_service.atualizar_perfil_usuario(usuario_id, request.tipo_perfil)
 return UsuarioSUAPResponse.model_validate(usuario)


@router.get("/alunos/{aluno_id}/perfil", response_model=PerfilAlunoResponse)
async def obter_perfil_aluno(
 aluno_id: int,
 request: Request,
 auth_data: AuthData = Depends(require_napne),
 db: Session = Depends(get_db),
):
    aluno = db.query(Aluno).options(selectinload(Aluno.perfil)).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")
    perfil = aluno.perfil
    perfil_id = perfil.id if perfil else 0
    AuditService(db).registrar(
        usuario_id=auth_data.usuario.id,
        acao="leitura",
        recurso_tipo="perfil_aluno",
        recurso_id=perfil_id,
        aluno_id=aluno_id,
        ip_origem=request.client.host if request.client else None,
    )
    if not perfil:
        return PerfilAlunoResponse(
            id=0,
            aluno_id=aluno_id,
            nivel_atencao=None,
            dificuldade_leitura=False,
            preferencia=None,
            interesses=None,
            diagnostico=None,
        )
    return PerfilAlunoResponse.model_validate(aluno.perfil)


@router.put("/alunos/{aluno_id}/perfil", response_model=PerfilAlunoResponse)
async def criar_ou_atualizar_perfil_aluno(
    aluno_id: int,
    request: PerfilAlunoCreate,
    req: Request,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    aluno = db.query(Aluno).options(selectinload(Aluno.perfil)).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")
    perfil = aluno.perfil
    is_update = perfil is not None
    if not perfil:
        perfil = PerfilAluno(aluno_id=aluno_id)
        db.add(perfil)
        db.flush()
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(perfil, key, value)
    db.commit()
    db.refresh(perfil)
    AuditService(db).registrar(
        usuario_id=auth_data.usuario.id,
        acao="atualizacao" if is_update else "criacao",
        recurso_tipo="perfil_aluno",
        recurso_id=perfil.id,
        aluno_id=aluno_id,
        detalhes=str(list(update_data.keys())),
        ip_origem=req.client.host if req.client else None,
    )
    return PerfilAlunoResponse.model_validate(perfil)


@router.get("/alunos/{aluno_id}/observacoes", response_model=list[ObservacaoResponse])
async def listar_observacoes_aluno(
    aluno_id: int,
    request: Request,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    from backend.repositories.acomodacao_observacao import AcomodacaoObservacaoRepository
    repo = AcomodacaoObservacaoRepository(db)
    observacoes = repo.listar_por_aluno(aluno_id)
    AuditService(db).registrar(
        usuario_id=auth_data.usuario.id,
        acao="leitura",
        recurso_tipo="observacao_acomodacao",
        recurso_id=0,
        aluno_id=aluno_id,
        detalhes=f"{len(observacoes)} observacoes listadas",
        ip_origem=request.client.host if request.client else None,
    )
    return observacoes


# =====================
# DASHBOARD METRICS
# =====================

class DashboardMetricsResponse(BaseModel):
    alunos_ativos: int
    pendencias_pendentes: int
    observacoes_mes: int
    conteudos_gerados: int

@router.get("/dashboard", response_model=DashboardMetricsResponse)
async def get_dashboard(
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    """
    Retorna métricas agregadas para o dashboard NAPNE.
    - alunos_ativos: total de alunos com status_acompanhamento = 'ativo'
    - pendencias_pendentes: total de pendências com status = 'pendente'
    - observacoes_mes: total de observações criadas no mês atual
    - conteudos_gerados: total de conteúdos gerados por IA
    """
    # Alunos ativos
    alunos_ativos = db.query(func.count(Aluno.id)).filter(
        Aluno.status_acompanhamento == 'ativo'
    ).scalar() or 0
    
    # Pendências pendentes
    pendencias_pendentes = db.query(func.count(PendenciaValidacao.id)).filter(
        PendenciaValidacao.status == StatusPendencia.pendente.value
    ).scalar() or 0
    
    # Observações do mês atual
    inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    observacoes_mes = db.query(func.count(AcomodacaoObservacao.id)).filter(
        AcomodacaoObservacao.criado_em >= inicio_mes
    ).scalar() or 0
    
    # Conteúdos gerados
    conteudos_gerados = db.query(func.count(ConteudoGerado.id)).scalar() or 0
    
    return DashboardMetricsResponse(
        alunos_ativos=alunos_ativos,
        pendencias_pendentes=pendencias_pendentes,
        observacoes_mes=observacoes_mes,
        conteudos_gerados=conteudos_gerados,
    )
