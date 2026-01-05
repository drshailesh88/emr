"""Centralized state management for the DocAssist EMR application."""

import threading
from dataclasses import dataclass, field
from typing import Optional, List, Callable
import logging

from ..models.schemas import Patient, Visit, Prescription

logger = logging.getLogger(__name__)


@dataclass
class AppState:
    """Application state container."""
    current_patient: Optional[Patient] = None
    current_prescription: Optional[Prescription] = None
    patients: List[Patient] = field(default_factory=list)
    visits: List[Visit] = field(default_factory=list)
    is_loading: bool = False
    status_message: str = "Ready"
    status_error: bool = False


class StateManager:
    """Thread-safe state manager with listener pattern."""

    def __init__(self):
        self._state = AppState()
        self._lock = threading.Lock()
        self._listeners: List[Callable[[AppState], None]] = []
        logger.debug("StateManager initialized")

    def get_state(self) -> AppState:
        """Get a copy of the current state.

        Returns:
            AppState: The current application state
        """
        with self._lock:
            return self._state

    def update(self, **kwargs):
        """Update state attributes and notify listeners.

        Args:
            **kwargs: Attribute names and values to update
        """
        with self._lock:
            for key, value in kwargs.items():
                if not hasattr(self._state, key):
                    logger.warning(f"Attempted to update non-existent state attribute: {key}")
                    continue
                setattr(self._state, key, value)
                logger.debug(f"State updated: {key}={value}")

        self._notify_listeners()

    def add_listener(self, callback: Callable[[AppState], None]):
        """Add a state change listener.

        Args:
            callback: Function to call when state changes
        """
        if callback not in self._listeners:
            self._listeners.append(callback)
            logger.debug(f"Listener added: {callback.__name__}")

    def remove_listener(self, callback: Callable[[AppState], None]):
        """Remove a state change listener.

        Args:
            callback: Listener to remove
        """
        if callback in self._listeners:
            self._listeners.remove(callback)
            logger.debug(f"Listener removed: {callback.__name__}")

    def _notify_listeners(self):
        """Notify all listeners of state changes."""
        state_copy = self.get_state()
        for listener in self._listeners:
            try:
                listener(state_copy)
            except Exception as e:
                logger.error(f"Error in state listener {listener.__name__}: {e}", exc_info=True)

    def get_current_patient(self) -> Optional[Patient]:
        """Convenience method to get current patient.

        Returns:
            Optional[Patient]: The currently selected patient
        """
        with self._lock:
            return self._state.current_patient

    def get_current_prescription(self) -> Optional[Prescription]:
        """Convenience method to get current prescription.

        Returns:
            Optional[Prescription]: The current prescription
        """
        with self._lock:
            return self._state.current_prescription

    def set_loading(self, is_loading: bool, message: str = ""):
        """Convenience method to set loading state.

        Args:
            is_loading: Whether the app is loading
            message: Optional status message
        """
        update_dict = {"is_loading": is_loading}
        if message:
            update_dict["status_message"] = message
        self.update(**update_dict)

    def set_status(self, message: str, error: bool = False):
        """Convenience method to set status message.

        Args:
            message: Status message to display
            error: Whether this is an error message
        """
        self.update(status_message=message, status_error=error)
