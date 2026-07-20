from datetime import UTC, datetime
from sqlalchemy import Column, String, Text, DateTime, Integer
from app.database import Base

class PMQuestion(Base):
    __tablename__ = "pm_questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, index=True, nullable=True) # e.g., 'Product Sense', 'Execution', 'Strategy'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
