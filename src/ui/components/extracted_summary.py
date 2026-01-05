"""Extracted clinical summary panel with editing capabilities.

Shows a compact, organized summary of entities extracted from clinical notes.
Allows doctor to correct extractions which feed back to improve the system.
"""

import flet as ft
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExtractedData:
    """Container for all extracted clinical data."""
    patient_info: Dict[str, str] = field(default_factory=dict)  # Age, gender
    chief_complaint: List[str] = field(default_factory=list)
    history: List[str] = field(default_factory=list)  # Past medical history
    vitals: Dict[str, str] = field(default_factory=dict)  # BP, pulse, etc.
    symptoms: List[str] = field(default_factory=list)
    diagnoses: List[str] = field(default_factory=list)
    medications: List[Dict[str, str]] = field(default_factory=list)  # Current meds
    investigations: List[str] = field(default_factory=list)
    extracted_at: datetime = field(default_factory=datetime.now)


class ExtractedSummaryPanel(ft.Container):
    """
    Compact summary panel showing extracted clinical entities.

    Features:
    - Organized by clinical category
    - Inline editing for corrections
    - Visual indicators for confidence
    - Feedback mechanism to improve extraction
    """

    def __init__(
        self,
        extracted_data: Optional[ExtractedData] = None,
        on_correction: Optional[Callable[[str, str, str], None]] = None,
        on_accept_all: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize extracted summary panel.

        Args:
            extracted_data: The extracted clinical data
            on_correction: Callback when user corrects an extraction (category, old_value, new_value)
            on_accept_all: Callback when user accepts all extractions
            **kwargs: Additional Container parameters
        """
        self.extracted_data = extracted_data or ExtractedData()
        self.on_correction = on_correction
        self.on_accept_all = on_accept_all

        # Build summary content
        content = self._build_summary()

        super().__init__(
            content=content,
            padding=15,
            border_radius=8,
            bgcolor=ft.Colors.BLUE_50,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            **kwargs
        )

    def _build_summary(self) -> ft.Control:
        """Build the summary panel content."""
        sections = []

        # Header with accept button
        header = ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME, size=18, color=ft.Colors.BLUE_700),
                ft.Text(
                    "AI Extracted Summary",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_900
                ),
            ], spacing=5),
            ft.IconButton(
                icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                icon_size=18,
                tooltip="Accept all extractions",
                icon_color=ft.Colors.GREEN_700,
                on_click=self._on_accept_all_click,
            ) if self.on_accept_all else ft.Container(),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        sections.append(header)
        sections.append(ft.Divider(height=5, color=ft.Colors.BLUE_300))

        # Check if we have any data
        has_data = any([
            self.extracted_data.patient_info,
            self.extracted_data.chief_complaint,
            self.extracted_data.history,
            self.extracted_data.vitals,
            self.extracted_data.symptoms,
            self.extracted_data.diagnoses,
            self.extracted_data.medications,
            self.extracted_data.investigations,
        ])

        if not has_data:
            sections.append(
                ft.Text(
                    "Start typing clinical notes to see AI extraction...",
                    size=12,
                    color=ft.Colors.GREY_600,
                    italic=True
                )
            )
            return ft.Column(sections, spacing=8)

        # Patient Info
        if self.extracted_data.patient_info:
            sections.append(self._build_section(
                "Patient",
                [f"{k}: {v}" for k, v in self.extracted_data.patient_info.items()],
                ft.Icons.PERSON,
                "patient_info"
            ))

        # Chief Complaint
        if self.extracted_data.chief_complaint:
            sections.append(self._build_section(
                "Chief Complaint",
                self.extracted_data.chief_complaint,
                ft.Icons.CHAT_BUBBLE_OUTLINE,
                "chief_complaint"
            ))

        # History
        if self.extracted_data.history:
            sections.append(self._build_section(
                "History",
                self.extracted_data.history,
                ft.Icons.HISTORY,
                "history"
            ))

        # Vitals
        if self.extracted_data.vitals:
            vitals_list = [f"{k}: {v}" for k, v in self.extracted_data.vitals.items()]
            sections.append(self._build_section(
                "Vitals",
                vitals_list,
                ft.Icons.FAVORITE,
                "vitals",
                color=ft.Colors.PINK_700
            ))

        # Symptoms
        if self.extracted_data.symptoms:
            sections.append(self._build_section(
                "Symptoms",
                self.extracted_data.symptoms,
                ft.Icons.WARNING_AMBER,
                "symptoms",
                color=ft.Colors.ORANGE_700
            ))

        # Diagnoses
        if self.extracted_data.diagnoses:
            sections.append(self._build_section(
                "Diagnoses",
                self.extracted_data.diagnoses,
                ft.Icons.LOCAL_HOSPITAL,
                "diagnoses",
                color=ft.Colors.BLUE_700
            ))

        # Current Medications
        if self.extracted_data.medications:
            med_list = []
            for med in self.extracted_data.medications:
                med_str = med.get('drug_name', '')
                if med.get('strength'):
                    med_str += f" {med['strength']}"
                if med.get('frequency'):
                    med_str += f" {med['frequency']}"
                med_list.append(med_str)

            sections.append(self._build_section(
                "Current Medications",
                med_list,
                ft.Icons.MEDICATION,
                "medications",
                color=ft.Colors.GREEN_700
            ))

        # Investigations
        if self.extracted_data.investigations:
            sections.append(self._build_section(
                "Investigations",
                self.extracted_data.investigations,
                ft.Icons.SCIENCE,
                "investigations",
                color=ft.Colors.AMBER_700
            ))

        return ft.Column(
            sections,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

    def _build_section(
        self,
        title: str,
        items: List[str],
        icon: str,
        category: str,
        color: str = ft.Colors.BLUE_700
    ) -> ft.Control:
        """
        Build a section for a category of extracted data.

        Args:
            title: Section title
            items: List of extracted items
            icon: Icon to display
            category: Category name for corrections
            color: Color for the section

        Returns:
            Section widget
        """
        # Build item chips with edit capability
        item_widgets = []
        for item in items:
            item_widgets.append(
                self._build_editable_chip(item, category, color)
            )

        return ft.Column([
            ft.Row([
                ft.Icon(icon, size=14, color=color),
                ft.Text(
                    title,
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=color
                ),
            ], spacing=5),
            ft.Column(
                item_widgets,
                spacing=4,
            ),
        ], spacing=5)

    def _build_editable_chip(
        self,
        text: str,
        category: str,
        color: str
    ) -> ft.Control:
        """
        Build an editable chip for an extracted item.

        Args:
            text: The extracted text
            category: Category name
            color: Color for the chip

        Returns:
            Editable chip widget
        """
        # State for edit mode
        is_editing = [False]  # Use list to allow mutation in closure
        edit_field = ft.TextField(
            value=text,
            text_size=11,
            dense=True,
            border_radius=5,
            visible=False,
            on_submit=lambda e: self._save_correction(e, text, category, chip_container),
        )

        chip_text = ft.Text(
            text,
            size=11,
            weight=ft.FontWeight.W_500,
        )

        def toggle_edit(e):
            if not is_editing[0]:
                # Enter edit mode
                chip_text.visible = False
                edit_icon.visible = False
                edit_field.visible = True
                edit_field.focus()
                is_editing[0] = True
            if chip_container.page:
                chip_container.update()

        edit_icon = ft.IconButton(
            icon=ft.Icons.EDIT,
            icon_size=12,
            tooltip="Edit this extraction",
            on_click=toggle_edit,
        )

        chip_container = ft.Container(
            content=ft.Row([
                chip_text,
                edit_field,
                edit_icon,
            ], spacing=5, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor=ft.Colors.WHITE,
            border_radius=5,
            border=ft.border.all(1, color),
        )

        return chip_container

    def _save_correction(self, e, old_value: str, category: str, container: ft.Container):
        """Save a correction made by the user."""
        new_value = e.control.value.strip()

        if new_value and new_value != old_value:
            # Trigger correction callback
            if self.on_correction:
                self.on_correction(category, old_value, new_value)

            # Update the display
            container.content.controls[0].value = new_value  # Update chip text
            container.content.controls[0].visible = True
            container.content.controls[1].visible = False  # Hide edit field
            container.content.controls[2].visible = True  # Show edit icon

            if container.page:
                container.update()

    def _on_accept_all_click(self, e):
        """Handle accept all button click."""
        if self.on_accept_all:
            self.on_accept_all()

    def update_data(self, extracted_data: ExtractedData):
        """
        Update the displayed extracted data.

        Args:
            extracted_data: New extracted data
        """
        self.extracted_data = extracted_data
        self.content = self._build_summary()
        if self.page:
            self.update()


class ExtractionLoadingIndicator(ft.Container):
    """Loading indicator for extraction in progress."""

    def __init__(self, **kwargs):
        """Initialize extraction loading indicator."""
        content = ft.Row([
            ft.ProgressRing(width=16, height=16, stroke_width=2),
            ft.Text(
                "Extracting entities...",
                size=12,
                color=ft.Colors.BLUE_700,
                italic=True
            ),
        ], spacing=10)

        super().__init__(
            content=content,
            padding=10,
            border_radius=8,
            bgcolor=ft.Colors.BLUE_50,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            **kwargs
        )
