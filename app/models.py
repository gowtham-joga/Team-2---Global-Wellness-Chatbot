from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    language = Column(String, default="en")
    is_admin = Column(Boolean, default=False)   # NEW: admin flag
    chat_history = relationship("ChatHistory", back_populates="owner")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    intent = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("User", back_populates="chat_history")

class UnansweredQuestion(Base):
    __tablename__ = "unanswered_questions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_text = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    id = Column(Integer, primary_key=True, index=True)
    intent = Column(String, nullable=False)
    entity_value = Column(String, nullable=True)
    response_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    intent = Column(String, nullable=True)
    entities = Column(Text, nullable=True)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    feedback = Column(Integer, nullable=False)  # 1 = thumbs up, 0 = thumbs down
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
