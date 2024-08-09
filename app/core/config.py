from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Stability AI Image Generator"
    PROJECT_VERSION: str = "1.0.0"
    STABILITY_API_KEY: str
    STABILITY_API_HOST: str = "https://api.stability.ai"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    FASTAPI_HOST: str = "127.0.0.1"  
    FASTAPI_PORT: int = 8000
    
    @property
    def FASTAPI_BASE_URL(self):
        return f"http://{self.FASTAPI_HOST}:{self.FASTAPI_PORT}"

    class Config:
        env_file = ".env"

DATABASE_URL = "postgresql+asyncpg://postgres:mysecretpassword@localhost:5432/postgres"


settings = Settings()