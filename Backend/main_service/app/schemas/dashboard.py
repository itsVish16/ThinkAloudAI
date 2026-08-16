from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class HeatmapDataPoint(BaseModel):
    date: str
    count: int


class SkillScore(BaseModel):
    domain: str
    score: float = 1000.0
    problems_solved: Optional[int] = 0
    interviews_done: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)


class RecentActivityItem(BaseModel):
    id: int
    event_type: str
    reference_id: Optional[str] = None
    score_change: float = 0.0
    domain: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    problems_solved_total: int = 0
    problems_solved_easy: Optional[int] = 0
    problems_solved_medium: Optional[int] = 0
    problems_solved_hard: Optional[int] = 0
    acceptance_rate: Optional[float] = 0.0
    interviews_completed: int = 0
    avg_interview_score: Optional[float] = 0.0
    best_interview_score: Optional[int] = 0
    current_streak: Optional[int] = 0
    longest_streak: Optional[int] = 0
    rating: Optional[int] = 1200
    model_config = ConfigDict(from_attributes=True)


class DashboardOverviewResponse(BaseModel):
    user_id: str
    stats: Optional[DashboardStats] = None
    heatmap: List[HeatmapDataPoint] = []
    skills: List[SkillScore] = []
    recent_activity: List[RecentActivityItem] = []
