from datetime import UTC, datetime
from sqlalchemy import Column, String, Text, DateTime, Integer
from app.database import Base

class SystemDesignQuestion(Base):
    __tablename__ = "system_design_questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    domain = Column(String, index=True, nullable=True)
    role = Column(String, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class SystemDesignSubmission(Base):
    __tablename__ = "system_design_submissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question_id = Column(Integer, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=True)
    answer_text = Column(Text, nullable=False)
    score = Column(Integer, nullable=False, default=0)
    feedback = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    improvements = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
