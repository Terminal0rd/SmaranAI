"""
User schemas for API validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)


class UserCreate(UserBase):
    """User registration schema"""
    password: str = Field(..., min_length=6, max_length=100)
    age: Optional[int] = Field(None, ge=5, le=100)
    class_standard: Optional[str] = Field(None, max_length=50)
    branch_specialization: Optional[str] = Field(None, max_length=100)
    learning_goal: Optional[str] = Field(None, max_length=50)


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User profile update schema"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    age: Optional[int] = Field(None, ge=5, le=100)
    class_standard: Optional[str] = Field(None, max_length=50)
    branch_specialization: Optional[str] = Field(None, max_length=100)
    learning_goal: Optional[str] = Field(None, max_length=50)


class UserResponse(UserBase):
    """User response schema"""
    id: str
    age: Optional[int] = None
    class_standard: Optional[str] = None
    branch_specialization: Optional[str] = None
    learning_goal: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT token payload"""
    user_id: Optional[str] = None
