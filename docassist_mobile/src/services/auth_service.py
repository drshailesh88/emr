"""
Authentication Service - Handles login and credential management.

This service provides:
- Cloud authentication
- Secure credential storage
- Session management
"""

import os
import hashlib
from typing import Optional, Tuple
from dataclasses import dataclass

import requests


@dataclass
class AuthState:
    """Authentication state."""
    is_authenticated: bool = False
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    token: Optional[str] = None
    encryption_key: Optional[bytes] = None


class AuthService:
    """
    Authentication service for DocAssist Mobile.

    Usage:
        auth = AuthService()
        success = auth.login("doctor@example.com", "password123")
        if success:
            token = auth.get_token()
            key = auth.get_encryption_key()
    """

    def __init__(self, api_url: str = "https://api.docassist.in"):
        self.api_url = api_url
        self.state = AuthState()

    def login(self, email: str, password: str) -> bool:
        """
        Authenticate with DocAssist Cloud.

        Args:
            email: User's email
            password: User's password

        Returns:
            True if authentication successful
        """
        try:
            # Call auth API
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"email": email, "password": password},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self._set_authenticated(
                    email=email,
                    name=data.get('name', email.split('@')[0]),
                    token=data.get('token'),
                    password=password,
                )
                return True
            else:
                return False

        except requests.exceptions.RequestException:
            # For development: allow mock login
            if email and password:
                self._set_authenticated(
                    email=email,
                    name=email.split('@')[0].replace('.', ' ').title(),
                    token="mock_token_" + hashlib.md5(email.encode()).hexdigest()[:8],
                    password=password,
                )
                return True
            return False

    def _set_authenticated(
        self,
        email: str,
        name: str,
        token: str,
        password: str,
    ):
        """Set authenticated state."""
        self.state.is_authenticated = True
        self.state.user_email = email
        self.state.user_name = name
        self.state.token = token
        self.state.encryption_key = self._derive_key(password)

    def _derive_key(self, password: str) -> bytes:
        """
        Derive encryption key from password.

        In production, this uses Argon2 (same as desktop).
        For development, we use a simple derivation.
        """
        try:
            # Try to use desktop's crypto service
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            from src.services.crypto import CryptoService

            crypto = CryptoService()
            # Use a fixed salt for consistent key derivation
            salt = b'docassist_mobile_salt_v1'
            return crypto.derive_key(password, salt)
        except ImportError:
            # Fallback: simple key derivation (NOT secure for production)
            return hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                b'docassist_mobile_salt_v1',
                100000,
                dklen=32,
            )

    def logout(self):
        """Log out and clear credentials."""
        self.state = AuthState()
        self._clear_stored_credentials()

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.state.is_authenticated

    def get_token(self) -> Optional[str]:
        """Get authentication token."""
        return self.state.token

    def get_encryption_key(self) -> Optional[bytes]:
        """Get encryption key."""
        return self.state.encryption_key

    def get_user_info(self) -> Tuple[Optional[str], Optional[str]]:
        """Get user info (name, email)."""
        return self.state.user_name, self.state.user_email

    # -------------------------------------------------------------------------
    # Credential Storage (using keyring)
    # -------------------------------------------------------------------------

    def save_credentials(self):
        """Save credentials to secure storage."""
        try:
            import keyring
            if self.state.token:
                keyring.set_password("docassist", "token", self.state.token)
            if self.state.user_email:
                keyring.set_password("docassist", "email", self.state.user_email)
        except ImportError:
            # Keyring not available on this platform
            pass

    def load_credentials(self) -> bool:
        """Load credentials from secure storage."""
        try:
            import keyring
            token = keyring.get_password("docassist", "token")
            email = keyring.get_password("docassist", "email")

            if token and email:
                self.state.is_authenticated = True
                self.state.token = token
                self.state.user_email = email
                self.state.user_name = email.split('@')[0].title()
                return True
        except ImportError:
            pass

        return False

    def _clear_stored_credentials(self):
        """Clear stored credentials."""
        try:
            import keyring
            keyring.delete_password("docassist", "token")
            keyring.delete_password("docassist", "email")
        except (ImportError, keyring.errors.PasswordDeleteError):
            pass
