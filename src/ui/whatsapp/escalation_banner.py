"""Escalation banner for urgent patient messages"""
import flet as ft
from typing import Callable, Optional
from datetime import datetime


class EscalationBanner(ft.UserControl):
    """Banner displayed when patient message needs doctor attention"""

    def __init__(
        self,
        message_id: str,
        patient_name: str,
        patient_id: int,
        urgency: str = "medium",  # low, medium, high, emergency
        reason: str = "",
        message_content: str = "",
        detected_symptoms: Optional[list] = None,
        timestamp: Optional[datetime] = None,
        on_call: Optional[Callable] = None,
        on_view_history: Optional[Callable] = None,
        on_respond: Optional[Callable] = None,
        on_dismiss: Optional[Callable] = None,
        is_dark: bool = False,
    ):
        super().__init__()
        self.message_id = message_id
        self.patient_name = patient_name
        self.patient_id = patient_id
        self.urgency = urgency
        self.reason = reason
        self.message_content = message_content
        self.detected_symptoms = detected_symptoms or []
        self.timestamp = timestamp or datetime.now()
        self.on_call = on_call
        self.on_view_history = on_view_history
        self.on_respond = on_respond
        self.on_dismiss = on_dismiss
        self.is_dark = is_dark

    def _get_urgency_config(self) -> dict:
        """Get colors and icons based on urgency level"""
        configs = {
            "emergency": {
                "color": ft.Colors.RED_700 if not self.is_dark else ft.Colors.RED_400,
                "bg_color": ft.Colors.RED_50 if not self.is_dark else "#4A1B1B",
                "border_color": ft.Colors.RED_400 if not self.is_dark else ft.Colors.RED_600,
                "icon": ft.Icons.EMERGENCY_ROUNDED,
                "label": "EMERGENCY",
                "pulse": True,
            },
            "high": {
                "color": ft.Colors.ORANGE_700 if not self.is_dark else ft.Colors.ORANGE_400,
                "bg_color": ft.Colors.ORANGE_50 if not self.is_dark else "#4A3318",
                "border_color": ft.Colors.ORANGE_400 if not self.is_dark else ft.Colors.ORANGE_600,
                "icon": ft.Icons.PRIORITY_HIGH_ROUNDED,
                "label": "HIGH PRIORITY",
                "pulse": False,
            },
            "medium": {
                "color": ft.Colors.YELLOW_900 if not self.is_dark else ft.Colors.YELLOW_400,
                "bg_color": ft.Colors.YELLOW_50 if not self.is_dark else "#4A4518",
                "border_color": ft.Colors.YELLOW_600 if not self.is_dark else ft.Colors.YELLOW_700,
                "icon": ft.Icons.WARNING_ROUNDED,
                "label": "NEEDS ATTENTION",
                "pulse": False,
            },
            "low": {
                "color": ft.Colors.BLUE_700 if not self.is_dark else ft.Colors.BLUE_400,
                "bg_color": ft.Colors.BLUE_50 if not self.is_dark else "#1A2F4A",
                "border_color": ft.Colors.BLUE_400 if not self.is_dark else ft.Colors.BLUE_600,
                "icon": ft.Icons.INFO_ROUNDED,
                "label": "REVIEW REQUESTED",
                "pulse": False,
            },
        }
        return configs.get(self.urgency, configs["medium"])

    def _format_time_ago(self) -> str:
        """Format timestamp to 'time ago' format"""
        now = datetime.now()
        diff = now - self.timestamp

        if diff.seconds < 60:
            return "Just now"
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        elif diff.seconds < 86400:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        else:
            return self.timestamp.strftime("%d %b, %I:%M %p")

    def _handle_call(self, e):
        """Handle call button click"""
        if self.on_call:
            self.on_call(self.patient_id, self.patient_name)

    def _handle_view_history(self, e):
        """Handle view history button click"""
        if self.on_view_history:
            self.on_view_history(self.patient_id)

    def _handle_respond(self, e):
        """Handle respond button click"""
        if self.on_respond:
            self.on_respond(self.message_id, self.patient_id)

    def _handle_dismiss(self, e):
        """Handle dismiss button click"""
        if self.on_dismiss:
            self.on_dismiss(self.message_id)

    def build(self):
        config = self._get_urgency_config()

        # Build symptoms chips if available
        symptom_chips = []
        if self.detected_symptoms:
            for symptom in self.detected_symptoms[:3]:  # Show max 3 symptoms
                symptom_chips.append(
                    ft.Container(
                        content=ft.Text(
                            symptom,
                            size=11,
                            color=config["color"],
                            weight=ft.FontWeight.BOLD,
                        ),
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=ft.border_radius.all(12),
                        bgcolor=ft.Colors.with_opacity(0.2, config["border_color"]),
                        border=ft.border.all(1, config["border_color"]),
                    )
                )

        # Create banner content
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header row
                    ft.Row(
                        controls=[
                            # Urgency indicator
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(
                                            config["icon"],
                                            size=20,
                                            color=config["color"],
                                        ),
                                        ft.Text(
                                            config["label"],
                                            size=12,
                                            weight=ft.FontWeight.BOLD,
                                            color=config["color"],
                                        ),
                                    ],
                                    spacing=6,
                                ),
                            ),
                            # Time
                            ft.Text(
                                self._format_time_ago(),
                                size=11,
                                color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                            ),
                            # Dismiss button
                            ft.IconButton(
                                icon=ft.Icons.CLOSE_ROUNDED,
                                icon_size=18,
                                tooltip="Dismiss",
                                on_click=self._handle_dismiss,
                                icon_color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    # Patient info and reason
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.PERSON_ROUNDED,
                                        size=16,
                                        color=config["color"],
                                    ),
                                    ft.Text(
                                        self.patient_name,
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BLACK if not self.is_dark else ft.Colors.WHITE,
                                    ),
                                ],
                                spacing=6,
                            ),
                            ft.Text(
                                self.reason,
                                size=13,
                                color=ft.Colors.GREY_700 if not self.is_dark else ft.Colors.GREY_300,
                                italic=True,
                            ) if self.reason else ft.Container(),
                        ],
                        spacing=4,
                    ),
                    # Message preview
                    ft.Container(
                        content=ft.Text(
                            self.message_content,
                            size=13,
                            color=ft.Colors.GREY_800 if not self.is_dark else ft.Colors.GREY_200,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        padding=ft.padding.all(10),
                        border_radius=ft.border_radius.all(6),
                        bgcolor=ft.Colors.with_opacity(0.1, config["border_color"]),
                        border=ft.border.all(1, ft.Colors.with_opacity(0.3, config["border_color"])),
                    ) if self.message_content else ft.Container(),
                    # Detected symptoms
                    ft.Row(
                        controls=symptom_chips,
                        spacing=6,
                        wrap=True,
                    ) if symptom_chips else ft.Container(),
                    # Action buttons
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.CALL_ROUNDED, size=16),
                                        ft.Text("Call", size=13),
                                    ],
                                    spacing=6,
                                    tight=True,
                                ),
                                on_click=self._handle_call,
                                style=ft.ButtonStyle(
                                    bgcolor=config["color"],
                                    color=ft.Colors.WHITE,
                                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                                ),
                            ),
                            ft.OutlinedButton(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.HISTORY_ROUNDED, size=16),
                                        ft.Text("History", size=13),
                                    ],
                                    spacing=6,
                                    tight=True,
                                ),
                                on_click=self._handle_view_history,
                                style=ft.ButtonStyle(
                                    side=ft.BorderSide(1, config["color"]),
                                    color=config["color"],
                                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                                ),
                            ),
                            ft.ElevatedButton(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.REPLY_ROUNDED, size=16),
                                        ft.Text("Respond", size=13),
                                    ],
                                    spacing=6,
                                    tight=True,
                                ),
                                on_click=self._handle_respond,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE_600,
                                    color=ft.Colors.WHITE,
                                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                                ),
                            ),
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.padding.all(16),
            border_radius=ft.border_radius.all(8),
            bgcolor=config["bg_color"],
            border=ft.border.all(2, config["border_color"]),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
        )
