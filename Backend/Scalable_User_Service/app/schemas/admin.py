from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.profile import UserPreferenceResponse, AchievementResponse


class UserAdminSummary(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserAdminListResponse(BaseModel):
    items: List[UserAdminSummary]
    total: int
    page: int
    limit: int
    pages: int


class ProfileDetailResponse(BaseModel):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    institution: Optional[str] = None
    preferred_language: Optional[str] = None
    resume_url: Optional[str] = None

    model_config = {"from_attributes": True}


class UserAdminDetailResponse(BaseModel):
    user: UserAdminSummary
    profile: Optional[ProfileDetailResponse] = None
    preferences: Optional[UserPreferenceResponse] = None
    achievements: List[AchievementResponse] = []


class UserAdminStatusUpdateRequest(BaseModel):
    is_verified: Optional[bool] = None
    full_name: Optional[str] = None


class AchievementCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=5, max_length=500)
    icon_url: str = Field(..., min_length=5, max_length=500)
