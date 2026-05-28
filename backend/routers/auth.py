import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import urlencode
import httpx

from backend.config import settings
from backend.database import get_db
from backend.dependencies import AuthData, get_current_usuario, require_napne, require_psicopedagogo_or_admin
from backend.models.conta_local import ContaLocal
from backend.models.usuario import Usuario
from backend.repositories.conta_local import ContaLocalRepository
from backend.repositories.usuario import UsuarioRepository
from backend.security import hash_senha, verificar_senha, criar_jwt
from backend.services.auth_service import AuthService
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
)

router = APIRouter(prefix="/auth", tags=["Autenticacao"])


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
        result = await auth_service.login_com_suap(request.access_token, request.semestre)
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
            detail=f"Erro ao comunicar com o SUAP (codigo {e.response.status_code}).",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro inesperado: {str(e)}",
        )


@router.post("/local-login", response_model=LoginResponse)
async def local_login(request: LocalLoginRequest, db: Session = Depends(get_db)):
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
    if not verificar_senha(request.senha, conta.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha invalidos.",
        )

    usuario_repo = UsuarioRepository(db)
    usuario = usuario_repo.get_by_id(conta.usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha invalidos.",
        )

    jwt_token = criar_jwt({"usuario_id": usuario.id, "tipo_perfil": usuario.tipo_perfil})

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
    if not verificar_senha(request.senha_atual, conta.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha atual incorreta.",
        )
    conta.senha_hash = hash_senha(request.nova_senha)
    conta.senha_temporaria = False
    db.commit()
    return {"detail": "Senha alterada com sucesso."}


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
            detail=f"Nao foi possivel buscar as disciplinas: {str(e)}",
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
            detail=f"Erro ao buscar alunos assistidos: {str(e)}",
        )
