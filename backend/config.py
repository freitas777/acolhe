from pydantic_settings import BaseSettings
import os
from pydantic import ValidationError
class Settings(BaseSettings):
    database_url: str
    suap_client_id: str
    suap_client_secret: str
    suap_redirect_uri: str
    secret_key: str

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings() #type:ignore
