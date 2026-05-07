import httpx
from backend.config import settings


class SUAPService:
    def __init__(self):
        self.base_url = settings.suap_base_url

    async def get_meus_dados(self, token: str) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.base_url}/api/rh/meus-dados/",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_disciplinas(self, token: str, semestre: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.base_url}/api/ensino/disciplinas/{semestre}/",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else data.get("results", [])

    async def validar_token(self, token: str) -> bool:
        try:
            await self.get_meus_dados(token)
            return True
        except httpx.HTTPStatusError:
            return False
