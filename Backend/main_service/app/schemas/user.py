from pydantic import BaseModel
from typing import List
import datetime

class SubmissionSummary(BaseModel):
    id: int
    question_id: int
    question_title: str
    language: str
    status: str
    created_at: datetime.datetime

class HeatmapData(BaseModel):
    date: str
    count: int

class UserProfileResponse(BaseModel):
    session_id: str
    total_submissions: int
    total_solved: int
    accuracy_percentage: float
    current_streak: int = 0
    max_streak: int = 0
    heatmap: List[HeatmapData]
    recent_submissions: List[SubmissionSummary]
