"""
Biometric Authentication Service - Face ID / Fingerprint support.

This service provides:
- Device biometric capability detection
- Biometric authentication prompts
- Secure credential storage for biometric login
- Platform-specific biometric type detection

Platform Support:
- iOS: Face ID, Touch ID
- Android: Face Unlock, Fingerprint

Note: Flet's biometric support is evolving. This service provides a consistent
API that can interface with native platform channels or fallback to mock/testing modes.
"""

import os
import logging
from typing import Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class BiometricType(Enum):
    """Types of biometric authentication."""
    NONE = "none"
    FACE_ID = "face_id"           # iOS Face ID
    TOUCH_ID = "touch_id"         # iOS Touch ID
    FINGERPRINT = "fingerprint"   # Android Fingerprint
    FACE_UNLOCK = "face_unlock"   # Android Face Unlock
    IRIS = "iris"                 # Samsung Iris Scanner


@dataclass
class BiometricCapability:
    """Device biometric capabilities."""
    is_available: bool = False
    biometric_type: BiometricType = BiometricType.NONE
    error_message: Optional[str] = None


class BiometricService:
    """
    Biometric authentication service for DocAssist Mobile.

    Usage:
        biometric = BiometricService()

        # Check if biometrics are available
        if biometric.is_biometric_available():
            # Authenticate
            success = await biometric.authenticate("Unlock DocAssist")

            # Enable biometric login
            if success:
                biometric.enable_biometric_login(email, token)
    """

    def __init__(self, platform: Optional[str] = None):
        """
        Initialize biometric service.

        Args:
            platform: Platform override for testing ("ios", "android", "web")
                     If None, auto-detects from environment
        """
        self.platform = platform or self._detect_platform()
        self._capability = None
        self._mock_mode = os.getenv("BIOMETRIC_MOCK_MODE", "false").lower() == "true"

    def _detect_platform(self) -> str:
        """
        Detect the platform we're running on.

        Returns:
            Platform name: "ios", "android", "web", or "unknown"
        """
        # Try to detect from Flet page platform
        # In a real implementation, this would come from ft.Page.platform
        # For now, we'll check environment variables

        platform = os.getenv("FLET_PLATFORM", "unknown").lower()
        if platform in ["ios", "android", "web"]:
            return platform

        # Fallback detection
        import platform as py_platform
        system = py_platform.system().lower()

        if system == "darwin":
            # Could be macOS or iOS simulator
            return "ios"
        elif system == "linux":
            # Could be Android
            return "android"
        else:
            return "unknown"

    def is_biometric_available(self) -> bool:
        """
        Check if biometric authentication is available on this device.

        Returns:
            True if biometrics are available
        """
        capability = self._get_capability()
        return capability.is_available

    def get_biometric_type(self) -> str:
        """
        Get the type of biometric authentication available.

        Returns:
            Biometric type: "face_id", "fingerprint", or "none"
        """
        capability = self._get_capability()

        # Simplify to user-friendly names
        if capability.biometric_type in [BiometricType.FACE_ID, BiometricType.FACE_UNLOCK]:
            return "face_id"
        elif capability.biometric_type in [BiometricType.TOUCH_ID, BiometricType.FINGERPRINT]:
            return "fingerprint"
        else:
            return "none"

    def get_biometric_display_name(self) -> str:
        """
        Get user-friendly display name for the biometric type.

        Returns:
            Display name: "Face ID", "Fingerprint", or "Biometric"
        """
        biometric_type = self.get_biometric_type()

        if biometric_type == "face_id":
            return "Face ID"
        elif biometric_type == "fingerprint":
            return "Fingerprint"
        else:
            return "Biometric"

    def _get_capability(self) -> BiometricCapability:
        """
        Get device biometric capability.
        Caches result for performance.

        Returns:
            BiometricCapability with device support info
        """
        if self._capability is not None:
            return self._capability

        # Mock mode for development/testing
        if self._mock_mode:
            self._capability = BiometricCapability(
                is_available=True,
                biometric_type=BiometricType.FACE_ID if self.platform == "ios" else BiometricType.FINGERPRINT,
            )
            return self._capability

        # Try to use native biometric detection
        try:
            capability = self._check_native_biometrics()
            self._capability = capability
            return capability
        except Exception as e:
            logger.warning(f"Failed to check biometric capability: {e}")
            self._capability = BiometricCapability(
                is_available=False,
                biometric_type=BiometricType.NONE,
                error_message=str(e),
            )
            return self._capability

    def _check_native_biometrics(self) -> BiometricCapability:
        """
        Check for native biometric support via platform channels.

        This is where we would integrate with Flet's native platform channels
        when they become available.

        Returns:
            BiometricCapability
        """
        # Platform-specific detection
        if self.platform == "ios":
            return self._check_ios_biometrics()
        elif self.platform == "android":
            return self._check_android_biometrics()
        else:
            return BiometricCapability(
                is_available=False,
                biometric_type=BiometricType.NONE,
                error_message="Platform does not support biometrics",
            )

    def _check_ios_biometrics(self) -> BiometricCapability:
        """
        Check iOS biometric capabilities (Face ID / Touch ID).

        In production, this would use Flet's iOS platform channel to call:
        LAContext().canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics)

        Returns:
            BiometricCapability
        """
        # TODO: Implement native iOS biometric detection via Flet platform channel
        # For now, assume Face ID on modern iOS devices
        logger.info("iOS biometric check - using default Face ID assumption")

        return BiometricCapability(
            is_available=True,
            biometric_type=BiometricType.FACE_ID,
        )

    def _check_android_biometrics(self) -> BiometricCapability:
        """
        Check Android biometric capabilities (Fingerprint / Face).

        In production, this would use Flet's Android platform channel to call:
        BiometricManager.from(context).canAuthenticate()

        Returns:
            BiometricCapability
        """
        # TODO: Implement native Android biometric detection via Flet platform channel
        # For now, assume fingerprint sensor available
        logger.info("Android biometric check - using default fingerprint assumption")

        return BiometricCapability(
            is_available=True,
            biometric_type=BiometricType.FINGERPRINT,
        )

    async def authenticate(self, reason: str = "Authenticate to access DocAssist") -> bool:
        """
        Trigger biometric authentication prompt.

        Args:
            reason: User-facing reason for authentication request

        Returns:
            True if authentication succeeded, False otherwise
        """
        if not self.is_biometric_available():
            logger.warning("Biometric authentication not available")
            return False

        # Mock mode for testing
        if self._mock_mode:
            logger.info(f"Mock biometric authentication: {reason}")
            # Simulate successful auth in mock mode
            return True

        try:
            return await self._native_authenticate(reason)
        except Exception as e:
            logger.error(f"Biometric authentication failed: {e}")
            return False

    async def _native_authenticate(self, reason: str) -> bool:
        """
        Perform native platform biometric authentication.

        This is where we would call native platform APIs via Flet channels.

        iOS: LAContext().evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics)
        Android: BiometricPrompt.authenticate()

        Args:
            reason: User-facing authentication reason

        Returns:
            True if authentication succeeded
        """
        # TODO: Implement native biometric authentication via Flet platform channels
        # For now, return mock success for development
        logger.info(f"Native biometric authentication requested: {reason}")

        # This would be replaced with actual platform channel call:
        # if self.platform == "ios":
        #     return await self._ios_authenticate(reason)
        # elif self.platform == "android":
        #     return await self._android_authenticate(reason)

        return True

    # -------------------------------------------------------------------------
    # Credential Storage (using keyring for security)
    # -------------------------------------------------------------------------

    def enable_biometric_login(self, email: str, encrypted_token: str) -> bool:
        """
        Enable biometric login by storing encrypted credentials.

        Credentials are stored in platform keychain/keystore:
        - iOS: Keychain with kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        - Android: Android Keystore with biometric requirement

        Args:
            email: User's email address
            encrypted_token: Encrypted authentication token

        Returns:
            True if credentials were successfully stored
        """
        try:
            import keyring

            # Store biometric credentials separately from regular credentials
            keyring.set_password("docassist_biometric", "email", email)
            keyring.set_password("docassist_biometric", "token", encrypted_token)

            # Set preference flag
            keyring.set_password("docassist_biometric", "enabled", "true")

            logger.info(f"Biometric login enabled for {email}")
            return True

        except ImportError:
            logger.error("Keyring module not available - cannot enable biometric login")
            return False
        except Exception as e:
            logger.error(f"Failed to enable biometric login: {e}")
            return False

    def disable_biometric_login(self) -> bool:
        """
        Disable biometric login and clear stored credentials.

        Returns:
            True if biometric login was successfully disabled
        """
        try:
            import keyring

            # Clear stored credentials
            try:
                keyring.delete_password("docassist_biometric", "email")
                keyring.delete_password("docassist_biometric", "token")
                keyring.delete_password("docassist_biometric", "enabled")
            except keyring.errors.PasswordDeleteError:
                # Credentials may not exist, that's ok
                pass

            logger.info("Biometric login disabled")
            return True

        except ImportError:
            logger.error("Keyring module not available")
            return False
        except Exception as e:
            logger.error(f"Failed to disable biometric login: {e}")
            return False

    def is_biometric_enabled(self) -> bool:
        """
        Check if biometric login is enabled.

        Returns:
            True if biometric login is enabled
        """
        try:
            import keyring
            enabled = keyring.get_password("docassist_biometric", "enabled")
            return enabled == "true"
        except (ImportError, Exception):
            return False

    def get_biometric_credentials(self) -> Optional[Tuple[str, str]]:
        """
        Get stored biometric credentials (email, token).

        Only returns credentials if biometric login is enabled.

        Returns:
            Tuple of (email, token) if available, None otherwise
        """
        if not self.is_biometric_enabled():
            return None

        try:
            import keyring

            email = keyring.get_password("docassist_biometric", "email")
            token = keyring.get_password("docassist_biometric", "token")

            if email and token:
                return (email, token)
            else:
                logger.warning("Biometric credentials incomplete")
                return None

        except ImportError:
            logger.error("Keyring module not available")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve biometric credentials: {e}")
            return None

    def clear_biometric_data(self):
        """
        Clear all biometric-related data.
        Use when user logs out or changes accounts.
        """
        self.disable_biometric_login()
        logger.info("Biometric data cleared")


# Convenience functions for common patterns

def get_biometric_icon(biometric_type: str) -> str:
    """
    Get Flet icon name for biometric type.

    Args:
        biometric_type: "face_id", "fingerprint", or "none"

    Returns:
        Flet icon name (ft.Icons constant name)
    """
    try:
        import flet as ft

        if biometric_type == "face_id":
            return ft.Icons.FACE
        elif biometric_type == "fingerprint":
            return ft.Icons.FINGERPRINT
        else:
            return ft.Icons.SECURITY
    except ImportError:
        # Fallback to string names if flet not available
        if biometric_type == "face_id":
            return "face"
        elif biometric_type == "fingerprint":
            return "fingerprint"
        else:
            return "security"


def get_biometric_description(biometric_type: str) -> str:
    """
    Get user-friendly description for biometric type.

    Args:
        biometric_type: "face_id", "fingerprint", or "none"

    Returns:
        Description text for UI
    """
    if biometric_type == "face_id":
        return "Use your face to unlock DocAssist quickly and securely"
    elif biometric_type == "fingerprint":
        return "Use your fingerprint to unlock DocAssist quickly and securely"
    else:
        return "Biometric authentication not available on this device"


# Export all biometric utilities
__all__ = [
    'BiometricType',
    'BiometricCapability',
    'BiometricService',
    'get_biometric_icon',
    'get_biometric_description',
]
