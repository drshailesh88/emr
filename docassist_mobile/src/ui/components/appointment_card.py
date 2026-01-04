"""Appointment Card Component - Displays appointment info."""

import flet as ft
from typing import Optional, Callable
from ..tokens import Colors, MobileSpacing, MobileTypography, Radius


class AppointmentCard(ft.Container):
    """Appointment card with time and patient info."""

    def __init__(
        self,
        time: str,
        patient_name: str,
        reason: Optional[str] = None,
        on_click: Optional[Callable] = None,
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

        super().__init__(
            content=content,
            bgcolor=Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
            ink=True,
            on_click=on_click,
        )
