from typing import List, Dict
from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.image import GeneratedImage
from app.services.stability_ai import generate_images
from app.core.celery_app import celery_app
from app.core.database import get_session
from app.models.image import GeneratedImage as DBGeneratedImage
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/generate")
async def create_images(
    prompt: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    try:
        task = generate_images.delay(prompt, 3, current_user.id)
        return {"task_id": task.id, "prompt": prompt, "status": "processing", "user_id": current_user.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/task-complete")
async def task_complete_webhook(task_data: Dict, session: AsyncSession = Depends(get_session)):
    task_id = task_data["task_id"]
    result = task_data["result"]
    async with session.begin():
        for image_data in result:
            db_image = DBGeneratedImage(
                task_id=task_id,
                prompt=image_data['prompt'],
                image_url=image_data['image_url'],
                user_id=image_data['user_id'],
                status="completed"
            )
            session.add(db_image)      
        await session.commit()
    
    return {"status": "success", "message": f"Task {task_id} completed and data saved"}


@router.post("/webhook/task-failed")
async def task_failed_webhook(task_data: Dict):
    task_id = task_data["task_id"]
    error = task_data["error"]
    return {"status": "error", "message": f"Task {task_id} failed"}

@router.get("/status/{task_id}/")
async def get_task_status(task_id: str, session: AsyncSession = Depends(get_session)):
    async with session.begin():
        result = await session.execute(select(DBGeneratedImage).where(DBGeneratedImage.task_id == task_id))
        db_images = result.scalars().all()
        if db_images:
            return [
                {
                    "id": img.id,  
                    "task_id": str(img.task_id),
                    "prompt": img.prompt,
                    "image_url": img.image_url,
                    "status": "completed",
                    "created_at": img.created_at
                } for img in db_images
            ]
        else:
            task = celery_app.AsyncResult(task_id)
            if task.state == 'PENDING':
                return [{"task_id":task_id,"status":"processing"}]
            else:
                raise HTTPException(status_code=404, detail="Task not found or failed")

@router.get("/images", response_model=List[GeneratedImage])
async def get_all_images(session: AsyncSession = Depends(get_session)):
    async with session.begin():
        result = await session.execute(select(DBGeneratedImage))
        db_images = result.scalars().all()
        return [GeneratedImage(
            task_id=str(img.task_id),
            prompt=img.prompt,
            image_url=img.image_url,
            status="completed",
            created_at=img.created_at
        ) for img in db_images]