from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class RoadmapItemBase(BaseModel):
    title: str = Field(..., description="Title of the learning item")
    content_type: str = Field(default="custom", description="Type of content: dsa, system_design, or custom")
    content_id: Optional[str] = Field(None, description="ID of the related question if not custom")
    timeline_days: Optional[int] = Field(None, description="Estimated days to complete")
    is_completed: bool = Field(default=False)

class RoadmapItemCreate(RoadmapItemBase):
    pass

class RoadmapItemOut(RoadmapItemBase):
    id: int
    topic_id: int

    class Config:
        from_attributes = True

class RoadmapTopicBase(BaseModel):
    title: str = Field(..., description="Title of the topic/module")
    order_index: int = Field(default=0, description="Order index of the topic")

class RoadmapTopicCreate(RoadmapTopicBase):
    items: List[RoadmapItemCreate] = Field(default_factory=list)

class RoadmapTopicOut(RoadmapTopicBase):
    id: int
    roadmap_id: int
    items: List[RoadmapItemOut] = Field(default_factory=list)

    class Config:
        from_attributes = True

class RoadmapBase(BaseModel):
    title: str = Field(..., description="Title of the roadmap")
    description: Optional[str] = Field(None, description="Optional description of the roadmap")

class RoadmapCreate(RoadmapBase):
    topics: List[RoadmapTopicCreate] = Field(default_factory=list)

class RoadmapOut(RoadmapBase):
    id: int
    user_id: str
    created_at: datetime
    topics: List[RoadmapTopicOut] = Field(default_factory=list)

    class Config:
        from_attributes = True
