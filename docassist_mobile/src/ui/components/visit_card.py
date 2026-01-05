"""Visit Card Component - Displays visit summary."""

import flet as ft
from typing import Optional
from ..tokens import Colors, MobileSpacing, MobileTypography, Radius


class VisitCard(ft.Container):
    """Expandable visit card showing visit details."""

    def __init__(
        self,
        visit_date: str,
        chief_complaint: Optional[str] = None,
        diagnosis: Optional[str] = None,
        expanded: bool = False,
    ):
        self.expanded = expanded

        content = ft.Column(
            [
                # Header
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=Colors.PRIMARY_500),
                        ft.Text(
                            visit_date,
                            size=MobileTypography.BODY_MEDIUM,
                            weight=ft.FontWeight.W_500,
                            color=Colors.NEUTRAL_900,
                        ),
                        ft.Container(expand=True),
                        ft.Icon(
                            ft.Icons.EXPAND_MORE if not expanded else ft.Icons.EXPAND_LESS,
                            color=Colors.NEUTRAL_400,
                        ),
                    ],
                    spacing=MobileSpacing.XS,
                ),
                # Chief complaint
                ft.Text(
                    chief_complaint or "No chief complaint recorded",
                    size=MobileTypography.BODY_SMALL,
                    color=Colors.NEUTRAL_600,
                    max_lines=2 if not expanded else None,
                ),
                # Diagnosis (if expanded)
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Diagnosis",
                            size=MobileTypography.LABEL_MEDIUM,
                            color=Colors.NEUTRAL_500,
                        ),
                        ft.Text(
                            diagnosis or "No diagnosis recorded",
                            size=MobileTypography.BODY_SMALL,
                            color=Colors.NEUTRAL_800,
                        ),
                    ]),
                    visible=expanded,
                ),
            ],
            spacing=MobileSpacing.XS,
        )

        super().__init__(
            content=content,
            bgcolor=Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
            ink=True,
        )
