from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://user:1234@localhost:5432/acolhe"
    gemini_api_key: str = ""
    suap_client_id: str = ""
    suap_client_secret: str = ""
    suap_redirect_uri: str = "http://localhost:8000/auth/suap/callback"
    secret_key: str = "change-me-in-production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
