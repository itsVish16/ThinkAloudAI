from datetime import UTC, datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean, Float, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class DSAQuestion(Base):
    __tablename__ = "dsa_questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String, nullable=False)
    function_name = Column(String, nullable=False, default="solution")
    python_starter_code = Column(Text, nullable=True)
    cpp_starter_code = Column(Text, nullable=True)
    cpp_test_harness = Column(Text, nullable=True)
    test_cases = Column(Text, nullable=False)
    
    # New fields for AI platform
    hints = Column(Text, nullable=True) # JSON encoded hints array
    optimal_time_complexity = Column(String, nullable=True)
    optimal_space_complexity = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    submissions = relationship("CodeSubmission", back_populates="question")


class CodeSubmission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        Index("ix_submissions_session_question", "session_id", "question_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    question_id = Column(Integer, ForeignKey("dsa_questions.id"))
    code = Column(String)
    language = Column(String)
    status = Column(String)
    error_message = Column(String, nullable=True)
    is_submission = Column(Boolean, default=True)
    
    # New metrics
    execution_time_ms = Column(Float, nullable=True)
    memory_used_kb = Column(Float, nullable=True)
    passed_tests = Column(Integer, nullable=True)
    total_tests = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    question = relationship("DSAQuestion", back_populates="submissions")


class ProblemTag(Base):
    __tablename__ = "problem_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("dsa_questions.id"))
    tag_name = Column(String, index=True)
    
    question = relationship("DSAQuestion", backref="tags")


class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    question_id = Column(Integer, ForeignKey("dsa_questions.id"))
    reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    question = relationship("DSAQuestion")


class UserProblemStatus(Base):
    __tablename__ = "user_problem_status"
    __table_args__ = (
        Index("ix_user_problem_status_user_question", "user_id", "question_id"),
    )
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False) # Maps to session_id
    question_id = Column(Integer, ForeignKey("dsa_questions.id"), nullable=False)
    
    status = Column(String, nullable=False) # e.g. "Attempted", "Solved"
    last_attempted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    best_runtime_ms = Column(Float, nullable=True)
    best_memory_kb = Column(Float, nullable=True)
    
    question = relationship("DSAQuestion")
