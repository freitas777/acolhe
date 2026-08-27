import secrets
import string

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import urlencode
import httpx

logger = logging.getLogger(__name__)

from backend.config import settings
from backend.database import get_db
from backend.dependencies import AuthData, get_current_usuario, require_napne, require_psicopedagogo_or_admin
from backend.models.conta_local import ContaLocal
from backend.models.usuario import Usuario
from backend.repositories.conta_local import ContaLocalRepository
from backend.repositories.usuario import UsuarioRepository
from backend.security import hash_senha, verificar_senha, criar_jwt
from backend.services.auth_service import AuthService
from backend.services.audit_service import AuditService
from backend.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LocalLoginRequest,
    ConviteRequest,
    ConviteResponse,
    AlterarSenhaRequest,
    UsuarioSUAPResponse,
    DisciplinaResponse,
    AlunoAssistidoResponse,
    SolicitarApoioRequest,
    ObservacaoRequest,
    ObservacaoResponse,
    PendenciaResponse,
)
from backend.schemas.perfil_aluno import PerfilAlunoResponse
from backend.schemas.conteudo_gerado import ConteudoGeradoResponse
from backend.repositories.acomodacao_observacao import AcomodacaoObservacaoRepository

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/login")
async def login():
    params = {
        "response_type": "token",
        "client_id": settings.suap_client_id,
        "redirect_uri": settings.suap_redirect_uri,
        "scope": settings.suap_scope,
    }
    auth_url = f"{settings.suap_base_url}/o/authorize/?{urlencode(params)}"
    return RedirectResponse(url=auth_url, status_code=302)


@router.post("/callback", response_model=LoginResponse)
async def callback(request: LoginRequest, auth_service: AuthService = Depends()):
    try:
        semestre = request.semestre or settings.semestre_vigente
        result = await auth_service.login_com_suap(request.access_token, semestre)
        result["token"] = request.access_token
        return result
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SUAP indisponivel no momento. Tente novamente mais tarde.",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Tempo esgotado ao conectar com o SUAP. Tente novamente mais tarde.",
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais invalidas. Faca login novamente.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao comunicar com SUAP: {e.response.status_code}",
        )
    except Exception as e:
        logger.error("Erro inesperado no callback SUAP: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar login. Tente novamente.",
        )

# --- Professor Dashboard endpoints ---

# View full student profile (read‑only)
@router.get("/disciplinas/alunos/{aluno_id}/perfil", response_model=PerfilAlunoResponse)
async def aluno_perfil(
    aluno_id: int,
    request: Request,
    auth_data: AuthData = Depends(get_current_usuario),
    auth_service: AuthService = Depends(),
    db: Session = Depends(get_db),
):
    try:
        perfil = auth_service.obter_perfil_aluno(auth_data.usuario.id, aluno_id)
        AuditService(db).registrar(
            usuario_id=auth_data.usuario.id,
            acao="leitura",
            recurso_tipo="perfil_aluno",
            recurso_id=perfil.id if perfil else 0,
            aluno_id=aluno_id,
            ip_origem=request.client.host if request.client else None,
        )
        return perfil
    except HTTPException as e:
        raise e

# View adaptive content generated for a student
@router.get("/disciplinas/alunos/{aluno_id}/conteudos", response_model=list[ConteudoGeradoResponse])
async def aluno_conteudos(
    aluno_id: int,
    request: Request,
    auth_data: AuthData = Depends(get_current_usuario),
    auth_service: AuthService = Depends(),
    db: Session = Depends(get_db),
):
    try:
        conteudos = auth_service.obter_conteudos_aluno(auth_data.usuario.id, aluno_id)
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
    except HTTPException as e:
        raise e

# Request NAPNE support for a student (creates a pendência)
@router.post("/disciplinas/alunos/{aluno_id}/solicitar-apoio", response_model=PendenciaResponse)
async def solicitar_apoio(
    aluno_id: int,
    request: SolicitarApoioRequest,
    req: Request,
    auth_data: AuthData = Depends(get_current_usuario),
    auth_service: AuthService = Depends(),
    db: Session = Depends(get_db),
):
    try:
        pend = auth_service.solicitar_apoio_napne(auth_data.usuario.id, aluno_id, request.motivo)
        AuditService(db).registrar(
            usuario_id=auth_data.usuario.id,
            acao="criacao",
            recurso_tipo="pendencia",
            recurso_id=pend.id,
            aluno_id=aluno_id,
            detalhes=request.motivo,
            ip_origem=req.client.host if req.client else None,
        )
        return pend
    except HTTPException as e:
        raise e

# Create or update a professor's observation for a student in a discipline
@router.post("/disciplinas/alunos/{aluno_id}/observacao", response_model=ObservacaoResponse)
async def criar_observacao(
    aluno_id: int,
    request: ObservacaoRequest,
    req: Request,
    auth_data: AuthData = Depends(get_current_usuario),
    auth_service: AuthService = Depends(),
    db: Session = Depends(get_db),
):
    try:
        obs = auth_service.criar_ou_atualizar_observacao(
            auth_data.usuario.id, aluno_id, request.disciplina_id, request.texto
        )
        is_update = obs.criado_em != obs.atualizado_em if hasattr(obs, 'atualizado_em') else False
        AuditService(db).registrar(
            usuario_id=auth_data.usuario.id,
            acao="atualizacao" if is_update else "criacao",
            recurso_tipo="observacao_acomodacao",
            recurso_id=obs.id,
            aluno_id=aluno_id,
            detalhes=f"disciplina_id={request.disciplina_id}",
            ip_origem=req.client.host if req.client else None,
        )
        return obs
    except HTTPException as e:
        raise e

# Retrieve an existing observation (if any) for a student in a discipline
@router.get("/disciplinas/alunos/{aluno_id}/observacao", response_model=ObservacaoResponse)
async def obter_observacao(
    aluno_id: int,
    disciplina_id: int,
    request: Request,
    auth_data: AuthData = Depends(get_current_usuario),
    auth_service: AuthService = Depends(),
    db: Session = Depends(get_db),
):
    obs = auth_service.obter_observacao(auth_data.usuario.id, aluno_id, disciplina_id)
    AuditService(db).registrar(
        usuario_id=auth_data.usuario.id,
        acao="leitura",
        recurso_tipo="observacao_acomodacao",
        recurso_id=obs.id if obs else 0,
        aluno_id=aluno_id,
        detalhes=f"disciplina_id={disciplina_id}",
        ip_origem=request.client.host if request.client else None,
    )
    return obs


@router.post("/logout")
async def logout(
    request: Request,
    auth_data: AuthData = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    from datetime import datetime, timezone
    from backend.security import validar_jwt
    from backend.repositories.token_revogado import TokenRevogadoRepository
    from backend.services.audit_service import AuditService

    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        payload = validar_jwt(token)
        if payload:
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                token_repo = TokenRevogadoRepository(db)
                expira_em = datetime.fromtimestamp(exp, tz=timezone.utc)
                token_repo.revogar_token(jti, auth_data.usuario.id, expira_em)

                AuditService(db).registrar(
                    usuario_id=auth_data.usuario.id,
                    acao="logout",
                    recurso_tipo="usuario",
                    recurso_id=auth_data.usuario.id,
                )

    return {"detail": "Logout realizado com sucesso."}


@router.post("/local-login", response_model=LoginResponse)
async def local_login(request: LocalLoginRequest, req: Request, db: Session = Depends(get_db)):
    from backend.services.audit_service import AuditService
    from datetime import datetime, timezone, timedelta
    conta_repo = ContaLocalRepository(db)
    conta = conta_repo.get_by_email(request.email)
    if not conta:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha invalidos.",
        )
    if not conta.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada.",
        )
    if conta.bloqueado_ate:
        agora = datetime.now(timezone.utc)
        bloqueado_ate = conta.bloqueado_ate if conta.bloqueado_ate.tzinfo else conta.bloqueado_ate.replace(tzinfo=timezone.utc)
        if bloqueado_ate > agora:
            minutos_restantes = int((bloqueado_ate - agora).total_seconds() / 60)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Conta bloqueada. Tente novamente em {minutos_restantes} minutos.",
            )
    import asyncio
    senha_valida = await asyncio.to_thread(verificar_senha, request.senha, conta.senha_hash)
    if not senha_valida:
        conta.tentativas_login += 1
        if conta.tentativas_login >= 10:
            conta.bloqueado_ate = datetime.now(timezone.utc) + timedelta(minutes=30)
        db.commit()
        AuditService(db).registrar(
            usuario_id=conta.usuario_id,
            acao="login_falha",
            recurso_tipo="usuario",
            recurso_id=conta.usuario_id,
            ip_origem=req.client.host if req.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha invalidos.",
        )

    if not (conta.senha_hash.startswith('$2b$') or conta.senha_hash.startswith('$2a$')):
        conta.senha_hash = hash_senha(request.senha)
        db.commit()

    conta.tentativas_login = 0
    conta.bloqueado_ate = None
    db.commit()

    usuario_repo = UsuarioRepository(db)
    usuario = usuario_repo.get_by_id(conta.usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha invalidos.",
        )

    AuditService(db).registrar(
        usuario_id=usuario.id,
        acao="login_sucesso",
        recurso_tipo="usuario",
        recurso_id=usuario.id,
        ip_origem=req.client.host if req.client else None,
    )

    jwt_token = criar_jwt({
        "usuario_id": usuario.id,
        "tipo_perfil": usuario.tipo_perfil,
        "nome": usuario.nome,
        "senha_temporaria": conta.senha_temporaria,
    })

    resp = LoginResponse(
        usuario=UsuarioSUAPResponse.model_validate(usuario),
        tipo_perfil=usuario.tipo_perfil,
        disciplinas=[],
        token=jwt_token,
    )
    resp.usuario.senha_temporaria = conta.senha_temporaria
    return resp


@router.post("/convite", response_model=ConviteResponse)
async def criar_convite(
 request: ConviteRequest,
 auth_data: AuthData = Depends(require_psicopedagogo_or_admin),
 db: Session = Depends(get_db),
):
    if request.tipo_perfil not in ("psicopedagogo", "servidor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tipo_perfil deve ser psicopedagogo, servidor ou admin.",
        )

    conta_repo = ContaLocalRepository(db)
    existing = conta_repo.get_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe uma conta com este email.",
        )

    existing_usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    if existing_usuario:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe um usuario com este email.",
        )

    senha_temp = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))

    usuario_repo = UsuarioRepository(db)
    novo_usuario = usuario_repo.create({
        "suap_id": f"local_{request.email}",
        "nome": request.nome,
        "email": request.email,
        "tipo_perfil": request.tipo_perfil,
        "aprovado_napne": True,
    })

    conta_repo.create({
        "email": request.email,
        "senha_hash": hash_senha(senha_temp),
        "usuario_id": novo_usuario.id,
        "ativo": True,
        "senha_temporaria": request.tipo_perfil != "admin",
    })

    return ConviteResponse(
        email=request.email,
        senha_temporaria=senha_temp,
        tipo_perfil=request.tipo_perfil,
        usuario_id=novo_usuario.id,
    )


@router.put("/alterar-senha")
async def alterar_senha(
    request: AlterarSenhaRequest,
    auth_data: AuthData = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    conta = db.query(ContaLocal).filter(ContaLocal.usuario_id == auth_data.usuario.id).first()
    if not conta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario nao possui conta local.",
        )
    import asyncio
    senha_valida = await asyncio.to_thread(verificar_senha, request.senha_atual, conta.senha_hash)
    if not senha_valida:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha atual incorreta.",
        )
    conta.senha_hash = await asyncio.to_thread(hash_senha, request.nova_senha)
    conta.senha_temporaria = False
    db.commit()
    new_token = criar_jwt({
        "usuario_id": auth_data.usuario.id,
        "tipo_perfil": auth_data.usuario.tipo_perfil,
        "nome": auth_data.usuario.nome,
        "senha_temporaria": False,
    })
    return {"detail": "Senha alterada com sucesso.", "token": new_token}


@router.get("/me", response_model=UsuarioSUAPResponse)
async def me(auth_data: AuthData = Depends(get_current_usuario), db: Session = Depends(get_db)):
    usuario = auth_data.usuario
    conta = db.query(ContaLocal).filter(ContaLocal.usuario_id == usuario.id).first()
    resp = UsuarioSUAPResponse.model_validate(usuario)
    resp.senha_temporaria = conta.senha_temporaria if conta else None
    return resp


@router.get("/disciplinas", response_model=list[DisciplinaResponse])
async def disciplinas(
    semestre: str = None,
    apenas_assistidos: bool = False,
    auth_data: AuthData = Depends(get_current_usuario),
    auth_service: AuthService = Depends(),
):
    try:
        usuario = auth_data.usuario
        disciplinas_db = auth_service.obter_disciplinas(usuario.id, semestre)
        result = []
        for d in disciplinas_db:
            qtd = auth_service.diario_aluno_repo.contar_por_disciplina(d.id)
            if apenas_assistidos and qtd == 0:
                continue
            disc_resp = DisciplinaResponse.model_validate(d)
            disc_resp.qtd_alunos_assistidos = qtd
            result.append(disc_resp)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível buscar as disciplinas. Tente novamente.",
        )


@router.get("/disciplinas/{disciplina_id}/alunos-assistidos", response_model=list[AlunoAssistidoResponse])
async def alunos_assistidos(
    disciplina_id: int,
    auth_data: AuthData = Depends(get_current_usuario),
    auth_service: AuthService = Depends(),
):
    try:
        return auth_service.obter_alunos_assistidos(disciplina_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar alunos assistidos. Tente novamente.",
        )
