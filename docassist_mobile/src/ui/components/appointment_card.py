"""Appointment Card Component - Displays appointment info."""

import flet as ft
from typing import Optional, Callable
from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..animations import Animations


class AppointmentCard(ft.Container):
    """Appointment card with time and patient info."""

    def __init__(
        self,
        time: str,
        patient_name: str,
        reason: Optional[str] = None,
        on_click: Optional[Callable] = None,
        haptic_feedback=None,
    ):
        content = ft.Row(
            [
                # Time
                ft.Container(
                    content=ft.Text(
                        time,
                        size=MobileTypography.BODY_MEDIUM,
                        weight=ft.FontWeight.W_600,
                        color=Colors.PRIMARY_500,
                    ),
                    width=70,
                ),
                # Patient info
                ft.Column(
                    [
                        ft.Text(
                            patient_name,
                            size=MobileTypography.BODY_LARGE,
                            weight=ft.FontWeight.W_500,
                            color=Colors.NEUTRAL_900,
                        ),
                        ft.Text(
                            reason or "Appointment",
                            size=MobileTypography.BODY_SMALL,
                            color=Colors.NEUTRAL_600,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                # Arrow
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=Colors.NEUTRAL_400),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Store haptic feedback for click handler
        self.haptic_feedback = haptic_feedback
        self._original_on_click = on_click

        super().__init__(
            content=content,
            bgcolor=Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
            ink=True,
            on_click=self._handle_click if on_click else None,
            # Add tap animation
            animate_scale=Animations.scale_tap(),
            scale=1.0,
        )

    def _handle_click(self, e):
        """Handle click with haptic feedback and animation."""
        # Trigger haptic
        if self.haptic_feedback:
            self.haptic_feedback.light()

        # Scale animation
        self.scale = 0.97
        self.update()

        # Call original handler
        if self._original_on_click:
            self._original_on_click(e)

        # Scale back
        self.scale = 1.0
        self.update()
