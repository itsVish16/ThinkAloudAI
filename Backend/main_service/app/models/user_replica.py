from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class UserProfileReplica(Base):
    __tablename__ = "user_profile_replica"

    id = Column(String, primary_key=True, index=True) # Usually matches the central User Service ID
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
