"""Central panel - Main content area with prescription form."""

import flet as ft
from typing import Callable, Optional, List
import json
from datetime import date

from ..models.schemas import Patient, Visit, Prescription, Medication
from ..services.llm import LLMService
from ..services.database import DatabaseService
from .audit_history_dialog import AuditHistoryDialog
from .template_browser import TemplateBrowser, SaveTemplateDialog


class CentralPanel:
    """Central panel for clinical notes and prescription."""

    def __init__(
        self,
        on_generate_rx: Callable[[str, Callable], None],
        on_save_visit: Callable[[dict], bool],
        on_print_pdf: Callable[[Prescription, str], Optional[str]],
        llm: LLMService,
        db: DatabaseService
    ):
        self.on_generate_rx = on_generate_rx
        self.on_save_visit = on_save_visit
        self.on_print_pdf = on_print_pdf
        self.llm = llm
        self.db = db

        self.current_patient: Optional[Patient] = None
        self.current_prescription: Optional[Prescription] = None
        self.visits: List[Visit] = []

        # UI components
        self.patient_header: Optional[ft.Container] = None
        self.complaint_field: Optional[ft.TextField] = None
        self.notes_field: Optional[ft.TextField] = None
        self.rx_display: Optional[ft.Column] = None
        self.generate_btn: Optional[ft.ElevatedButton] = None
        self.templates_btn: Optional[ft.ElevatedButton] = None
        self.save_template_btn: Optional[ft.ElevatedButton] = None
        self.save_btn: Optional[ft.ElevatedButton] = None
        self.print_btn: Optional[ft.ElevatedButton] = None
        self.loading_indicator: Optional[ft.ProgressRing] = None
        self.tabs: Optional[ft.Tabs] = None
        self.audit_history_btn: Optional[ft.IconButton] = None

        # Audit dialog
        self.audit_dialog = AuditHistoryDialog(db)

        # Template browser
        self.template_browser = TemplateBrowser(db, self._on_template_applied)

    def build(self) -> ft.Control:
        """Build the central panel UI."""

        # Patient header
        self.patient_header = ft.Container(
            content=ft.Text(
                "Select a patient to begin",
                size=16,
                color=ft.Colors.GREY_500,
                italic=True,
            ),
            padding=15,
            bgcolor=ft.Colors.GREY_100,
        )

        # Chief complaint field
        self.complaint_field = ft.TextField(
            label="Chief Complaint",
            hint_text="e.g., Chest pain x 2 days, fever, breathlessness",
            multiline=True,
            min_lines=1,
            max_lines=2,
            border_radius=8,
        )

        # Clinical notes field
        self.notes_field = ft.TextField(
            label="Clinical Notes",
            hint_text="Enter clinical findings, vitals, examination notes...\n\nExample:\nPt c/o chest pain x 2 days, radiating to left arm.\nH/o HTN, DM type 2.\nBP: 140/90, PR: 88/min\nCVS: S1S2 normal, no murmur\nRS: NVBS bilateral\n\nImpr: Unstable angina, r/o ACS",
            multiline=True,
            min_lines=8,
            max_lines=12,
            border_radius=8,
            text_size=13,
        )

        # Loading indicator
        self.loading_indicator = ft.ProgressRing(visible=False, width=20, height=20)

        # Templates button
        self.templates_btn = ft.ElevatedButton(
            text="Templates",
            icon=ft.Icons.DESCRIPTION,
            tooltip="Use clinical template",
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
            ),
            on_click=self._on_templates_click,
            disabled=True,
        )

        # Generate button
        self.generate_btn = ft.ElevatedButton(
            text="Generate Rx",
            icon=ft.Icons.AUTO_AWESOME,
            tooltip="Generate prescription with AI (Ctrl+G)",
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
            ),
            on_click=self._on_generate_click,
            disabled=True,
        )

        # Prescription display area
        self.rx_display = ft.Column(
            [],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

        # Save button
        self.save_btn = ft.ElevatedButton(
            text="Save Visit",
            icon=ft.Icons.SAVE,
            tooltip="Save current visit (Ctrl+S)",
            on_click=self._on_save_click,
            disabled=True,
        )

        # Print button
        self.print_btn = ft.ElevatedButton(
            text="Print PDF",
            icon=ft.Icons.PRINT,
            tooltip="Print prescription as PDF (Ctrl+P)",
            on_click=self._on_print_click,
            disabled=True,
        )

        # Save as template button
        self.save_template_btn = ft.ElevatedButton(
            text="Save as Template",
            icon=ft.Icons.BOOKMARK_ADD,
            tooltip="Save this prescription as a template",
            on_click=self._on_save_template_click,
            disabled=True,
        )

        # Prescription tab content
        rx_tab_content = ft.Container(
            content=ft.Column([
                self.complaint_field,
                self.notes_field,
                ft.Row([
                    self.templates_btn,
                    self.generate_btn,
                    self.loading_indicator,
                ], spacing=10),
                ft.Divider(),
                ft.Text("Generated Prescription:", weight=ft.FontWeight.BOLD, size=14),
                ft.Container(
                    content=self.rx_display,
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=8,
                    padding=15,
                    expand=True,
                ),
                ft.Row([
                    self.save_btn,
                    self.print_btn,
                    self.save_template_btn,
                ], spacing=10),
            ], spacing=15, expand=True),
            padding=20,
            expand=True,
        )

        # History tab content
        self.history_list = ft.ListView(spacing=10, padding=10, expand=True)
        history_tab_content = ft.Container(
            content=self.history_list,
            padding=10,
            expand=True,
        )

        # Tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="Prescription",
                    icon=ft.Icons.MEDICATION,
                    content=rx_tab_content,
                ),
                ft.Tab(
                    text="History",
                    icon=ft.Icons.HISTORY,
                    content=history_tab_content,
                ),
            ],
            expand=True,
        )

        return ft.Column([
            self.patient_header,
            ft.Container(
                content=self.tabs,
                expand=True,
            ),
        ], spacing=0, expand=True)

    def set_patient(self, patient: Patient):
        """Set the current patient."""
        self.current_patient = patient
        self.current_prescription = None

        # Update header
        header_text = f"{patient.name}"
        details = []
        if patient.age:
            details.append(f"{patient.age}y")
        if patient.gender:
            details.append(patient.gender)
        if patient.uhid:
            details.append(f"UHID: {patient.uhid}")

        # Create audit history button
        self.audit_history_btn = ft.IconButton(
            icon=ft.Icons.HISTORY,
            tooltip="View audit history",
            on_click=self._show_audit_history,
            icon_size=20,
        )

        self.patient_header.content = ft.Row([
            ft.Column([
                ft.Text(header_text, size=18, weight=ft.FontWeight.BOLD),
                ft.Text(" | ".join(details), size=13, color=ft.Colors.GREY_600),
            ], spacing=2),
            self.audit_history_btn,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Enable generate and templates buttons
        self.generate_btn.disabled = False
        self.templates_btn.disabled = False
        self.save_btn.disabled = True
        self.print_btn.disabled = True
        self.save_template_btn.disabled = True

        # Clear fields
        self.complaint_field.value = ""
        self.notes_field.value = ""
        self.rx_display.controls.clear()

        if self.patient_header.page:
            self.patient_header.page.update()

    def _show_audit_history(self, e):
        """Show audit history dialog for current patient."""
        if self.current_patient and e.page:
            self.audit_dialog.show(e.page, self.current_patient)

    def set_visits(self, visits: List[Visit]):
        """Set visits for history tab."""
        self.visits = visits
        self._refresh_history()

    def _refresh_history(self):
        """Refresh the history list."""
        self.history_list.controls.clear()

        if not self.visits:
            self.history_list.controls.append(
                ft.Text("No previous visits", color=ft.Colors.GREY_500, italic=True)
            )
        else:
            for visit in self.visits:
                visit_card = self._create_visit_card(visit)
                self.history_list.controls.append(visit_card)

        if self.history_list.page:
            self.history_list.update()

    def _create_visit_card(self, visit: Visit) -> ft.Control:
        """Create a card for a visit."""
        content_parts = []

        if visit.chief_complaint:
            content_parts.append(ft.Text(
                f"CC: {visit.chief_complaint}",
                size=13,
                weight=ft.FontWeight.W_500,
            ))

        if visit.diagnosis:
            content_parts.append(ft.Text(
                f"Dx: {visit.diagnosis}",
                size=12,
                color=ft.Colors.BLUE_700,
            ))

        if visit.prescription_json:
            try:
                rx = json.loads(visit.prescription_json)
                meds = rx.get("medications", [])
                if meds:
                    med_names = [m.get("drug_name", "") for m in meds[:3]]
                    content_parts.append(ft.Text(
                        f"Rx: {', '.join(med_names)}{'...' if len(meds) > 3 else ''}",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ))
            except:
                pass

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        str(visit.visit_date) if visit.visit_date else "Unknown date",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.COPY,
                        icon_size=16,
                        tooltip="Load this visit",
                        on_click=lambda e, v=visit: self._load_visit(v),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                *content_parts,
            ], spacing=5),
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )

    def _load_visit(self, visit: Visit):
        """Load a previous visit into the form."""
        self.complaint_field.value = visit.chief_complaint or ""
        self.notes_field.value = visit.clinical_notes or ""

        if visit.prescription_json:
            try:
                rx_data = json.loads(visit.prescription_json)
                self.current_prescription = Prescription(**rx_data)
                self._display_prescription(self.current_prescription)
            except:
                pass

        self.tabs.selected_index = 0
        if self.tabs.page:
            self.tabs.page.update()

    def _on_generate_click(self, e):
        """Handle generate prescription click."""
        clinical_notes = self.notes_field.value.strip()
        if not clinical_notes:
            self._show_snackbar("Please enter clinical notes first", error=True)
            return

        # Show loading
        self.loading_indicator.visible = True
        self.generate_btn.disabled = True
        e.page.update()

        def callback(success: bool, prescription: Optional[Prescription], raw: str):
            self.loading_indicator.visible = False
            self.generate_btn.disabled = False

            if success and prescription:
                self.current_prescription = prescription
                self._display_prescription(prescription)
                self.save_btn.disabled = False
                self.print_btn.disabled = False
                self.save_template_btn.disabled = False
            else:
                self.rx_display.controls.clear()
                self.rx_display.controls.append(
                    ft.Text(f"Error: {raw}", color=ft.Colors.RED_600)
                )

            if e.page:
                e.page.update()

        self.on_generate_rx(clinical_notes, callback)

    def _display_prescription(self, rx: Prescription):
        """Display the prescription in the UI."""
        self.rx_display.controls.clear()

        # Diagnosis
        if rx.diagnosis:
            self.rx_display.controls.append(
                ft.Text("DIAGNOSIS:", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.BLUE_700)
            )
            for dx in rx.diagnosis:
                self.rx_display.controls.append(ft.Text(f"  • {dx}", size=12))

        # Medications
        if rx.medications:
            self.rx_display.controls.append(ft.Divider(height=10))
            self.rx_display.controls.append(
                ft.Text("Rx", weight=ft.FontWeight.BOLD, size=16)
            )
            for i, med in enumerate(rx.medications, 1):
                med_text = f"{i}. {med.drug_name}"
                if med.strength:
                    med_text += f" {med.strength}"

                dosage_text = f"   {med.dose} {med.frequency}"
                if med.duration:
                    dosage_text += f" x {med.duration}"
                if med.instructions:
                    dosage_text += f" ({med.instructions})"

                self.rx_display.controls.append(
                    ft.Text(med_text, weight=ft.FontWeight.W_500, size=13)
                )
                self.rx_display.controls.append(
                    ft.Text(dosage_text, size=12, color=ft.Colors.GREY_700)
                )

        # Investigations
        if rx.investigations:
            self.rx_display.controls.append(ft.Divider(height=10))
            self.rx_display.controls.append(
                ft.Text("INVESTIGATIONS:", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.ORANGE_700)
            )
            for inv in rx.investigations:
                self.rx_display.controls.append(ft.Text(f"  • {inv}", size=12))

        # Advice
        if rx.advice:
            self.rx_display.controls.append(ft.Divider(height=10))
            self.rx_display.controls.append(
                ft.Text("ADVICE:", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.GREEN_700)
            )
            for adv in rx.advice:
                self.rx_display.controls.append(ft.Text(f"  • {adv}", size=12))

        # Follow-up
        if rx.follow_up:
            self.rx_display.controls.append(ft.Divider(height=10))
            self.rx_display.controls.append(
                ft.Text(f"FOLLOW-UP: {rx.follow_up}", weight=ft.FontWeight.W_500, size=12)
            )

        # Red flags
        if rx.red_flags:
            self.rx_display.controls.append(ft.Divider(height=10))
            self.rx_display.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("RED FLAGS:", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.RED_700),
                        *[ft.Text(f"  ⚠ {flag}", size=12, color=ft.Colors.RED_600) for flag in rx.red_flags]
                    ], spacing=2),
                    bgcolor=ft.Colors.RED_50,
                    padding=10,
                    border_radius=5,
                )
            )

        if self.rx_display.page:
            self.rx_display.update()

    def _on_save_click(self, e):
        """Handle save visit click."""
        if not self.current_patient or not self.current_prescription:
            return

        # Get diagnosis from prescription
        diagnosis = ", ".join(self.current_prescription.diagnosis) if self.current_prescription.diagnosis else ""

        visit_data = {
            "chief_complaint": self.complaint_field.value.strip(),
            "clinical_notes": self.notes_field.value.strip(),
            "diagnosis": diagnosis,
            "prescription_json": self.current_prescription.model_dump_json(),
        }

        success = self.on_save_visit(visit_data)
        if success:
            self._show_snackbar("Visit saved successfully")
            # Refresh visits
            # This would be called from the parent, but for now just disable save
            self.save_btn.disabled = True
            e.page.update()

    def _on_print_click(self, e):
        """Handle print PDF click."""
        if not self.current_prescription:
            return

        filepath = self.on_print_pdf(
            self.current_prescription,
            self.complaint_field.value.strip()
        )

        if filepath:
            self._show_snackbar(f"PDF saved: {filepath}")
        else:
            self._show_snackbar("Failed to generate PDF", error=True)

    def _show_snackbar(self, message: str, error: bool = False):
        """Show a snackbar message."""
        if self.tabs and self.tabs.page:
            self.tabs.page.open(
                ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700,
                )
            )

    def _on_templates_click(self, e):
        """Handle templates button click."""
        if e.page:
            self.template_browser.show(e.page)

    def _on_template_applied(self, prescription_data: dict):
        """Handle template application."""
        try:
            # Create Prescription object from template data
            self.current_prescription = Prescription(**prescription_data)

            # Display the prescription
            self._display_prescription(self.current_prescription)

            # Enable save and print buttons
            self.save_btn.disabled = False
            self.print_btn.disabled = False
            self.save_template_btn.disabled = False

            if self.tabs and self.tabs.page:
                self.tabs.page.update()

            # Show success message
            self._show_snackbar("Template applied successfully")

        except Exception as ex:
            self._show_snackbar(f"Error applying template: {str(ex)}", error=True)

    def _on_save_template_click(self, e):
        """Handle save as template button click."""
        if not self.current_prescription:
            self._show_snackbar("No prescription to save", error=True)
            return

        # Convert prescription to dict
        prescription_dict = self.current_prescription.model_dump()

        # Show save template dialog
        save_dialog = SaveTemplateDialog(
            db=self.db,
            prescription_dict=prescription_dict,
            on_save=lambda template_id: self._show_snackbar(
                "Template saved successfully!"
            )
        )

        if e.page:
            save_dialog.show(e.page)
