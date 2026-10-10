from fastapi import FastAPI
from app.routers.parsing import router  # <-- АБСОЛЮТНЫЙ импорт

app = FastAPI(title='Hackathon API')

app.include_router(router)

@app.get('/')
async def root() -> dict:
    return {'message': 'hi there!'}