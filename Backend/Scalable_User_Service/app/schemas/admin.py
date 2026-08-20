from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.profile import ProfileResponse, PreferenceResponse, AchievementResponse


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


class UserAdminDetailResponse(BaseModel):
    user: UserAdminSummary
    profile: Optional[ProfileResponse] = None
    preferences: Optional[PreferenceResponse] = None
    achievements: List[AchievementResponse] = []


class UserAdminStatusUpdateRequest(BaseModel):
    is_verified: Optional[bool] = None
    full_name: Optional[str] = None


class AchievementCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=5, max_length=500)
    icon_url: str = Field(..., min_length=5, max_length=500)
