from pydantic import BaseModel
from datetime import datetime

class SystemDesignQuestionBase(BaseModel):
    title: str
    description: str
    domain: str | None = None
    role: str | None = None

class SystemDesignQuestionCreate(SystemDesignQuestionBase):
    pass

class SystemDesignQuestionOut(SystemDesignQuestionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SystemDesignSubmitRequest(BaseModel):
    answer_text: str
    
class SystemDesignSubmitResponse(BaseModel):
    score: int
    feedback: str
    strengths: list[str]
    improvements: list[str]
