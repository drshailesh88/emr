"""Premium Patient Header Component.

Displays patient info with action buttons in a polished header style.
"""

import flet as ft
from typing import Optional, Callable

from ...models.schemas import Patient
from ..tokens import Colors, Typography, Spacing, Radius


class PatientHeader:
    """Premium patient header with info and action buttons."""

    def __init__(
        self,
        on_show_audit_history: Optional[Callable] = None,
        on_show_reminder_settings: Optional[Callable] = None,
        is_dark: bool = False,
    ):
        self.on_show_audit_history = on_show_audit_history
        self.on_show_reminder_settings = on_show_reminder_settings
        self.is_dark = is_dark
        self.current_patient: Optional[Patient] = None

        # UI references
        self._container: Optional[ft.Container] = None
        self._name_text: Optional[ft.Text] = None
        self._details_text: Optional[ft.Text] = None

    def build(self) -> ft.Container:
        """Build the patient header container."""
        self._container = ft.Container(
            content=self._build_empty_state(),
            padding=Spacing.MD,
            bgcolor=Colors.NEUTRAL_100 if not self.is_dark else Colors.NEUTRAL_800,
            border=ft.border.only(
                bottom=ft.BorderSide(1, Colors.NEUTRAL_200 if not self.is_dark else Colors.NEUTRAL_700)
            ),
        )
        return self._container

    def _build_empty_state(self) -> ft.Control:
        """Build empty state when no patient is selected."""
        return ft.Text(
            "Select a patient to begin",
            size=Typography.BODY_LARGE.size,
            color=Colors.NEUTRAL_500,
            italic=True,
        )

    def _build_patient_display(self, patient: Patient) -> ft.Control:
        """Build the patient info display."""
        # Patient name
        self._name_text = ft.Text(
            patient.name,
            size=Typography.HEADLINE_MEDIUM.size,
            weight=ft.FontWeight.W_600,
            color=Colors.NEUTRAL_900 if not self.is_dark else Colors.NEUTRAL_100,
        )

        # Details row
        details = []
        if patient.age:
            details.append(f"{patient.age}y")
        if patient.gender:
            details.append(patient.gender)
        if patient.uhid:
            details.append(f"UHID: {patient.uhid}")

        self._details_text = ft.Text(
            " · ".join(details),
            size=Typography.BODY_SMALL.size,
            color=Colors.NEUTRAL_600 if not self.is_dark else Colors.NEUTRAL_400,
        )

        # Action buttons
        action_buttons = ft.Row([
            ft.IconButton(
                icon=ft.Icons.NOTIFICATIONS_OUTLINED,
                tooltip="Reminder settings",
                icon_size=20,
                icon_color=Colors.NEUTRAL_600 if not self.is_dark else Colors.NEUTRAL_400,
                on_click=self._handle_reminder_click,
            ),
            ft.IconButton(
                icon=ft.Icons.HISTORY,
                tooltip="View audit history",
                icon_size=20,
                icon_color=Colors.NEUTRAL_600 if not self.is_dark else Colors.NEUTRAL_400,
                on_click=self._handle_audit_click,
            ),
        ], spacing=0)

        return ft.Row([
            ft.Column([
                self._name_text,
                self._details_text,
            ], spacing=2),
            action_buttons,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def set_patient(self, patient: Optional[Patient]):
        """Update the displayed patient."""
        self.current_patient = patient

        if patient:
            self._container.content = self._build_patient_display(patient)
        else:
            self._container.content = self._build_empty_state()

        if self._container.page:
            self._container.update()

    def _handle_audit_click(self, e):
        """Handle audit history button click."""
        if self.on_show_audit_history and self.current_patient:
            self.on_show_audit_history(e)

    def _handle_reminder_click(self, e):
        """Handle reminder settings button click."""
        if self.on_show_reminder_settings and self.current_patient:
            self.on_show_reminder_settings(e)

    def update_theme(self, is_dark: bool):
        """Update header colors for theme change."""
        self.is_dark = is_dark
        if self._container:
            self._container.bgcolor = Colors.NEUTRAL_100 if not is_dark else Colors.NEUTRAL_800
            if self.current_patient:
                self._container.content = self._build_patient_display(self.current_patient)
            if self._container.page:
                self._container.update()
