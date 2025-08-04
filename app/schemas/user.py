# Pydantic schemas for request/response validation
# Following Interface Segregation Principle - specific interfaces for specific needs

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schemas with common fields"""
    email: EmailStr = Field(..., description="User's email address")
    role: UserRole = Field(..., description="User role (admin or shareholder)")


class UserCreate(UserBase):
    """Schema for creating new users"""
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserResponse(UserBase):
    """Schema for user responses (excludes sensitive data)"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        # Enable ORM mode for SQLAlchemy integration
        from_attributes = True


class Token(BaseModel):
    """JWT token response schemas"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None
    role: Optional[UserRole] = None