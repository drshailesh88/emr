"""
Haptic Feedback System for DocAssist Mobile.

Provides tactile feedback for user interactions.
Enhances the premium feel of the app.

Note: Flet's HapticFeedback support varies by platform.
This module provides a consistent API with graceful fallbacks.
"""

import flet as ft
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class HapticType(Enum):
    """
    Types of haptic feedback.
    Mapped to platform-specific implementations.
    """
    # Light tap (selection, navigation)
    LIGHT = "light"

    # Medium impact (button press, toggle)
    MEDIUM = "medium"

    # Heavy impact (important action, error)
    HEAVY = "heavy"

    # Selection change (picker, segmented control)
    SELECTION = "selection"

    # Success feedback (save, sync complete)
    SUCCESS = "success"

    # Warning feedback (validation error)
    WARNING = "warning"

    # Error feedback (action failed)
    ERROR = "error"


class HapticFeedback:
    """
    Main haptic feedback controller.

    Usage:
        haptics = HapticFeedback(page)
        haptics.light()  # Light tap
        haptics.success()  # Success vibration
    """

    def __init__(self, page: Optional[ft.Page] = None):
        self.page = page
        self._enabled = True
        self._haptics_available = self._check_haptics_available()

    def _check_haptics_available(self) -> bool:
        """Check if haptics are available on this platform."""
        if not self.page:
            return False

        # Check platform
        # Flet supports haptics on mobile platforms
        # For now, we'll assume it's available and handle errors gracefully
        return True

    def _trigger(self, haptic_type: HapticType):
        """
        Trigger haptic feedback.

        Args:
            haptic_type: Type of haptic feedback to trigger
        """
        if not self._enabled or not self._haptics_available:
            return

        try:
            # Flet's haptic feedback API
            # Note: As of Flet's current version, haptic feedback might need
            # to be implemented via platform channels or may have limited support

            # For now, we'll use page.vibrate if available
            if hasattr(self.page, 'vibrate'):
                duration = self._get_vibration_duration(haptic_type)
                if duration > 0:
                    self.page.vibrate(duration)
            else:
                # Log that haptics aren't available
                logger.debug(f"Haptic feedback not available: {haptic_type.value}")

        except Exception as e:
            logger.warning(f"Failed to trigger haptic feedback: {e}")

    def _get_vibration_duration(self, haptic_type: HapticType) -> int:
        """
        Get vibration duration in milliseconds for each haptic type.

        Args:
            haptic_type: Type of haptic feedback

        Returns:
            Duration in milliseconds
        """
        durations = {
            HapticType.LIGHT: 10,
            HapticType.MEDIUM: 20,
            HapticType.HEAVY: 30,
            HapticType.SELECTION: 5,
            HapticType.SUCCESS: 15,
            HapticType.WARNING: 25,
            HapticType.ERROR: 40,
        }
        return durations.get(haptic_type, 15)

    def light(self):
        """Light haptic feedback (tap, hover, selection)."""
        self._trigger(HapticType.LIGHT)

    def medium(self):
        """Medium haptic feedback (button press, toggle)."""
        self._trigger(HapticType.MEDIUM)

    def heavy(self):
        """Heavy haptic feedback (important action, long press)."""
        self._trigger(HapticType.HEAVY)

    def selection(self):
        """Selection change haptic (picker scroll, tab switch)."""
        self._trigger(HapticType.SELECTION)

    def success(self):
        """Success haptic (save complete, sync success)."""
        self._trigger(HapticType.SUCCESS)

    def warning(self):
        """Warning haptic (validation issue, caution)."""
        self._trigger(HapticType.WARNING)

    def error(self):
        """Error haptic (action failed, critical error)."""
        self._trigger(HapticType.ERROR)

    def enable(self):
        """Enable haptic feedback."""
        self._enabled = True

    def disable(self):
        """Disable haptic feedback."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if haptic feedback is enabled."""
        return self._enabled

    def toggle(self):
        """Toggle haptic feedback on/off."""
        self._enabled = not self._enabled


class HapticButton(ft.Container):
    """
    Button with automatic haptic feedback on tap.

    Usage:
        button = HapticButton(
            content=ft.Text("Save"),
            on_click=handle_save,
            haptic_type=HapticType.MEDIUM,
        )
    """

    def __init__(
        self,
        *args,
        haptic_feedback: Optional[HapticFeedback] = None,
        haptic_type: HapticType = HapticType.MEDIUM,
        **kwargs,
    ):
        self.haptic_feedback = haptic_feedback
        self.haptic_type = haptic_type
        self._original_on_click = kwargs.get('on_click')

        # Override on_click to add haptic
        if self._original_on_click:
            kwargs['on_click'] = self._haptic_click

        super().__init__(*args, **kwargs)

    def _haptic_click(self, e):
        """Handle click with haptic feedback."""
        # Trigger haptic
        if self.haptic_feedback:
            self.haptic_feedback._trigger(self.haptic_type)

        # Call original handler
        if self._original_on_click:
            self._original_on_click(e)


class HapticSwitch(ft.Switch):
    """
    Switch with haptic feedback on toggle.

    Usage:
        switch = HapticSwitch(
            label="Dark Mode",
            on_change=handle_toggle,
            haptic_feedback=haptics,
        )
    """

    def __init__(
        self,
        *args,
        haptic_feedback: Optional[HapticFeedback] = None,
        **kwargs,
    ):
        self.haptic_feedback = haptic_feedback
        self._original_on_change = kwargs.get('on_change')

        # Override on_change to add haptic
        if self._original_on_change:
            kwargs['on_change'] = self._haptic_change

        super().__init__(*args, **kwargs)

    def _haptic_change(self, e):
        """Handle change with haptic feedback."""
        # Trigger haptic
        if self.haptic_feedback:
            self.haptic_feedback.selection()

        # Call original handler
        if self._original_on_change:
            self._original_on_change(e)


# Convenience functions for common haptic patterns

def with_haptic(
    control: ft.Control,
    haptic_feedback: HapticFeedback,
    haptic_type: HapticType = HapticType.MEDIUM,
) -> ft.Control:
    """
    Wrap a control to add haptic feedback on click.

    Args:
        control: The control to wrap
        haptic_feedback: HapticFeedback instance
        haptic_type: Type of haptic to trigger

    Returns:
        The same control with haptic feedback added

    Usage:
        button = with_haptic(
            ft.ElevatedButton("Save", on_click=save),
            haptics,
            HapticType.SUCCESS
        )
    """
    if hasattr(control, 'on_click'):
        original_handler = control.on_click

        def haptic_handler(e):
            haptic_feedback._trigger(haptic_type)
            if original_handler:
                original_handler(e)

        control.on_click = haptic_handler

    return control


def haptic_on_success(haptic_feedback: HapticFeedback):
    """
    Decorator to add success haptic to a function.

    Usage:
        @haptic_on_success(haptics)
        def save_data(e):
            # ... save logic ...
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            haptic_feedback.success()
            return result
        return wrapper
    return decorator


def haptic_on_error(haptic_feedback: HapticFeedback):
    """
    Decorator to add error haptic when function raises exception.

    Usage:
        @haptic_on_error(haptics)
        def risky_operation(e):
            # ... logic that might fail ...
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                haptic_feedback.error()
                raise
        return wrapper
    return decorator


# Export all haptic utilities
__all__ = [
    'HapticType',
    'HapticFeedback',
    'HapticButton',
    'HapticSwitch',
    'with_haptic',
    'haptic_on_success',
    'haptic_on_error',
]
