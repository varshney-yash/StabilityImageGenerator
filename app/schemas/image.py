from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ImageGenerationRequest(BaseModel):
    prompt: str

class GeneratedImage(BaseModel):
    id: str
    prompt: Optional[str] = None
    image_url: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True