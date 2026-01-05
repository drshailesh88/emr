"""
Edit Patient Screen - Edit patient information.

Premium screen for updating patient demographics.
"""

import flet as ft
from typing import Callable, Optional
from dataclasses import dataclass

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..haptics import HapticFeedback


@dataclass
class PatientFormData:
    """Patient form data."""
    name: str
    age: Optional[int] = None
    gender: str = "O"
    phone: str = ""
    address: str = ""


class EditPatientScreen(ft.Container):
    """
    Edit patient screen.

    Usage:
        screen = EditPatientScreen(
            patient_id=123,
            initial_data=PatientFormData(...),
            on_save=handle_save,
            on_cancel=handle_cancel,
        )
    """

    def __init__(
        self,
        patient_id: int,
        initial_data: Optional[PatientFormData] = None,
        on_save: Callable[[int, PatientFormData], None] = None,
        on_cancel: Callable[[], None] = None,
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.patient_id = patient_id
        self.initial_data = initial_data or PatientFormData(name="")
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.haptic_feedback = haptic_feedback

        # Form fields
        self.name_field = ft.TextField(
            label="Name *",
            value=self.initial_data.name,
            hint_text="Full name",
            border_radius=Radius.MD,
            autofocus=True,
        )

        self.age_field = ft.TextField(
            label="Age",
            value=str(self.initial_data.age) if self.initial_data.age else "",
            hint_text="Age in years",
            border_radius=Radius.MD,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # Gender radio buttons
        self.gender_male = ft.Radio(
            value="M",
            label="Male",
            fill_color=Colors.PRIMARY_500,
        )
        self.gender_female = ft.Radio(
            value="F",
            label="Female",
            fill_color=Colors.PRIMARY_500,
        )
        self.gender_other = ft.Radio(
            value="O",
            label="Other",
            fill_color=Colors.PRIMARY_500,
        )

        self.gender_group = ft.RadioGroup(
            content=ft.Row(
                [
                    self.gender_male,
                    self.gender_female,
                    self.gender_other,
                ],
                spacing=MobileSpacing.MD,
            ),
            value=self.initial_data.gender,
        )

        self.phone_field = ft.TextField(
            label="Phone",
            value=self.initial_data.phone,
            hint_text="10-digit mobile number",
            border_radius=Radius.MD,
            keyboard_type=ft.KeyboardType.PHONE,
            prefix_icon=ft.Icons.PHONE,
        )

        self.address_field = ft.TextField(
            label="Address",
            value=self.initial_data.address,
            hint_text="Complete address",
            border_radius=Radius.MD,
            multiline=True,
            min_lines=3,
            max_lines=5,
        )

        self.error_text = ft.Text(
            "",
            size=MobileTypography.BODY_SMALL,
            color=Colors.ERROR_MAIN,
            visible=False,
        )

        # Buttons
        self.save_button = ft.ElevatedButton(
            text="Save Changes",
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
                                "Edit Patient",
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
                                        # Basic info section
                                        ft.Text(
                                            "Basic Information",
                                            size=MobileTypography.TITLE_MEDIUM,
                                            weight=ft.FontWeight.W_500,
                                            color=Colors.NEUTRAL_900,
                                        ),
                                        ft.Container(height=MobileSpacing.SM),
                                        self.name_field,
                                        ft.Container(height=MobileSpacing.SM),
                                        self.age_field,
                                        ft.Container(height=MobileSpacing.MD),

                                        # Gender section
                                        ft.Text(
                                            "Gender",
                                            size=MobileTypography.BODY_MEDIUM,
                                            color=Colors.NEUTRAL_700,
                                        ),
                                        ft.Container(height=MobileSpacing.XS),
                                        ft.Container(
                                            content=self.gender_group,
                                            bgcolor=Colors.NEUTRAL_0,
                                            border_radius=Radius.MD,
                                            padding=MobileSpacing.CARD_PADDING,
                                        ),
                                        ft.Container(height=MobileSpacing.LG),

                                        # Contact section
                                        ft.Text(
                                            "Contact Information",
                                            size=MobileTypography.TITLE_MEDIUM,
                                            weight=ft.FontWeight.W_500,
                                            color=Colors.NEUTRAL_900,
                                        ),
                                        ft.Container(height=MobileSpacing.SM),
                                        self.phone_field,
                                        ft.Container(height=MobileSpacing.SM),
                                        self.address_field,
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

                                        # Required field note
                                        ft.Text(
                                            "* Required field",
                                            size=MobileTypography.CAPTION,
                                            color=Colors.NEUTRAL_500,
                                            italic=True,
                                        ),
                                    ],
                                ),
                                padding=MobileSpacing.SCREEN_PADDING,
                            ),
                        ],
                        expand=True,
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

    def _validate_form(self) -> bool:
        """Validate form data."""
        if not self.name_field.value or not self.name_field.value.strip():
            self._show_error("Name is required")
            return False

        # Validate age if provided
        if self.age_field.value:
            try:
                age = int(self.age_field.value)
                if age < 0 or age > 150:
                    self._show_error("Please enter a valid age")
                    return False
            except ValueError:
                self._show_error("Please enter a valid age")
                return False

        # Validate phone if provided
        if self.phone_field.value:
            phone = self.phone_field.value.strip()
            # Remove common separators
            phone = phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
            if not phone.isdigit() or len(phone) != 10:
                self._show_error("Please enter a valid 10-digit phone number")
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
        age = None
        if self.age_field.value:
            try:
                age = int(self.age_field.value)
            except ValueError:
                age = None

        form_data = PatientFormData(
            name=self.name_field.value.strip(),
            age=age,
            gender=self.gender_group.value or "O",
            phone=self.phone_field.value.strip(),
            address=self.address_field.value.strip(),
        )

        # Call save handler
        if self.on_save:
            self.on_save(self.patient_id, form_data)

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
        self.name_field.disabled = loading
        self.age_field.disabled = loading
        self.gender_group.disabled = loading
        self.phone_field.disabled = loading
        self.address_field.disabled = loading
        self.update()

    def show_save_error(self, message: str = "Failed to update patient"):
        """Show save error and reset loading state."""
        self._set_loading(False)
        self._show_error(message)
        if self.haptic_feedback:
            self.haptic_feedback.error()

    def reset(self):
        """Reset form to initial state."""
        self.name_field.value = self.initial_data.name
        self.age_field.value = str(self.initial_data.age) if self.initial_data.age else ""
        self.gender_group.value = self.initial_data.gender
        self.phone_field.value = self.initial_data.phone
        self.address_field.value = self.initial_data.address
        self._hide_error()
        self._set_loading(False)
        self.update()
