"""Communications services for automated patient engagement."""

from .template_manager import TemplateManager, MessageTemplate
from .reminder_service import (
    ReminderService,
    Reminder,
    ReminderType,
    ReminderChannel,
    ReminderStatus
)
from .broadcast_service import (
    BroadcastService,
    DeliveryStats,
    Segment,
    Campaign,
    BroadcastType,
    BroadcastStatus
)
from .notification_queue import (
    NotificationQueue,
    Notification,
    QueueStatus,
    NotificationPriority,
    NotificationStatus
)

__all__ = [
    # Template Manager
    "TemplateManager",
    "MessageTemplate",

    # Reminder Service
    "ReminderService",
    "Reminder",
    "ReminderType",
    "ReminderChannel",
    "ReminderStatus",

    # Broadcast Service
    "BroadcastService",
    "DeliveryStats",
    "Segment",
    "Campaign",
    "BroadcastType",
    "BroadcastStatus",

    # Notification Queue
    "NotificationQueue",
    "Notification",
    "QueueStatus",
    "NotificationPriority",
    "NotificationStatus",
]
