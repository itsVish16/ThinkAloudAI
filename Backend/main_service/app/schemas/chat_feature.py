from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import datetime

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatFeatureRequest(BaseModel):
    messages: List[ChatMessage]

class ChatStreamRequest(BaseModel):
    session_id: str
    message: str
    images: Optional[List[str]] = None

class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    role: str
    content: str
    created_at: datetime.datetime

class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: Optional[str] = None
    created_at: datetime.datetime