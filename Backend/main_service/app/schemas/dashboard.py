from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date, datetime

class HeatmapDataPoint(BaseModel):
    date: str
    count: int

class SkillScore(BaseModel):
    domain: str
    score: float
    problems_solved: int
    interviews_done: int
    model_config = ConfigDict(from_attributes=True)

class RecentActivityItem(BaseModel):
    id: int
    event_type: str
    reference_id: Optional[str] = None
    score_change: float
    domain: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DashboardStats(BaseModel):
    problems_solved_total: int
    problems_solved_easy: int
    problems_solved_medium: int
    problems_solved_hard: int
    acceptance_rate: float
    interviews_completed: int
    avg_interview_score: float
    best_interview_score: int
    current_streak: int
    longest_streak: int
    rating: int
    model_config = ConfigDict(from_attributes=True)

class DashboardOverviewResponse(BaseModel):
    user_id: str
    stats: Optional[DashboardStats] = None
    heatmap: List[HeatmapDataPoint] = []
    skills: List[SkillScore] = []
    recent_activity: List[RecentActivityItem] = []
