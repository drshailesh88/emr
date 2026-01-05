"""JWT token utilities"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic_settings import BaseSettings
from pydantic import Field
import os
from dotenv import load_dotenv

from .models import TokenData

load_dotenv()


class JWTSettings(BaseSettings):
    """JWT configuration"""
    JWT_SECRET_KEY: str = Field(default="")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 7

    class Config:
        env_file = ".env"


settings = JWTSettings()

# Validate secret key
if not settings.JWT_SECRET_KEY or settings.JWT_SECRET_KEY == "your-secret-key-here-generate-with-openssl-rand-hex-32":
    raise ValueError(
        "JWT_SECRET_KEY not configured. Generate one with: openssl rand -hex 32"
    )

security = HTTPBearer()


def create_access_token(user_id: int, email: str) -> tuple[str, int]:
    """
    Create JWT access token

    Returns:
        tuple: (token, expires_in_seconds)
    """
    expires_delta = timedelta(days=settings.JWT_EXPIRATION_DAYS)
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "user_id": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    expires_in_seconds = int(expires_delta.total_seconds())
    return encoded_jwt, expires_in_seconds


def decode_access_token(token: str) -> TokenData:
    """
    Decode and validate JWT token

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id: int = payload.get("user_id")
        email: str = payload.get("email")

        if user_id is None or email is None:
            raise credentials_exception

        return TokenData(user_id=user_id, email=email)

    except JWTError:
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    FastAPI dependency to get current authenticated user

    Usage:
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user_id": user.user_id}
    """
    token = credentials.credentials
    return decode_access_token(token)
