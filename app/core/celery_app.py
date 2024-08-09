from celery import Celery
from app.core.config import settings
from app.services import stability_ai

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.task_routes = {
    "app.services.stability_ai.generate_images": "main-queue"
}