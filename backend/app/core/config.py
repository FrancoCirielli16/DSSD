from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_name: str = "RescueSync"
    bonita_base_url: str = "http://localhost:8080/bonita"
    bonita_username: str = "walter.bates"
    bonita_password: str = "bpm"
    bonita_process_name: str = "Gestion Integral de la Emergencia"
    bonita_process_version: str = "1.0"
    database_url: str = "postgresql+psycopg://rescuesync:rescuesync@localhost:5432/rescuesync"
    session_secret: str = "dev-only-change-me"
    ventana_provisoria_horas: int = 72


@lru_cache
def get_settings() -> Settings:
    return Settings()
