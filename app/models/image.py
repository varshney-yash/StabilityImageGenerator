from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, nullable=False)
    prompt = Column(String)
    image_url = Column(String)
    status = Column(String, nullable=False)
    created_at = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.id"))