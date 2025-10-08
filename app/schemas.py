from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Any
from datetime import datetime

# -----------------------------
# User Schemas
# -----------------------------
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str
    language: Optional[str] = "en"

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

## NEW: A more appropriate schema for updating profiles (doesn't include password)
class UserUpdate(BaseModel):
    username: str
    email: EmailStr
    language: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    language: str
    is_admin: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# -----------------------------
# Forgot Password Schemas
# -----------------------------
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

## UPDATED: This now requires a token instead of an email for security
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_new_password: str

    @validator("confirm_new_password")
    def passwords_match(cls, v, values):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v

# -----------------------------
# (All other schemas for Chat, KB, Feedback are unchanged)
# -----------------------------
class Entity(BaseModel):
    label: str; text: str
class ChatRequest(BaseModel):
    message: str; language: str = "en"
class ChatResponse(BaseModel):
    response: str; intent: str; entities: List[Any]
class KBCreate(BaseModel):
    intent: str; entity_value: Optional[str] = None; response_text: str
class KBResponse(BaseModel):
    id: int; intent: str; entity_value: Optional[str]; response_text: str
    class Config: from_attributes = True
class FeedbackRequest(BaseModel):
    intent: str; entities: Optional[List[Any]] = None; user_message: str; bot_response: str; feedback: int; comment: Optional[str] = None
class FeedbackResponse(BaseModel):
    id: int; user_id: int; intent: Optional[str]; user_message: str; bot_response: str; feedback: int; comment: Optional[str]; created_at: datetime
    class Config: from_attributes = True
class UnansweredQuestionResponse(BaseModel):
    id: int; user_id: int; question_text: str; timestamp: datetime
    class Config: from_attributes = True