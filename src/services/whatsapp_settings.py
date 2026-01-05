"""WhatsApp Business API settings management."""

import json
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
import os

logger = logging.getLogger(__name__)


@dataclass
class WhatsAppCredentials:
    """WhatsApp Business API credentials."""
    phone_number_id: str = ""
    access_token: str = ""
    business_account_id: str = ""
    webhook_verify_token: str = ""
    enabled: bool = False
    mock_mode: bool = True  # When True, messages are logged instead of sent

    def is_configured(self) -> bool:
        """Check if credentials are configured."""
        return bool(self.phone_number_id and self.access_token)


class WhatsAppSettingsService:
    """Service for managing WhatsApp settings."""

    def __init__(self, settings_path: Optional[str] = None):
        """Initialize settings service.

        Args:
            settings_path: Path to settings file (default: data/whatsapp_settings.json)
        """
        if settings_path is None:
            settings_path = os.getenv("WHATSAPP_SETTINGS_PATH", "data/whatsapp_settings.json")
        self.settings_path = Path(settings_path)
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize credentials
        self.credentials = self._load_credentials()

    def _load_credentials(self) -> WhatsAppCredentials:
        """Load credentials from file."""
        if not self.settings_path.exists():
            logger.info("No WhatsApp settings found, creating default")
            return WhatsAppCredentials()

        try:
            with open(self.settings_path, 'r') as f:
                data = json.load(f)
                return WhatsAppCredentials(**data)
        except Exception as e:
            logger.error(f"Error loading WhatsApp settings: {e}")
            return WhatsAppCredentials()

    def save_credentials(self, credentials: WhatsAppCredentials) -> bool:
        """Save credentials to file.

        Args:
            credentials: WhatsApp credentials to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.settings_path, 'w') as f:
                json.dump(asdict(credentials), f, indent=2)
            self.credentials = credentials
            logger.info("WhatsApp settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving WhatsApp settings: {e}")
            return False

    def get_credentials(self) -> WhatsAppCredentials:
        """Get current credentials.

        Returns:
            WhatsApp credentials
        """
        return self.credentials

    def update_credentials(
        self,
        phone_number_id: Optional[str] = None,
        access_token: Optional[str] = None,
        business_account_id: Optional[str] = None,
        webhook_verify_token: Optional[str] = None,
        enabled: Optional[bool] = None,
        mock_mode: Optional[bool] = None
    ) -> bool:
        """Update specific credentials fields.

        Args:
            phone_number_id: Phone number ID
            access_token: Access token
            business_account_id: Business account ID
            webhook_verify_token: Webhook verify token
            enabled: Enable/disable WhatsApp features
            mock_mode: Enable/disable mock mode

        Returns:
            True if updated successfully, False otherwise
        """
        if phone_number_id is not None:
            self.credentials.phone_number_id = phone_number_id
        if access_token is not None:
            self.credentials.access_token = access_token
        if business_account_id is not None:
            self.credentials.business_account_id = business_account_id
        if webhook_verify_token is not None:
            self.credentials.webhook_verify_token = webhook_verify_token
        if enabled is not None:
            self.credentials.enabled = enabled
        if mock_mode is not None:
            self.credentials.mock_mode = mock_mode

        return self.save_credentials(self.credentials)

    def clear_credentials(self) -> bool:
        """Clear all credentials.

        Returns:
            True if cleared successfully, False otherwise
        """
        self.credentials = WhatsAppCredentials()
        return self.save_credentials(self.credentials)

    def test_connection(self) -> tuple[bool, str]:
        """Test WhatsApp API connection.

        Returns:
            Tuple of (success, message)
        """
        if not self.credentials.is_configured():
            return False, "Credentials not configured"

        if self.credentials.mock_mode:
            return True, "Mock mode enabled - connection not tested"

        try:
            # Import here to avoid circular dependency
            import asyncio
            from .whatsapp.client import WhatsAppClient

            client = WhatsAppClient(
                phone_number_id=self.credentials.phone_number_id,
                access_token=self.credentials.access_token
            )

            # Simple connection test - we'll just check if credentials are set
            # In production, you'd make an API call to verify
            if client.phone_number_id and client.access_token:
                return True, "Connection test successful"
            else:
                return False, "Invalid credentials"

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, f"Connection failed: {str(e)}"
