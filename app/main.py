from fastapi import FastAPI
from app.api.endpoints import image_generator, user
from app.core.config import settings
from app.core.database import engine, Base
from contextlib import asynccontextmanager

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

app.include_router(image_generator.router, prefix="/image-gen/api/1")
app.include_router(user.router, prefix="/auth/api/1")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await engine.dispose()

@app.get("/")
async def root():
    return {"status": "ok!"}