"""Stub webhook handler for WhatsApp integration.

This keeps imports stable even when webhook handling is not configured.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class WebhookEvent:
    """Minimal webhook event container."""

    event_type: str
    payload: Dict[str, Any]


class WebhookHandler:
    """No-op webhook handler placeholder."""

    def __init__(self) -> None:
        return

    def handle(self, event: WebhookEvent) -> Optional[Dict[str, Any]]:
        """Process a webhook event.

        Returns None because webhook processing is not configured locally.
        """
        return None
