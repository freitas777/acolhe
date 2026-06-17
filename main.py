from dotenv import load_dotenv
load_dotenv()

import logging
import re
import time
import threading
from collections import defaultdict
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pathlib import Path

from backend.config import settings

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

app = FastAPI(title="Acolhe+", version="1.0.0")

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

_CHAT_LIMITER = _RateLimiter(max_requests=10, window_seconds=60)
_RATE_LIMIT_PATHS = {"/api/chat/send", "/api/chat/stream"}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in _RATE_LIMIT_PATHS:
        auth_header = request.headers.get("authorization", "")
        client_key = auth_header or request.client.host if request.client else "unknown"
        if _CHAT_LIMITER.is_limited(client_key):
            return JSONResponse(
                status_code=429,
                content={"detail": "Muitas requisicoes. Aguarde um momento e tente novamente."},
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

@app.get("/health")
async def health():
    return {"status": "ok"}


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

app.include_router(chat_router)
app.include_router(aluno_router)
app.include_router(usuario_router)
app.include_router(conteudo_router)
app.include_router(auth_router)
app.include_router(equipe_router)
app.include_router(importacao_router)
app.include_router(portal_router)
app.include_router(notificacao_router)

# =====================
# ARQUIVOS ESTÁTICOS
# =====================
app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")