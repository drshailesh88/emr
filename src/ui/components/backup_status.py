"""Backup status indicator component for main app header.

Shows:
- Last backup time (e.g., "Last backup: 2 hours ago")
- Warning icon when no recent backup (>24 hours)
- Click to open full backup dialog
- Visual pulse/highlight when backup needed
"""

import flet as ft
from datetime import datetime, timedelta
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class BackupStatusIndicator(ft.UserControl):
    """Backup status indicator for app header."""

    def __init__(
        self,
        on_click: Optional[Callable] = None,
        warning_threshold_hours: int = 24,
    ):
        """Initialize backup status indicator.

        Args:
            on_click: Callback when indicator is clicked
            warning_threshold_hours: Show warning after this many hours
        """
        super().__init__()
        self.on_click_callback = on_click
        self.warning_threshold_hours = warning_threshold_hours
        self.last_backup_time: Optional[datetime] = None

        # UI elements
        self.status_text: Optional[ft.Text] = None
        self.status_icon: Optional[ft.Icon] = None
        self.container: Optional[ft.Container] = None

    def build(self):
        """Build the status indicator."""
        self.status_icon = ft.Icon(
            ft.Icons.BACKUP,
            size=18,
            color=ft.Colors.GREY_600,
        )

        self.status_text = ft.Text(
            "Checking backup...",
            size=12,
            color=ft.Colors.GREY_600,
        )

        self.container = ft.Container(
            content=ft.Row([
                self.status_icon,
                self.status_text,
            ], spacing=5, tight=True),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border_radius=5,
            bgcolor=ft.Colors.TRANSPARENT,
            on_click=self._on_click,
            tooltip="Click to manage backups",
            animate=ft.animation.Animation(300, "easeOut"),
        )

        return self.container

    def update_status(self, last_backup_time: Optional[datetime]):
        """Update the status indicator with last backup time.

        Args:
            last_backup_time: datetime of last backup, or None if no backups
        """
        self.last_backup_time = last_backup_time

        if not self.status_text or not self.status_icon or not self.container:
            return

        if last_backup_time is None:
            # No backup exists
            self.status_icon.name = ft.Icons.WARNING_AMBER
            self.status_icon.color = ft.Colors.ORANGE_700
            self.status_text.value = "No backup"
            self.status_text.color = ft.Colors.ORANGE_700
            self.container.bgcolor = ft.Colors.ORANGE_50
            self.container.tooltip = "Warning: No backup exists! Click to create one."
            logger.warning("No backup exists")

        else:
            # Calculate time since last backup
            now = datetime.now()
            delta = now - last_backup_time
            hours_ago = delta.total_seconds() / 3600

            if hours_ago < 1:
                # Less than 1 hour
                minutes_ago = int(delta.total_seconds() / 60)
                time_str = f"{minutes_ago} min ago" if minutes_ago > 0 else "Just now"
            elif hours_ago < 24:
                # Less than 24 hours
                time_str = f"{int(hours_ago)} hr ago"
            else:
                # More than 24 hours
                days_ago = int(hours_ago / 24)
                time_str = f"{days_ago} day{'s' if days_ago > 1 else ''} ago"

            self.status_text.value = f"Last backup: {time_str}"

            # Warning if backup is old
            if hours_ago > self.warning_threshold_hours:
                self.status_icon.name = ft.Icons.WARNING_AMBER
                self.status_icon.color = ft.Colors.ORANGE_700
                self.status_text.color = ft.Colors.ORANGE_700
                self.container.bgcolor = ft.Colors.ORANGE_50
                self.container.tooltip = f"Warning: Last backup was {time_str}. Click to create new backup."
                logger.warning(f"Last backup was {hours_ago:.1f} hours ago (threshold: {self.warning_threshold_hours})")
            else:
                self.status_icon.name = ft.Icons.BACKUP
                self.status_icon.color = ft.Colors.GREEN_700
                self.status_text.color = ft.Colors.GREEN_700
                self.container.bgcolor = ft.Colors.GREEN_50
                self.container.tooltip = f"Last backup: {time_str}. Click to manage backups."

        self.update()

    def _on_click(self, e):
        """Handle click event."""
        if self.on_click_callback:
            self.on_click_callback(e)

    def set_loading(self, message: str = "Backing up..."):
        """Show loading state.

        Args:
            message: Loading message to display
        """
        if not self.status_text or not self.status_icon or not self.container:
            return

        self.status_icon.name = ft.Icons.HOURGLASS_EMPTY
        self.status_icon.color = ft.Colors.BLUE_700
        self.status_text.value = message
        self.status_text.color = ft.Colors.BLUE_700
        self.container.bgcolor = ft.Colors.BLUE_50
        self.container.tooltip = "Backup in progress..."
        self.update()

    def set_error(self, message: str = "Backup failed"):
        """Show error state.

        Args:
            message: Error message to display
        """
        if not self.status_text or not self.status_icon or not self.container:
            return

        self.status_icon.name = ft.Icons.ERROR
        self.status_icon.color = ft.Colors.RED_700
        self.status_text.value = message
        self.status_text.color = ft.Colors.RED_700
        self.container.bgcolor = ft.Colors.RED_50
        self.container.tooltip = f"Error: {message}. Click to try again."
        self.update()

    def pulse_animation(self):
        """Trigger a pulse animation to draw attention."""
        if not self.container:
            return

        # Simple opacity animation
        original_opacity = self.container.opacity if self.container.opacity else 1.0

        def animate():
            if self.container:
                self.container.opacity = 0.5
                self.update()

                import time
                time.sleep(0.3)

                if self.container:
                    self.container.opacity = original_opacity
                    self.update()

        import threading
        threading.Thread(target=animate, daemon=True).start()
