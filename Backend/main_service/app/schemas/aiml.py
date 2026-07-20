from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AIMLQuestionBase(BaseModel):
    title: str
    description: str
    domain: Optional[str] = None
    role: Optional[str] = None

class AIMLQuestionCreate(AIMLQuestionBase):
    pass

class AIMLQuestionOut(AIMLQuestionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
