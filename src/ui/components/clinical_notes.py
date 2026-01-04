"""Premium Clinical Notes Component.

Chief complaint and clinical notes entry with voice input support.
"""

import flet as ft
from typing import Optional, Callable

from .expandable_text import ExpandableTextField, ExpandableTextArea
from .voice_input import VoiceInputButton
from ..tokens import Colors, Typography, Spacing, Radius
from ...services.database import DatabaseService


class ClinicalNotesForm:
    """Premium clinical notes entry form with voice support."""

    def __init__(
        self,
        db: DatabaseService,
        is_dark: bool = False,
    ):
        self.db = db
        self.is_dark = is_dark

        # Field references
        self.complaint_field: Optional[ExpandableTextField] = None
        self.notes_field: Optional[ExpandableTextArea] = None
        self.voice_btn: Optional[VoiceInputButton] = None

    def build(self) -> ft.Column:
        """Build the clinical notes form."""
        # Chief complaint field
        self.complaint_field = ExpandableTextField(
            db=self.db,
            label="Chief Complaint",
            hint_text="e.g., Chest pain × 2 days, fever, breathlessness (Try: c/o for 'complains of')",
            multiline=True,
            min_lines=1,
            max_lines=2,
            border_radius=Radius.INPUT,
        )

        # Clinical notes with examples
        notes_hint = """Enter clinical findings, vitals, examination notes...

Try shortcuts: c/o, h/o, vitals, cvs, rs, etc.

Example:
Pt c/o chest pain × 2 days, radiating to left arm.
H/o HTN, DM type 2.
BP: 140/90, PR: 88/min
CVS: S1S2 normal, no murmur
RS: NVBS bilateral

Impr: Unstable angina, r/o ACS"""

        self.notes_field = ExpandableTextArea(
            db=self.db,
            label="Clinical Notes",
            hint_text=notes_hint,
            multiline=True,
            min_lines=8,
            max_lines=12,
            border_radius=Radius.INPUT,
            text_size=Typography.BODY_MEDIUM.size,
        )

        # Voice input button
        self.voice_btn = VoiceInputButton(
            on_text=self._on_voice_text,
            size=40,
            tooltip="Voice dictation - click to start/stop"
        )

        # Notes row with voice button
        notes_container = ft.Row([
            ft.Container(content=self.notes_field, expand=True),
            ft.Container(
                content=self.voice_btn,
                alignment=ft.alignment.top_center,
                padding=ft.padding.only(top=5),
            ),
        ], spacing=Spacing.SM, vertical_alignment=ft.CrossAxisAlignment.START)

        return ft.Column([
            self.complaint_field,
            notes_container,
        ], spacing=Spacing.MD)

    def _on_voice_text(self, text: str):
        """Handle voice transcription - insert into notes field."""
        if not text:
            return

        current = self.notes_field.value or ""

        # Add space if needed
        if current and not current.endswith((' ', '\n', '.')):
            text = " " + text

        self.notes_field.value = current + text

        if self.notes_field.page:
            self.notes_field.update()

    def get_complaint(self) -> str:
        """Get the chief complaint text."""
        return self.complaint_field.value.strip() if self.complaint_field.value else ""

    def get_notes(self) -> str:
        """Get the clinical notes text."""
        return self.notes_field.value.strip() if self.notes_field.value else ""

    def set_complaint(self, value: str):
        """Set the chief complaint."""
        if self.complaint_field:
            self.complaint_field.value = value

    def set_notes(self, value: str):
        """Set the clinical notes."""
        if self.notes_field:
            self.notes_field.value = value

    def clear(self):
        """Clear both fields."""
        if self.complaint_field:
            self.complaint_field.value = ""
        if self.notes_field:
            self.notes_field.value = ""
