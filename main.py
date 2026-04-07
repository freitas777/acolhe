from fastapi import FastAPI

from backend.routers import aluno, conteudo_gerado, usuario

app = FastAPI(
    title="Acolhe+",
    description="Sistema inclusivo de apoio educacional com geracao de conteudo via IA",
    version="0.1.0",
)

app.include_router(usuario.router, prefix="/api")
app.include_router(aluno.router, prefix="/api")
app.include_router(conteudo_gerado.router, prefix="/api")


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Acolhe+"}
