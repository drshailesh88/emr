"""
Sync Status Bar - Shows sync status and pending changes.

Displays:
- Pending changes count
- Sync progress
- Error states
- Manual sync trigger
- Dismissable banner
"""

import flet as ft
from typing import Callable, Optional
from enum import Enum

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..haptics import HapticFeedback


class StatusBarType(Enum):
    """Status bar types."""
    INFO = "info"
    SYNCING = "syncing"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class SyncStatusBar(ft.Container):
    """
    Sync status banner shown at top of screen.

    Usage:
        status_bar = SyncStatusBar(
            pending_count=5,
            on_sync=handle_sync,
            on_dismiss=handle_dismiss,
        )
    """

    def __init__(
        self,
        pending_count: int = 0,
        is_syncing: bool = False,
        error_message: Optional[str] = None,
        on_sync: Optional[Callable] = None,
        on_dismiss: Optional[Callable] = None,
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.pending_count = pending_count
        self.is_syncing = is_syncing
        self.error_message = error_message
        self.on_sync = on_sync
        self.on_dismiss = on_dismiss
        self.haptic_feedback = haptic_feedback
        self._visible = pending_count > 0 or is_syncing or error_message is not None

        # Build content
        content = self._build_content()

        super().__init__(
            content=content,
            bgcolor=self._get_background_color(),
            padding=MobileSpacing.MD,
            visible=self._visible,
            animate_opacity=300,
            animate_size=300,
        )

    def _get_background_color(self) -> str:
        """Get background color based on state."""
        if self.error_message:
            return Colors.ERROR_LIGHT
        elif self.is_syncing:
            return Colors.PRIMARY_50
        elif self.pending_count > 0:
            return Colors.WARNING_MAIN + "20"  # Warning with 20% opacity
        else:
            return Colors.SUCCESS_LIGHT

    def _get_icon(self) -> ft.Icon:
        """Get icon based on state."""
        if self.error_message:
            return ft.Icon(
                ft.Icons.ERROR_OUTLINE,
                size=20,
                color=Colors.ERROR_MAIN,
            )
        elif self.is_syncing:
            return ft.ProgressRing(
                width=20,
                height=20,
                stroke_width=2,
                color=Colors.PRIMARY_500,
            )
        elif self.pending_count > 0:
            return ft.Icon(
                ft.Icons.CLOUD_UPLOAD,
                size=20,
                color=Colors.WARNING_MAIN,
            )
        else:
            return ft.Icon(
                ft.Icons.CHECK_CIRCLE,
                size=20,
                color=Colors.SUCCESS_MAIN,
            )

    def _get_message(self) -> str:
        """Get message based on state."""
        if self.error_message:
            return self.error_message
        elif self.is_syncing:
            return "Syncing changes..."
        elif self.pending_count > 0:
            return f"{self.pending_count} change{'s' if self.pending_count != 1 else ''} pending sync"
        else:
            return "All changes synced"

    def _build_content(self) -> ft.Control:
        """Build status bar content."""
        message_text = ft.Text(
            self._get_message(),
            size=MobileTypography.BODY_SMALL,
            color=Colors.NEUTRAL_900,
            weight=ft.FontWeight.W_500,
        )

        icon = self._get_icon()

        # Action button (sync or dismiss)
        action_button = None
        if self.error_message or self.pending_count > 0:
            # Show sync button
            action_button = ft.IconButton(
                icon=ft.Icons.SYNC,
                icon_size=20,
                tooltip="Sync now",
                on_click=self._handle_sync,
                icon_color=Colors.PRIMARY_500,
            )
        else:
            # Show dismiss button
            action_button = ft.IconButton(
                icon=ft.Icons.CLOSE,
                icon_size=20,
                tooltip="Dismiss",
                on_click=self._handle_dismiss,
                icon_color=Colors.NEUTRAL_600,
            )

        return ft.Row(
            [
                icon,
                ft.Container(width=MobileSpacing.SM),
                ft.Container(
                    content=message_text,
                    expand=True,
                ),
                action_button,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _handle_sync(self, e):
        """Handle sync button click."""
        if self.haptic_feedback:
            self.haptic_feedback.medium()

        if self.on_sync:
            self.on_sync()

    def _handle_dismiss(self, e):
        """Handle dismiss button click."""
        if self.haptic_feedback:
            self.haptic_feedback.light()

        self.hide()

        if self.on_dismiss:
            self.on_dismiss()

    def update_status(
        self,
        pending_count: Optional[int] = None,
        is_syncing: Optional[bool] = None,
        error_message: Optional[str] = None,
    ):
        """
        Update status bar state.

        Args:
            pending_count: Number of pending changes
            is_syncing: Whether sync is in progress
            error_message: Error message to display
        """
        if pending_count is not None:
            self.pending_count = pending_count

        if is_syncing is not None:
            self.is_syncing = is_syncing

        if error_message is not None:
            self.error_message = error_message

        # Update visibility
        self._visible = self.pending_count > 0 or self.is_syncing or self.error_message is not None

        # Rebuild content
        self.content = self._build_content()
        self.bgcolor = self._get_background_color()
        self.visible = self._visible
        self.update()

    def show(self):
        """Show status bar."""
        self._visible = True
        self.visible = True
        self.opacity = 1.0
        self.update()

    def hide(self):
        """Hide status bar."""
        self._visible = False
        self.visible = False
        self.opacity = 0
        self.update()

    def set_syncing(self):
        """Set to syncing state."""
        self.update_status(is_syncing=True, error_message=None)

    def set_success(self, message: str = "Synced successfully"):
        """Set to success state."""
        self.update_status(
            pending_count=0,
            is_syncing=False,
            error_message=None
        )

        # Auto-hide after delay
        import threading
        import time

        def hide_after_delay():
            time.sleep(2)
            if hasattr(self, 'page') and self.page:
                self.page.run_task(lambda: self.hide())

        threading.Thread(target=hide_after_delay, daemon=True).start()

    def set_error(self, error_message: str):
        """Set to error state."""
        self.update_status(
            is_syncing=False,
            error_message=error_message
        )

    def set_pending(self, count: int):
        """Set pending changes count."""
        self.update_status(
            pending_count=count,
            is_syncing=False,
            error_message=None
        )


class CompactSyncStatus(ft.Container):
    """
    Compact sync status indicator for headers.

    Usage:
        status = CompactSyncStatus(
            pending_count=3,
            on_tap=handle_tap,
        )
    """

    def __init__(
        self,
        pending_count: int = 0,
        on_tap: Optional[Callable] = None,
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.pending_count = pending_count
        self.on_tap = on_tap
        self.haptic_feedback = haptic_feedback

        # Build content
        content = self._build_content()

        super().__init__(
            content=content,
            on_click=self._handle_tap,
            border_radius=Radius.FULL,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor=Colors.WARNING_MAIN + "20" if pending_count > 0 else "transparent",
        )

    def _build_content(self) -> ft.Control:
        """Build compact status content."""
        if self.pending_count > 0:
            return ft.Row(
                [
                    ft.Icon(
                        ft.Icons.CLOUD_UPLOAD,
                        size=16,
                        color=Colors.WARNING_MAIN,
                    ),
                    ft.Container(width=4),
                    ft.Text(
                        str(self.pending_count),
                        size=MobileTypography.CAPTION,
                        color=Colors.WARNING_MAIN,
                        weight=ft.FontWeight.W_600,
                    ),
                ],
                spacing=0,
            )
        else:
            return ft.Icon(
                ft.Icons.CLOUD_DONE,
                size=16,
                color=Colors.SUCCESS_MAIN,
            )

    def _handle_tap(self, e):
        """Handle tap."""
        if self.haptic_feedback:
            self.haptic_feedback.light()

        if self.on_tap:
            self.on_tap()

    def update_count(self, count: int):
        """Update pending count."""
        self.pending_count = count
        self.content = self._build_content()
        self.bgcolor = Colors.WARNING_MAIN + "20" if count > 0 else "transparent"
        self.update()


# Export components
__all__ = [
    'SyncStatusBar',
    'CompactSyncStatus',
    'StatusBarType',
]
