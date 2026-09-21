from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://rescuesync:rescuesync@localhost:5433/rescuesync"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 480
    bonita_base_url: str = "http://localhost:8080/bonita"
    bonita_username: str = "operador.municipal"
    bonita_password: str = "bpm"
    bonita_process_name: str = "RescueSync"
    bonita_process_version: str = "1.0"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
