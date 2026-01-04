"""
Event Bus for publish-subscribe messaging between services.

Enables loose coupling between components through event-driven architecture.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from threading import Lock


logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Standard event types in the clinical workflow."""

    # Consultation events
    CONSULTATION_STARTED = "consultation.started"
    CONSULTATION_COMPLETED = "consultation.completed"
    CONSULTATION_CANCELLED = "consultation.cancelled"

    # Speech/Input events
    SPEECH_DETECTED = "speech.detected"
    SPEECH_TRANSCRIBED = "speech.transcribed"
    CLINICAL_NOTE_UPDATED = "clinical_note.updated"

    # Prescription events
    PRESCRIPTION_CREATED = "prescription.created"
    PRESCRIPTION_MODIFIED = "prescription.modified"
    PRESCRIPTION_SENT = "prescription.sent"

    # Alert events
    ALERT_TRIGGERED = "alert.triggered"
    RED_FLAG_DETECTED = "red_flag.detected"
    DRUG_INTERACTION_DETECTED = "drug_interaction.detected"
    CARE_GAP_DETECTED = "care_gap.detected"

    # Patient events
    PATIENT_CREATED = "patient.created"
    PATIENT_UPDATED = "patient.updated"
    PATIENT_SEARCHED = "patient.searched"

    # Reminder events
    REMINDER_CREATED = "reminder.created"
    REMINDER_SENT = "reminder.sent"
    REMINDER_FAILED = "reminder.failed"

    # Analytics events
    METRIC_RECORDED = "metric.recorded"
    REPORT_GENERATED = "report.generated"

    # System events
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPED = "service.stopped"
    ERROR_OCCURRED = "error.occurred"


@dataclass
class Event:
    """
    Event object containing event data.

    Attributes:
        type: Event type
        data: Event payload
        timestamp: When event was created
        source: Optional source identifier
        correlation_id: Optional ID for event correlation
    """

    type: EventType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    correlation_id: Optional[str] = None

    def __str__(self) -> str:
        """String representation of event."""
        return f"Event({self.type}, source={self.source}, id={self.correlation_id})"


class EventBus:
    """
    Centralized event bus for publish-subscribe messaging.

    Supports both synchronous and asynchronous event handlers.
    """

    _instance: Optional["EventBus"] = None
    _lock = Lock()

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the event bus on first creation."""
        if not self._initialized:
            self._subscribers: Dict[EventType, List[Callable]] = {}
            self._event_history: List[Event] = []
            self._max_history_size = 1000
            self._initialized = True
            logger.info("EventBus initialized")

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], Any],
        priority: int = 0
    ) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to listen for
            handler: Callback function (sync or async)
            priority: Higher priority handlers run first (default: 0)
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            # Store handler with priority
            self._subscribers[event_type].append((priority, handler))

            # Sort by priority (descending)
            self._subscribers[event_type].sort(key=lambda x: x[0], reverse=True)

            logger.info(f"Subscribed to {event_type}: {handler.__name__}")

    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Event type
            handler: Handler to remove
        """
        with self._lock:
            if event_type in self._subscribers:
                self._subscribers[event_type] = [
                    (p, h) for p, h in self._subscribers[event_type]
                    if h != handler
                ]
                logger.info(f"Unsubscribed from {event_type}: {handler.__name__}")

    async def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event_type: Type of event
            data: Event payload
            source: Optional source identifier
            correlation_id: Optional correlation ID
        """
        event = Event(
            type=event_type,
            data=data,
            source=source,
            correlation_id=correlation_id
        )

        # Add to history
        self._add_to_history(event)

        # Get subscribers
        subscribers = self._subscribers.get(event_type, [])

        logger.info(f"Publishing event: {event} to {len(subscribers)} subscribers")

        # Call handlers
        for priority, handler in subscribers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler {handler.__name__} for {event_type}: {e}",
                    exc_info=True
                )

    def publish_sync(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Publish an event synchronously (for non-async contexts).

        Args:
            event_type: Type of event
            data: Event payload
            source: Optional source identifier
            correlation_id: Optional correlation ID
        """
        event = Event(
            type=event_type,
            data=data,
            source=source,
            correlation_id=correlation_id
        )

        # Add to history
        self._add_to_history(event)

        # Get subscribers (only sync ones)
        subscribers = self._subscribers.get(event_type, [])

        logger.info(f"Publishing sync event: {event} to {len(subscribers)} subscribers")

        for priority, handler in subscribers:
            if asyncio.iscoroutinefunction(handler):
                logger.warning(
                    f"Skipping async handler {handler.__name__} in sync publish"
                )
                continue

            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler {handler.__name__} for {event_type}: {e}",
                    exc_info=True
                )

    def _add_to_history(self, event: Event) -> None:
        """
        Add event to history.

        Args:
            event: Event to add
        """
        with self._lock:
            self._event_history.append(event)

            # Trim history if too large
            if len(self._event_history) > self._max_history_size:
                self._event_history = self._event_history[-self._max_history_size:]

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get event history.

        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return

        Returns:
            List of events (most recent first)
        """
        with self._lock:
            events = self._event_history.copy()

        # Filter by type if specified
        if event_type:
            events = [e for e in events if e.type == event_type]

        # Return most recent first
        return list(reversed(events[-limit:]))

    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._event_history.clear()
            logger.info("Event history cleared")

    def get_subscriber_count(self, event_type: EventType) -> int:
        """
        Get number of subscribers for an event type.

        Args:
            event_type: Event type

        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_type, []))

    def reset(self) -> None:
        """
        Reset the event bus (primarily for testing).

        WARNING: This clears all subscribers and history.
        """
        with self._lock:
            self._subscribers.clear()
            self._event_history.clear()
            logger.warning("EventBus reset")


# Global instance accessor
def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    return EventBus()
