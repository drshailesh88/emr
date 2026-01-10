"""WhatsApp webhook handler for receiving messages.

Note: This is a placeholder. Full implementation requires WhatsApp Business API setup.
"""

from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class WebhookEventType(Enum):
    """Types of webhook events from WhatsApp."""
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_READ = "message_read"
    MESSAGE_FAILED = "message_failed"
    STATUS_UPDATE = "status_update"


@dataclass
class WebhookEvent:
    """Represents an incoming webhook event from WhatsApp."""
    event_type: WebhookEventType
    timestamp: datetime
    phone_number: str
    message_id: Optional[str] = None
    message_text: Optional[str] = None
    media_url: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


class WebhookHandler:
    """Handles incoming webhooks from WhatsApp Business API.

    Note: This is a placeholder implementation. To fully implement:
    1. Set up WhatsApp Business API account
    2. Configure webhook URL in Meta Developer Console
    3. Implement signature verification
    4. Handle different message types
    """

    def __init__(
        self,
        verify_token: str = "",
        app_secret: str = "",
        on_message: Optional[Callable[[WebhookEvent], None]] = None,
        on_status: Optional[Callable[[WebhookEvent], None]] = None,
    ):
        """Initialize webhook handler.

        Args:
            verify_token: Token for webhook verification (from Meta console)
            app_secret: App secret for signature verification
            on_message: Callback for incoming messages
            on_status: Callback for status updates
        """
        self.verify_token = verify_token
        self.app_secret = app_secret
        self.on_message = on_message
        self.on_status = on_status
        self._initialized = False

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify webhook subscription (called by Meta).

        Args:
            mode: Should be 'subscribe'
            token: Verification token (must match self.verify_token)
            challenge: Challenge string to return

        Returns:
            Challenge string if verified, None otherwise
        """
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature using app secret.

        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header value

        Returns:
            True if signature is valid
        """
        # Placeholder - implement HMAC-SHA256 verification
        if not self.app_secret:
            return True  # Skip verification if no secret configured

        import hmac
        import hashlib

        expected = hmac.new(
            self.app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected}", signature)

    def handle_webhook(self, data: Dict[str, Any]) -> None:
        """Process incoming webhook data.

        Args:
            data: Parsed JSON from webhook request
        """
        # Placeholder implementation
        if not data:
            return

        # Parse webhook structure (simplified)
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        # Handle messages
        messages = value.get("messages", [])
        for msg in messages:
            event = WebhookEvent(
                event_type=WebhookEventType.MESSAGE_RECEIVED,
                timestamp=datetime.now(),
                phone_number=msg.get("from", ""),
                message_id=msg.get("id"),
                message_text=msg.get("text", {}).get("body"),
                raw_data=msg
            )
            if self.on_message:
                self.on_message(event)

        # Handle status updates
        statuses = value.get("statuses", [])
        for status in statuses:
            event = WebhookEvent(
                event_type=WebhookEventType.STATUS_UPDATE,
                timestamp=datetime.now(),
                phone_number=status.get("recipient_id", ""),
                message_id=status.get("id"),
                status=status.get("status"),
                raw_data=status
            )
            if self.on_status:
                self.on_status(event)

    def is_configured(self) -> bool:
        """Check if webhook handler is properly configured."""
        return bool(self.verify_token and self.app_secret)
