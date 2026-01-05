"""Authentication and authorization management for DocAssist EMR.

Features:
- Optional PIN/password protection for app access
- Biometric authentication support (placeholder for mobile)
- Auto-lock after inactivity
- Failed attempt limiting (prevent brute force)
- Role-based access control (future: multi-user clinics)

Security principles:
- Passwords are never stored in plaintext
- Uses bcrypt/Argon2 for password hashing
- Rate limiting on failed attempts
- Session timeout enforcement
"""

import os
import secrets
import sqlite3
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Try to import password hashing libraries
_bcrypt_available = False
_argon2_available = False

try:
    import bcrypt
    _bcrypt_available = True
except ImportError:
    pass

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, InvalidHash
    _argon2_available = True
except ImportError:
    pass


class UserRole(Enum):
    """User roles for access control."""
    ADMIN = "admin"  # Full access, can manage users
    DOCTOR = "doctor"  # Can create/edit patient data
    STAFF = "staff"  # Can view, limited edit
    READONLY = "readonly"  # View only


class AuthMethod(Enum):
    """Authentication methods."""
    NONE = "none"  # No authentication (default for single doctor)
    PIN = "pin"  # 4-6 digit PIN
    PASSWORD = "password"  # Full password
    BIOMETRIC = "biometric"  # Fingerprint/Face (mobile only)


@dataclass
class User:
    """User account."""
    id: Optional[int]
    username: str
    full_name: str
    role: UserRole
    auth_method: AuthMethod
    password_hash: Optional[str]
    pin_hash: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    failed_attempts: int
    locked_until: Optional[datetime]


class AuthenticationManager:
    """Manages authentication and authorization."""

    # Security settings
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    SESSION_TIMEOUT_MINUTES = 30
    AUTO_LOCK_MINUTES = 10  # Auto-lock after inactivity

    def __init__(self, db_path: Optional[str] = None):
        """Initialize authentication manager.

        Args:
            db_path: Path to SQLite database
        """
        if db_path is None:
            db_path = os.getenv("DOCASSIST_DB_PATH", "data/clinic.db")
        self.db_path = Path(db_path)
        self._init_auth_tables()

        # Password hasher
        if _argon2_available:
            self.password_hasher = PasswordHasher()
            self.hash_method = "argon2"
        elif _bcrypt_available:
            self.hash_method = "bcrypt"
        else:
            logger.warning(
                "No secure password hashing library available. "
                "Install argon2-cffi or bcrypt for production use."
            )
            self.hash_method = "sha256"  # Fallback (NOT secure for passwords)

    @contextmanager
    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            logger.error(f"Database error in auth: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_auth_tables(self):
        """Initialize authentication tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'doctor',
                    auth_method TEXT NOT NULL DEFAULT 'none',
                    password_hash TEXT,
                    pin_hash TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    failed_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP
                )
            """)

            # App settings table (for global auth config)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Check if default user exists
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                # Create default doctor account (no password initially)
                cursor.execute("""
                    INSERT INTO users
                    (username, full_name, role, auth_method, is_active)
                    VALUES (?, ?, ?, ?, 1)
                """, ("doctor", "Default Doctor", UserRole.DOCTOR.value, AuthMethod.NONE.value))

                logger.info("Created default doctor account (no password)")

    # ============== PASSWORD HASHING ==============

    def hash_password(self, password: str) -> str:
        """Hash a password securely.

        Args:
            password: Plain text password

        Returns:
            Password hash
        """
        if self.hash_method == "argon2":
            return self.password_hasher.hash(password)
        elif self.hash_method == "bcrypt":
            return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            # Fallback (NOT secure for production)
            logger.warning("Using SHA256 for password - NOT SECURE. Install argon2-cffi.")
            salt = secrets.token_hex(16)
            hash_value = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return f"{salt}${hash_value.hex()}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against hash.

        Args:
            password: Plain text password
            password_hash: Stored hash

        Returns:
            True if password matches
        """
        try:
            if self.hash_method == "argon2":
                try:
                    self.password_hasher.verify(password_hash, password)
                    return True
                except (VerifyMismatchError, InvalidHash):
                    return False
            elif self.hash_method == "bcrypt":
                return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
            else:
                # Fallback verification
                parts = password_hash.split('$')
                if len(parts) != 2:
                    return False
                salt, stored_hash = parts
                computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
                return computed_hash.hex() == stored_hash

        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def hash_pin(self, pin: str) -> str:
        """Hash a PIN (simpler than password).

        Args:
            pin: PIN digits

        Returns:
            PIN hash
        """
        # For PINs, we can use a simpler hash (but still salted)
        salt = secrets.token_hex(8)
        hash_value = hashlib.pbkdf2_hmac('sha256', pin.encode(), salt.encode(), 10000)
        return f"{salt}${hash_value.hex()}"

    def verify_pin(self, pin: str, pin_hash: str) -> bool:
        """Verify PIN against hash.

        Args:
            pin: PIN digits
            pin_hash: Stored hash

        Returns:
            True if PIN matches
        """
        try:
            parts = pin_hash.split('$')
            if len(parts) != 2:
                return False
            salt, stored_hash = parts
            computed_hash = hashlib.pbkdf2_hmac('sha256', pin.encode(), salt.encode(), 10000)
            return computed_hash.hex() == stored_hash
        except Exception as e:
            logger.error(f"PIN verification error: {e}")
            return False

    # ============== USER MANAGEMENT ==============

    def create_user(
        self,
        username: str,
        full_name: str,
        role: UserRole,
        password: Optional[str] = None,
        pin: Optional[str] = None
    ) -> Optional[User]:
        """Create a new user account.

        Args:
            username: Unique username
            full_name: Full name
            role: User role
            password: Optional password
            pin: Optional PIN

        Returns:
            User object if successful
        """
        try:
            auth_method = AuthMethod.NONE
            password_hash = None
            pin_hash = None

            if password:
                auth_method = AuthMethod.PASSWORD
                password_hash = self.hash_password(password)
            elif pin:
                auth_method = AuthMethod.PIN
                pin_hash = self.hash_pin(pin)

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users
                    (username, full_name, role, auth_method, password_hash, pin_hash, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (username, full_name, role.value, auth_method.value, password_hash, pin_hash))

                user_id = cursor.lastrowid

                logger.info(f"Created user: {username} ({role.value})")

                return self.get_user(user_id)

        except sqlite3.IntegrityError:
            logger.error(f"User {username} already exists")
            return None
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_user(row)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User object or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_user(row)

    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Convert database row to User object."""
        return User(
            id=row['id'],
            username=row['username'],
            full_name=row['full_name'],
            role=UserRole(row['role']),
            auth_method=AuthMethod(row['auth_method']),
            password_hash=row['password_hash'],
            pin_hash=row['pin_hash'],
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']),
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
            failed_attempts=row['failed_attempts'],
            locked_until=datetime.fromisoformat(row['locked_until']) if row['locked_until'] else None
        )

    # ============== AUTHENTICATION ==============

    def authenticate(self, username: str, password: Optional[str] = None,
                    pin: Optional[str] = None) -> Tuple[bool, Optional[User], str]:
        """Authenticate a user.

        Args:
            username: Username
            password: Password (if using password auth)
            pin: PIN (if using PIN auth)

        Returns:
            Tuple of (success, user, message)
        """
        user = self.get_user_by_username(username)

        if not user:
            return False, None, "User not found"

        if not user.is_active:
            return False, None, "Account is disabled"

        # Check if account is locked
        if user.locked_until:
            if datetime.now() < user.locked_until:
                return False, None, f"Account locked until {user.locked_until.strftime('%H:%M')}"
            else:
                # Unlock account
                self._unlock_user(user.id)

        # Check authentication method
        if user.auth_method == AuthMethod.NONE:
            # No authentication required
            self._record_successful_login(user.id)
            return True, user, "Login successful (no auth required)"

        elif user.auth_method == AuthMethod.PASSWORD:
            if not password:
                return False, None, "Password required"

            if self.verify_password(password, user.password_hash):
                self._record_successful_login(user.id)
                return True, user, "Login successful"
            else:
                self._record_failed_attempt(user.id)
                return False, None, "Invalid password"

        elif user.auth_method == AuthMethod.PIN:
            if not pin:
                return False, None, "PIN required"

            if self.verify_pin(pin, user.pin_hash):
                self._record_successful_login(user.id)
                return True, user, "Login successful"
            else:
                self._record_failed_attempt(user.id)
                return False, None, "Invalid PIN"

        return False, None, "Authentication method not supported"

    def _record_successful_login(self, user_id: int):
        """Record successful login and reset failed attempts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET last_login = CURRENT_TIMESTAMP,
                    failed_attempts = 0,
                    locked_until = NULL
                WHERE id = ?
            """, (user_id,))

    def _record_failed_attempt(self, user_id: int):
        """Record failed login attempt and lock account if needed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Increment failed attempts
            cursor.execute("""
                UPDATE users
                SET failed_attempts = failed_attempts + 1
                WHERE id = ?
            """, (user_id,))

            # Check if we should lock the account
            cursor.execute("SELECT failed_attempts FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

            if row and row[0] >= self.MAX_FAILED_ATTEMPTS:
                # Lock account
                locked_until = datetime.now() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
                cursor.execute("""
                    UPDATE users
                    SET locked_until = ?
                    WHERE id = ?
                """, (locked_until, user_id))

                logger.warning(
                    f"User {user_id} locked due to {row[0]} failed attempts. "
                    f"Locked until {locked_until}"
                )

    def _unlock_user(self, user_id: int):
        """Unlock a user account."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET locked_until = NULL,
                    failed_attempts = 0
                WHERE id = ?
            """, (user_id,))

    # ============== PASSWORD MANAGEMENT ==============

    def set_password(self, user_id: int, new_password: str) -> bool:
        """Set/change user password.

        Args:
            user_id: User ID
            new_password: New password

        Returns:
            True if successful
        """
        try:
            password_hash = self.hash_password(new_password)

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET password_hash = ?,
                        auth_method = ?
                    WHERE id = ?
                """, (password_hash, AuthMethod.PASSWORD.value, user_id))

                logger.info(f"Password updated for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to set password: {e}")
            return False

    def set_pin(self, user_id: int, new_pin: str) -> bool:
        """Set/change user PIN.

        Args:
            user_id: User ID
            new_pin: New PIN (4-6 digits)

        Returns:
            True if successful
        """
        # Validate PIN format
        if not new_pin.isdigit() or len(new_pin) < 4 or len(new_pin) > 6:
            logger.error("PIN must be 4-6 digits")
            return False

        try:
            pin_hash = self.hash_pin(new_pin)

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET pin_hash = ?,
                        auth_method = ?
                    WHERE id = ?
                """, (pin_hash, AuthMethod.PIN.value, user_id))

                logger.info(f"PIN updated for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to set PIN: {e}")
            return False

    def remove_authentication(self, user_id: int) -> bool:
        """Remove authentication (set to NONE).

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET auth_method = ?,
                        password_hash = NULL,
                        pin_hash = NULL
                    WHERE id = ?
                """, (AuthMethod.NONE.value, user_id))

                logger.info(f"Authentication removed for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to remove authentication: {e}")
            return False

    # ============== BIOMETRIC SUPPORT (PLACEHOLDER) ==============

    def enable_biometric(self, user_id: int) -> bool:
        """Enable biometric authentication (mobile only).

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        # This is a placeholder for mobile implementation
        # Actual biometric auth is handled by the OS

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET auth_method = ?
                    WHERE id = ?
                """, (AuthMethod.BIOMETRIC.value, user_id))

                logger.info(f"Biometric enabled for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to enable biometric: {e}")
            return False

    # ============== APP-LEVEL SETTINGS ==============

    def is_auth_enabled(self) -> bool:
        """Check if authentication is enabled for the app."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT value FROM app_settings WHERE key = 'auth_enabled'
            """)
            row = cursor.fetchone()
            return row and row[0] == 'true'

    def enable_auth(self):
        """Enable authentication for the app."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO app_settings (key, value, updated_at)
                VALUES ('auth_enabled', 'true', CURRENT_TIMESTAMP)
            """)

    def disable_auth(self):
        """Disable authentication for the app."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO app_settings (key, value, updated_at)
                VALUES ('auth_enabled', 'false', CURRENT_TIMESTAMP)
            """)


# Global instance
_auth_manager = None


def get_auth_manager() -> AuthenticationManager:
    """Get global authentication manager instance.

    Returns:
        AuthenticationManager instance
    """
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthenticationManager()
    return _auth_manager
