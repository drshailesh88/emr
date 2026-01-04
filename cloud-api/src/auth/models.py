"""Authentication data models"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=15)
    license_number: Optional[str] = Field(None, max_length=50)


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response (no sensitive data)"""
    id: int
    email: str
    name: str
    phone: Optional[str]
    license_number: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class TokenData(BaseModel):
    """JWT token payload data"""
    user_id: int
    email: str
