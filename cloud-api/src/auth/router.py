"""Authentication API endpoints"""

from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from datetime import datetime
import logging

from .models import UserRegister, UserLogin, TokenResponse, UserResponse
from .jwt import create_access_token
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new doctor

    - **email**: Unique email address
    - **password**: Minimum 8 characters
    - **name**: Doctor's full name
    - **phone**: Optional phone number
    - **license_number**: Optional medical license number
    """
    db = get_db()

    # Check if user already exists
    async with await db.get_connection() as conn:
        cursor = await conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (user_data.email,)
        )
        existing_user = await cursor.fetchone()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password
        password_hash = hash_password(user_data.password)

        # Insert user
        cursor = await conn.execute(
            """
            INSERT INTO users (email, password_hash, name, phone, license_number)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_data.email,
                password_hash,
                user_data.name,
                user_data.phone,
                user_data.license_number
            )
        )
        await conn.commit()

        user_id = cursor.lastrowid

        # Fetch created user
        cursor = await conn.execute(
            """
            SELECT id, email, name, phone, license_number, created_at, last_login
            FROM users WHERE id = ?
            """,
            (user_id,)
        )
        user_row = await cursor.fetchone()

    # Create JWT token
    token, expires_in = create_access_token(user_id, user_data.email)

    # Build response
    user_response = UserResponse(
        id=user_row["id"],
        email=user_row["email"],
        name=user_row["name"],
        phone=user_row["phone"],
        license_number=user_row["license_number"],
        created_at=user_row["created_at"],
        last_login=user_row["last_login"]
    )

    logger.info(f"New user registered: {user_data.email}")

    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=user_response
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Authenticate doctor and return JWT token

    - **email**: Registered email address
    - **password**: Account password
    """
    db = get_db()

    async with await db.get_connection() as conn:
        # Fetch user
        cursor = await conn.execute(
            """
            SELECT id, email, password_hash, name, phone, license_number,
                   created_at, last_login, is_active
            FROM users WHERE email = ?
            """,
            (credentials.email,)
        )
        user_row = await cursor.fetchone()

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check if account is active
        if not user_row["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )

        # Verify password
        if not verify_password(credentials.password, user_row["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Update last login
        await conn.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user_row["id"],)
        )
        await conn.commit()

    # Create JWT token
    token, expires_in = create_access_token(user_row["id"], user_row["email"])

    # Build response
    user_response = UserResponse(
        id=user_row["id"],
        email=user_row["email"],
        name=user_row["name"],
        phone=user_row["phone"],
        license_number=user_row["license_number"],
        created_at=user_row["created_at"],
        last_login=datetime.utcnow()  # Use current time since we just updated it
    )

    logger.info(f"User logged in: {credentials.email}")

    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=user_response
    )
