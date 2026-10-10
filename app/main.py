from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import positions


app = FastAPI(title='Hackathon API',)

# Добавляем настройку CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],  # Разрешаем запросы с вашего Next.js фронтенда
    allow_credentials=True,
    allow_methods=['*'],  # Разрешаем все методы (GET, POST и т.д.)
    allow_headers=['*'],  # Разрешаем любые заголовки
)


@app.get('/', tags=['Root'])
async def root():
    return {'message': 'API is running'}

app.include_router(positions.router)
