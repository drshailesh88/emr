"""
Add Visit Screen - Create new patient visit.

Premium screen for adding visit with prescription builder.
"""

import flet as ft
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass, field

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..haptics import HapticFeedback


@dataclass
class MedicationData:
    """Medication entry data."""
    drug_name: str = ""
    strength: str = ""
    form: str = "tablet"
    dose: str = "1"
    frequency: str = "BD"
    duration: str = "7 days"
    instructions: str = "after meals"


@dataclass
class VisitFormData:
    """Visit form data."""
    chief_complaint: str = ""
    clinical_notes: str = ""
    diagnosis: str = ""
    medications: List[MedicationData] = field(default_factory=list)
    investigations: str = ""
    advice: str = ""
    follow_up: str = ""


class AddVisitScreen(ft.Container):
    """
    Add visit screen with prescription builder.

    Usage:
        screen = AddVisitScreen(
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
        on_save: Callable[[int, VisitFormData], None],
        on_cancel: Callable[[], None],
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.haptic_feedback = haptic_feedback
        self.medications: List[MedicationData] = []

        # Form fields
        self.chief_complaint_field = ft.TextField(
            label="Chief Complaint",
            hint_text="e.g., Chest pain x 2 days",
            border_radius=Radius.MD,
            multiline=False,
            max_lines=1,
        )

        self.clinical_notes_field = ft.TextField(
            label="Clinical Notes",
            hint_text="History, examination findings...",
            border_radius=Radius.MD,
            multiline=True,
            min_lines=4,
            max_lines=8,
        )

        self.diagnosis_field = ft.TextField(
            label="Diagnosis",
            hint_text="e.g., NSTEMI, Hypertension",
            border_radius=Radius.MD,
            multiline=False,
            max_lines=1,
        )

        self.investigations_field = ft.TextField(
            label="Investigations (comma-separated)",
            hint_text="e.g., CBC, ECG, Troponin",
            border_radius=Radius.MD,
            multiline=False,
            max_lines=1,
        )

        self.advice_field = ft.TextField(
            label="Advice (comma-separated)",
            hint_text="e.g., Rest, Low salt diet",
            border_radius=Radius.MD,
            multiline=False,
            max_lines=1,
        )

        self.follow_up_field = ft.TextField(
            label="Follow-up",
            hint_text="e.g., 1 week, 2 weeks",
            border_radius=Radius.MD,
            multiline=False,
            max_lines=1,
        )

        self.error_text = ft.Text(
            "",
            size=MobileTypography.BODY_SMALL,
            color=Colors.ERROR_MAIN,
            visible=False,
        )

        # Medication list container
        self.medications_list = ft.Column(spacing=MobileSpacing.SM)

        # Buttons
        self.save_button = ft.ElevatedButton(
            text="Save Visit",
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
                            ft.Column(
                                [
                                    ft.Text(
                                        "New Visit",
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
                                        # Basic information
                                        self.chief_complaint_field,
                                        ft.Container(height=MobileSpacing.SM),
                                        self.clinical_notes_field,
                                        ft.Container(height=MobileSpacing.SM),
                                        self.diagnosis_field,
                                        ft.Container(height=MobileSpacing.LG),

                                        # Prescription section
                                        ft.Row(
                                            [
                                                ft.Text(
                                                    "Prescription",
                                                    size=MobileTypography.TITLE_MEDIUM,
                                                    weight=ft.FontWeight.W_500,
                                                    color=Colors.NEUTRAL_900,
                                                ),
                                                ft.IconButton(
                                                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                                    icon_color=Colors.PRIMARY_500,
                                                    icon_size=24,
                                                    tooltip="Add medication",
                                                    on_click=self._add_medication,
                                                ),
                                            ],
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        ),
                                        ft.Container(height=MobileSpacing.XS),

                                        # Medications list
                                        self.medications_list,
                                        ft.Container(height=MobileSpacing.LG),

                                        # Additional fields
                                        self.investigations_field,
                                        ft.Container(height=MobileSpacing.SM),
                                        self.advice_field,
                                        ft.Container(height=MobileSpacing.SM),
                                        self.follow_up_field,
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
            ],
            spacing=0,
            expand=True,
        )

    def _add_medication(self, e):
        """Add a new medication entry."""
        if self.haptic_feedback:
            self.haptic_feedback.light()

        med_data = MedicationData()
        self.medications.append(med_data)
        self._render_medication(med_data, len(self.medications) - 1)
        self.medications_list.update()

    def _render_medication(self, med_data: MedicationData, index: int):
        """Render a medication entry."""
        # Create fields for this medication
        drug_field = ft.TextField(
            label="Drug Name",
            value=med_data.drug_name,
            border_radius=Radius.MD,
            on_change=lambda e: setattr(med_data, 'drug_name', e.control.value),
        )

        strength_field = ft.TextField(
            label="Strength",
            value=med_data.strength,
            hint_text="e.g., 500mg",
            border_radius=Radius.MD,
            on_change=lambda e: setattr(med_data, 'strength', e.control.value),
        )

        dose_field = ft.TextField(
            label="Dose",
            value=med_data.dose,
            hint_text="e.g., 1",
            border_radius=Radius.MD,
            on_change=lambda e: setattr(med_data, 'dose', e.control.value),
        )

        frequency_dropdown = ft.Dropdown(
            label="Frequency",
            value=med_data.frequency,
            options=[
                ft.dropdown.Option("OD", "Once daily"),
                ft.dropdown.Option("BD", "Twice daily"),
                ft.dropdown.Option("TDS", "Three times daily"),
                ft.dropdown.Option("QID", "Four times daily"),
                ft.dropdown.Option("SOS", "As needed"),
            ],
            border_radius=Radius.MD,
            on_change=lambda e: setattr(med_data, 'frequency', e.control.value),
        )

        duration_field = ft.TextField(
            label="Duration",
            value=med_data.duration,
            hint_text="e.g., 7 days, 2 weeks",
            border_radius=Radius.MD,
            on_change=lambda e: setattr(med_data, 'duration', e.control.value),
        )

        instructions_field = ft.TextField(
            label="Instructions",
            value=med_data.instructions,
            hint_text="e.g., after meals",
            border_radius=Radius.MD,
            on_change=lambda e: setattr(med_data, 'instructions', e.control.value),
        )

        # Medication card
        med_card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                f"Medication {index + 1}",
                                size=MobileTypography.BODY_MEDIUM,
                                weight=ft.FontWeight.W_500,
                                color=Colors.NEUTRAL_900,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=Colors.ERROR_MAIN,
                                icon_size=20,
                                tooltip="Remove",
                                on_click=lambda e: self._remove_medication(index),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    drug_field,
                    ft.Container(height=MobileSpacing.XS),
                    ft.Row(
                        [strength_field, dose_field],
                        spacing=MobileSpacing.SM,
                    ),
                    ft.Container(height=MobileSpacing.XS),
                    frequency_dropdown,
                    ft.Container(height=MobileSpacing.XS),
                    duration_field,
                    ft.Container(height=MobileSpacing.XS),
                    instructions_field,
                ],
                spacing=MobileSpacing.XS,
            ),
            bgcolor=Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
            border=ft.border.all(1, Colors.NEUTRAL_200),
        )

        self.medications_list.controls.append(med_card)

    def _remove_medication(self, index: int):
        """Remove a medication entry."""
        if self.haptic_feedback:
            self.haptic_feedback.light()

        if 0 <= index < len(self.medications):
            self.medications.pop(index)
            self.medications_list.controls.clear()
            # Re-render all medications
            for i, med in enumerate(self.medications):
                self._render_medication(med, i)
            self.medications_list.update()

    def _validate_form(self) -> bool:
        """Validate form data."""
        if not self.chief_complaint_field.value:
            self._show_error("Chief complaint is required")
            return False

        if not self.diagnosis_field.value:
            self._show_error("Diagnosis is required")
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
        form_data = VisitFormData(
            chief_complaint=self.chief_complaint_field.value or "",
            clinical_notes=self.clinical_notes_field.value or "",
            diagnosis=self.diagnosis_field.value or "",
            medications=self.medications.copy(),
            investigations=self.investigations_field.value or "",
            advice=self.advice_field.value or "",
            follow_up=self.follow_up_field.value or "",
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
        self.update()

    def show_save_error(self, message: str = "Failed to save visit"):
        """Show save error and reset loading state."""
        self._set_loading(False)
        self._show_error(message)
        if self.haptic_feedback:
            self.haptic_feedback.error()

    def reset(self):
        """Reset form to initial state."""
        self.chief_complaint_field.value = ""
        self.clinical_notes_field.value = ""
        self.diagnosis_field.value = ""
        self.investigations_field.value = ""
        self.advice_field.value = ""
        self.follow_up_field.value = ""
        self.medications.clear()
        self.medications_list.controls.clear()
        self._hide_error()
        self._set_loading(False)
        self.update()
