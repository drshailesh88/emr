"""Premium Prescription View Component.

Displays generated prescriptions with premium styling.
"""

import flet as ft
from typing import Optional

from ...models.schemas import Prescription
from ..tokens import Colors, Typography, Spacing, Radius


class PrescriptionView:
    """Premium prescription display component."""

    def __init__(self, is_dark: bool = False):
        self.is_dark = is_dark
        self._column: Optional[ft.Column] = None

    def build(self) -> ft.Container:
        """Build the prescription view container."""
        self._column = ft.Column([], spacing=10, scroll=ft.ScrollMode.AUTO)

        return ft.Container(
            content=self._column,
            bgcolor=Colors.NEUTRAL_50 if not self.is_dark else Colors.NEUTRAL_800,
            border_radius=Radius.MD,
            padding=Spacing.MD,
            expand=True,
        )

    def display(self, rx: Prescription):
        """Display a prescription in the view."""
        self._column.controls.clear()

        # Diagnosis section
        if rx.diagnosis:
            self._column.controls.append(self._section_header("DIAGNOSIS", Colors.PRIMARY_700))
            for dx in rx.diagnosis:
                self._column.controls.append(self._bullet_item(dx))

        # Medications section
        if rx.medications:
            self._column.controls.append(ft.Divider(height=Spacing.SM, color=Colors.NEUTRAL_200))
            self._column.controls.append(
                ft.Text(
                    "℞",
                    size=Typography.HEADLINE_MEDIUM.size,
                    weight=ft.FontWeight.W_700,
                    color=Colors.NEUTRAL_900 if not self.is_dark else Colors.NEUTRAL_100,
                )
            )

            for i, med in enumerate(rx.medications, 1):
                med_text = f"{i}. {med.drug_name}"
                if med.strength:
                    med_text += f" {med.strength}"

                dosage_parts = [med.dose, med.frequency]
                if med.duration:
                    dosage_parts.append(f"× {med.duration}")
                if med.instructions:
                    dosage_parts.append(f"({med.instructions})")
                dosage_text = " ".join(filter(None, dosage_parts))

                self._column.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                med_text,
                                weight=ft.FontWeight.W_500,
                                size=Typography.BODY_MEDIUM.size,
                                color=Colors.NEUTRAL_900 if not self.is_dark else Colors.NEUTRAL_100,
                            ),
                            ft.Text(
                                dosage_text,
                                size=Typography.BODY_SMALL.size,
                                color=Colors.NEUTRAL_600 if not self.is_dark else Colors.NEUTRAL_400,
                            ),
                        ], spacing=2),
                        padding=ft.padding.only(left=Spacing.SM, bottom=Spacing.XS),
                    )
                )

        # Investigations section
        if rx.investigations:
            self._column.controls.append(ft.Divider(height=Spacing.SM, color=Colors.NEUTRAL_200))
            self._column.controls.append(self._section_header("INVESTIGATIONS", Colors.WARNING_MAIN))
            for inv in rx.investigations:
                self._column.controls.append(self._bullet_item(inv))

        # Advice section
        if rx.advice:
            self._column.controls.append(ft.Divider(height=Spacing.SM, color=Colors.NEUTRAL_200))
            self._column.controls.append(self._section_header("ADVICE", Colors.SUCCESS_MAIN))
            for adv in rx.advice:
                self._column.controls.append(self._bullet_item(adv))

        # Follow-up
        if rx.follow_up:
            self._column.controls.append(ft.Divider(height=Spacing.SM, color=Colors.NEUTRAL_200))
            self._column.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=Colors.PRIMARY_600),
                        ft.Text(
                            f"FOLLOW-UP: {rx.follow_up}",
                            weight=ft.FontWeight.W_500,
                            size=Typography.BODY_MEDIUM.size,
                            color=Colors.PRIMARY_700 if not self.is_dark else Colors.PRIMARY_300,
                        ),
                    ], spacing=Spacing.XS),
                )
            )

        # Red flags
        if rx.red_flags:
            self._column.controls.append(ft.Divider(height=Spacing.SM, color=Colors.NEUTRAL_200))
            self._column.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.WARNING_ROUNDED, size=16, color=Colors.ERROR_MAIN),
                            ft.Text(
                                "RED FLAGS",
                                weight=ft.FontWeight.W_600,
                                size=Typography.LABEL_MEDIUM.size,
                                color=Colors.ERROR_DARK,
                            ),
                        ], spacing=Spacing.XS),
                        *[
                            ft.Text(
                                f"⚠ {flag}",
                                size=Typography.BODY_SMALL.size,
                                color=Colors.ERROR_MAIN,
                            )
                            for flag in rx.red_flags
                        ]
                    ], spacing=Spacing.XS),
                    bgcolor=Colors.ERROR_LIGHT if not self.is_dark else "rgba(234, 67, 53, 0.15)",
                    padding=Spacing.SM,
                    border_radius=Radius.SM,
                )
            )

        if self._column.page:
            self._column.update()

    def _section_header(self, title: str, color: str) -> ft.Text:
        """Create a section header."""
        return ft.Text(
            title,
            weight=ft.FontWeight.W_600,
            size=Typography.LABEL_MEDIUM.size,
            color=color,
        )

    def _bullet_item(self, text: str) -> ft.Text:
        """Create a bullet item."""
        return ft.Text(
            f"  • {text}",
            size=Typography.BODY_SMALL.size,
            color=Colors.NEUTRAL_800 if not self.is_dark else Colors.NEUTRAL_200,
        )

    def clear(self):
        """Clear the prescription display."""
        if self._column:
            self._column.controls.clear()
            if self._column.page:
                self._column.update()

    def show_error(self, message: str):
        """Show an error message in the view."""
        if self._column:
            self._column.controls.clear()
            self._column.controls.append(
                ft.Text(message, color=Colors.ERROR_MAIN, size=Typography.BODY_MEDIUM.size)
            )
            if self._column.page:
                self._column.update()
