from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    frontend_origin: str
    environment: str = "local"
    # Fuso usado para decidir o que e "hoje" nos alertas de vencimento: o
    # servidor (Render/Docker) roda em UTC, que ja virou o dia seguinte
    # entre 21h e 24h no horario de Brasilia.
    timezone: str = "America/Sao_Paulo"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
