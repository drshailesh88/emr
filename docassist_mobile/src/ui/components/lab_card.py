"""Lab Card Component - Displays lab result."""

import flet as ft
from typing import Optional
from ..tokens import Colors, MobileSpacing, MobileTypography, Radius


class LabCard(ft.Container):
    """Lab result card with abnormal highlighting."""

    def __init__(
        self,
        test_name: str,
        result: str,
        unit: Optional[str] = None,
        reference_range: Optional[str] = None,
        test_date: Optional[str] = None,
        is_abnormal: bool = False,
    ):
        # Result with unit
        result_text = f"{result} {unit}" if unit else result

        content = ft.Row(
            [
                # Test info
                ft.Column(
                    [
                        ft.Text(
                            test_name,
                            size=MobileTypography.BODY_MEDIUM,
                            weight=ft.FontWeight.W_500,
                            color=Colors.NEUTRAL_900,
                        ),
                        ft.Text(
                            test_date or "",
                            size=MobileTypography.CAPTION,
                            color=Colors.NEUTRAL_500,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                # Result
                ft.Column(
                    [
                        ft.Text(
                            result_text,
                            size=MobileTypography.BODY_LARGE,
                            weight=ft.FontWeight.W_600,
                            color=Colors.ERROR_MAIN if is_abnormal else Colors.NEUTRAL_900,
                        ),
                        ft.Text(
                            reference_range or "",
                            size=MobileTypography.CAPTION,
                            color=Colors.NEUTRAL_500,
                        ),
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                ),
                # Abnormal indicator
                ft.Container(
                    width=4,
                    height=40,
                    bgcolor=Colors.ERROR_MAIN if is_abnormal else ft.Colors.TRANSPARENT,
                    border_radius=Radius.SM,
                ),
            ],
            spacing=MobileSpacing.SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        super().__init__(
            content=content,
            bgcolor=Colors.ERROR_LIGHT if is_abnormal else Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
        )
