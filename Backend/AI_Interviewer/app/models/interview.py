from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid

from .base import Base

def generate_uuid():
    return str(uuid.uuid4())

class UserProfileReplica(Base):
    __tablename__ = 'user_profile_replica'
    
    id = Column(String, primary_key=True)
    username = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    sessions = relationship("InterviewSession", back_populates="user")

class InterviewSession(Base):
    __tablename__ = 'interview_sessions'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('user_profile_replica.id'), nullable=False)
    candidate_name = Column(String, nullable=False)
    interview_type = Column(String, nullable=False, default="Behavioral") # "DSA", "System Design", "Behavioral"
    difficulty = Column(String, nullable=True) # "Easy", "Medium", "Hard"
    stage = Column(String, nullable=False)
    state_data = Column(JSON, nullable=False, default=dict)
    
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))
    
    user = relationship("UserProfileReplica", back_populates="sessions")
    questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan")
    feedback = relationship("InterviewFeedback", back_populates="session", uselist=False, cascade="all, delete-orphan")

class InterviewQuestion(Base):
    __tablename__ = 'interview_questions'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey('interview_sessions.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    
    session = relationship("InterviewSession", back_populates="questions")
    responses = relationship("InterviewResponse", back_populates="question", cascade="all, delete-orphan")

class InterviewResponse(Base):
    __tablename__ = 'interview_responses'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    question_id = Column(String, ForeignKey('interview_questions.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    
    question = relationship("InterviewQuestion", back_populates="responses")

class InterviewFeedback(Base):
    __tablename__ = 'interview_feedback'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey('interview_sessions.id'), nullable=False, unique=True)
    
    technical_score = Column(Integer, nullable=True)
    communication_score = Column(Integer, nullable=True)
    english_score = Column(Integer, nullable=True)
    
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    improvement_plan = Column(Text, nullable=True)
    recommended_topics = Column(JSON, nullable=True)
    detailed_metrics = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    
    session = relationship("InterviewSession", back_populates="feedback")
