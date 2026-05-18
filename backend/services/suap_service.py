from __future__ import annotations

import httpx
import logging
from typing import List, Dict, Optional

from backend.config import settings

logger = logging.getLogger(__name__)


class SUAPService:
    def __init__(self):
        self.base_url = settings.suap_base_url

    async def _get(self, token: str, path: str, params: Optional[dict] = None, timeout: float = 15.0) -> httpx.Response:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                f"{self.base_url}{path}",
                params=params,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            return response

    async def get_meus_dados(self, token: str) -> dict:
        response = await self._get(token, "/api/rh/meus-dados/")
        return response.json()

    async def get_eu(self, token: str) -> dict:
        response = await self._get(token, "/api/rh/eu/")
        return response.json()

    async def get_meus_vinculos(self, token: str) -> list[dict]:
        all_results = []
        page = 1
        while True:
            response = await self._get(
                token, "/api/rh/meus-vinculos/",
                params={"page": page},
            )
            data = response.json()
            results = data.get("results", [])
            all_results.extend(results)
            if data.get("next"):
                page += 1
            else:
                break
        return all_results

    async def get_disciplinas(self, token: str, semestre: str) -> list[dict]:
        response = await self._get(token, f"/api/ensino/disciplinas/{semestre}/")
        data = response.json()
        return data if isinstance(data, list) else data.get("results", [])

    async def get_meus_diarios(self, token: str, ano_letivo: int, periodo_letivo: int) -> list[dict]:
        all_results = []
        page = 1
        while True:
            response = await self._get(
                token, f"/api/ensino/meus-diarios/{ano_letivo}/{periodo_letivo}/",
                params={"page": page},
            )
            data = response.json()
            results = data.get("results", [])
            all_results.extend(results)
            if data.get("next"):
                page += 1
            else:
                break
        return all_results

    async def get_alunos_diario(self, token: str, id_diario: int) -> list[dict]:
        all_results = []
        page = 1
        while True:
            response = await self._get(
                token, f"/api/ensino/diarios/{id_diario}/alunos/",
                params={"page": page},
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
                logger.info(f"[SUAP] aluno-matriculado 404 para matricula={matricula}")
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
                logger.info(f"[SUAP] aluno-resumido 404 para matricula={matricula}")
                return []
            raise

    async def validar_token(self, token: str) -> bool:
        try:
            await self.get_meus_dados(token)
            return True
        except httpx.HTTPStatusError:
            return False
