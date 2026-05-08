from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import httpx

from backend.config import settings
from backend.services.auth_service import AuthService
from backend.schemas.auth import LoginRequest, LoginResponse, UsuarioSUAPResponse, DisciplinaResponse, AlunoAssistidoResponse

router = APIRouter(prefix="/auth", tags=["Autenticação"])

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
        return result
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SUAP indisponível no momento. Tente novamente mais tarde.",
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
                detail="Credenciais inválidas. Faça login novamente.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao comunicar com o SUAP (código {e.response.status_code}).",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro inesperado: {str(e)}",
        )

@router.get("/me", response_model=UsuarioSUAPResponse)
async def me(usuario_id: int = 1, auth_service: AuthService = Depends()):
    usuario = auth_service.obter_usuario_atual(usuario_id)
    return usuario

@router.get("/disciplinas", response_model=list[DisciplinaResponse])
async def disciplinas(usuario_id: int = 1, semestre: str = None, apenas_assistidos: bool = False, auth_service: AuthService = Depends()):
    try:
        usuario = auth_service.obter_usuario_atual(usuario_id)
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
            detail=f"Não foi possível buscar as disciplinas: {str(e)}",
        )

@router.get("/disciplinas/{disciplina_id}/alunos-assistidos", response_model=list[AlunoAssistidoResponse])
async def alunos_assistidos(disciplina_id: int, auth_service: AuthService = Depends()):
    try:
        return auth_service.obter_alunos_assistidos(disciplina_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar alunos assistidos: {str(e)}",
        )
