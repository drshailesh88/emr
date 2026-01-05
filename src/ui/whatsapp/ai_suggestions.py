"""AI-powered response suggestions for patient messages"""
import flet as ft
from typing import Callable, Optional, List
from datetime import datetime


class AISuggestion:
    """Data class for AI suggestion"""

    def __init__(
        self,
        suggestion_id: str,
        text: str,
        confidence: float,
        reason: str,
        category: str = "general",  # general, urgent, prescription, appointment
        requires_escalation: bool = False,
    ):
        self.suggestion_id = suggestion_id
        self.text = text
        self.confidence = confidence
        self.reason = reason
        self.category = category
        self.requires_escalation = requires_escalation


class AISuggestions(ft.UserControl):
    """AI-powered response suggestion panel"""

    def __init__(
        self,
        on_suggestion_selected: Callable[[str], None],
        on_escalate: Optional[Callable] = None,
        is_dark: bool = False,
    ):
        super().__init__()
        self.on_suggestion_selected = on_suggestion_selected
        self.on_escalate = on_escalate
        self.is_dark = is_dark

        self.suggestions: List[AISuggestion] = []
        self.is_loading = False
        self.suggestions_container = None
        self.loading_indicator = None

    def set_suggestions(self, suggestions: List[AISuggestion]):
        """Update suggestions list"""
        self.suggestions = suggestions
        self.is_loading = False
        self._update_view()

    def set_loading(self, loading: bool):
        """Set loading state"""
        self.is_loading = loading
        self._update_view()

    def _update_view(self):
        """Update the suggestions view"""
        if not self.suggestions_container or not self.loading_indicator:
            return

        # Toggle loading indicator
        self.loading_indicator.visible = self.is_loading
        self.suggestions_container.visible = not self.is_loading

        if not self.is_loading and self.suggestions:
            # Build suggestion items
            suggestion_items = []

            for suggestion in self.suggestions:
                suggestion_items.append(
                    self._build_suggestion_item(suggestion)
                )

            self.suggestions_container.controls = suggestion_items
            self.suggestions_container.update()

        self.loading_indicator.update()
        self.suggestions_container.update()

    def _build_suggestion_item(self, suggestion: AISuggestion) -> ft.Container:
        """Build individual suggestion item"""

        # Get category config
        category_config = self._get_category_config(suggestion.category)

        # Confidence bar
        confidence_pct = int(suggestion.confidence * 100)
        confidence_color = (
            ft.Colors.GREEN_500 if confidence_pct >= 80
            else ft.Colors.ORANGE_500 if confidence_pct >= 60
            else ft.Colors.RED_500
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header with category and confidence
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(
                                            category_config["icon"],
                                            size=14,
                                            color=category_config["color"],
                                        ),
                                        ft.Text(
                                            category_config["label"],
                                            size=11,
                                            weight=ft.FontWeight.BOLD,
                                            color=category_config["color"],
                                        ),
                                    ],
                                    spacing=4,
                                    tight=True,
                                ),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=ft.border_radius.all(12),
                                bgcolor=ft.Colors.with_opacity(0.2, category_config["color"]),
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        f"{confidence_pct}%",
                                        size=11,
                                        weight=ft.FontWeight.BOLD,
                                        color=confidence_color,
                                    ),
                                    ft.Container(
                                        content=ft.ProgressBar(
                                            value=suggestion.confidence,
                                            color=confidence_color,
                                            bgcolor=ft.Colors.GREY_300 if not self.is_dark else ft.Colors.GREY_700,
                                            height=4,
                                        ),
                                        width=50,
                                    ),
                                ],
                                spacing=6,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    # Suggestion text
                    ft.Container(
                        content=ft.Text(
                            suggestion.text,
                            size=14,
                            color=ft.Colors.BLACK if not self.is_dark else ft.Colors.WHITE,
                        ),
                        padding=ft.padding.symmetric(vertical=8),
                    ),
                    # Reason
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.LIGHTBULB_OUTLINE_ROUNDED,
                                size=12,
                                color=ft.Colors.GREY_500,
                            ),
                            ft.Text(
                                suggestion.reason,
                                size=11,
                                color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                                italic=True,
                                expand=True,
                            ),
                        ],
                        spacing=6,
                    ),
                    # Actions
                    ft.Row(
                        controls=[
                            ft.TextButton(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.SEND_ROUNDED, size=14),
                                        ft.Text("Use this", size=12),
                                    ],
                                    spacing=4,
                                    tight=True,
                                ),
                                on_click=lambda e, text=suggestion.text: self._handle_use_suggestion(text),
                                style=ft.ButtonStyle(
                                    color=ft.Colors.BLUE_600,
                                ),
                            ),
                            ft.TextButton(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.EDIT_ROUNDED, size=14),
                                        ft.Text("Edit", size=12),
                                    ],
                                    spacing=4,
                                    tight=True,
                                ),
                                on_click=lambda e, text=suggestion.text: self._handle_edit_suggestion(text),
                                style=ft.ButtonStyle(
                                    color=ft.Colors.GREY_600,
                                ),
                            ),
                            ft.TextButton(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.PHONE_FORWARDED_ROUNDED, size=14, color=ft.Colors.RED_600),
                                        ft.Text("Escalate", size=12, color=ft.Colors.RED_600),
                                    ],
                                    spacing=4,
                                    tight=True,
                                ),
                                on_click=lambda e: self._handle_escalate(),
                                visible=suggestion.requires_escalation,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.RED_600,
                                ),
                            ),
                        ],
                        spacing=4,
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.all(12),
            border_radius=ft.border_radius.all(8),
            bgcolor=ft.Colors.WHITE if not self.is_dark else "#2D2D2D",
            border=ft.border.all(
                1,
                category_config["color"] if suggestion.requires_escalation else (
                    ft.Colors.GREY_300 if not self.is_dark else ft.Colors.GREY_700
                )
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 1),
            ),
        )

    def _get_category_config(self, category: str) -> dict:
        """Get configuration for suggestion category"""
        configs = {
            "urgent": {
                "label": "URGENT",
                "icon": ft.Icons.PRIORITY_HIGH_ROUNDED,
                "color": ft.Colors.RED_600 if not self.is_dark else ft.Colors.RED_400,
            },
            "prescription": {
                "label": "PRESCRIPTION",
                "icon": ft.Icons.MEDICATION_ROUNDED,
                "color": ft.Colors.PURPLE_600 if not self.is_dark else ft.Colors.PURPLE_400,
            },
            "appointment": {
                "label": "APPOINTMENT",
                "icon": ft.Icons.CALENDAR_TODAY_ROUNDED,
                "color": ft.Colors.BLUE_600 if not self.is_dark else ft.Colors.BLUE_400,
            },
            "general": {
                "label": "GENERAL",
                "icon": ft.Icons.CHAT_ROUNDED,
                "color": ft.Colors.GREEN_600 if not self.is_dark else ft.Colors.GREEN_400,
            },
        }
        return configs.get(category, configs["general"])

    def _handle_use_suggestion(self, text: str):
        """Handle using a suggestion as-is"""
        if self.on_suggestion_selected:
            self.on_suggestion_selected(text)

    def _handle_edit_suggestion(self, text: str):
        """Handle editing a suggestion"""
        # This will populate the input field with the suggestion text
        # The user can then edit before sending
        if self.on_suggestion_selected:
            self.on_suggestion_selected(text)

    def _handle_escalate(self):
        """Handle escalation request"""
        if self.on_escalate:
            self.on_escalate()

    def build(self):
        # Loading indicator
        self.loading_indicator = ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(
                        width=32,
                        height=32,
                        color=ft.Colors.BLUE_400,
                    ),
                    ft.Text(
                        "AI is analyzing message...",
                        size=12,
                        color=ft.Colors.GREY_600 if not self.is_dark else ft.Colors.GREY_400,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(30),
            alignment=ft.alignment.center,
            visible=self.is_loading,
        )

        # Suggestions container
        self.suggestions_container = ft.Column(
            controls=[],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            visible=not self.is_loading,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.AUTO_AWESOME_ROUNDED,
                                    size=18,
                                    color=ft.Colors.PURPLE_400,
                                ),
                                ft.Text(
                                    "AI Suggestions",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLACK if not self.is_dark else ft.Colors.WHITE,
                                ),
                            ],
                            spacing=8,
                        ),
                        padding=ft.padding.all(12),
                        border=ft.border.only(
                            bottom=ft.BorderSide(1, ft.Colors.GREY_300 if not self.is_dark else ft.Colors.GREY_700)
                        ),
                    ),
                    # Content (loading or suggestions)
                    ft.Container(
                        content=ft.Stack(
                            controls=[
                                self.suggestions_container,
                                self.loading_indicator,
                            ],
                        ),
                        padding=ft.padding.all(12),
                        expand=True,
                    ),
                ],
                spacing=0,
            ),
            bgcolor=ft.Colors.GREY_50 if not self.is_dark else "#1E1E1E",
            border_radius=ft.border_radius.all(8),
            border=ft.border.all(1, ft.Colors.GREY_300 if not self.is_dark else ft.Colors.GREY_700),
            expand=True,
        )
