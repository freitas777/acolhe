from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from urllib.parse import urlencode
from pathlib import Path

app = FastAPI(title="Acolhe+")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

SUAP_URL = "https://suap.ifrn.edu.br"
CLIENT_ID = "z3PqIRdRxQYX1Wct9HZDHg3U5CkY5WZvrmi1C838"
REDIRECT_URI = "http://localhost:8000/"
SCOPE = "identificacao email documentos_pessoais"

@app.get("/")
async def root():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

# @app.get("/auth/login")
# async def login():
#     params = {
#         "response_type": "token",
#         "client_id": CLIENT_ID,
#         "redirect_uri": REDIRECT_URI,
#         "scope": SCOPE,
#     }
#     auth_url = f"{SUAP_URL}/o/authorize/?{urlencode(params)}"
#     return RedirectResponse(url=auth_url, status_code=302)

@app.get("/health")
async def health():
    return {"status": "ok"}

app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

@app.get("/js.cookie.js")
async def js_cookie():
    return FileResponse(str(FRONTEND_DIR / "js.cookie.js"), media_type="application/javascript")

@app.get("/settings.js")
async def settings_js():
    return FileResponse(str(FRONTEND_DIR / "settings.js"), media_type="application/javascript")
