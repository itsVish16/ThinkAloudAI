from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base

class AIMLQuestion(Base):
    __tablename__ = "aiml_questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    domain = Column(String(100), nullable=True) # e.g., 'MLOps', 'Deep Learning', 'Generative AI'
    role = Column(String(100), nullable=True)   # e.g., 'Machine Learning Engineer', 'AI Researcher'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
