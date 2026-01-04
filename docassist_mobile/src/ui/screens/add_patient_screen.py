"""
Add Patient Screen - Quick patient entry form.

Minimal fields for fast patient registration on mobile.
Designed for quick entry between consultations.
"""

import flet as ft
from typing import Callable, Optional
from datetime import datetime

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..animations import Animations
from ..haptics import HapticFeedback


class AddPatientScreen(ft.Container):
    """
    Quick add patient screen for mobile.

    Features:
    - Minimal required fields (name, phone, age, gender)
    - Two action buttons: "Add & Open" and "Add Another"
    - Form validation with visual feedback
    - Haptic feedback on interactions
    - Premium UI with smooth animations

    Usage:
        screen = AddPatientScreen(
            on_back=handle_back,
            on_save=handle_save_patient,
            haptic_feedback=haptics,
        )
    """

    def __init__(
        self,
        on_back: Callable,
        on_save: Callable[[dict, bool], None],  # (patient_data, open_after_save)
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.on_back = on_back
        self.on_save = on_save
        self.haptic_feedback = haptic_feedback

        # Form fields
        self.name_field = ft.TextField(
            label="Patient Name *",
            hint_text="Enter full name",
            text_size=MobileTypography.BODY_LARGE,
            border_color=Colors.NEUTRAL_300,
            focused_border_color=Colors.PRIMARY_500,
            cursor_color=Colors.PRIMARY_500,
            autofocus=True,
        )

        self.phone_field = ft.TextField(
            label="Phone Number",
            hint_text="10-digit mobile number",
            text_size=MobileTypography.BODY_LARGE,
            keyboard_type=ft.KeyboardType.PHONE,
            border_color=Colors.NEUTRAL_300,
            focused_border_color=Colors.PRIMARY_500,
            cursor_color=Colors.PRIMARY_500,
            max_length=10,
        )

        self.age_field = ft.TextField(
            label="Age",
            hint_text="Years",
            text_size=MobileTypography.BODY_LARGE,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=Colors.NEUTRAL_300,
            focused_border_color=Colors.PRIMARY_500,
            cursor_color=Colors.PRIMARY_500,
            width=150,
        )

        # Gender selector
        self.gender_selector = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="M", label="Male"),
                    ft.Radio(value="F", label="Female"),
                    ft.Radio(value="O", label="Other"),
                ],
                spacing=MobileSpacing.MD,
            ),
            value="M",
        )

        # Error message
        self.error_text = ft.Text(
            "",
            color=Colors.ERROR_MAIN,
            size=MobileTypography.BODY_SMALL,
            visible=False,
        )

        # Action buttons
        self.save_and_open_button = ft.ElevatedButton(
            "Add & Open",
            icon=ft.Icons.PERSON_ADD,
            bgcolor=Colors.PRIMARY_500,
            color=Colors.NEUTRAL_0,
            height=48,
            on_click=lambda e: self._handle_save(open_after=True),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
            ),
        )

        self.save_another_button = ft.OutlinedButton(
            "Add Another",
            icon=ft.Icons.ADD,
            height=48,
            on_click=lambda e: self._handle_save(open_after=False),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=Radius.BUTTON),
                side=ft.BorderSide(2, Colors.PRIMARY_500),
            ),
        )

        # Build UI
        content = ft.Column(
            [
                # Header
                ft.Container(
                    content=ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                icon_color=Colors.NEUTRAL_900,
                                on_click=self._handle_back,
                                tooltip="Back",
                            ),
                            ft.Text(
                                "Add Patient",
                                size=MobileTypography.HEADLINE_LARGE,
                                weight=ft.FontWeight.W_600,
                                color=Colors.NEUTRAL_900,
                            ),
                        ],
                        spacing=MobileSpacing.SM,
                    ),
                    bgcolor=Colors.NEUTRAL_0,
                    padding=MobileSpacing.SCREEN_PADDING,
                    border=ft.border.only(bottom=ft.BorderSide(1, Colors.NEUTRAL_200)),
                ),

                # Form
                ft.Container(
                    content=ft.Column(
                        [
                            # Name field
                            self.name_field,

                            # Phone field
                            self.phone_field,

                            # Age field
                            self.age_field,

                            # Gender selector
                            ft.Column(
                                [
                                    ft.Text(
                                        "Gender",
                                        size=MobileTypography.BODY_MEDIUM,
                                        color=Colors.NEUTRAL_700,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    self.gender_selector,
                                ],
                                spacing=MobileSpacing.XS,
                            ),

                            # Error message
                            self.error_text,

                            # Spacer
                            ft.Container(height=MobileSpacing.LG),

                            # Action buttons
                            ft.Column(
                                [
                                    self.save_and_open_button,
                                    self.save_another_button,
                                ],
                                spacing=MobileSpacing.SM,
                            ),
                        ],
                        spacing=MobileSpacing.LG,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    padding=MobileSpacing.SCREEN_PADDING,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

        super().__init__(
            content=content,
            bgcolor=Colors.NEUTRAL_50,
            expand=True,
        )

    def _handle_back(self, e):
        """Handle back button."""
        if self.haptic_feedback:
            self.haptic_feedback.light()

        if self.on_back:
            self.on_back()

    def _validate_form(self) -> tuple[bool, str]:
        """
        Validate form fields.

        Returns:
            (is_valid, error_message)
        """
        # Name is required
        if not self.name_field.value or not self.name_field.value.strip():
            return False, "Patient name is required"

        # Phone validation (optional but if provided, must be valid)
        if self.phone_field.value:
            phone = self.phone_field.value.strip()
            if len(phone) > 0 and len(phone) != 10:
                return False, "Phone number must be 10 digits"
            if phone and not phone.isdigit():
                return False, "Phone number must contain only digits"

        # Age validation (optional but if provided, must be valid)
        if self.age_field.value:
            try:
                age = int(self.age_field.value)
                if age < 0 or age > 150:
                    return False, "Age must be between 0 and 150"
            except ValueError:
                return False, "Age must be a number"

        return True, ""

    def _handle_save(self, open_after: bool):
        """Handle save button."""
        # Validate form
        is_valid, error = self._validate_form()

        if not is_valid:
            # Show error
            self.error_text.value = error
            self.error_text.visible = True
            self.error_text.update()

            # Error haptic
            if self.haptic_feedback:
                self.haptic_feedback.warning()

            return

        # Hide error
        self.error_text.visible = False
        self.error_text.update()

        # Success haptic
        if self.haptic_feedback:
            self.haptic_feedback.success()

        # Collect data
        patient_data = {
            "name": self.name_field.value.strip(),
            "phone": self.phone_field.value.strip() if self.phone_field.value else None,
            "age": int(self.age_field.value) if self.age_field.value else None,
            "gender": self.gender_selector.value,
            "created_at": datetime.now(),
        }

        # Call save handler
        if self.on_save:
            self.on_save(patient_data, open_after)

        # If "Add Another", clear form
        if not open_after:
            self._clear_form()

    def _clear_form(self):
        """Clear all form fields for next entry."""
        self.name_field.value = ""
        self.phone_field.value = ""
        self.age_field.value = ""
        self.gender_selector.value = "M"
        self.error_text.visible = False

        # Focus name field
        self.name_field.focus()

        self.update()

    def show_success_message(self, message: str):
        """Show success message (e.g., "Patient added successfully")."""
        # Create snackbar
        snackbar = ft.SnackBar(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=Colors.SUCCESS_MAIN),
                    ft.Text(message, color=Colors.NEUTRAL_900),
                ],
                spacing=MobileSpacing.SM,
            ),
            bgcolor=Colors.SUCCESS_LIGHT,
            duration=3000,
        )

        # Show snackbar
        # Note: This requires access to page.overlay
        # In practice, the parent would handle showing this
        return snackbar


class QuickAddPatientDialog(ft.AlertDialog):
    """
    Quick add patient dialog (modal).
    Alternative to full-screen form for even faster entry.

    Usage:
        dialog = QuickAddPatientDialog(
            on_save=handle_save,
        )
        page.overlay.append(dialog)
        dialog.open = True
    """

    def __init__(
        self,
        on_save: Callable[[dict], None],
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.on_save = on_save
        self.haptic_feedback = haptic_feedback

        # Form fields
        self.name_field = ft.TextField(
            label="Patient Name *",
            autofocus=True,
        )

        self.phone_field = ft.TextField(
            label="Phone",
            keyboard_type=ft.KeyboardType.PHONE,
        )

        self.age_field = ft.TextField(
            label="Age",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=100,
        )

        self.gender_selector = ft.Dropdown(
            label="Gender",
            options=[
                ft.dropdown.Option("M", "Male"),
                ft.dropdown.Option("F", "Female"),
                ft.dropdown.Option("O", "Other"),
            ],
            value="M",
            width=120,
        )

        # Error text
        self.error_text = ft.Text(
            "",
            color=Colors.ERROR_MAIN,
            size=MobileTypography.BODY_SMALL,
            visible=False,
        )

        super().__init__(
            title=ft.Text("Quick Add Patient"),
            content=ft.Container(
                content=ft.Column(
                    [
                        self.name_field,
                        self.phone_field,
                        ft.Row(
                            [self.age_field, self.gender_selector],
                            spacing=MobileSpacing.SM,
                        ),
                        self.error_text,
                    ],
                    spacing=MobileSpacing.MD,
                    tight=True,
                ),
                width=300,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self._handle_cancel),
                ft.ElevatedButton(
                    "Add Patient",
                    on_click=self._handle_save,
                    bgcolor=Colors.PRIMARY_500,
                    color=Colors.NEUTRAL_0,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _handle_cancel(self, e):
        """Handle cancel button."""
        if self.haptic_feedback:
            self.haptic_feedback.light()

        self.open = False
        self.update()

    def _handle_save(self, e):
        """Handle save button."""
        # Validate
        if not self.name_field.value or not self.name_field.value.strip():
            self.error_text.value = "Name is required"
            self.error_text.visible = True
            self.error_text.update()

            if self.haptic_feedback:
                self.haptic_feedback.warning()
            return

        # Success haptic
        if self.haptic_feedback:
            self.haptic_feedback.success()

        # Collect data
        patient_data = {
            "name": self.name_field.value.strip(),
            "phone": self.phone_field.value.strip() if self.phone_field.value else None,
            "age": int(self.age_field.value) if self.age_field.value else None,
            "gender": self.gender_selector.value,
            "created_at": datetime.now(),
        }

        # Call save handler
        if self.on_save:
            self.on_save(patient_data)

        # Close dialog
        self.open = False
        self.update()


__all__ = [
    'AddPatientScreen',
    'QuickAddPatientDialog',
]
