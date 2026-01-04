"""
Prescription Viewer Screen - Full-screen prescription viewer.

Shows:
- Patient name and date in header
- Back button
- Share button (native share sheet)
- Download/save button
- Prescription details in scrollable view
- Loading state while PDF generates
- Error state if PDF not found

Note: True PDF rendering requires platform-specific implementation.
For Mobile Lite, we show a formatted text view with PDF export/share.
"""

import flet as ft
from typing import Optional, Callable, Dict, Any
import json
import logging

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..haptics import HapticFeedback

logger = logging.getLogger(__name__)


class PrescriptionViewer(ft.Container):
    """
    Full-screen prescription viewer.

    Usage:
        viewer = PrescriptionViewer(
            visit_data=visit,
            patient_data=patient,
            on_back=handle_back,
            on_share=handle_share,
            haptic_feedback=haptics,
        )
    """

    def __init__(
        self,
        visit_data: Optional[Dict[str, Any]] = None,
        patient_data: Optional[Dict[str, Any]] = None,
        on_back: Optional[Callable] = None,
        on_share: Optional[Callable[[bytes, str], None]] = None,
        on_download: Optional[Callable[[bytes, str], None]] = None,
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.visit_data = visit_data
        self.patient_data = patient_data
        self.on_back = on_back
        self.on_share = on_share
        self.on_download = on_download
        self.haptic_feedback = haptic_feedback

        # State
        self.is_loading = True
        self.error_message = None
        self.prescription = None
        self.pdf_bytes = None

        # UI elements
        self.content_view = ft.ListView(
            spacing=MobileSpacing.SM,
            padding=MobileSpacing.SCREEN_PADDING,
            expand=True,
        )

        self.loading_view = self._create_loading_view()
        self.error_view = self._create_error_view()

        # Parse prescription
        self._parse_prescription()

        # Build content
        content = self._build_content()

        super().__init__(
            content=content,
            expand=True,
            bgcolor=Colors.NEUTRAL_50,
        )

    def _parse_prescription(self):
        """Parse prescription JSON from visit data."""
        if not self.visit_data:
            self.error_message = "No visit data provided"
            self.is_loading = False
            return

        prescription_json = self.visit_data.get('prescription_json')
        if not prescription_json:
            self.error_message = "No prescription found for this visit"
            self.is_loading = False
            return

        try:
            if isinstance(prescription_json, str):
                self.prescription = json.loads(prescription_json)
            else:
                self.prescription = prescription_json

            self.is_loading = False

        except Exception as e:
            logger.error(f"Error parsing prescription: {e}")
            self.error_message = "Failed to load prescription"
            self.is_loading = False

    def _build_content(self) -> ft.Column:
        """Build screen content."""
        patient_name = self.patient_data.get('name', 'Unknown') if self.patient_data else 'Unknown'
        visit_date = self.visit_data.get('visit_date', '') if self.visit_data else ''

        return ft.Column(
            [
                # Header
                ft.Container(
                    content=ft.Column(
                        [
                            # Top bar with back button
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.ARROW_BACK,
                                        icon_color=Colors.NEUTRAL_900,
                                        icon_size=24,
                                        on_click=self._handle_back,
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text(
                                                patient_name,
                                                size=MobileTypography.TITLE_MEDIUM,
                                                weight=ft.FontWeight.W_600,
                                                color=Colors.NEUTRAL_900,
                                            ),
                                            ft.Text(
                                                f"Prescription - {visit_date}",
                                                size=MobileTypography.BODY_SMALL,
                                                color=Colors.NEUTRAL_600,
                                            ),
                                        ],
                                        spacing=0,
                                        expand=True,
                                    ),
                                    # Share button
                                    ft.IconButton(
                                        icon=ft.Icons.SHARE,
                                        icon_color=Colors.PRIMARY_500,
                                        icon_size=24,
                                        on_click=self._handle_share,
                                        tooltip="Share prescription",
                                    ),
                                    # Download button
                                    ft.IconButton(
                                        icon=ft.Icons.DOWNLOAD,
                                        icon_color=Colors.PRIMARY_500,
                                        icon_size=24,
                                        on_click=self._handle_download,
                                        tooltip="Save prescription",
                                    ),
                                ],
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

                # Content area (stack for loading/error states)
                ft.Stack(
                    [
                        # Main content
                        self.content_view,
                        # Loading overlay
                        self.loading_view,
                        # Error overlay
                        self.error_view,
                    ],
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

    def _create_loading_view(self) -> ft.Container:
        """Create loading state view."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(color=Colors.PRIMARY_500),
                    ft.Container(height=MobileSpacing.MD),
                    ft.Text(
                        "Loading prescription...",
                        size=MobileTypography.BODY_MEDIUM,
                        color=Colors.NEUTRAL_600,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            bgcolor=Colors.NEUTRAL_50,
            visible=self.is_loading,
            expand=True,
        )

    def _create_error_view(self) -> ft.Container:
        """Create error state view."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=Colors.ERROR_MAIN),
                    ft.Container(height=MobileSpacing.MD),
                    ft.Text(
                        self.error_message or "Failed to load prescription",
                        size=MobileTypography.BODY_MEDIUM,
                        color=Colors.NEUTRAL_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=MobileSpacing.LG),
                    ft.ElevatedButton(
                        "Go Back",
                        icon=ft.Icons.ARROW_BACK,
                        on_click=self._handle_back,
                        style=ft.ButtonStyle(
                            bgcolor=Colors.PRIMARY_500,
                            color=Colors.NEUTRAL_0,
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            bgcolor=Colors.NEUTRAL_50,
            visible=bool(self.error_message),
            expand=True,
        )

    def set_data(
        self,
        visit_data: Dict[str, Any],
        patient_data: Dict[str, Any],
    ):
        """
        Set prescription data and render.

        Args:
            visit_data: Visit information including prescription_json
            patient_data: Patient information
        """
        self.visit_data = visit_data
        self.patient_data = patient_data
        self.is_loading = True
        self.error_message = None

        # Update visibility
        self.loading_view.visible = True
        self.error_view.visible = False

        # Parse prescription
        self._parse_prescription()

        # Render content
        if not self.error_message and self.prescription:
            self._render_prescription()
            self.loading_view.visible = False
        else:
            self.loading_view.visible = False
            self.error_view.visible = True

        self.update()

    def _render_prescription(self):
        """Render prescription details."""
        self.content_view.controls.clear()

        if not self.prescription:
            return

        # Patient Info Card
        self.content_view.controls.append(
            self._create_section_card(
                "Patient Information",
                self._render_patient_info(),
            )
        )

        # Chief Complaint
        chief_complaint = self.visit_data.get('chief_complaint')
        if chief_complaint:
            self.content_view.controls.append(
                self._create_section_card(
                    "Chief Complaint",
                    [ft.Text(chief_complaint, size=MobileTypography.BODY_MEDIUM, color=Colors.NEUTRAL_800)],
                )
            )

        # Diagnosis
        diagnoses = self.prescription.get('diagnosis', [])
        if diagnoses:
            self.content_view.controls.append(
                self._create_section_card(
                    "Diagnosis",
                    [
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.CIRCLE, size=6, color=Colors.NEUTRAL_600),
                                        ft.Text(dx, size=MobileTypography.BODY_MEDIUM, color=Colors.NEUTRAL_800),
                                    ],
                                    spacing=MobileSpacing.XS,
                                )
                                for dx in diagnoses
                            ],
                            spacing=4,
                        )
                    ],
                )
            )

        # Medications (Rx)
        medications = self.prescription.get('medications', [])
        if medications:
            self.content_view.controls.append(
                self._create_rx_section(medications)
            )

        # Investigations
        investigations = self.prescription.get('investigations', [])
        if investigations:
            self.content_view.controls.append(
                self._create_section_card(
                    "Investigations Advised",
                    [
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.CIRCLE, size=6, color=Colors.INFO_MAIN),
                                        ft.Text(inv, size=MobileTypography.BODY_MEDIUM, color=Colors.NEUTRAL_800),
                                    ],
                                    spacing=MobileSpacing.XS,
                                )
                                for inv in investigations
                            ],
                            spacing=4,
                        )
                    ],
                    icon=ft.Icons.SCIENCE,
                    icon_color=Colors.INFO_MAIN,
                )
            )

        # Advice
        advice = self.prescription.get('advice', [])
        if advice:
            self.content_view.controls.append(
                self._create_section_card(
                    "Advice",
                    [
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.CIRCLE, size=6, color=Colors.SUCCESS_MAIN),
                                        ft.Text(adv, size=MobileTypography.BODY_MEDIUM, color=Colors.NEUTRAL_800),
                                    ],
                                    spacing=MobileSpacing.XS,
                                )
                                for adv in advice
                            ],
                            spacing=4,
                        )
                    ],
                    icon=ft.Icons.LIGHTBULB_OUTLINE,
                    icon_color=Colors.SUCCESS_MAIN,
                )
            )

        # Follow-up
        follow_up = self.prescription.get('follow_up')
        if follow_up:
            self.content_view.controls.append(
                self._create_section_card(
                    "Follow-up",
                    [
                        ft.Text(
                            follow_up,
                            size=MobileTypography.BODY_LARGE,
                            weight=ft.FontWeight.W_500,
                            color=Colors.ACCENT_500,
                        )
                    ],
                    icon=ft.Icons.EVENT,
                    icon_color=Colors.ACCENT_500,
                )
            )

        # Red Flags
        red_flags = self.prescription.get('red_flags', [])
        if red_flags:
            self.content_view.controls.append(
                self._create_red_flags_section(red_flags)
            )

    def _render_patient_info(self) -> list:
        """Render patient information."""
        info_items = []

        if self.patient_data:
            name = self.patient_data.get('name', 'Unknown')
            age = self.patient_data.get('age')
            gender = self.patient_data.get('gender', 'O')
            uhid = self.patient_data.get('uhid', '')

            info_items.append(
                ft.Text(
                    name,
                    size=MobileTypography.TITLE_MEDIUM,
                    weight=ft.FontWeight.W_600,
                    color=Colors.NEUTRAL_900,
                )
            )

            demographics = []
            if age:
                demographics.append(f"{age} years")
            if gender:
                demographics.append(gender)
            if uhid:
                demographics.append(f"UHID: {uhid}")

            if demographics:
                info_items.append(
                    ft.Text(
                        " • ".join(demographics),
                        size=MobileTypography.BODY_SMALL,
                        color=Colors.NEUTRAL_600,
                    )
                )

        return info_items

    def _create_section_card(
        self,
        title: str,
        content: list,
        icon: Optional[str] = None,
        icon_color: Optional[str] = None,
    ) -> ft.Container:
        """Create a section card."""
        header_items = []

        if icon:
            header_items.append(
                ft.Icon(icon, size=20, color=icon_color or Colors.PRIMARY_500)
            )

        header_items.append(
            ft.Text(
                title,
                size=MobileTypography.BODY_LARGE,
                weight=ft.FontWeight.W_600,
                color=Colors.NEUTRAL_900,
            )
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(header_items, spacing=MobileSpacing.XS),
                    ft.Container(height=MobileSpacing.XS),
                    *content,
                ],
                spacing=0,
            ),
            bgcolor=Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
        )

    def _create_rx_section(self, medications: list) -> ft.Container:
        """Create Rx section with medications."""
        med_items = []

        for i, med in enumerate(medications, 1):
            # Medication name and strength
            med_line = f"{i}. {med.get('drug_name', 'Unknown')}"
            if med.get('strength'):
                med_line += f" {med['strength']}"
            if med.get('form') and med['form'] != "tablet":
                med_line += f" ({med['form']})"

            # Dosage instructions
            dosage_parts = []
            if med.get('dose'):
                dosage_parts.append(med['dose'])
            if med.get('frequency'):
                dosage_parts.append(med['frequency'])
            if med.get('duration'):
                dosage_parts.append(f"× {med['duration']}")

            dosage_line = " ".join(dosage_parts)

            if med.get('instructions'):
                instructions_line = med['instructions']
            else:
                instructions_line = None

            # Build medication card
            med_card = ft.Column(
                [
                    ft.Text(
                        med_line,
                        size=MobileTypography.BODY_LARGE,
                        weight=ft.FontWeight.W_600,
                        color=Colors.NEUTRAL_900,
                    ),
                    ft.Text(
                        dosage_line,
                        size=MobileTypography.BODY_MEDIUM,
                        color=Colors.NEUTRAL_700,
                    ),
                    ft.Text(
                        instructions_line,
                        size=MobileTypography.BODY_SMALL,
                        color=Colors.NEUTRAL_600,
                        italic=True,
                    ) if instructions_line else ft.Container(),
                ],
                spacing=2,
            )

            med_items.append(med_card)

            # Add divider between medications
            if i < len(medications):
                med_items.append(
                    ft.Divider(height=1, color=Colors.NEUTRAL_200)
                )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "Rx",
                                size=MobileTypography.DISPLAY_MEDIUM,
                                weight=ft.FontWeight.W_700,
                                color=Colors.PRIMARY_500,
                            ),
                        ],
                    ),
                    ft.Container(height=MobileSpacing.SM),
                    *med_items,
                ],
                spacing=MobileSpacing.SM,
            ),
            bgcolor=Colors.NEUTRAL_0,
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
        )

    def _create_red_flags_section(self, red_flags: list) -> ft.Container:
        """Create red flags warning section."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.WARNING_AMBER, size=24, color=Colors.ERROR_MAIN),
                            ft.Text(
                                "RED FLAGS",
                                size=MobileTypography.BODY_LARGE,
                                weight=ft.FontWeight.W_700,
                                color=Colors.ERROR_MAIN,
                            ),
                        ],
                        spacing=MobileSpacing.XS,
                    ),
                    ft.Text(
                        "Seek immediate medical attention if:",
                        size=MobileTypography.BODY_SMALL,
                        color=Colors.NEUTRAL_700,
                    ),
                    ft.Container(height=MobileSpacing.XS),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.CIRCLE, size=6, color=Colors.ERROR_MAIN),
                                    ft.Text(
                                        flag,
                                        size=MobileTypography.BODY_MEDIUM,
                                        color=Colors.NEUTRAL_900,
                                    ),
                                ],
                                spacing=MobileSpacing.XS,
                            )
                            for flag in red_flags
                        ],
                        spacing=4,
                    ),
                ],
                spacing=4,
            ),
            bgcolor=Colors.ERROR_LIGHT,
            border=ft.border.all(1, Colors.ERROR_MAIN),
            border_radius=Radius.CARD,
            padding=MobileSpacing.CARD_PADDING,
        )

    def _handle_back(self, e=None):
        """Handle back button with haptic feedback."""
        if self.haptic_feedback:
            self.haptic_feedback.light()

        if self.on_back:
            self.on_back()

    def _handle_share(self, e=None):
        """Handle share button with haptic feedback."""
        if self.haptic_feedback:
            self.haptic_feedback.medium()

        # Generate PDF on-the-fly if needed
        # For now, trigger callback
        if self.on_share:
            patient_name = self.patient_data.get('name', 'Unknown') if self.patient_data else 'Unknown'
            # Pass visit and patient data to callback
            self.on_share(self.visit_data, patient_name)

    def _handle_download(self, e=None):
        """Handle download button with haptic feedback."""
        if self.haptic_feedback:
            self.haptic_feedback.medium()

        # Generate PDF and save
        if self.on_download:
            patient_name = self.patient_data.get('name', 'Unknown') if self.patient_data else 'Unknown'
            # Pass visit and patient data to callback
            self.on_download(self.visit_data, patient_name)
