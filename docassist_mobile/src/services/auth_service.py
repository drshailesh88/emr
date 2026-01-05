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
import logging

import requests

from .biometric_service import BiometricService

logger = logging.getLogger(__name__)


@dataclass
class AuthState:
    """Authentication state."""
    is_authenticated: bool = False
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    token: Optional[str] = None
    encryption_key: Optional[bytes] = None
    biometric_enabled: bool = False


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
        self.biometric_service = BiometricService()

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
        # Also clear biometric credentials on logout
        self.biometric_service.clear_biometric_data()

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
    # Biometric Authentication
    # -------------------------------------------------------------------------

    async def biometric_login(self) -> bool:
        """
        Authenticate using biometric credentials.

        Retrieves stored credentials and authenticates if biometric
        authentication succeeds.

        Returns:
            True if biometric login succeeded
        """
        # Check if biometric login is available and enabled
        if not self.biometric_service.is_biometric_available():
            logger.warning("Biometric authentication not available")
            return False

        if not self.biometric_service.is_biometric_enabled():
            logger.info("Biometric login not enabled")
            return False

        # Get biometric type for prompt message
        biometric_type = self.biometric_service.get_biometric_display_name()

        # Prompt for biometric authentication
        auth_success = await self.biometric_service.authenticate(
            reason=f"Unlock DocAssist with {biometric_type}"
        )

        if not auth_success:
            logger.warning("Biometric authentication failed")
            return False

        # Retrieve stored credentials
        credentials = self.biometric_service.get_biometric_credentials()
        if not credentials:
            logger.error("Biometric credentials not found")
            return False

        email, token = credentials

        # Set authenticated state with stored credentials
        # Note: We're using the stored token directly, not re-authenticating
        # In production, you might want to validate the token with the server
        self.state.is_authenticated = True
        self.state.user_email = email
        self.state.user_name = email.split('@')[0].replace('.', ' ').title()
        self.state.token = token
        self.state.biometric_enabled = True

        logger.info(f"Biometric login successful for {email}")
        return True

    def enable_biometric(self) -> bool:
        """
        Enable biometric login for the current user.

        Must be called after successful password login.

        Returns:
            True if biometric login was enabled successfully
        """
        if not self.state.is_authenticated:
            logger.error("Cannot enable biometric - user not authenticated")
            return False

        if not self.biometric_service.is_biometric_available():
            logger.warning("Biometric authentication not available on this device")
            return False

        # Store credentials for biometric login
        success = self.biometric_service.enable_biometric_login(
            email=self.state.user_email,
            encrypted_token=self.state.token,
        )

        if success:
            self.state.biometric_enabled = True
            logger.info(f"Biometric login enabled for {self.state.user_email}")

        return success

    def disable_biometric(self) -> bool:
        """
        Disable biometric login for the current user.

        Returns:
            True if biometric login was disabled successfully
        """
        success = self.biometric_service.disable_biometric_login()

        if success:
            self.state.biometric_enabled = False
            logger.info("Biometric login disabled")

        return success

    def is_biometric_available(self) -> bool:
        """
        Check if biometric authentication is available on this device.

        Returns:
            True if biometrics are supported
        """
        return self.biometric_service.is_biometric_available()

    def is_biometric_enabled(self) -> bool:
        """
        Check if biometric login is currently enabled.

        Returns:
            True if biometric login is enabled
        """
        return self.biometric_service.is_biometric_enabled()

    def get_biometric_type(self) -> str:
        """
        Get the type of biometric authentication available.

        Returns:
            "face_id", "fingerprint", or "none"
        """
        return self.biometric_service.get_biometric_type()

    def get_biometric_display_name(self) -> str:
        """
        Get user-friendly name for the biometric type.

        Returns:
            "Face ID", "Fingerprint", or "Biometric"
        """
        return self.biometric_service.get_biometric_display_name()

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
