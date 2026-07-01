from datetime import UTC, datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True) # e.g. Session UUID or client-provided ID
    user_id = Column(String, index=True, nullable=True) # To separate histories by user
    title = Column(String, nullable=True) # Dynamically generated chat title
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationship to store individual messages inside this session
    # cascade="all, delete-orphan" ensures messages are deleted when the session is deleted
    messages = relationship("ChatMessageModel", back_populates="session", cascade="all, delete-orphan")

class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False) # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    session = relationship("ChatSession", back_populates="messages")
