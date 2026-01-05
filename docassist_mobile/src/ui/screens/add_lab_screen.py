"""
Add Lab Screen - Add laboratory test results.

Premium screen for quickly adding lab results with save-and-add-another.
"""

import flet as ft
from typing import Callable, Optional
from dataclasses import dataclass
from datetime import date, datetime

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..haptics import HapticFeedback


@dataclass
class LabFormData:
    """Lab result form data."""
    test_name: str
    result: str
    unit: str = ""
    reference_range: str = ""
    test_date: str = ""
    is_abnormal: bool = False


class AddLabScreen(ft.Container):
    """
    Add lab result screen.

    Usage:
        screen = AddLabScreen(
            patient_id=123,
            patient_name="John Doe",
            on_save=handle_save,
            on_cancel=handle_cancel,
        )
    """

    def __init__(
        self,
        patient_id: int,
        patient_name: str,
        on_save: Callable[[int, LabFormData, bool], None],  # bool: add_another
        on_cancel: Callable[[], None],
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.haptic_feedback = haptic_feedback

        # Form fields
        self.test_name_field = ft.TextField(
            label="Test Name",
            hint_text="e.g., Hemoglobin, Creatinine",
            border_radius=Radius.MD,
            autofocus=True,
        )

        self.result_field = ft.TextField(
            label="Result",
            hint_text="e.g., 12.5, Positive",
            border_radius=Radius.MD,
        )

        self.unit_field = ft.TextField(
            label="Unit (optional)",
            hint_text="e.g., mg/dL, g/dL",
            border_radius=Radius.MD,
        )

        self.reference_range_field = ft.TextField(
            label="Reference Range (optional)",
            hint_text="e.g., 12-16 g/dL",
            border_radius=Radius.MD,
        )

        # Date picker
        today = date.today()
        self.test_date_field = ft.TextField(
            label="Test Date",
            value=today.strftime("%Y-%m-%d"),
            border_radius=Radius.MD,
            read_only=True,
            on_click=self._show_date_picker,
        )

        self.date_picker = ft.DatePicker(
            on_change=self._on_date_selected,
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
        )

        # Abnormal toggle
        self.is_abnormal_switch = ft.Switch(
            label="Mark as abnormal",
            value=False,
            active_color=Colors.ERROR_MAIN,
        )

        self.error_text = ft.Text(
            "",
            size=MobileTypography.BODY_SMALL,
            color=Colors.ERROR_MAIN,
            visible=False,
        )

        # Buttons
        self.save_button = ft.ElevatedButton(
            text="Save",
            icon=ft.Icons.CHECK,
            height=MobileSpacing.TOUCH_TARGET,
            style=ft.ButtonStyle(
                bgcolor=Colors.PRIMARY_500,
                color=Colors.NEUTRAL_0,
                shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
            ),
            on_click=lambda e: self._handle_save(False),
            expand=True,
        )

        self.save_and_add_button = ft.ElevatedButton(
            text="Save & Add Another",
            icon=ft.Icons.ADD,
            height=MobileSpacing.TOUCH_TARGET,
            style=ft.ButtonStyle(
                bgcolor=Colors.ACCENT_500,
                color=Colors.NEUTRAL_900,
                shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
            ),
            on_click=lambda e: self._handle_save(True),
            expand=True,
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
                            ft.Column(
                                [
                                    ft.Text(
                                        "Add Lab Result",
                                        size=MobileTypography.TITLE_LARGE,
                                        weight=ft.FontWeight.W_500,
                                        color=Colors.NEUTRAL_900,
                                    ),
                                    ft.Text(
                                        self.patient_name,
                                        size=MobileTypography.BODY_SMALL,
                                        color=Colors.NEUTRAL_600,
                                    ),
                                ],
                                spacing=2,
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
                                        # Form fields
                                        self.test_name_field,
                                        ft.Container(height=MobileSpacing.SM),
                                        self.result_field,
                                        ft.Container(height=MobileSpacing.SM),
                                        self.unit_field,
                                        ft.Container(height=MobileSpacing.SM),
                                        self.reference_range_field,
                                        ft.Container(height=MobileSpacing.SM),
                                        self.test_date_field,
                                        ft.Container(height=MobileSpacing.MD),

                                        # Abnormal toggle
                                        ft.Container(
                                            content=self.is_abnormal_switch,
                                            bgcolor=Colors.NEUTRAL_0,
                                            border_radius=Radius.MD,
                                            padding=MobileSpacing.CARD_PADDING,
                                        ),
                                        ft.Container(height=MobileSpacing.SM),

                                        # Error message
                                        self.error_text,
                                        ft.Container(height=MobileSpacing.LG),

                                        # Action buttons
                                        ft.Row(
                                            [
                                                ft.Stack(
                                                    [
                                                        self.save_button,
                                                        ft.Container(
                                                            content=self.loading_indicator,
                                                            alignment=ft.alignment.center,
                                                            height=MobileSpacing.TOUCH_TARGET,
                                                        ),
                                                    ],
                                                    expand=True,
                                                ),
                                                ft.Container(width=MobileSpacing.SM),
                                                self.save_and_add_button,
                                            ],
                                            expand=True,
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

                # Date picker (hidden)
                self.date_picker,
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
            self.test_date_field.value = self.date_picker.value.strftime("%Y-%m-%d")
            self.test_date_field.update()

    def _validate_form(self) -> bool:
        """Validate form data."""
        if not self.test_name_field.value:
            self._show_error("Test name is required")
            return False

        if not self.result_field.value:
            self._show_error("Result is required")
            return False

        return True

    def _handle_save(self, add_another: bool):
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
        form_data = LabFormData(
            test_name=self.test_name_field.value or "",
            result=self.result_field.value or "",
            unit=self.unit_field.value or "",
            reference_range=self.reference_range_field.value or "",
            test_date=self.test_date_field.value or "",
            is_abnormal=self.is_abnormal_switch.value or False,
        )

        # Call save handler
        if self.on_save:
            self.on_save(self.patient_id, form_data, add_another)

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
        self.save_and_add_button.disabled = loading
        self.loading_indicator.visible = loading
        self.update()

    def show_save_error(self, message: str = "Failed to save lab result"):
        """Show save error and reset loading state."""
        self._set_loading(False)
        self._show_error(message)
        if self.haptic_feedback:
            self.haptic_feedback.error()

    def reset(self):
        """Reset form to initial state."""
        self.test_name_field.value = ""
        self.result_field.value = ""
        self.unit_field.value = ""
        self.reference_range_field.value = ""
        today = date.today()
        self.test_date_field.value = today.strftime("%Y-%m-%d")
        self.is_abnormal_switch.value = False
        self._hide_error()
        self._set_loading(False)
        self.update()
