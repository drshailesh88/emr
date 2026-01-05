"""
Consultation Context Manager for maintaining state during clinical workflows.

Provides thread-safe access to consultation data and supports serialization
for recovery scenarios.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


@dataclass
class ConsultationContext:
    """
    Context for a single consultation session.

    Contains all relevant data for the current clinical interaction.
    """

    # Consultation identifiers
    consultation_id: str
    patient_id: int
    doctor_id: str
    started_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Patient information
    patient_data: Dict[str, Any] = field(default_factory=dict)
    patient_timeline: List[Dict[str, Any]] = field(default_factory=list)

    # Current visit data
    visit_id: Optional[int] = None
    chief_complaint: str = ""
    clinical_notes: str = ""
    diagnosis: List[str] = field(default_factory=list)

    # Speech/transcription data
    transcription_buffer: List[str] = field(default_factory=list)
    audio_segments: List[bytes] = field(default_factory=list)

    # Extracted clinical entities
    symptoms: List[str] = field(default_factory=list)
    medications_mentioned: List[str] = field(default_factory=list)
    investigations_mentioned: List[str] = field(default_factory=list)

    # Prescriptions
    current_prescription: Optional[Dict[str, Any]] = None
    medications: List[Dict[str, Any]] = field(default_factory=list)
    investigations_ordered: List[str] = field(default_factory=list)
    advice: List[str] = field(default_factory=list)
    follow_up: Optional[str] = None

    # Alerts and warnings
    active_alerts: List[Dict[str, Any]] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    drug_interactions: List[Dict[str, Any]] = field(default_factory=list)
    care_gaps: List[Dict[str, Any]] = field(default_factory=list)

    # Reminders
    pending_reminders: List[Dict[str, Any]] = field(default_factory=list)
    scheduled_reminders: List[Dict[str, Any]] = field(default_factory=list)

    # Workflow state
    workflow_state: str = "IDLE"
    is_active: bool = True
    is_saved: bool = False

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_timestamp(self) -> None:
        """Update the last modified timestamp."""
        self.updated_at = datetime.now()

    def add_transcription(self, text: str) -> None:
        """
        Add transcribed text to buffer.

        Args:
            text: Transcribed text
        """
        self.transcription_buffer.append(text)
        self.update_timestamp()

    def get_full_transcription(self) -> str:
        """
        Get complete transcription.

        Returns:
            Combined transcription text
        """
        return " ".join(self.transcription_buffer)

    def add_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add an alert to the consultation.

        Args:
            alert_type: Type of alert (e.g., "red_flag", "drug_interaction")
            severity: Severity level (e.g., "high", "medium", "low")
            message: Alert message
            metadata: Optional additional data
        """
        alert = {
            "type": alert_type,
            "severity": severity,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.active_alerts.append(alert)
        self.update_timestamp()

    def clear_alerts(self) -> None:
        """Clear all active alerts."""
        self.active_alerts.clear()
        self.update_timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize context to dictionary.

        Returns:
            Dictionary representation
        """
        data = asdict(self)

        # Convert datetimes to ISO format
        data["started_at"] = self.started_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()

        # Don't serialize audio segments (too large)
        data.pop("audio_segments", None)

        return data

    def to_json(self) -> str:
        """
        Serialize context to JSON.

        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConsultationContext":
        """
        Deserialize context from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ConsultationContext instance
        """
        # Convert ISO datetime strings back to datetime objects
        if isinstance(data.get("started_at"), str):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "ConsultationContext":
        """
        Deserialize context from JSON.

        Args:
            json_str: JSON string

        Returns:
            ConsultationContext instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


class ContextManager:
    """
    Manager for consultation contexts.

    Provides thread-safe access to the current consultation context
    and supports context switching for multi-consultation scenarios.
    """

    _instance: Optional["ContextManager"] = None
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
        """Initialize the context manager on first creation."""
        if not self._initialized:
            self._current_context: Optional[ConsultationContext] = None
            self._context_history: Dict[str, ConsultationContext] = {}
            self._max_history_size = 100
            self._initialized = True
            logger.info("ContextManager initialized")

    def create_context(
        self,
        consultation_id: str,
        patient_id: int,
        doctor_id: str
    ) -> ConsultationContext:
        """
        Create a new consultation context.

        Args:
            consultation_id: Unique consultation identifier
            patient_id: Patient ID
            doctor_id: Doctor ID

        Returns:
            New ConsultationContext
        """
        with self._lock:
            context = ConsultationContext(
                consultation_id=consultation_id,
                patient_id=patient_id,
                doctor_id=doctor_id
            )

            self._current_context = context
            logger.info(f"Created consultation context: {consultation_id}")

            return context

    def get_current_context(self) -> Optional[ConsultationContext]:
        """
        Get the current consultation context.

        Returns:
            Current ConsultationContext or None
        """
        return self._current_context

    def set_current_context(self, context: ConsultationContext) -> None:
        """
        Set the current consultation context.

        Args:
            context: ConsultationContext to set as current
        """
        with self._lock:
            self._current_context = context
            logger.info(f"Set current context: {context.consultation_id}")

    def update_context(self, key: str, value: Any) -> None:
        """
        Update a field in the current context.

        Args:
            key: Field name
            value: New value

        Raises:
            ValueError: If no active context
        """
        if self._current_context is None:
            raise ValueError("No active consultation context")

        with self._lock:
            if hasattr(self._current_context, key):
                setattr(self._current_context, key, value)
                self._current_context.update_timestamp()
                logger.debug(f"Updated context field: {key}")
            else:
                # Store in metadata if not a known field
                self._current_context.metadata[key] = value
                self._current_context.update_timestamp()
                logger.debug(f"Updated context metadata: {key}")

    def save_context(self) -> None:
        """
        Save the current context to history.

        Raises:
            ValueError: If no active context
        """
        if self._current_context is None:
            raise ValueError("No active consultation context")

        with self._lock:
            consultation_id = self._current_context.consultation_id
            self._context_history[consultation_id] = self._current_context
            self._current_context.is_saved = True

            # Trim history if too large
            if len(self._context_history) > self._max_history_size:
                # Remove oldest entries
                oldest_keys = sorted(
                    self._context_history.keys(),
                    key=lambda k: self._context_history[k].updated_at
                )[:len(self._context_history) - self._max_history_size]

                for key in oldest_keys:
                    del self._context_history[key]

            logger.info(f"Saved consultation context: {consultation_id}")

    def close_context(self) -> None:
        """
        Close the current consultation context.

        Saves context to history and marks it as inactive.
        """
        if self._current_context is None:
            return

        with self._lock:
            self._current_context.is_active = False
            self.save_context()
            consultation_id = self._current_context.consultation_id
            self._current_context = None

            logger.info(f"Closed consultation context: {consultation_id}")

    def load_context(self, consultation_id: str) -> Optional[ConsultationContext]:
        """
        Load a context from history.

        Args:
            consultation_id: Consultation ID

        Returns:
            ConsultationContext if found, None otherwise
        """
        context = self._context_history.get(consultation_id)

        if context:
            logger.info(f"Loaded context from history: {consultation_id}")

        return context

    def get_context_history(self, limit: int = 10) -> List[ConsultationContext]:
        """
        Get recent consultation contexts.

        Args:
            limit: Maximum number of contexts to return

        Returns:
            List of contexts (most recent first)
        """
        contexts = sorted(
            self._context_history.values(),
            key=lambda c: c.updated_at,
            reverse=True
        )
        return contexts[:limit]

    def clear_history(self) -> None:
        """Clear all context history."""
        with self._lock:
            self._context_history.clear()
            logger.info("Context history cleared")

    def reset(self) -> None:
        """
        Reset the context manager (primarily for testing).

        WARNING: This clears all contexts and history.
        """
        with self._lock:
            self._current_context = None
            self._context_history.clear()
            logger.warning("ContextManager reset")


# Global instance accessor
def get_context_manager() -> ContextManager:
    """Get the global context manager instance."""
    return ContextManager()


def get_current_context() -> Optional[ConsultationContext]:
    """
    Get the current consultation context (convenience function).

    Returns:
        Current ConsultationContext or None
    """
    return get_context_manager().get_current_context()
