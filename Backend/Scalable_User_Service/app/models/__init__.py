from app.models.learning import Achievement, LearningEvent, UserAchievement, UserSkillScore, UserStats, DailyActivity  # noqa: F401
from app.models.profile import UserPreference, UserProfile  # noqa: F401
from app.models.user import User  # noqa: F401

# This file explicitly imports all models so that Alembic's env.py can discover them.
