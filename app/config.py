from pydantic_settings import BaseSettings, SettingsConfigDict

from pathlib import Path
from datetime import timedelta


project_root = Path(__file__).parent.parent


class PostgresSettings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    model_config = SettingsConfigDict(
        env_file=project_root / '.env',
    )


settings = PostgresSettings() # type: ignore


def get_db_url() -> str:
    return (
        f'postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@'
        f'{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}'
    )
