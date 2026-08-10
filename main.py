from dotenv import load_dotenv
load_dotenv()

import json
import logging
import re
import time
import threading
import uuid
import httpx
from collections import defaultdict
from contextlib import asynccontextmanager
from contextvars import ContextVar
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pathlib import Path
from sqlalchemy import text

from backend.config import settings
from backend.database import engine, get_db
from backend.services.suap_service import SUAPService

# Context variable para request_id (thread-safe em async)
_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

class JSONFormatter(logging.Formatter):
    """Formatter JSON estruturado para logs."""
    def format(self, record):
        log_data = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "timestamp": self.formatTime(record),
            "request_id": _request_id_ctx.get(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        return json.dumps(log_data, ensure_ascii=False)

def setup_logging():
    """Configura logging estruturado JSON."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    logger = logging.getLogger("acolhe")
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    logger.addHandler(handler)
    
    # Silenciar logs verbosos de bibliotecas terceiras
    logging.getLogger("google.api_core").setLevel(logging.WARNING)
    logging.getLogger("google.auth").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger("acolhe")

_WEAK_SECRET_PATTERNS = [
    "change-me", "secret", "password", "changeme", "default",
    "acolhe-mais", "chave-secreta",
]

def _check_secret_key():
    key = settings.secret_key
    if len(key) < 32:
        logger.warning("SECRET_KEY tem menos de 32 caracteres — use uma chave forte em produção!")
    lower = key.lower()
    for pattern in _WEAK_SECRET_PATTERNS:
        if pattern in lower:
            logger.warning(f"SECRET_KEY contem padrao fraco '{pattern}' — troque em producao!")
            break

_check_secret_key()

# Metadata para OpenAPI/Swagger
tags_metadata = [
    {"name": "Auth", "description": "Autenticação e login (SUAP e local)"},
    {"name": "Chat", "description": "Chat com IA e geração de conteúdos educacionais"},
    {"name": "Aluno", "description": "CRUD de alunos e perfis"},
    {"name": "Usuario", "description": "Gestão de usuários da equipe NAPNE"},
    {"name": "Conteudos Gerados", "description": "Conteúdos educacionais gerados por IA"},
    {"name": "NAPNE", "description": "Operações exclusivas da equipe NAPNE (equipe, importação do SUAP)"},
    {"name": "Portal", "description": "Portal do aluno (perfil, conteúdos, acomodações)"},
    {"name": "Notificacoes", "description": "Sistema de notificações internas"},
    {"name": "Audit", "description": "Logs de auditoria (LGPD)"},
]

app = FastAPI(
    title="Acolhe+",
    description="Sistema de Apoio à Educação Inclusiva do IFRN",
    version="1.0.0",
    openapi_tags=tags_metadata,
)

# =====================
# HEALTH CHECKS
# =====================
async def check_database() -> tuple[bool, str]:
    """Verifica conectividade com o banco de dados."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        return True, "Database connection OK"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False, f"Database connection failed: {str(e)}"

async def check_suap() -> tuple[bool, str]:
    """Verifica conectividade com o SUAP (apenas reachability, sem auth)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.suap_base_url}/api/rh/",
                params={"format": "json"},
            )
            if response.status_code in (200, 401, 403):
                return True, f"SUAP reachable (status {response.status_code})"
            return False, f"SUAP returned unexpected status {response.status_code}"
    except httpx.TimeoutException:
        logger.warning("SUAP health check timed out")
        return False, "SUAP connection timed out"
    except Exception as e:
        logger.error(f"SUAP health check failed: {e}")
        return False, f"SUAP connection failed: {str(e)}"

@app.get("/health")
async def health_check():
    """
    Health check com verificação de dependências.
    Retorna 200 se saudável, 503 se alguma dependência estiver fora.
    """
    db_ok, db_msg = await check_database()
    suap_ok, suap_msg = await check_suap()
    
    status = "healthy" if (db_ok and suap_ok) else "unhealthy"
    status_code = 200 if (db_ok and suap_ok) else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "checks": {
                "database": {"ok": db_ok, "message": db_msg},
                "suap": {"ok": suap_ok, "message": suap_msg},
            }
        }
    )

# =====================
# RATE LIMITER
# =====================
class _RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _cleanup(self, key: str, now: float):
        self._buckets[key] = [t for t in self._buckets[key] if now - t < self.window_seconds]

    def is_limited(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            self._cleanup(key, now)
            if len(self._buckets[key]) >= self.max_requests:
                return True
            self._buckets[key].append(now)
            return False

# Rate limiters para diferentes categorias de endpoints
_CHAT_LIMITER = _RateLimiter(max_requests=10, window_seconds=60)
_SENSITIVE_LIMITER = _RateLimiter(max_requests=20, window_seconds=60)  # Para operaÃ§Ãµes sensÃ­veis
_LOGIN_LIMITER = _RateLimiter(max_requests=5, window_seconds=300)  # 5 tentativas a cada 5 min

# Endpoints de chat (limitaÃ§Ã£o mais restrita)
_RATE_LIMIT_PATHS = {"/api/chat/send", "/api/chat/stream"}

# Endpoints sensÃ­veis (importaÃ§Ã£o, observaÃ§Ãµes, solicitaÃ§Ã£o de apoio)
_SENSITIVE_PATHS = {
    "/api/importacao",
    "/api/importacao/search",
    "/api/importacao/importar",
}

# Prefixos sensÃ­veis (para matching parcial)
_SENSITIVE_PREFIXES = {
    "/auth/disciplinas/alunos/",  # ObservaÃ§Ãµes, solicitaÃ§Ã£o de apoio
}

def _is_sensitive_path(path: str) -> bool:
    """Verifica se o path Ã© um endpoint sensÃ­vel."""
    if path in _SENSITIVE_PATHS:
        return True
    for prefix in _SENSITIVE_PREFIXES:
        if path.startswith(prefix):
            return True
    return False

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Injeta request_id (correlation ID) em cada requisição e nos logs."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    _request_id_ctx.set(request_id)
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Determinar chave de rate limit: usuÃ¡rio autenticado > IP
    auth_header = request.headers.get("authorization", "")
    if auth_header:
        # Extrair usuario_id do token (simplificado: usar hash do token)
        client_key = f"user:{hash(auth_header) % 1000000}"
    elif request.client:
        client_key = f"ip:{request.client.host}"
    else:
        client_key = "unknown"

    # Rate limit especÃ­fico para login
    if request.url.path == "/auth/local-login":
        login_key = f"login:{request.client.host}" if request.client else "login:unknown"
        if _LOGIN_LIMITER.is_limited(login_key):
            return JSONResponse(
                status_code=429,
                content={"detail": "Muitas tentativas de login. Aguarde 5 minutos."},
            )

    # Aplicar rate limit baseado no tipo de endpoint
    if request.url.path in _RATE_LIMIT_PATHS:
        if _CHAT_LIMITER.is_limited(client_key):
            return JSONResponse(
                status_code=429,
                content={"detail": "Muitas requisiÃ§Ãµes. Aguarde um momento e tente novamente."},
            )
    elif _is_sensitive_path(request.url.path):
        if _SENSITIVE_LIMITER.is_limited(client_key):
            return JSONResponse(
                status_code=429,
                content={"detail": "Muitas requisiÃ§Ãµes. Aguarde um momento e tente novamente."},
            )

    return await call_next(request)

# =====================
# CORS
# =====================
ALLOWED_ORIGINS = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# SECURITY HEADERS
# =====================
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https://fonts.googleapis.com;"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# =====================
# CAMINHOS
# =====================
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

# =====================
# ROTAS DE PÁGINAS
# =====================
@app.get("/")
async def root():
    return FileResponse(str(BASE_DIR / "index.html"))

@app.get("/login")
async def login_page():
    return RedirectResponse(url="/", status_code=302)

@app.get("/chat")
async def chat_page():
    return FileResponse(str(FRONTEND_DIR / "chat.html"))

@app.get("/disciplinas")
async def disciplinas():
    return FileResponse(str(FRONTEND_DIR / "disciplinas.html"))

@app.get("/painel")
async def painel():
    return FileResponse(str(FRONTEND_DIR / "painel.html"))

@app.get("/importacao")
async def importacao():
    return FileResponse(str(FRONTEND_DIR / "importacao.html"))

@app.get("/portal")
async def portal():
    return FileResponse(str(FRONTEND_DIR / "portal.html"))

@app.get("/notificacoes")
async def notificacoes():
    return FileResponse(str(FRONTEND_DIR / "notificacoes.html"))


@app.get("/api/config")
async def config():
    return {
        "suap_client_id": settings.suap_client_id,
        "suap_redirect_uri": settings.suap_redirect_uri,
        "suap_base_url": settings.suap_base_url,
        "suap_scope": settings.suap_scope,
        "semestre_vigente": settings.semestre_vigente,
    }

# =====================
# API ROUTERS
# =====================
from backend.routers.chat import router as chat_router
from backend.routers.aluno import router as aluno_router
from backend.routers.usuario import router as usuario_router
from backend.routers.conteudo_gerado import router as conteudo_router
from backend.routers.auth import router as auth_router
from backend.routers.equipe import router as equipe_router
from backend.routers.importacao import router as importacao_router
from backend.routers.portal import router as portal_router
from backend.routers.notificacao import router as notificacao_router
from backend.routers.audit import router as audit_router

app.include_router(chat_router)
app.include_router(aluno_router)
app.include_router(usuario_router)
app.include_router(conteudo_router)
app.include_router(auth_router)
app.include_router(equipe_router)
app.include_router(importacao_router)
app.include_router(portal_router)
app.include_router(notificacao_router)
app.include_router(audit_router)
from backend.routers.feedback import router as feedback_router
app.include_router(feedback_router)
from backend.routers.lgpd import router as lgpd_router
app.include_router(lgpd_router)
from backend.routers.relatorios import router as relatorios_router
app.include_router(relatorios_router)
from backend.routers.material import router as material_router
app.include_router(material_router)

# =====================
# ARQUIVOS ESTÁTICOS
# =====================
app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.dev_mode)