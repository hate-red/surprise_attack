import os

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
        extra='ignore',
    )


settings = PostgresSettings() # type: ignore


def get_db_url() -> str:
    # docker-compose передаёт готовый DATABASE_URL; локально собираем из .env
    url = os.environ.get('DATABASE_URL')
    if url:
        return url
    return (
        f'postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@'
        f'{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}'
    )


def get_asyncpg_dsn() -> str:
    """DSN для прямого подключения asyncpg (массовая загрузка через COPY)."""
    return get_db_url().replace('postgresql+asyncpg://', 'postgresql://', 1)


# Папка с исходными выгрузками (XML КТРУ и xlsx портала поставщиков)
initial_files_dir = project_root / 'initial files'
ktru_xml_dir = initial_files_dir / 'xmls'
