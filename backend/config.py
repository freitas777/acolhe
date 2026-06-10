from pydantic_settings import BaseSettings
from pydantic import ValidationError
class Settings(BaseSettings):
    database_url: str
    suap_client_id: str
    suap_client_secret: str
    suap_redirect_uri: str
    suap_base_url: str = "https://suap.ifrn.edu.br"
    suap_scope: str = "identificacao email documentos_pessoais"
    secret_key: str

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    debug: bool = False
    dev_mode: bool = False
    allowed_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings() #type:ignore
