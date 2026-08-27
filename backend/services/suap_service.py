from __future__ import annotations

import httpx
import logging
from typing import List, Dict, Optional

from backend.config import settings

logger = logging.getLogger(__name__)


class SUAPService:
    def __init__(self):
        self.base_url = settings.suap_base_url
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    async def _get(self, token: str, path: str, params: Optional[dict] = None, timeout: float = 15.0) -> httpx.Response:
        logger.info("[SUAP] GET %s%s (params=%s)", self.base_url, path, params)
        client = await self._get_client()
        response = await client.get(
            f"{self.base_url}{path}",
            params=params,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=timeout,
        )
        logger.info("[SUAP] Resposta: status=%s", response.status_code)
        response.raise_for_status()
        return response

    async def get_eu(self, token: str, scope: str = "") -> dict:
        params = {}
        if scope:
            params["scope"] = scope
        logger.info("[SUAP] GET /api/rh/eu/ (scope=%s)", scope)
        response = await self._get(token, "/api/rh/eu/", params=params)
        data = response.json()
        logger.info("[SUAP] /api/rh/eu/ resposta: keys=%s", list(data.keys()) if isinstance(data, dict) else "N/A")
        return data

    async def get_meus_vinculos(self, token: str, scope: str = "") -> list[dict]:
        all_results = []
        page = 1
        while True:
            params = {"page": page}
            if scope:
                params["scope"] = scope
            response = await self._get(
                token, "/api/rh/meus-vinculos/",
                params=params,
            )
            data = response.json()
            results = data.get("results", [])
            all_results.extend(results)
            if data.get("next"):
                page += 1
            else:
                break
        return all_results

    async def get_disciplinas(self, token: str, semestre: str, scope: str = "") -> list[dict]:
        logger.info("[SUAP] Buscando disciplinas para semestre=%s", semestre)
        params = {}
        if scope:
            params["scope"] = scope
        response = await self._get(token, f"/api/ensino/disciplinas/{semestre}/", params=params)
        data = response.json()
        logger.info("[SUAP] Resposta de disciplinas: tipo=%s, tamanho=%s",
                   type(data).__name__, len(data) if isinstance(data, (list, dict)) else "N/A")
        result = data if isinstance(data, list) else data.get("results", [])
        logger.info("[SUAP] Total de disciplinas extraidas: %d", len(result))
        return result

    async def get_meus_diarios(self, token: str, ano_letivo: int, periodo_letivo: int, scope: str = "") -> list[dict]:
        all_results = []
        page = 1
        while True:
            params = {"page": page}
            if scope:
                params["scope"] = scope
            response = await self._get(
                token, f"/api/ensino/meus-diarios/{ano_letivo}/{periodo_letivo}/",
                params=params,
            )
            data = response.json()
            results = data.get("results", [])
            all_results.extend(results)
            if data.get("next"):
                page += 1
            else:
                break
        return all_results

    async def get_alunos_diario(self, token: str, id_diario: int, scope: str = "") -> list[dict]:
        all_results = []
        page = 1
        while True:
            params = {"page": page}
            if scope:
                params["scope"] = scope
            response = await self._get(
                token, f"/api/ensino/diarios/{id_diario}/alunos/",
                params=params,
            )
            data = response.json()
            results = data.get("results", [])
            all_results.extend(results)
            if data.get("next"):
                page += 1
            else:
                break
        return all_results

    async def get_aluno_matriculado(self, token: str, matricula: str) -> Optional[dict]:
        try:
            response = await self._get(
                token, "/api/ensino/aluno-matriculado/",
                params={"matricula": matricula},
            )
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info("[SUAP] aluno-matriculado 404 para matricula=%s", matricula)
                return None
            raise

    async def buscar_alunos_resumido(self, token: str, matricula: Optional[str] = None, codigo_curso: Optional[str] = None, ano_conclusao: Optional[str] = None) -> List[Dict]:
        params = {}
        if matricula:
            params["matricula"] = matricula
        if codigo_curso:
            params["codigo_curso"] = codigo_curso
        if ano_conclusao:
            params["ano_conclusao"] = ano_conclusao
        try:
            response = await self._get(
                token, "/api/ensino/aluno-resumido/",
                params=params, timeout=20.0,
            )
            data = response.json()
            return data if isinstance(data, list) else data.get("results", [])
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info("[SUAP] aluno-resumido 404 para matricula=%s", matricula)
                return []
            raise

    async def validar_token(self, token: str) -> bool:
        try:
            await self.get_eu(token, scope="identificacao")
            return True
        except httpx.HTTPStatusError:
            return False
