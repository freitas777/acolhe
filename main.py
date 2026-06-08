from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path

from backend.config import settings

app = FastAPI(title="Acolhe+", version="1.0.0")

# =====================
# CORS
# =====================
ALLOWED_ORIGINS = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
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

@app.get("/dashboard")
async def dashboard():
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"))

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

@app.get("/health")
async def health():
    return {"status": "ok"}

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

app.include_router(chat_router)
app.include_router(aluno_router)
app.include_router(usuario_router)
app.include_router(conteudo_router)
app.include_router(auth_router)
app.include_router(equipe_router)
app.include_router(importacao_router)
app.include_router(portal_router)

# =====================
# ARQUIVOS ESTÁTICOS
# =====================
app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
