"""
Pull-to-Refresh Component - Premium pull-to-refresh wrapper.

Provides smooth pull-to-refresh functionality with:
- Visual refresh indicator
- Haptic feedback
- Loading states
- Success/error animations
- DocAssist branding
"""

import flet as ft
from typing import Callable, Optional
from enum import Enum
import threading
import time

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..haptics import HapticFeedback, HapticType
from ..animations import Animations


class RefreshState(Enum):
    """Refresh states."""
    IDLE = "idle"
    PULLING = "pulling"
    THRESHOLD_REACHED = "threshold_reached"
    REFRESHING = "refreshing"
    SUCCESS = "success"
    ERROR = "error"


class PullToRefresh(ft.Container):
    """
    Pull-to-refresh wrapper for scrollable content.

    Usage:
        pull_refresh = PullToRefresh(
            content=my_list_view,
            on_refresh=handle_refresh,
            haptic_feedback=haptics,
        )
    """

    # Constants
    PULL_THRESHOLD = 80  # Pixels to pull before triggering refresh
    MAX_PULL_DISTANCE = 120  # Maximum pull distance (visual limit)

    def __init__(
        self,
        content: ft.Control,
        on_refresh: Optional[Callable] = None,
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.content_widget = content
        self.on_refresh = on_refresh
        self.haptic_feedback = haptic_feedback

        self.state = RefreshState.IDLE
        self._pull_distance = 0.0
        self._threshold_reached = False
        self._is_refreshing = False

        # Refresh indicator
        self.refresh_indicator = ft.Container(
            content=self._build_indicator(),
            height=0,
            opacity=0,
            alignment=ft.alignment.center,
            bgcolor=Colors.NEUTRAL_50,
            animate_opacity=200,
            animate_size=200,
        )

        # Main content with gesture detector
        self.scroll_container = ft.GestureDetector(
            content=self.content_widget,
            on_vertical_drag_start=self._on_drag_start,
            on_vertical_drag_update=self._on_drag_update,
            on_vertical_drag_end=self._on_drag_end,
        )

        # Build layout
        layout = ft.Column(
            [
                self.refresh_indicator,
                ft.Container(
                    content=self.scroll_container,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

        super().__init__(
            content=layout,
            expand=True,
        )

    def _build_indicator(self) -> ft.Control:
        """Build the refresh indicator content."""
        return ft.Column(
            [
                ft.ProgressRing(
                    width=24,
                    height=24,
                    stroke_width=2.5,
                    color=Colors.PRIMARY_500,
                ),
                ft.Container(height=4),
                ft.Text(
                    "Syncing...",
                    size=MobileTypography.CAPTION,
                    color=Colors.NEUTRAL_600,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )

    def _on_drag_start(self, e: ft.DragStartEvent):
        """Handle drag start."""
        # Only allow pull-to-refresh if scrolled to top
        # Note: Flet's scroll position tracking may be limited
        # This is a simplified implementation
        if self._is_refreshing:
            return

        self.state = RefreshState.PULLING
        self._threshold_reached = False

    def _on_drag_update(self, e: ft.DragUpdateEvent):
        """Handle drag update."""
        if self._is_refreshing or self.state == RefreshState.IDLE:
            return

        # Calculate pull distance (only downward pulls)
        if e.delta_y > 0:
            self._pull_distance = min(
                self._pull_distance + e.delta_y * 0.5,  # Damping factor
                self.MAX_PULL_DISTANCE
            )

        # Update indicator height and opacity
        indicator_height = min(self._pull_distance, self.MAX_PULL_DISTANCE)
        opacity = min(self._pull_distance / self.PULL_THRESHOLD, 1.0)

        self.refresh_indicator.height = indicator_height
        self.refresh_indicator.opacity = opacity

        # Check threshold
        if self._pull_distance >= self.PULL_THRESHOLD and not self._threshold_reached:
            self._threshold_reached = True
            self.state = RefreshState.THRESHOLD_REACHED

            # Haptic feedback when threshold reached
            if self.haptic_feedback:
                self.haptic_feedback.light()

            # Update indicator text
            self._update_indicator_text("Release to sync")

        self.refresh_indicator.update()

    def _on_drag_end(self, e: ft.DragEndEvent):
        """Handle drag end."""
        if self._is_refreshing:
            return

        # Trigger refresh if threshold was reached
        if self._threshold_reached:
            self._start_refresh()
        else:
            # Reset to idle
            self._reset_indicator()

    def _start_refresh(self):
        """Start the refresh process."""
        self._is_refreshing = True
        self.state = RefreshState.REFRESHING

        # Set indicator to refreshing state
        self.refresh_indicator.height = 60
        self.refresh_indicator.opacity = 1.0
        self._update_indicator_text("Syncing...")
        self.refresh_indicator.update()

        # Trigger haptic feedback
        if self.haptic_feedback:
            self.haptic_feedback.medium()

        # Call refresh callback
        if self.on_refresh:
            # Run in thread to avoid blocking
            def do_refresh():
                try:
                    self.on_refresh()
                except Exception as e:
                    print(f"Refresh error: {e}")
                    # Show error state briefly
                    if hasattr(self, 'page') and self.page:
                        self.page.run_task(lambda: self._show_error())

            threading.Thread(target=do_refresh, daemon=True).start()

    def complete_refresh(self, success: bool = True):
        """
        Complete the refresh operation.

        Args:
            success: Whether the refresh was successful
        """
        if not self._is_refreshing:
            return

        if success:
            self._show_success()
        else:
            self._show_error()

    def _show_success(self):
        """Show success state."""
        self.state = RefreshState.SUCCESS

        # Update indicator
        self._update_indicator_content(
            ft.Column(
                [
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE,
                        size=24,
                        color=Colors.SUCCESS_MAIN,
                    ),
                    ft.Container(height=4),
                    ft.Text(
                        "Synced",
                        size=MobileTypography.CAPTION,
                        color=Colors.SUCCESS_MAIN,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            )
        )

        # Haptic feedback
        if self.haptic_feedback:
            self.haptic_feedback.success()

        # Auto-hide after delay
        def hide_after_delay():
            time.sleep(0.8)
            if hasattr(self, 'page') and self.page:
                self.page.run_task(lambda: self._reset_indicator())

        threading.Thread(target=hide_after_delay, daemon=True).start()

    def _show_error(self):
        """Show error state."""
        self.state = RefreshState.ERROR

        # Update indicator
        self._update_indicator_content(
            ft.Column(
                [
                    ft.Icon(
                        ft.Icons.ERROR_OUTLINE,
                        size=24,
                        color=Colors.ERROR_MAIN,
                    ),
                    ft.Container(height=4),
                    ft.Text(
                        "Sync failed",
                        size=MobileTypography.CAPTION,
                        color=Colors.ERROR_MAIN,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            )
        )

        # Haptic feedback
        if self.haptic_feedback:
            self.haptic_feedback.error()

        # Auto-hide after delay
        def hide_after_delay():
            time.sleep(1.2)
            if hasattr(self, 'page') and self.page:
                self.page.run_task(lambda: self._reset_indicator())

        threading.Thread(target=hide_after_delay, daemon=True).start()

    def _reset_indicator(self):
        """Reset indicator to idle state."""
        self._is_refreshing = False
        self._pull_distance = 0
        self._threshold_reached = False
        self.state = RefreshState.IDLE

        # Animate out
        self.refresh_indicator.height = 0
        self.refresh_indicator.opacity = 0
        self.refresh_indicator.update()

        # Reset content after animation
        def reset_content():
            time.sleep(0.3)
            if hasattr(self, 'page') and self.page:
                self.page.run_task(lambda: self._update_indicator_content(self._build_indicator()))

        threading.Thread(target=reset_content, daemon=True).start()

    def _update_indicator_text(self, text: str):
        """Update the indicator text."""
        if isinstance(self.refresh_indicator.content, ft.Column):
            for control in self.refresh_indicator.content.controls:
                if isinstance(control, ft.Text):
                    control.value = text
                    break
        self.refresh_indicator.update()

    def _update_indicator_content(self, new_content: ft.Control):
        """Update the entire indicator content."""
        self.refresh_indicator.content = new_content
        self.refresh_indicator.update()

    def trigger_refresh(self):
        """Programmatically trigger a refresh."""
        if not self._is_refreshing:
            self._threshold_reached = True
            self._start_refresh()


class PullToRefreshList(PullToRefresh):
    """
    Convenience wrapper for ListView with pull-to-refresh.

    Usage:
        refresh_list = PullToRefreshList(
            on_refresh=handle_refresh,
            haptic_feedback=haptics,
            spacing=8,
            padding=16,
        )
        refresh_list.add_item(patient_card)
    """

    def __init__(
        self,
        on_refresh: Optional[Callable] = None,
        haptic_feedback: Optional[HapticFeedback] = None,
        spacing: int = 8,
        padding: int = 16,
    ):
        # Create ListView
        self.list_view = ft.ListView(
            spacing=spacing,
            padding=padding,
            expand=True,
        )

        super().__init__(
            content=self.list_view,
            on_refresh=on_refresh,
            haptic_feedback=haptic_feedback,
        )

    def add_item(self, item: ft.Control):
        """Add an item to the list."""
        self.list_view.controls.append(item)

    def clear_items(self):
        """Clear all items from the list."""
        self.list_view.controls.clear()

    def set_items(self, items: list):
        """Set list items."""
        self.list_view.controls = items
        self.list_view.update()


# Export components
__all__ = [
    'PullToRefresh',
    'PullToRefreshList',
    'RefreshState',
]
