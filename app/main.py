import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import batches, positions
from app.services.batch_service import resume_unfinished_batches
from app.services.ktru_index import load_index

logger = logging.getLogger(__name__)


async def _warm_up() -> None:
    """Индекс КТРУ строится при старте, чтобы первый запрос не ждал его."""
    try:
        index = await load_index()
        logger.info('KTRU index ready: %s', index.stats)
        await resume_unfinished_batches()
    except Exception:  # БД ещё не готова или справочник не загружен
        logger.exception('Warm-up failed; the index will be loaded on first request')


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_warm_up())
    yield
    task.cancel()


app = FastAPI(title='Hackathon API', lifespan=lifespan)

# Добавляем настройку CORS (адреса фронтенда можно переопределить через CORS_ORIGINS)
allowed_origins = [
    origin.strip()
    for origin in os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Разрешаем запросы с Next.js фронтенда
    allow_credentials=True,
    allow_methods=['*'],  # Разрешаем все методы (GET, POST и т.д.)
    allow_headers=['*'],  # Разрешаем любые заголовки
)


@app.get('/', tags=['Root'])
async def root():
    return {'message': 'API is running'}

app.include_router(positions.router)
app.include_router(batches.router)
