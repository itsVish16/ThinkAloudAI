from datetime import datetime, date
from pydantic import BaseModel, ConfigDict
from typing import Any


class SkillResponse(BaseModel):
    domain: str
    score: int
    problems_solved: int = 0
    interviews_done: int = 0

    model_config = ConfigDict(from_attributes=True)


class UserStatsResponse(BaseModel):
    problems_solved_total: int = 0
    problems_solved_easy: int = 0
    problems_solved_medium: int = 0
    problems_solved_hard: int = 0
    total_submissions: int = 0
    acceptance_rate: float = 0.0

    interviews_completed: int = 0
    avg_interview_score: float = 0.0
    best_interview_score: int = 0

    current_streak: int = 0
    longest_streak: int = 0
    last_activity_date: date | None = None
    rating: int = 0

    model_config = ConfigDict(from_attributes=True)


class DailyActivityResponse(BaseModel):
    activity_date: date
    problems_solved: int = 0
    problems_attempted: int = 0
    submissions_count: int = 0
    interviews_done: int = 0
    study_minutes: int = 0

    model_config = ConfigDict(from_attributes=True)


class AchievementResponse(BaseModel):
    title: str
    description: str
    icon_url: str | None = None
    earned_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LearningEventResponse(BaseModel):
    event_type: str
    reference_id: str | None = None
    score_change: int = 0
    domain: str | None = None
    metadata_json: dict | list | str | Any = {}
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FullUserProfileResponse(BaseModel):
    username: str
    email: str
    full_name: str
    is_verified: bool
    created_at: datetime

    bio: str | None = None
    avatar_url: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    headline: str | None = None
    location: str | None = None
    institution: str | None = None
    preferred_language: str | None = None
    resume_url: str | None = None

    model_config = ConfigDict(from_attributes=True)

class PublicUserProfileResponse(BaseModel):
    username: str
    full_name: str
    is_verified: bool
    created_at: datetime

    bio: str | None = None
    avatar_url: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    headline: str | None = None
    location: str | None = None
    institution: str | None = None
    preferred_language: str | None = None
    resume_url: str | None = None

    model_config = ConfigDict(from_attributes=True)

class UpdateProfileDetailsRequest(BaseModel):
    bio: str | None = None
    avatar_url: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    headline: str | None = None
    location: str | None = None
    institution: str | None = None
    preferred_language: str | None = None
    resume_url: str | None = None

class UserPreferenceResponse(BaseModel):
    theme: str
    email_notifications: bool
    push_notifications: bool
    
    model_config = ConfigDict(from_attributes=True)

class UpdateUserPreferenceRequest(BaseModel):
    theme: str | None = None
    email_notifications: bool | None = None
    push_notifications: bool | None = None
