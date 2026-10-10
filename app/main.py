from fastapi import FastAPI
from app.routers import parsing

app = FastAPI(
    title="Hackathon API",
    version="0.1.0"
)

app.include_router(parsing.router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "API is running"}