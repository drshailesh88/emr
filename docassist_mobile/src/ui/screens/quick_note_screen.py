"""
Quick Note Screen - Voice-to-text clinical notes.

Allows doctors to quickly capture clinical notes using voice input
with automatic SOAP note extraction.
"""

import flet as ft
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import threading

from ..tokens import Colors, MobileSpacing, MobileTypography, Radius
from ..components.patient_card import PatientCard
from ..animations import Animations
from ..haptics import HapticFeedback


@dataclass
class QuickNoteData:
    """Quick note data for saving."""
    patient_id: Optional[int]
    note_text: str
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class QuickNoteScreen(ft.Container):
    """
    Quick note screen for voice-to-text clinical notes.

    Features:
    - Large voice input button
    - Text input fallback
    - AI-extracted SOAP note preview
    - Save as draft / Save to patient
    - Works offline, syncs later

    Usage:
        quick_note = QuickNoteScreen(
            on_save=handle_save,
            on_back=handle_back,
            haptic_feedback=haptic,
        )
    """

    def __init__(
        self,
        on_save: Optional[Callable[[QuickNoteData], None]] = None,
        on_back: Optional[Callable] = None,
        patient_id: Optional[int] = None,
        patient_name: Optional[str] = None,
        haptic_feedback: Optional[HapticFeedback] = None,
    ):
        self.on_save = on_save
        self.on_back = on_back
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.haptic_feedback = haptic_feedback

        # State
        self.is_recording = False
        self.note_text = ""
        self.soap_preview: Optional[Dict[str, str]] = None

        # Build UI
        self._build_ui()

        super().__init__(
            content=self.main_column,
            bgcolor=Colors.NEUTRAL_50,
            expand=True,
        )

    def _build_ui(self):
        """Build the screen UI."""
        # App bar
        self.app_bar = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=self._handle_back,
                        icon_color=Colors.NEUTRAL_900,
                    ),
                    ft.Text(
                        "Quick Note",
                        size=MobileTypography.TITLE_LARGE,
                        weight=ft.FontWeight.W_600,
                        color=Colors.NEUTRAL_900,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.HISTORY,
                        on_click=self._show_recent_notes,
                        icon_color=Colors.NEUTRAL_600,
                        tooltip="Recent notes",
                    ),
                ],
                spacing=MobileSpacing.SM,
            ),
            bgcolor=Colors.NEUTRAL_0,
            padding=ft.padding.symmetric(
                horizontal=MobileSpacing.SCREEN_PADDING,
                vertical=MobileSpacing.SM,
            ),
        )

        # Patient selector (if no patient selected)
        self.patient_selector = self._build_patient_selector()

        # Voice input button
        self.voice_button = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.MIC,
                            size=64,
                            color=Colors.NEUTRAL_0,
                        ),
                        width=120,
                        height=120,
                        border_radius=Radius.FULL,
                        bgcolor=Colors.PRIMARY_500,
                        alignment=ft.alignment.center,
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=20,
                            color=Colors.PRIMARY_500 + "40",
                            offset=ft.Offset(0, 4),
                        ),
                    ),
                    ft.Container(height=MobileSpacing.MD),
                    ft.Text(
                        "Tap to record",
                        size=MobileTypography.BODY_LARGE,
                        weight=ft.FontWeight.W_500,
                        color=Colors.NEUTRAL_900,
                    ),
                    ft.Text(
                        "Speak your clinical notes",
                        size=MobileTypography.BODY_SMALL,
                        color=Colors.NEUTRAL_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=self._toggle_recording,
            ink=True,
            border_radius=Radius.LG,
            padding=MobileSpacing.XL,
            alignment=ft.alignment.center,
            animate_scale=Animations.scale_tap(),
            scale=1.0,
        )

        # Text input (fallback)
        self.text_input = ft.TextField(
            label="Or type your notes",
            hint_text="Chief complaint, examination findings, diagnosis...",
            multiline=True,
            min_lines=4,
            max_lines=8,
            border_color=Colors.NEUTRAL_300,
            focused_border_color=Colors.PRIMARY_500,
            on_change=self._handle_text_change,
        )

        # SOAP preview (shown after text entry)
        self.soap_preview_container = ft.Container(
            visible=False,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.AUTO_AWESOME, color=Colors.PRIMARY_500, size=20),
                            ft.Text(
                                "AI-Extracted SOAP Note",
                                size=MobileTypography.TITLE_SMALL,
                                weight=ft.FontWeight.W_600,
                                color=Colors.NEUTRAL_900,
                            ),
                        ],
                        spacing=MobileSpacing.SM,
                    ),
                    ft.Container(height=MobileSpacing.SM),
                    ft.Container(
                        content=ft.Column(
                            spacing=MobileSpacing.MD,
                        ),
                        bgcolor=Colors.NEUTRAL_0,
                        border_radius=Radius.MD,
                        padding=MobileSpacing.CARD_PADDING,
                    ),
                ],
            ),
        )

        # Action buttons
        self.action_buttons = ft.Row(
            [
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.DRAFTS, size=20),
                            ft.Text("Save as Draft"),
                        ],
                        spacing=MobileSpacing.XS,
                    ),
                    on_click=self._save_as_draft,
                    style=ft.ButtonStyle(
                        bgcolor=Colors.NEUTRAL_0,
                        color=Colors.NEUTRAL_900,
                    ),
                    expand=True,
                ),
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.SAVE, size=20),
                            ft.Text("Save to Patient"),
                        ],
                        spacing=MobileSpacing.XS,
                    ),
                    on_click=self._save_to_patient,
                    style=ft.ButtonStyle(
                        bgcolor=Colors.PRIMARY_500,
                        color=Colors.NEUTRAL_0,
                    ),
                    expand=True,
                    disabled=not self.patient_id,
                ),
            ],
            spacing=MobileSpacing.MD,
        )

        # Recording indicator
        self.recording_indicator = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=12,
                        height=12,
                        border_radius=Radius.FULL,
                        bgcolor=Colors.ERROR_MAIN,
                        animate_opacity=ft.animation.Animation(800, ft.AnimationCurve.EASE_IN_OUT),
                    ),
                    ft.Text(
                        "Recording...",
                        size=MobileTypography.BODY_MEDIUM,
                        weight=ft.FontWeight.W_500,
                        color=Colors.ERROR_MAIN,
                    ),
                ],
                spacing=MobileSpacing.SM,
            ),
            bgcolor=Colors.ERROR_MAIN + "20",
            border_radius=Radius.FULL,
            padding=ft.padding.symmetric(horizontal=MobileSpacing.MD, vertical=MobileSpacing.SM),
            visible=False,
            alignment=ft.alignment.center,
        )

        # Main content
        content_column = ft.Column(
            [
                self.patient_selector,
                ft.Container(height=MobileSpacing.LG),
                self.voice_button,
                ft.Container(height=MobileSpacing.XL),
                self.recording_indicator,
                self.text_input,
                ft.Container(height=MobileSpacing.LG),
                self.soap_preview_container,
            ],
            spacing=MobileSpacing.MD,
            scroll=ft.ScrollMode.AUTO,
        )

        # Main column
        self.main_column = ft.Column(
            [
                self.app_bar,
                ft.Container(
                    content=content_column,
                    padding=MobileSpacing.SCREEN_PADDING,
                    expand=True,
                ),
                ft.Container(
                    content=self.action_buttons,
                    bgcolor=Colors.NEUTRAL_0,
                    padding=MobileSpacing.SCREEN_PADDING,
                    border=ft.border.only(top=ft.BorderSide(1, Colors.NEUTRAL_200)),
                ),
            ],
            spacing=0,
            expand=True,
        )

    def _build_patient_selector(self) -> ft.Container:
        """Build patient selector if no patient selected."""
        if self.patient_id and self.patient_name:
            # Show selected patient
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.PERSON, color=Colors.PRIMARY_500),
                        ft.Text(
                            self.patient_name,
                            size=MobileTypography.BODY_LARGE,
                            weight=ft.FontWeight.W_500,
                            color=Colors.NEUTRAL_900,
                            expand=True,
                        ),
                        ft.TextButton(
                            "Change",
                            on_click=self._change_patient,
                        ),
                    ],
                    spacing=MobileSpacing.SM,
                ),
                bgcolor=Colors.PRIMARY_50,
                border_radius=Radius.MD,
                padding=MobileSpacing.CARD_PADDING,
            )
        else:
            # Show patient selector button
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.PERSON_ADD, color=Colors.NEUTRAL_600),
                        ft.Text(
                            "Select Patient (Optional)",
                            size=MobileTypography.BODY_LARGE,
                            color=Colors.NEUTRAL_600,
                        ),
                    ],
                    spacing=MobileSpacing.SM,
                ),
                bgcolor=Colors.NEUTRAL_100,
                border_radius=Radius.MD,
                padding=MobileSpacing.CARD_PADDING,
                on_click=self._select_patient,
                ink=True,
            )

    def _toggle_recording(self, e):
        """Toggle voice recording."""
        if self.haptic_feedback:
            self.haptic_feedback.medium()

        self.is_recording = not self.is_recording

        if self.is_recording:
            # Start recording
            self._start_recording()
        else:
            # Stop recording
            self._stop_recording()

    def _start_recording(self):
        """Start voice recording."""
        # Update UI
        self.voice_button.content.controls[0].content.name = ft.Icons.STOP
        self.voice_button.content.controls[0].bgcolor = Colors.ERROR_MAIN
        self.voice_button.content.controls[2].value = "Tap to stop"
        self.recording_indicator.visible = True

        self.update()

        # TODO: Integrate with speech-to-text service
        # For now, show a placeholder message after 3 seconds
        def simulate_transcription():
            import time
            time.sleep(3)
            if self.is_recording:
                self.is_recording = False
                self.page.run_task(self._on_transcription_complete)

        threading.Thread(target=simulate_transcription, daemon=True).start()

    def _stop_recording(self):
        """Stop voice recording."""
        # Update UI
        self.voice_button.content.controls[0].content.name = ft.Icons.MIC
        self.voice_button.content.controls[0].bgcolor = Colors.PRIMARY_500
        self.voice_button.content.controls[2].value = "Tap to record"
        self.recording_indicator.visible = False

        self.update()

    def _on_transcription_complete(self):
        """Handle transcription completion."""
        # Simulated transcription result
        transcribed_text = "Patient complains of chest pain radiating to left arm. Started 2 hours ago. BP 140/90, HR 88. ECG shows ST elevation. Diagnosis: Acute MI. Plan: Aspirin 300mg stat, shift to CCU."

        self.text_input.value = transcribed_text
        self.note_text = transcribed_text

        # Extract SOAP note
        self._extract_soap_note()

        # Update UI
        self._stop_recording()
        self.update()

    def _handle_text_change(self, e):
        """Handle text input change."""
        self.note_text = e.control.value

        # Auto-extract SOAP if text is long enough
        if len(self.note_text) > 50:
            self._extract_soap_note()

    def _extract_soap_note(self):
        """Extract SOAP note from text using simple parsing."""
        # TODO: Integrate with LLM for better extraction
        # For now, use simple keyword matching

        text = self.note_text.lower()

        soap = {
            "subjective": "",
            "objective": "",
            "assessment": "",
            "plan": "",
        }

        # Simple extraction (placeholder)
        # In production, this should use the LLM service
        if "complains" in text or "c/o" in text:
            soap["subjective"] = self.note_text[:100] + "..."

        if "bp" in text or "hr" in text or "ecg" in text:
            soap["objective"] = "Vitals and examination findings extracted"

        if "diagnosis" in text or "dx:" in text:
            soap["assessment"] = "Diagnosis extracted from note"

        if "plan" in text or "rx:" in text:
            soap["plan"] = "Treatment plan extracted"

        self.soap_preview = soap
        self._update_soap_preview()

    def _update_soap_preview(self):
        """Update SOAP preview UI."""
        if not self.soap_preview:
            self.soap_preview_container.visible = False
            self.update()
            return

        # Build SOAP sections
        soap_sections = []

        sections = [
            ("Subjective", self.soap_preview.get("subjective")),
            ("Objective", self.soap_preview.get("objective")),
            ("Assessment", self.soap_preview.get("assessment")),
            ("Plan", self.soap_preview.get("plan")),
        ]

        for title, content in sections:
            if content:
                soap_sections.append(
                    ft.Column(
                        [
                            ft.Text(
                                title,
                                size=MobileTypography.BODY_SMALL,
                                weight=ft.FontWeight.W_600,
                                color=Colors.PRIMARY_500,
                            ),
                            ft.Text(
                                content,
                                size=MobileTypography.BODY_MEDIUM,
                                color=Colors.NEUTRAL_700,
                            ),
                        ],
                        spacing=4,
                    )
                )

        # Update preview container
        preview_content = self.soap_preview_container.content.controls[2]
        preview_content.content.controls.clear()
        preview_content.content.controls.extend(soap_sections)

        self.soap_preview_container.visible = True
        self.update()

    def _save_as_draft(self, e):
        """Save note as draft."""
        if self.haptic_feedback:
            self.haptic_feedback.success()

        note_data = QuickNoteData(
            patient_id=self.patient_id,
            note_text=self.note_text,
            subjective=self.soap_preview.get("subjective") if self.soap_preview else None,
            objective=self.soap_preview.get("objective") if self.soap_preview else None,
            assessment=self.soap_preview.get("assessment") if self.soap_preview else None,
            plan=self.soap_preview.get("plan") if self.soap_preview else None,
        )

        if self.on_save:
            self.on_save(note_data)

        # Show confirmation
        self._show_snackbar("Note saved as draft", Colors.SUCCESS_MAIN)

    def _save_to_patient(self, e):
        """Save note to patient record."""
        if not self.patient_id:
            self._show_snackbar("Please select a patient first", Colors.ERROR_MAIN)
            return

        if self.haptic_feedback:
            self.haptic_feedback.success()

        note_data = QuickNoteData(
            patient_id=self.patient_id,
            note_text=self.note_text,
            subjective=self.soap_preview.get("subjective") if self.soap_preview else None,
            objective=self.soap_preview.get("objective") if self.soap_preview else None,
            assessment=self.soap_preview.get("assessment") if self.soap_preview else None,
            plan=self.soap_preview.get("plan") if self.soap_preview else None,
        )

        if self.on_save:
            self.on_save(note_data)

        # Show confirmation and clear
        self._show_snackbar(f"Note saved to {self.patient_name}", Colors.SUCCESS_MAIN)
        self._clear_note()

    def _clear_note(self):
        """Clear the note."""
        self.note_text = ""
        self.text_input.value = ""
        self.soap_preview = None
        self.soap_preview_container.visible = False
        self.update()

    def _select_patient(self, e):
        """Show patient selector."""
        # TODO: Implement patient selector dialog
        self._show_snackbar("Patient selector - Coming soon", Colors.INFO_MAIN)

    def _change_patient(self, e):
        """Change selected patient."""
        # TODO: Implement patient selector dialog
        self._show_snackbar("Patient selector - Coming soon", Colors.INFO_MAIN)

    def _show_recent_notes(self, e):
        """Show recent notes."""
        # TODO: Implement recent notes view
        self._show_snackbar("Recent notes - Coming soon", Colors.INFO_MAIN)

    def _handle_back(self, e):
        """Handle back button."""
        if self.haptic_feedback:
            self.haptic_feedback.light()

        if self.on_back:
            self.on_back()

    def _show_snackbar(self, message: str, bgcolor: str):
        """Show snackbar message."""
        if hasattr(self, 'page') and self.page:
            snackbar = ft.SnackBar(
                content=ft.Text(message, color=Colors.NEUTRAL_0),
                bgcolor=bgcolor,
                duration=3000,
            )
            self.page.overlay.append(snackbar)
            snackbar.open = True
            self.page.update()
