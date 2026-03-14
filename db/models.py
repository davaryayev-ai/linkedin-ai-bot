from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class AnalyzedPost(Base):
    __tablename__ = "analyzed_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True) # Telegram User ID
    post_text = Column(Text, nullable=False)
    views = Column(Integer, nullable=True)
    likes = Column(Integer, nullable=True)
    comments = Column(Integer, nullable=True)
    analysis_result = Column(JSON, nullable=True) # OpenAI JSON analysis
    created_at = Column(DateTime, default=datetime.utcnow)

class UserMemory(Base):
    __tablename__ = "user_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, unique=True)
    successful_hooks = Column(JSON, nullable=True) # Array of strings
    successful_structures = Column(JSON, nullable=True) # Array of strings
    tone_of_voice = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
