"""
Prescription Card Component - Shows prescription summary with view PDF action.

Displays:
- Visit date
- Diagnosis (truncated)
- Number of medications
- View PDF button
"""

import flet as ft
from typing import Optional, Callable, Dict, Any
from ..tokens import Colors, MobileSpacing, MobileTypography, Radius


class PrescriptionCard(ft.Container):
    """
    Prescription summary card.

    Tapping the card or "View PDF" button opens the full prescription viewer.

    Usage:
        card = PrescriptionCard(
            visit_id=123,
            visit_date="2024-01-15",
            diagnosis="Hypertension",
            medication_count=3,
            on_view_pdf=handle_view_pdf,
        )
    """

    def __init__(
        self,
        visit_id: int,
        visit_date: str,
        diagnosis: Optional[str] = None,
        medication_count: int = 0,
        has_investigations: bool = False,
        has_follow_up: bool = False,
        on_view_pdf: Optional[Callable[[int], None]] = None,
    ):
        self.visit_id = visit_id
        self.visit_date = visit_date
        self.diagnosis = diagnosis or "No diagnosis"
        self.medication_count = medication_count
        self.has_investigations = has_investigations
        self.has_follow_up = has_follow_up
        self.on_view_pdf = on_view_pdf

        content = self._build_content()

        super().__init__(
            content=content,
            bgcolor=Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
            ink=True,
            on_click=self._handle_tap,
        )

    def _build_content(self) -> ft.Column:
        """Build card content."""
        # Diagnosis text (truncated)
        diagnosis_text = self.diagnosis
        if len(diagnosis_text) > 60:
            diagnosis_text = diagnosis_text[:60] + "..."

        # Build info chips
        info_chips = []

        # Medication count chip
        if self.medication_count > 0:
            info_chips.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.MEDICATION, size=12, color=Colors.PRIMARY_500),
                            ft.Text(
                                f"{self.medication_count} med{'s' if self.medication_count != 1 else ''}",
                                size=MobileTypography.CAPTION,
                                color=Colors.PRIMARY_500,
                            ),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    bgcolor=Colors.PRIMARY_50,
                    border_radius=Radius.SM,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                )
            )

        # Investigations chip
        if self.has_investigations:
            info_chips.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.SCIENCE, size=12, color=Colors.INFO_MAIN),
                            ft.Text(
                                "Labs",
                                size=MobileTypography.CAPTION,
                                color=Colors.INFO_MAIN,
                            ),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    bgcolor=Colors.PRIMARY_50,
                    border_radius=Radius.SM,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                )
            )

        # Follow-up chip
        if self.has_follow_up:
            info_chips.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.EVENT, size=12, color=Colors.ACCENT_500),
                            ft.Text(
                                "F/U",
                                size=MobileTypography.CAPTION,
                                color=Colors.ACCENT_500,
                            ),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    bgcolor=Colors.PRIMARY_50,
                    border_radius=Radius.SM,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                )
            )

        return ft.Column(
            [
                # Header with date and PDF icon
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=Colors.PRIMARY_500),
                        ft.Text(
                            self.visit_date,
                            size=MobileTypography.BODY_MEDIUM,
                            weight=ft.FontWeight.W_500,
                            color=Colors.NEUTRAL_900,
                        ),
                        ft.Container(expand=True),
                        ft.Icon(
                            ft.Icons.PICTURE_AS_PDF,
                            size=20,
                            color=Colors.ERROR_MAIN,
                        ),
                    ],
                    spacing=MobileSpacing.XS,
                ),

                # Diagnosis
                ft.Text(
                    diagnosis_text,
                    size=MobileTypography.BODY_SMALL,
                    color=Colors.NEUTRAL_700,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),

                # Info chips
                ft.Row(
                    info_chips,
                    spacing=MobileSpacing.XS,
                    wrap=True,
                ) if info_chips else ft.Container(),

                # View PDF button
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                "View Prescription",
                                size=MobileTypography.LABEL_MEDIUM,
                                weight=ft.FontWeight.W_500,
                                color=Colors.PRIMARY_500,
                            ),
                            ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color=Colors.PRIMARY_500),
                        ],
                        spacing=MobileSpacing.XS,
                    ),
                    margin=ft.margin.only(top=MobileSpacing.XS),
                ),
            ],
            spacing=MobileSpacing.XS,
        )

    def _handle_tap(self, e):
        """Handle card tap."""
        if self.on_view_pdf:
            self.on_view_pdf(self.visit_id)
