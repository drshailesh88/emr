"""Central panel - Main content area with prescription form."""

import flet as ft
from typing import Callable, Optional, List
import json
from datetime import date

from ..models.schemas import Patient, Visit, Prescription, Medication, PatientSnapshot, SafetyAlert
from ..services.safety import PrescriptionSafetyChecker, CriticalInfoBanner
from ..services.app_mode import ModeCapabilities

# Optional LLM import
try:
    from ..services.llm import LLMService
except ImportError:
    LLMService = None


class CentralPanel:
    """Central panel for clinical notes and prescription."""

    def __init__(
        self,
        on_generate_rx: Callable[[str, Callable], None],
        on_save_visit: Callable[[dict], bool],
        on_print_pdf: Callable[[Prescription, str], Optional[str]],
        llm=None,
        safety_checker: Optional[PrescriptionSafetyChecker] = None,
        capabilities: Optional[ModeCapabilities] = None,
    ):
        self.on_generate_rx = on_generate_rx
        self.on_save_visit = on_save_visit
        self.on_print_pdf = on_print_pdf
        self.llm = llm
        self.safety_checker = safety_checker or PrescriptionSafetyChecker()
        self.capabilities = capabilities

        self.current_patient: Optional[Patient] = None
        self.current_snapshot: Optional[PatientSnapshot] = None
        self.current_prescription: Optional[Prescription] = None
        self.current_alerts: List[SafetyAlert] = []
        self.visits: List[Visit] = []

        # UI components
        self.patient_header: Optional[ft.Container] = None
        self.critical_banner: Optional[ft.Container] = None
        self.complaint_field: Optional[ft.TextField] = None
        self.notes_field: Optional[ft.TextField] = None
        self.rx_display: Optional[ft.Column] = None
        self.alerts_display: Optional[ft.Column] = None
        self.generate_btn: Optional[ft.ElevatedButton] = None
        self.save_btn: Optional[ft.ElevatedButton] = None
        self.print_btn: Optional[ft.ElevatedButton] = None
        self.loading_indicator: Optional[ft.ProgressRing] = None
        self.tabs: Optional[ft.Tabs] = None
        self.history_list: Optional[ft.ListView] = None

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

        # Critical info banner (hidden initially)
        self.critical_banner = ft.Container(
            content=ft.Column([], spacing=5),
            visible=False,
            padding=10,
            bgcolor=ft.Colors.AMBER_100,
            border=ft.border.all(2, ft.Colors.AMBER_700),
            border_radius=8,
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

        # Generate button - disabled if LLM not available
        llm_available = self.capabilities and self.capabilities.llm_prescription
        self.generate_btn = ft.ElevatedButton(
            text="Generate Rx" if llm_available else "Generate Rx (AI Disabled)",
            icon=ft.Icons.AUTO_AWESOME,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700 if llm_available else ft.Colors.GREY_400,
                color=ft.Colors.WHITE,
            ),
            on_click=self._on_generate_click,
            disabled=True,  # Enabled when patient is selected
            tooltip="AI prescription generation" if llm_available else "Upgrade to Standard mode for AI",
        )

        # Safety alerts display
        self.alerts_display = ft.Column([], spacing=5, visible=False)

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
            on_click=self._on_save_click,
            disabled=True,
        )

        # Print button
        self.print_btn = ft.ElevatedButton(
            text="Print PDF",
            icon=ft.Icons.PRINT,
            on_click=self._on_print_click,
            disabled=True,
        )

        # Prescription tab content
        rx_tab_content = ft.Container(
            content=ft.Column([
                self.critical_banner,
                self.complaint_field,
                self.notes_field,
                ft.Row([
                    self.generate_btn,
                    self.loading_indicator,
                ], spacing=10),
                self.alerts_display,
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
                ], spacing=10),
            ], spacing=15, expand=True, scroll=ft.ScrollMode.AUTO),
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

    def set_patient(self, patient: Patient, snapshot: Optional[PatientSnapshot] = None):
        """Set the current patient."""
        self.current_patient = patient
        self.current_snapshot = snapshot
        self.current_prescription = None
        self.current_alerts = []

        # Update header
        header_text = f"{patient.name}"
        details = []
        if patient.age:
            details.append(f"{patient.age}y")
        if patient.gender:
            details.append(patient.gender)
        if patient.uhid:
            details.append(f"UHID: {patient.uhid}")

        self.patient_header.content = ft.Column([
            ft.Text(header_text, size=18, weight=ft.FontWeight.BOLD),
            ft.Text(" | ".join(details), size=13, color=ft.Colors.GREY_600),
        ], spacing=2)

        # Update critical info banner
        self._update_critical_banner(snapshot)

        # Enable generate button if LLM is available
        if self.capabilities and self.capabilities.llm_prescription:
            self.generate_btn.disabled = False
        self.save_btn.disabled = True
        self.print_btn.disabled = True

        # Clear fields
        self.complaint_field.value = ""
        self.notes_field.value = ""
        self.rx_display.controls.clear()
        self.alerts_display.controls.clear()
        self.alerts_display.visible = False

        if self.patient_header.page:
            self.patient_header.page.update()

    def _update_critical_banner(self, snapshot: Optional[PatientSnapshot]):
        """Update the critical info banner based on patient snapshot."""
        if not snapshot or not self.critical_banner:
            self.critical_banner.visible = False
            return

        banner_content = self.critical_banner.content
        banner_content.controls.clear()

        # Get critical info from safety module
        critical_info = CriticalInfoBanner.get_critical_info(snapshot)

        if critical_info:
            # Title
            banner_content.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.AMBER_900, size=20),
                    ft.Text("Critical Patient Info", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_900),
                ], spacing=5)
            )

            # Allergies
            if critical_info.get('allergies'):
                allergies_text = ", ".join(critical_info['allergies'])
                banner_content.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DO_NOT_DISTURB, color=ft.Colors.RED_700, size=16),
                            ft.Text(f"ALLERGIES: {allergies_text}", color=ft.Colors.RED_700, weight=ft.FontWeight.W_500),
                        ], spacing=5),
                        bgcolor=ft.Colors.RED_50,
                        padding=5,
                        border_radius=4,
                    )
                )

            # Anticoagulation
            if critical_info.get('on_anticoagulation'):
                banner_content.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.BLOODTYPE, color=ft.Colors.ORANGE_700, size=16),
                            ft.Text("ON ANTICOAGULATION", color=ft.Colors.ORANGE_700, weight=ft.FontWeight.W_500),
                        ], spacing=5),
                        bgcolor=ft.Colors.ORANGE_50,
                        padding=5,
                        border_radius=4,
                    )
                )

            # Active problems summary
            if critical_info.get('active_problems'):
                problems_text = ", ".join(critical_info['active_problems'][:5])
                if len(critical_info['active_problems']) > 5:
                    problems_text += f" +{len(critical_info['active_problems']) - 5} more"
                banner_content.controls.append(
                    ft.Text(f"Problems: {problems_text}", size=12, color=ft.Colors.GREY_700)
                )

            self.critical_banner.visible = True
        else:
            self.critical_banner.visible = False

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

        if not self.capabilities or not self.capabilities.llm_prescription:
            self._show_snackbar("AI prescription not available in current mode", error=True)
            return

        # Show loading
        self.loading_indicator.visible = True
        self.generate_btn.disabled = True
        e.page.update()

        def callback(success: bool, prescription: Optional[Prescription], alerts: List[SafetyAlert], raw: str):
            self.loading_indicator.visible = False
            self.generate_btn.disabled = False

            if success and prescription:
                self.current_prescription = prescription
                self.current_alerts = alerts
                self._display_prescription(prescription)
                self._display_safety_alerts(alerts)

                # Check if any CRITICAL alerts that should block
                has_critical = any(a.action == "BLOCK" for a in alerts)
                self.save_btn.disabled = has_critical
                self.print_btn.disabled = has_critical

                if has_critical:
                    self._show_snackbar("Prescription blocked due to critical safety issue!", error=True)
            else:
                self.rx_display.controls.clear()
                self.rx_display.controls.append(
                    ft.Text(f"Error: {raw}", color=ft.Colors.RED_600)
                )

            if e.page:
                e.page.update()

        self.on_generate_rx(clinical_notes, callback)

    def _display_safety_alerts(self, alerts: List[SafetyAlert]):
        """Display safety alerts."""
        self.alerts_display.controls.clear()

        if not alerts:
            self.alerts_display.visible = False
            return

        self.alerts_display.visible = True

        # Group by severity
        for alert in sorted(alerts, key=lambda a: ["CRITICAL", "HIGH", "MEDIUM", "LOW"].index(a.severity)):
            # Color based on severity
            colors = {
                "CRITICAL": (ft.Colors.RED_700, ft.Colors.RED_50, ft.Icons.BLOCK),
                "HIGH": (ft.Colors.ORANGE_700, ft.Colors.ORANGE_50, ft.Icons.WARNING),
                "MEDIUM": (ft.Colors.AMBER_700, ft.Colors.AMBER_50, ft.Icons.INFO),
                "LOW": (ft.Colors.BLUE_700, ft.Colors.BLUE_50, ft.Icons.INFO_OUTLINE),
            }
            text_color, bg_color, icon = colors.get(alert.severity, colors["LOW"])

            alert_container = ft.Container(
                content=ft.Row([
                    ft.Icon(icon, color=text_color, size=18),
                    ft.Column([
                        ft.Text(
                            f"[{alert.severity}] {alert.category.upper()}",
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=text_color,
                        ),
                        ft.Text(alert.message, size=12, color=text_color),
                    ], spacing=2, expand=True),
                ], spacing=10),
                bgcolor=bg_color,
                padding=10,
                border_radius=5,
                border=ft.border.all(1, text_color),
            )
            self.alerts_display.controls.append(alert_container)

    def _display_prescription(self, rx: Prescription):
        """Display the prescription in the UI."""
        self.rx_display.controls.clear()

        # Diagnosis
        if rx.diagnosis:
            self.rx_display.controls.append(
                ft.Text("DIAGNOSIS:", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.BLUE_700)
            )
            for dx in rx.diagnosis:
                self.rx_display.controls.append(ft.Text(f"  - {dx}", size=12))

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
                self.rx_display.controls.append(ft.Text(f"  - {inv}", size=12))

        # Advice
        if rx.advice:
            self.rx_display.controls.append(ft.Divider(height=10))
            self.rx_display.controls.append(
                ft.Text("ADVICE:", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.GREEN_700)
            )
            for adv in rx.advice:
                self.rx_display.controls.append(ft.Text(f"  - {adv}", size=12))

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
                        *[ft.Text(f"  ! {flag}", size=12, color=ft.Colors.RED_600) for flag in rx.red_flags]
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

        # Check for blocking alerts
        if any(a.action == "BLOCK" for a in self.current_alerts):
            self._show_snackbar("Cannot save: Critical safety issue must be resolved", error=True)
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
            self.save_btn.disabled = True
            e.page.update()

    def _on_print_click(self, e):
        """Handle print PDF click."""
        if not self.current_prescription:
            return

        # Check for blocking alerts
        if any(a.action == "BLOCK" for a in self.current_alerts):
            self._show_snackbar("Cannot print: Critical safety issue must be resolved", error=True)
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
