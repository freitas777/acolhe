from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, FileResponse
from urllib.parse import urlencode
import os

router = APIRouter(tags=["Autenticação"])

SUAP_URL = "https://suap.ifrn.edu.br"
CLIENT_ID = os.getenv("SUAP_CLIENT_ID", "z3PqIRdRxQYX1Wct9HZDHg3U5CkY5WZvrmi1C838")
REDIRECT_URI = os.getenv("SUAP_REDIRECT_URI", "http://localhost:8000/")
SCOPE = "identificacao email documentos_pessoais"

@router.get("/")
async def root():
    return FileResponse("frontend/index.html")
