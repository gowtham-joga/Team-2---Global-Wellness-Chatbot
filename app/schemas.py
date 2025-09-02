from pydantic import BaseModel, EmailStr
from typing import Optional

# ----- Requests -----
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    age: Optional[int] = None
    language: Optional[str] = None

class UpdateProfileRequest(BaseModel):
    age: Optional[int] = None
    language: Optional[str] = None

# ----- Responses -----
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    age: Optional[int] = None
    language: Optional[str] = None

    class Config:
        from_attributes = True  # Pydantic v2 (use orm_mode=True in v1)

class Token(BaseModel):
    access_token: str
    token_type: str
