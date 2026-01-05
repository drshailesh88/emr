"""WhatsApp-specific message queue service wrapper."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from ..communications.notification_queue import (
    NotificationQueue,
    Notification,
    NotificationPriority,
    NotificationStatus,
    QueueStatus
)

logger = logging.getLogger(__name__)


class WhatsAppMessageQueue:
    """WhatsApp-specific message queue wrapper with additional features."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize WhatsApp message queue.

        Args:
            db_path: Path to database (default: data/clinic.db)
        """
        self.queue = NotificationQueue(db_path=db_path)

    def send_text_message(
        self,
        patient_id: int,
        phone: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        scheduled_for: Optional[datetime] = None
    ) -> str:
        """Queue a text message for sending.

        Args:
            patient_id: Patient ID
            phone: Patient phone number
            message: Message text
            priority: Message priority
            scheduled_for: When to send (default: now)

        Returns:
            Notification ID
        """
        notification = Notification(
            patient_id=patient_id,
            phone=phone,
            message=message,
            priority=priority,
            channel="whatsapp",
            scheduled_for=scheduled_for or datetime.now(),
            metadata={"message_type": "text"}
        )

        return self.queue.enqueue(notification)

    def send_template_message(
        self,
        patient_id: int,
        phone: str,
        template_name: str,
        template_params: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        scheduled_for: Optional[datetime] = None
    ) -> str:
        """Queue a template message for sending.

        Args:
            patient_id: Patient ID
            phone: Patient phone number
            template_name: WhatsApp template name
            template_params: Template parameters
            priority: Message priority
            scheduled_for: When to send (default: now)

        Returns:
            Notification ID
        """
        notification = Notification(
            patient_id=patient_id,
            phone=phone,
            message=f"Template: {template_name}",  # Placeholder
            priority=priority,
            channel="whatsapp",
            scheduled_for=scheduled_for or datetime.now(),
            metadata={
                "message_type": "template",
                "template_name": template_name,
                "template_params": template_params
            }
        )

        return self.queue.enqueue(notification)

    def send_document(
        self,
        patient_id: int,
        phone: str,
        document_path: str,
        caption: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        scheduled_for: Optional[datetime] = None
    ) -> str:
        """Queue a document for sending.

        Args:
            patient_id: Patient ID
            phone: Patient phone number
            document_path: Path to document file
            caption: Optional caption
            priority: Message priority
            scheduled_for: When to send (default: now)

        Returns:
            Notification ID
        """
        notification = Notification(
            patient_id=patient_id,
            phone=phone,
            message=caption or "Document",
            priority=priority,
            channel="whatsapp",
            scheduled_for=scheduled_for or datetime.now(),
            metadata={
                "message_type": "document",
                "document_path": document_path,
                "caption": caption
            }
        )

        return self.queue.enqueue(notification)

    def send_prescription(
        self,
        patient_id: int,
        phone: str,
        prescription_pdf_path: str,
        visit_date: str,
        priority: NotificationPriority = NotificationPriority.HIGH
    ) -> str:
        """Queue a prescription PDF for sending.

        Args:
            patient_id: Patient ID
            phone: Patient phone number
            prescription_pdf_path: Path to prescription PDF
            visit_date: Visit date string
            priority: Message priority (default: HIGH)

        Returns:
            Notification ID
        """
        caption = f"Your prescription from visit on {visit_date}"

        return self.send_document(
            patient_id=patient_id,
            phone=phone,
            document_path=prescription_pdf_path,
            caption=caption,
            priority=priority
        )

    def schedule_appointment_reminder(
        self,
        patient_id: int,
        phone: str,
        patient_name: str,
        appointment_date: datetime,
        appointment_time: str,
        reminder_before_hours: int = 24
    ) -> str:
        """Schedule an appointment reminder.

        Args:
            patient_id: Patient ID
            phone: Patient phone number
            patient_name: Patient name
            appointment_date: Appointment date and time
            appointment_time: Appointment time string (for display)
            reminder_before_hours: Hours before appointment to send (default: 24)

        Returns:
            Notification ID
        """
        # Calculate when to send reminder
        scheduled_for = appointment_date - timedelta(hours=reminder_before_hours)

        # Generate message
        date_str = appointment_date.strftime("%A, %d %B %Y")
        message = f"""Dear {patient_name},

This is a reminder for your appointment.

📅 Date: {date_str}
🕐 Time: {appointment_time}
📍 Location: Kumar Clinic

Please arrive 10 minutes early. If you need to reschedule, please contact us.

Thank you!"""

        notification = Notification(
            patient_id=patient_id,
            phone=phone,
            message=message,
            priority=NotificationPriority.NORMAL,
            channel="whatsapp",
            scheduled_for=scheduled_for,
            metadata={
                "message_type": "appointment_reminder",
                "appointment_date": appointment_date.isoformat(),
                "appointment_time": appointment_time
            }
        )

        return self.queue.enqueue(notification)

    def get_status(self) -> QueueStatus:
        """Get queue status.

        Returns:
            Queue status object
        """
        return self.queue.get_queue_status()

    def retry_failed_message(self, notification_id: str) -> bool:
        """Retry a failed message.

        Args:
            notification_id: Notification ID to retry

        Returns:
            True if retry scheduled, False otherwise
        """
        return self.queue.retry_failed(notification_id)

    def cancel_message(self, notification_id: str) -> bool:
        """Cancel a pending message.

        Args:
            notification_id: Notification ID to cancel

        Returns:
            True if cancelled, False otherwise
        """
        return self.queue.cancel_notification(notification_id)

    async def process_pending_messages(self, max_batch_size: int = 50) -> Dict[str, int]:
        """Process pending messages in the queue.

        Args:
            max_batch_size: Maximum messages to process in one batch

        Returns:
            Dictionary with processing statistics
        """
        return await self.queue.process_queue(max_batch_size=max_batch_size)


# Singleton instance
_whatsapp_queue_instance: Optional[WhatsAppMessageQueue] = None


def get_whatsapp_queue(db_path: Optional[str] = None) -> WhatsAppMessageQueue:
    """Get singleton WhatsApp message queue instance.

    Args:
        db_path: Path to database (optional)

    Returns:
        WhatsApp message queue instance
    """
    global _whatsapp_queue_instance

    if _whatsapp_queue_instance is None:
        _whatsapp_queue_instance = WhatsAppMessageQueue(db_path=db_path)

    return _whatsapp_queue_instance
