from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from urllib.parse import urlencode
from pathlib import Path

app = FastAPI(title="Acolhe+", version="1.0.0")

# =====================
# CORS
# =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
# CONFIGURAÇÕES SUAP
# =====================
SUAP_URL = "https://suap.ifrn.edu.br"
CLIENT_ID = "z3PqIRdRxQYX1Wct9HZDHg3U5CkY5WZvrmi1C838"
REDIRECT_URI = "http://localhost:8000/"
SCOPE = "identificacao email documentos_pessoais"

# =====================
# ROTAS
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

@app.get("/auth/login")
async def login():
    params = {
        "response_type": "token",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
    }
    auth_url = f"{SUAP_URL}/o/authorize/?{urlencode(params)}"
    return RedirectResponse(url=auth_url, status_code=302)

@app.get("/auth/me")
async def get_current_user():
    # TODO: Validar token e retornar usuário
    return {"nome": "Usuário Teste", "email": "teste@ifrn.edu.br"}

@app.get("/health")
async def health():
    return {"status": "ok", "frontend_dir": str(FRONTEND_DIR)}

# =====================
# API ROUTERS
# =====================
from backend.routers.chat import router as chat_router
from backend.routers.aluno import router as aluno_router
from backend.routers.usuario import router as usuario_router
from backend.routers.conteudo_gerado import router as conteudo_router

app.include_router(chat_router)
app.include_router(aluno_router)
app.include_router(usuario_router)
app.include_router(conteudo_router)

# =====================
# ARQUIVOS ESTÁTICOS
# =====================
app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

@app.get("/js.cookie.js")
async def js_cookie():
    return FileResponse(str(FRONTEND_DIR / "js.cookie.js"), media_type="application/javascript")

@app.get("/settings.js")
async def settings_js():
    return FileResponse(str(FRONTEND_DIR / "settings.js"), media_type="application/javascript")
