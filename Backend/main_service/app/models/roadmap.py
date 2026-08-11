from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import UTC, datetime
from app.database import Base
import enum

class ContentType(str, enum.Enum):
    dsa = "dsa"
    system_design = "system_design"
    mock_interview = "mock_interview"
    custom = "custom"

class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=True) # Nullable for general roadmaps
    is_general = Column(Boolean, default=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    topics = relationship("RoadmapTopic", back_populates="roadmap", cascade="all, delete-orphan")

class RoadmapTopic(Base):
    __tablename__ = "roadmap_topics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    roadmap_id = Column(Integer, ForeignKey("roadmaps.id"), nullable=False)
    title = Column(String, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    
    roadmap = relationship("Roadmap", back_populates="topics")
    items = relationship("RoadmapItem", back_populates="topic", cascade="all, delete-orphan")

class RoadmapItem(Base):
    __tablename__ = "roadmap_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("roadmap_topics.id"), nullable=False)
    title = Column(String, nullable=False)
    content_type = Column(Enum(ContentType), nullable=False, default=ContentType.custom)
    estimated_minutes = Column(Integer, default=30)
    content_id = Column(String, nullable=True) # ID of the DSA or System Design question, if applicable
    timeline_days = Column(Integer, nullable=True) # Estimated duration for flexibility
    is_completed = Column(Boolean, default=False)
    
    topic = relationship("RoadmapTopic", back_populates="items")
