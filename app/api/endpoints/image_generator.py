from typing import List, Dict
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.image import ImageGenerationRequest, GeneratedImage
from app.services.stability_ai import generate_images
from app.core.celery_app import celery_app
from app.core.database import get_session
from app.models.image import GeneratedImage as DBGeneratedImage

router = APIRouter()

@router.post("/generate", response_model=List[GeneratedImage])
async def create_images(
    request: ImageGenerationRequest,
    session: AsyncSession = Depends(get_session)
):
    try:
        task = generate_images.delay(request.prompt, 3)
        return [GeneratedImage(id=task.id, prompt=request.prompt, status="processing", image_url="")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/task-complete")
async def task_complete_webhook(task_data: Dict, session: AsyncSession = Depends(get_session)):
    task_id = task_data["task_id"]
    result = task_data["result"]
    
    async with session.begin():
        for image_data in result:
            db_image = DBGeneratedImage(
                prompt=image_data['prompt'],
                image_url=image_data['image_url']
            )
            session.add(db_image)      
        await session.commit()
    
    return {"status": "success", "message": f"Task {task_id} completed and data saved"}

@router.post("/webhook/task-failed")
async def task_failed_webhook(task_data: Dict):
    task_id = task_data["task_id"]
    error = task_data["error"]
    print(f"Task {task_id} failed: {error}")
    return {"status": "error", "message": f"Task {task_id} failed"}

@router.get("/status/{task_id}", response_model=List[GeneratedImage])
async def get_task_status(task_id: str, session: AsyncSession = Depends(get_session)):
    async with session.begin():
        result = await session.execute(select(DBGeneratedImage).where(DBGeneratedImage.id == task_id))
        db_images = result.scalars().all()
        if db_images:
            return [GeneratedImage(
                id=str(img.id),
                prompt=img.prompt,
                image_url=img.image_url,
                status="completed",
                created_at=img.created_at
            ) for img in db_images]
        else:
            task = celery_app.AsyncResult(task_id)
            if task.state == 'PENDING':
                return [GeneratedImage(id=task_id, prompt="", status="processing", image_url="")]
            else:
                raise HTTPException(status_code=404, detail="Task not found or failed")

@router.get("/images", response_model=List[GeneratedImage])
async def get_all_images(session: AsyncSession = Depends(get_session)):
    async with session.begin():
        result = await session.execute(select(DBGeneratedImage))
        db_images = result.scalars().all()
        return [GeneratedImage(
            id=str(img.id),
            prompt=img.prompt,
            image_url=img.image_url,
            status="completed",
            created_at=img.created_at
        ) for img in db_images]