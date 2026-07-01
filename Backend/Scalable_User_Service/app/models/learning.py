from datetime import UTC, datetime, date

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.db.database import Base


class UserStats(Base):
    """Denormalized user stats for dashboard."""

    __tablename__ = "user_stats"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    # Problem stats
    problems_solved_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    problems_solved_easy: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    problems_solved_medium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    problems_solved_hard: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_submissions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    acceptance_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Interview stats
    interviews_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_interview_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    best_interview_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Streaks
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Global
    rating: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )


class DailyActivity(Base):
    """One row per user per day. Heatmap engine."""

    __tablename__ = "daily_activity"
    __table_args__ = (
        UniqueConstraint("user_id", "activity_date", name="uix_daily_activity_user_date"),
        Index("idx_daily_activity_user_date", "user_id", "activity_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)

    problems_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    problems_attempted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    submissions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interviews_done: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    study_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class UserSkillScore(Base):
    """Tracks proficiency in different domains (e.g., Python, System Design)"""

    __tablename__ = "user_skill_scores"
    __table_args__ = (
        UniqueConstraint("user_id", "domain", name="uix_user_skill_scores_user_id_domain"),
        Index("idx_skill_scores_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    domain: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "python", "frontend"
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    problems_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interviews_done: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )


class Achievement(Base):
    """Global achievements that can be earned."""

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class UserAchievement(Base):
    """Mapping table for which users have earned which achievements."""

    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)

    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class LearningEvent(Base):
    """An append-only log of user learning events (e.g., ProblemSolved, InterviewCompleted)"""

    __tablename__ = "learning_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "ProblemSolved"
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g. "42" or "interview_1234"
    score_change: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    domain: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
