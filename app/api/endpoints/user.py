from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.image import GeneratedImage
from app.core.database import get_session
from app.core.auth import *
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import User


router = APIRouter()

from pydantic import BaseModel
class UserCreate(BaseModel):
    username: str
    password: str

@router.post("/register")
async def register(user: UserCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.username == user.username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = pwd_context.hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/user/prompts")
async def get_user_prompts(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    print(current_user, current_user.id)
    result = await session.execute(select(GeneratedImage).where(GeneratedImage.user_id == current_user.id))
    user_images = result.scalars().all()
    
    return [
        {
            "prompt": img.prompt,
            "image_url": img.image_url,
            "status": img.status,
            "created_at": img.created_at
        } for img in user_images
    ]