from datetime import datetime, UTC, date
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, Text, JSON
from app.database import Base

class UserStats(Base):
    """Denormalized user stats for dashboard."""
    __tablename__ = "user_stats"

    # In main_service, user_id is a String (extracted from JWT 'sub')
    user_id = Column(String, primary_key=True, index=True)

    # Problem stats
    problems_solved_total = Column(Integer, default=0, nullable=False)
    problems_solved_easy = Column(Integer, default=0, nullable=False)
    problems_solved_medium = Column(Integer, default=0, nullable=False)
    problems_solved_hard = Column(Integer, default=0, nullable=False)
    total_submissions = Column(Integer, default=0, nullable=False)
    acceptance_rate = Column(Float, default=0.0, nullable=False)

    # Interview stats
    interviews_completed = Column(Integer, default=0, nullable=False)
    avg_interview_score = Column(Float, default=0.0, nullable=False)
    best_interview_score = Column(Integer, default=0, nullable=False)

    # Streaks
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    last_activity_date = Column(Date, nullable=True)

    # Global
    rating = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class DailyActivity(Base):
    """Tracks daily activity for the contribution heatmap."""
    __tablename__ = "daily_activity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    activity_date = Column(Date, default=lambda: datetime.now(UTC).date(), nullable=False)
    
    problems_solved = Column(Integer, default=0, nullable=False)
    problems_attempted = Column(Integer, default=0, nullable=False)
    submissions_count = Column(Integer, default=0, nullable=False)
    interviews_done = Column(Integer, default=0, nullable=False)
    study_minutes = Column(Integer, default=0, nullable=False)


class UserSkillScore(Base):
    """Tracks proficiency in different domains (e.g., Arrays, System Design, Communication)."""
    __tablename__ = "user_skill_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    domain = Column(String, index=True, nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    problems_solved = Column(Integer, default=0, nullable=False)
    interviews_done = Column(Integer, default=0, nullable=False)
    
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class LearningEvent(Base):
    """Audit log of significant learning events for the timeline feed."""
    __tablename__ = "learning_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    
    # Event types: "PROBLEM_SOLVED", "INTERVIEW_COMPLETED", "ACHIEVEMENT_UNLOCKED", "COURSE_COMPLETED"
    event_type = Column(String, index=True, nullable=False)
    
    # E.g., ID of the problem or interview
    reference_id = Column(String, nullable=True) 
    
    score_change = Column(Float, default=0.0, nullable=False)
    domain = Column(String, nullable=True)
    
    metadata_json = Column(JSON, default=dict, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
