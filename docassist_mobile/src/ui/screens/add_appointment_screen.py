"""
Add Appointment Screen - Schedule patient appointments.

Premium screen for scheduling appointments with date/time pickers.
"""

import flet as ft
from typing import Callable, Optional
from dataclasses import dataclass
from datetime import date, datetime, time

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..haptics import HapticFeedback


@dataclass
class AppointmentFormData:
    """Appointment form data."""
    patient_id: int
    appointment_date: str
    appointment_time: str
    duration_minutes: int
    reason: str = ""
    notes: str = ""


class AddAppointmentScreen(ft.Container):
    """
    Add appointment screen.

    Usage:
        screen = AddAppointmentScreen(
            patient_id=123,
            patient_name="John Doe",
            on_save=handle_save,
            on_cancel=handle_cancel,
        )
    """

    def __init__(
        self,
        patient_id: Optional[int] = None,
        patient_name: Optional[str] = None,
        on_save: Callable[[AppointmentFormData], None] = None,
        on_cancel: Callable[[], None] = None,
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.haptic_feedback = haptic_feedback

        # Selected date and time
        self.selected_date = date.today()
        self.selected_time = time(9, 0)  # Default 9:00 AM
        self.selected_duration = 30  # Default 30 minutes

        # Form fields
        self.patient_name_field = ft.TextField(
            label="Patient Name",
            value=patient_name or "",
            border_radius=Radius.MD,
            read_only=bool(patient_id),
            hint_text="Patient name" if not patient_id else None,
        )

        # Date picker field
        self.date_field = ft.TextField(
            label="Appointment Date",
            value=self.selected_date.strftime("%d %b %Y"),
            border_radius=Radius.MD,
            read_only=True,
            on_click=self._show_date_picker,
            prefix_icon=ft.Icons.CALENDAR_TODAY,
        )

        self.date_picker = ft.DatePicker(
            on_change=self._on_date_selected,
            first_date=datetime.now(),
            last_date=datetime(2100, 12, 31),
        )

        # Time picker field
        self.time_field = ft.TextField(
            label="Appointment Time",
            value=self.selected_time.strftime("%I:%M %p"),
            border_radius=Radius.MD,
            read_only=True,
            on_click=self._show_time_picker,
            prefix_icon=ft.Icons.ACCESS_TIME,
        )

        self.time_picker = ft.TimePicker(
            on_change=self._on_time_selected,
        )

        # Duration selector
        self.duration_dropdown = ft.Dropdown(
            label="Duration",
            value="30",
            options=[
                ft.dropdown.Option("15", "15 minutes"),
                ft.dropdown.Option("30", "30 minutes"),
                ft.dropdown.Option("45", "45 minutes"),
                ft.dropdown.Option("60", "1 hour"),
            ],
            border_radius=Radius.MD,
            on_change=self._on_duration_changed,
        )

        # Reason and notes
        self.reason_field = ft.TextField(
            label="Reason for Visit",
            hint_text="e.g., Follow-up, Routine check-up",
            border_radius=Radius.MD,
        )

        self.notes_field = ft.TextField(
            label="Notes (optional)",
            hint_text="Additional notes...",
            border_radius=Radius.MD,
            multiline=True,
            min_lines=2,
            max_lines=4,
        )

        self.error_text = ft.Text(
            "",
            size=MobileTypography.BODY_SMALL,
            color=Colors.ERROR_MAIN,
            visible=False,
        )

        # Buttons
        self.save_button = ft.ElevatedButton(
            text="Schedule Appointment",
            icon=ft.Icons.CHECK,
            width=float("inf"),
            height=MobileSpacing.TOUCH_TARGET,
            style=ft.ButtonStyle(
                bgcolor=Colors.PRIMARY_500,
                color=Colors.NEUTRAL_0,
                shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
            ),
            on_click=self._handle_save,
        )

        self.loading_indicator = ft.ProgressRing(
            width=20,
            height=20,
            stroke_width=2,
            visible=False,
        )

        # Build content
        content = self._build_content()

        super().__init__(
            content=content,
            expand=True,
            bgcolor=Colors.NEUTRAL_50,
        )

    def _build_content(self) -> ft.Column:
        """Build screen content."""
        return ft.Column(
            [
                # Header
                ft.Container(
                    content=ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color=Colors.NEUTRAL_900,
                                icon_size=24,
                                on_click=lambda e: self._handle_cancel(),
                            ),
                            ft.Text(
                                "Schedule Appointment",
                                size=MobileTypography.TITLE_LARGE,
                                weight=ft.FontWeight.W_500,
                                color=Colors.NEUTRAL_900,
                                expand=True,
                            ),
                        ],
                    ),
                    bgcolor=Colors.NEUTRAL_0,
                    padding=ft.padding.only(
                        left=MobileSpacing.XS,
                        right=MobileSpacing.MD,
                        top=MobileSpacing.SM,
                        bottom=MobileSpacing.SM,
                    ),
                ),

                # Form content (scrollable)
                ft.Container(
                    content=ft.ListView(
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    [
                                        # Patient info
                                        self.patient_name_field if not self.patient_id else ft.Container(
                                            content=ft.Column(
                                                [
                                                    ft.Text(
                                                        "Patient",
                                                        size=MobileTypography.BODY_SMALL,
                                                        color=Colors.NEUTRAL_600,
                                                    ),
                                                    ft.Text(
                                                        self.patient_name or "",
                                                        size=MobileTypography.BODY_LARGE,
                                                        weight=ft.FontWeight.W_500,
                                                        color=Colors.NEUTRAL_900,
                                                    ),
                                                ],
                                                spacing=4,
                                            ),
                                            bgcolor=Colors.NEUTRAL_0,
                                            border_radius=Radius.MD,
                                            padding=MobileSpacing.CARD_PADDING,
                                        ),
                                        ft.Container(height=MobileSpacing.MD),

                                        # Date and time section
                                        ft.Text(
                                            "Date & Time",
                                            size=MobileTypography.TITLE_MEDIUM,
                                            weight=ft.FontWeight.W_500,
                                            color=Colors.NEUTRAL_900,
                                        ),
                                        ft.Container(height=MobileSpacing.SM),
                                        self.date_field,
                                        ft.Container(height=MobileSpacing.SM),
                                        self.time_field,
                                        ft.Container(height=MobileSpacing.SM),
                                        self.duration_dropdown,
                                        ft.Container(height=MobileSpacing.LG),

                                        # Reason and notes
                                        ft.Text(
                                            "Details",
                                            size=MobileTypography.TITLE_MEDIUM,
                                            weight=ft.FontWeight.W_500,
                                            color=Colors.NEUTRAL_900,
                                        ),
                                        ft.Container(height=MobileSpacing.SM),
                                        self.reason_field,
                                        ft.Container(height=MobileSpacing.SM),
                                        self.notes_field,
                                        ft.Container(height=MobileSpacing.SM),

                                        # Error message
                                        self.error_text,
                                        ft.Container(height=MobileSpacing.LG),

                                        # Save button
                                        ft.Stack(
                                            [
                                                self.save_button,
                                                ft.Container(
                                                    content=self.loading_indicator,
                                                    alignment=ft.alignment.center,
                                                    height=MobileSpacing.TOUCH_TARGET,
                                                ),
                                            ],
                                        ),
                                        ft.Container(height=MobileSpacing.MD),

                                        # Cancel button
                                        ft.TextButton(
                                            text="Cancel",
                                            style=ft.ButtonStyle(
                                                color=Colors.NEUTRAL_600,
                                            ),
                                            on_click=lambda e: self._handle_cancel(),
                                        ),
                                        ft.Container(height=MobileSpacing.XL),
                                    ],
                                ),
                                padding=MobileSpacing.SCREEN_PADDING,
                            ),
                        ],
                        expand=True,
                    ),
                    expand=True,
                ),

                # Date and time pickers (hidden)
                self.date_picker,
                self.time_picker,
            ],
            spacing=0,
            expand=True,
        )

    def _show_date_picker(self, e):
        """Show date picker dialog."""
        if self.haptic_feedback:
            self.haptic_feedback.light()
        self.date_picker.pick_date()

    def _on_date_selected(self, e):
        """Handle date selection."""
        if self.date_picker.value:
            self.selected_date = self.date_picker.value.date()
            self.date_field.value = self.selected_date.strftime("%d %b %Y")
            self.date_field.update()

    def _show_time_picker(self, e):
        """Show time picker dialog."""
        if self.haptic_feedback:
            self.haptic_feedback.light()
        self.time_picker.pick_time()

    def _on_time_selected(self, e):
        """Handle time selection."""
        if self.time_picker.value:
            # time_picker.value is a time string like "09:30"
            time_parts = str(self.time_picker.value).split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            self.selected_time = time(hour, minute)
            self.time_field.value = self.selected_time.strftime("%I:%M %p")
            self.time_field.update()

    def _on_duration_changed(self, e):
        """Handle duration change."""
        self.selected_duration = int(e.control.value)

    def _validate_form(self) -> bool:
        """Validate form data."""
        if not self.patient_id and not self.patient_name_field.value:
            self._show_error("Patient name is required")
            return False

        if not self.reason_field.value:
            self._show_error("Reason for visit is required")
            return False

        return True

    def _handle_save(self, e):
        """Handle save button click."""
        if not self._validate_form():
            if self.haptic_feedback:
                self.haptic_feedback.error()
            return

        # Show loading
        self._set_loading(True)
        self._hide_error()

        # Trigger haptic feedback
        if self.haptic_feedback:
            self.haptic_feedback.success()

        # Build form data
        form_data = AppointmentFormData(
            patient_id=self.patient_id or 0,
            appointment_date=self.selected_date.strftime("%Y-%m-%d"),
            appointment_time=self.selected_time.strftime("%H:%M"),
            duration_minutes=self.selected_duration,
            reason=self.reason_field.value or "",
            notes=self.notes_field.value or "",
        )

        # Call save handler
        if self.on_save:
            self.on_save(form_data)

    def _handle_cancel(self):
        """Handle cancel button click."""
        if self.haptic_feedback:
            self.haptic_feedback.light()

        if self.on_cancel:
            self.on_cancel()

    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        self.error_text.update()

    def _hide_error(self):
        """Hide error message."""
        self.error_text.visible = False
        self.error_text.update()

    def _set_loading(self, loading: bool):
        """Set loading state."""
        self.save_button.visible = not loading
        self.loading_indicator.visible = loading
        self.update()

    def show_save_error(self, message: str = "Failed to schedule appointment"):
        """Show save error and reset loading state."""
        self._set_loading(False)
        self._show_error(message)
        if self.haptic_feedback:
            self.haptic_feedback.error()

    def reset(self):
        """Reset form to initial state."""
        if not self.patient_id:
            self.patient_name_field.value = ""
        self.selected_date = date.today()
        self.selected_time = time(9, 0)
        self.date_field.value = self.selected_date.strftime("%d %b %Y")
        self.time_field.value = self.selected_time.strftime("%I:%M %p")
        self.duration_dropdown.value = "30"
        self.selected_duration = 30
        self.reason_field.value = ""
        self.notes_field.value = ""
        self._hide_error()
        self._set_loading(False)
        self.update()
