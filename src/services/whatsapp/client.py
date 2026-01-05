"""WhatsApp Business Cloud API client"""
import httpx
import asyncio
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
import os
import logging

logger = logging.getLogger(__name__)


class MessageStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass
class SendResult:
    message_id: str
    status: MessageStatus
    timestamp: str
    error: Optional[str] = None


@dataclass
class MediaUploadResult:
    media_id: str
    mime_type: str


class WhatsAppClient:
    """WhatsApp Business Cloud API client"""

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self,
                 phone_number_id: Optional[str] = None,
                 access_token: Optional[str] = None):
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = access_token or os.getenv("WHATSAPP_ACCESS_TOKEN")

        if not self.phone_number_id or not self.access_token:
            logger.warning("WhatsApp credentials not configured")

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=30.0
        )

    async def send_text(self, to: str, message: str,
                       preview_url: bool = False) -> SendResult:
        """Send a text message"""
        to = self._format_phone(to)

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": message
            }
        }

        try:
            response = await self.client.post(
                f"/{self.phone_number_id}/messages",
                json=payload
            )
            response.raise_for_status()
            return self._parse_response(response)
        except httpx.HTTPError as e:
            logger.error(f"Failed to send text message: {e}")
            return SendResult(
                message_id="",
                status=MessageStatus.FAILED,
                timestamp="",
                error=str(e)
            )

    async def send_template(self,
                           to: str,
                           template_name: str,
                           language: str = "en",
                           components: Optional[List[Dict]] = None) -> SendResult:
        """Send a pre-approved template message"""
        to = self._format_phone(to)

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language
                }
            }
        }

        if components:
            payload["template"]["components"] = components

        try:
            response = await self.client.post(
                f"/{self.phone_number_id}/messages",
                json=payload
            )
            response.raise_for_status()
            return self._parse_response(response)
        except httpx.HTTPError as e:
            logger.error(f"Failed to send template message: {e}")
            return SendResult(
                message_id="",
                status=MessageStatus.FAILED,
                timestamp="",
                error=str(e)
            )

    async def send_document(self,
                           to: str,
                           document_url: str,
                           filename: str,
                           caption: Optional[str] = None) -> SendResult:
        """Send a document (PDF, etc.)"""
        to = self._format_phone(to)

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename
            }
        }

        if caption:
            payload["document"]["caption"] = caption

        try:
            response = await self.client.post(
                f"/{self.phone_number_id}/messages",
                json=payload
            )
            response.raise_for_status()
            return self._parse_response(response)
        except httpx.HTTPError as e:
            logger.error(f"Failed to send document: {e}")
            return SendResult(
                message_id="",
                status=MessageStatus.FAILED,
                timestamp="",
                error=str(e)
            )

    async def send_document_by_id(self,
                                  to: str,
                                  media_id: str,
                                  filename: str,
                                  caption: Optional[str] = None) -> SendResult:
        """Send a document using uploaded media ID"""
        to = self._format_phone(to)

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": {
                "id": media_id,
                "filename": filename
            }
        }

        if caption:
            payload["document"]["caption"] = caption

        try:
            response = await self.client.post(
                f"/{self.phone_number_id}/messages",
                json=payload
            )
            response.raise_for_status()
            return self._parse_response(response)
        except httpx.HTTPError as e:
            logger.error(f"Failed to send document by ID: {e}")
            return SendResult(
                message_id="",
                status=MessageStatus.FAILED,
                timestamp="",
                error=str(e)
            )

    async def send_image(self,
                        to: str,
                        image_url: str,
                        caption: Optional[str] = None) -> SendResult:
        """Send an image"""
        to = self._format_phone(to)

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": {
                "link": image_url
            }
        }

        if caption:
            payload["image"]["caption"] = caption

        try:
            response = await self.client.post(
                f"/{self.phone_number_id}/messages",
                json=payload
            )
            response.raise_for_status()
            return self._parse_response(response)
        except httpx.HTTPError as e:
            logger.error(f"Failed to send image: {e}")
            return SendResult(
                message_id="",
                status=MessageStatus.FAILED,
                timestamp="",
                error=str(e)
            )

    async def send_interactive_buttons(self,
                                       to: str,
                                       body: str,
                                       buttons: List[Dict],
                                       header: Optional[str] = None,
                                       footer: Optional[str] = None) -> SendResult:
        """Send interactive message with buttons (max 3 buttons)"""
        to = self._format_phone(to)

        interactive_payload = {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": buttons[:3]  # WhatsApp limits to 3 buttons
            }
        }

        if header:
            interactive_payload["header"] = {"type": "text", "text": header}

        if footer:
            interactive_payload["footer"] = {"text": footer}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive_payload
        }

        try:
            response = await self.client.post(
                f"/{self.phone_number_id}/messages",
                json=payload
            )
            response.raise_for_status()
            return self._parse_response(response)
        except httpx.HTTPError as e:
            logger.error(f"Failed to send interactive buttons: {e}")
            return SendResult(
                message_id="",
                status=MessageStatus.FAILED,
                timestamp="",
                error=str(e)
            )

    async def send_interactive_list(self,
                                   to: str,
                                   body: str,
                                   button_text: str,
                                   sections: List[Dict],
                                   header: Optional[str] = None,
                                   footer: Optional[str] = None) -> SendResult:
        """Send interactive message with list selection"""
        to = self._format_phone(to)

        interactive_payload = {
            "type": "list",
            "body": {"text": body},
            "action": {
                "button": button_text,
                "sections": sections
            }
        }

        if header:
            interactive_payload["header"] = {"type": "text", "text": header}

        if footer:
            interactive_payload["footer"] = {"text": footer}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive_payload
        }

        try:
            response = await self.client.post(
                f"/{self.phone_number_id}/messages",
                json=payload
            )
            response.raise_for_status()
            return self._parse_response(response)
        except httpx.HTTPError as e:
            logger.error(f"Failed to send interactive list: {e}")
            return SendResult(
                message_id="",
                status=MessageStatus.FAILED,
                timestamp="",
                error=str(e)
            )

    async def upload_media(self,
                          file_path: str,
                          mime_type: str) -> MediaUploadResult:
        """Upload media file and get media ID"""
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(file_path), f, mime_type)
                }
                data = {
                    'messaging_product': 'whatsapp'
                }

                response = await self.client.post(
                    f"/{self.phone_number_id}/media",
                    files=files,
                    data=data
                )
                response.raise_for_status()

                result = response.json()
                return MediaUploadResult(
                    media_id=result['id'],
                    mime_type=mime_type
                )
        except Exception as e:
            logger.error(f"Failed to upload media: {e}")
            raise

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read"""
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        try:
            response = await self.client.post(
                f"/{self.phone_number_id}/messages",
                json=payload
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to mark message as read: {e}")
            return False

    def _format_phone(self, phone: str) -> str:
        """Format phone number to E.164 format (India)"""
        # Remove all non-digit characters
        phone = ''.join(filter(str.isdigit, phone))

        # Handle Indian phone numbers
        if len(phone) == 10:
            phone = '91' + phone
        elif not phone.startswith('91'):
            phone = '91' + phone

        return phone

    def _parse_response(self, response: httpx.Response) -> SendResult:
        """Parse API response"""
        try:
            data = response.json()
            messages = data.get('messages', [])

            if messages:
                message = messages[0]
                return SendResult(
                    message_id=message.get('id', ''),
                    status=MessageStatus.SENT,
                    timestamp=str(data.get('timestamp', ''))
                )
            else:
                return SendResult(
                    message_id="",
                    status=MessageStatus.FAILED,
                    timestamp="",
                    error="No message ID in response"
                )
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            return SendResult(
                message_id="",
                status=MessageStatus.FAILED,
                timestamp="",
                error=str(e)
            )

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
