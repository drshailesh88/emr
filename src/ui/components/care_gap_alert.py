"""
Care Gap Alert Banner

Displays care gaps for preventive care, monitoring, and follow-ups.
"""

import flet as ft
from typing import Optional, Callable, List
from ...services.analytics.care_gap_detector import CareGap, CareGapPriority


class CareGapAlert(ft.UserControl):
    """
    Care gap alert banner for preventive care and monitoring reminders.

    Features:
    - Priority-based color coding (red=urgent, yellow=soon, blue=routine)
    - Shows care gap description and recommendation
    - Dismissible with reason
    - Click to create order/reminder
    - Time-based prioritization
    """

    def __init__(
        self,
        on_action_clicked: Optional[Callable[[CareGap], None]] = None,
        on_dismissed: Optional[Callable[[CareGap, str], None]] = None,
        is_dark: bool = False,
    ):
        """Initialize care gap alert.

        Args:
            on_action_clicked: Callback when action button is clicked (e.g., create order)
            on_dismissed: Callback when gap is dismissed (gap, reason)
            is_dark: Whether dark mode is active
        """
        super().__init__()
        self.on_action_clicked = on_action_clicked
        self.on_dismissed = on_dismissed
        self.is_dark = is_dark

        self.care_gaps: List[CareGap] = []
        self.container: Optional[ft.Container] = None
        self.alerts_column: Optional[ft.Column] = None

    def build(self):
        """Build the care gap alert UI."""
        self.alerts_column = ft.Column(
            controls=[],
            spacing=10,
        )

        self.container = ft.Container(
            content=self.alerts_column,
            visible=False,
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )

        return self.container

    def show_care_gaps(self, care_gaps: List[CareGap]):
        """Show care gap alerts.

        Args:
            care_gaps: List of CareGap objects from CareGapDetector
        """
        self.care_gaps = care_gaps
        self._rebuild_alerts()

        if self.container:
            self.container.visible = len(care_gaps) > 0
            if self.page:
                self.container.update()

    def _rebuild_alerts(self):
        """Rebuild alert content with current care gaps."""
        if not self.alerts_column:
            return

        self.alerts_column.controls.clear()

        # Group by priority
        urgent_gaps = [g for g in self.care_gaps if g.priority == CareGapPriority.URGENT]
        soon_gaps = [g for g in self.care_gaps if g.priority == CareGapPriority.SOON]
        routine_gaps = [g for g in self.care_gaps if g.priority == CareGapPriority.ROUTINE]

        # Show urgent first, then soon, then routine
        for gap in urgent_gaps + soon_gaps + routine_gaps:
            alert = self._create_care_gap_alert(gap)
            self.alerts_column.controls.append(alert)

        if self.page:
            self.alerts_column.update()

    def _create_care_gap_alert(self, gap: CareGap) -> ft.Control:
        """Create an alert for a single care gap.

        Args:
            gap: CareGap object

        Returns:
            Flet control for the alert
        """
        # Get colors based on priority
        bg_color, border_color, icon_color, text_color = self._get_priority_colors(gap.priority)

        # Priority indicator
        priority_text = {
            CareGapPriority.URGENT: "🔴 URGENT",
            CareGapPriority.SOON: "🟡 DUE SOON",
            CareGapPriority.ROUTINE: "🔵 ROUTINE",
        }.get(gap.priority, "ℹ️ REMINDER")

        # Icon based on category
        category_icon = {
            "preventive": ft.Icons.HEALTH_AND_SAFETY,
            "monitoring": ft.Icons.MONITOR_HEART,
            "follow_up": ft.Icons.EVENT,
        }.get(gap.category, ft.Icons.INFO)

        # Build content rows
        content_rows = [
            # Title row with priority
            ft.Row([
                ft.Container(
                    content=ft.Text(
                        priority_text,
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    bgcolor=icon_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    border_radius=4,
                ),
                ft.Text(
                    gap.description,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=text_color,
                ),
            ], spacing=8),
        ]

        # Recommendation
        content_rows.append(
            ft.Row([
                ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=14, color=icon_color),
                ft.Text(
                    gap.recommendation,
                    size=12,
                    color=text_color,
                ),
            ], spacing=6)
        )

        # Days overdue (if applicable)
        if gap.days_overdue and gap.days_overdue > 0:
            content_rows.append(
                ft.Row([
                    ft.Icon(ft.Icons.TIMER_OFF, size=14, color=ft.Colors.RED_700),
                    ft.Text(
                        f"⏱️ {gap.days_overdue} days overdue",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_700,
                    ),
                ], spacing=6)
            )

        # Last done date
        if gap.last_done_date:
            content_rows.append(
                ft.Text(
                    f"Last done: {gap.last_done_date}",
                    size=10,
                    italic=True,
                    color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                )
            )

        # Details
        if gap.details:
            content_rows.append(
                ft.Text(
                    gap.details,
                    size=10,
                    italic=True,
                    color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                )
            )

        # Action buttons
        action_row = ft.Row([
            ft.TextButton(
                text=self._get_action_button_text(gap.action_type),
                icon=self._get_action_icon(gap.action_type),
                on_click=lambda e, g=gap: self._on_action_click(g),
                style=ft.ButtonStyle(
                    color=icon_color,
                ),
            ),
            ft.TextButton(
                text="Dismiss",
                icon=ft.Icons.CLOSE,
                on_click=lambda e, g=gap: self._show_dismiss_dialog(g),
                style=ft.ButtonStyle(
                    color=ft.Colors.GREY_600,
                ),
            ),
        ], spacing=5)

        # Create alert container
        return ft.Container(
            content=ft.Row([
                # Category icon
                ft.Container(
                    content=ft.Icon(
                        category_icon,
                        size=32,
                        color=icon_color,
                    ),
                    padding=10,
                ),
                # Content
                ft.Container(
                    content=ft.Column([
                        ft.Column(
                            content_rows,
                            spacing=6,
                        ),
                        action_row,
                    ], spacing=8),
                    expand=True,
                    padding=ft.padding.only(top=10, bottom=10, right=10),
                ),
            ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
            bgcolor=bg_color,
            border=ft.border.all(2, border_color),
            border_radius=8,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.2, border_color),
                offset=ft.Offset(0, 2),
            ),
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
        )

    def _get_priority_colors(self, priority: CareGapPriority) -> tuple:
        """Get colors for priority level.

        Args:
            priority: CareGapPriority enum

        Returns:
            Tuple of (bg_color, border_color, icon_color, text_color)
        """
        if priority == CareGapPriority.URGENT:
            if self.is_dark:
                return ("#3D1414", ft.Colors.RED_700, ft.Colors.RED_500, ft.Colors.RED_100)
            else:
                return ("#FFEBEE", ft.Colors.RED_600, ft.Colors.RED_700, ft.Colors.RED_900)

        elif priority == CareGapPriority.SOON:
            if self.is_dark:
                return ("#3D2E14", ft.Colors.ORANGE_700, ft.Colors.ORANGE_500, ft.Colors.ORANGE_100)
            else:
                return ("#FFF8E1", ft.Colors.ORANGE_600, ft.Colors.ORANGE_700, ft.Colors.ORANGE_900)

        else:  # ROUTINE
            if self.is_dark:
                return ("#14233D", ft.Colors.BLUE_700, ft.Colors.BLUE_500, ft.Colors.BLUE_100)
            else:
                return ("#E3F2FD", ft.Colors.BLUE_600, ft.Colors.BLUE_700, ft.Colors.BLUE_900)

    def _get_action_button_text(self, action_type: str) -> str:
        """Get action button text based on action type.

        Args:
            action_type: Action type (order, reminder, schedule)

        Returns:
            Button text
        """
        return {
            "order": "Create Order",
            "reminder": "Set Reminder",
            "schedule": "Schedule",
        }.get(action_type, "Take Action")

    def _get_action_icon(self, action_type: str):
        """Get action button icon based on action type.

        Args:
            action_type: Action type (order, reminder, schedule)

        Returns:
            Icon
        """
        return {
            "order": ft.Icons.ADD_TASK,
            "reminder": ft.Icons.ALARM_ADD,
            "schedule": ft.Icons.CALENDAR_MONTH,
        }.get(action_type, ft.Icons.ARROW_FORWARD)

    def _on_action_click(self, gap: CareGap):
        """Handle action button click.

        Args:
            gap: CareGap that was actioned
        """
        if self.on_action_clicked:
            self.on_action_clicked(gap)

    def _show_dismiss_dialog(self, gap: CareGap):
        """Show dialog to dismiss care gap with reason.

        Args:
            gap: CareGap to dismiss
        """
        if not self.page:
            return

        reason_field = ft.TextField(
            label="Reason for dismissing (optional)",
            hint_text="e.g., Already done elsewhere, Not applicable",
            multiline=True,
            min_lines=2,
            max_lines=3,
        )

        def dismiss_confirmed(e):
            reason = reason_field.value or "No reason provided"
            self._dismiss_care_gap(gap, reason)
            dialog.open = False
            if self.page:
                self.page.update()

        def cancel_dismiss(e):
            dialog.open = False
            if self.page:
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Dismiss Care Gap"),
            content=ft.Column([
                ft.Text(f"Dismissing: {gap.description}"),
                reason_field,
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_dismiss),
                ft.TextButton("Dismiss", on_click=dismiss_confirmed),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _dismiss_care_gap(self, gap: CareGap, reason: str):
        """Dismiss a care gap and remove from display.

        Args:
            gap: CareGap to dismiss
            reason: Reason for dismissal
        """
        # Remove from list
        if gap in self.care_gaps:
            self.care_gaps.remove(gap)

        # Rebuild alerts
        self._rebuild_alerts()

        # Hide container if no more care gaps
        if not self.care_gaps and self.container:
            self.container.visible = False

        # Callback
        if self.on_dismissed:
            self.on_dismissed(gap, reason)

        # Log dismissal
        self._log_dismissal(gap, reason)

        if self.page:
            self.update()

    def _log_dismissal(self, gap: CareGap, reason: str):
        """Log care gap dismissal for audit trail.

        Args:
            gap: CareGap that was dismissed
            reason: Reason for dismissal
        """
        from datetime import datetime

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "patient_id": gap.patient_id,
            "category": gap.category,
            "description": gap.description,
            "priority": gap.priority.value,
            "action": "dismissed",
            "reason": reason,
        }

        # TODO: Save to audit database
        print(f"[AUDIT] Care gap dismissed: {log_entry}")

    def clear(self):
        """Clear all care gaps and hide alert."""
        self.care_gaps = []
        if self.alerts_column:
            self.alerts_column.controls.clear()
        if self.container:
            self.container.visible = False
        if self.page:
            self.update()
