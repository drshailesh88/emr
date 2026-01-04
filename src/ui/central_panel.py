"""Central panel - Main content area with prescription form.

Refactored to use extracted premium components for maintainability.
Each tab's specific logic is kept in this file as it's panel-specific.
"""

import flet as ft
from typing import Callable, Optional, List
import json

from ..models.schemas import Patient, Visit, Prescription, Investigation, Procedure
from ..services.llm import LLMService
from ..services.database import DatabaseService
from .components import (
    PatientHeader,
    VitalsForm,
    ClinicalNotesForm,
    PrescriptionView,
    ActionBar,
)
from .audit_history_dialog import AuditHistoryDialog
from .dialogs import ConfirmationDialog, EditInvestigationDialog, EditProcedureDialog
from .template_browser import TemplateBrowser, SaveTemplateDialog
from .lab_trends_dialog import LabTrendsDialog
from ..services.reference_ranges import TREND_PANELS, get_reference_range
from ..services.trend_calculator import calculate_trend
from .flowsheet_panel import ConditionManager
from .whatsapp_share_dialog import show_whatsapp_share
from .appointment_panel import show_schedule_followup
from .reminder_dialog import show_reminder_settings
from .tokens import Colors, Typography, Spacing, Radius


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
        self.investigations: List[Investigation] = []
        self.procedures: List[Procedure] = []
        self.editing_visit_id: Optional[int] = None

        # Premium components
        self.patient_header = PatientHeader(
            on_show_audit_history=self._show_audit_history,
            on_show_reminder_settings=self._show_reminder_settings,
        )
        self.vitals_form = VitalsForm(db=db)
        self.clinical_notes = ClinicalNotesForm(db=db)
        self.prescription_view = PrescriptionView()
        self.action_bar = ActionBar(
            on_templates=self._on_templates_click,
            on_generate=self._on_generate_click,
            on_save=self._on_save_click,
            on_print=self._on_print_click,
            on_whatsapp=self._on_whatsapp_click,
            on_save_template=self._on_save_template_click,
        )

        # Dialogs
        self.audit_dialog = AuditHistoryDialog(db)
        self.template_browser = TemplateBrowser(db, self._on_template_applied)

        # Tab list views
        self.tabs: Optional[ft.Tabs] = None
        self.history_list: Optional[ft.ListView] = None
        self.investigations_list: Optional[ft.ListView] = None
        self.procedures_list: Optional[ft.ListView] = None
        self.vitals_history_list: Optional[ft.ListView] = None
        self.trends_container: Optional[ft.Container] = None
        self.flowsheets_container: Optional[ft.Container] = None

    def build(self) -> ft.Control:
        """Build the central panel UI."""
        # Build prescription tab content
        rx_tab = ft.Container(
            content=ft.Column([
                self.vitals_form.build(),
                self.clinical_notes.build(),
                self.action_bar.build_top_row(),
                ft.Divider(height=1, color=Colors.NEUTRAL_200),
                ft.Text("Generated Prescription:", weight=ft.FontWeight.W_600,
                       size=Typography.LABEL_MEDIUM.size, color=Colors.NEUTRAL_700),
                self.prescription_view.build(),
                self.action_bar.build_bottom_row(),
            ], spacing=Spacing.MD, expand=True),
            padding=Spacing.LG,
            expand=True,
        )

        # Build other tabs
        self.history_list = ft.ListView(spacing=10, padding=10, expand=True)
        self.investigations_list = ft.ListView(spacing=10, padding=10, expand=True)
        self.procedures_list = ft.ListView(spacing=10, padding=10, expand=True)
        self.vitals_history_list = ft.ListView(spacing=10, padding=10, expand=True)

        self.trends_container = ft.Container(
            content=ft.Text("Select a patient to view trends",
                          size=14, color=Colors.NEUTRAL_500, italic=True),
            padding=20, alignment=ft.alignment.center, expand=True,
        )
        self.flowsheets_container = ft.Container(
            content=ft.Text("Select a patient to view flowsheets",
                          size=14, color=Colors.NEUTRAL_500, italic=True),
            padding=20, alignment=ft.alignment.center, expand=True,
        )

        # Create tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Prescription", icon=ft.Icons.MEDICATION, content=rx_tab),
                ft.Tab(text="History", icon=ft.Icons.HISTORY,
                      content=ft.Container(content=self.history_list, padding=10, expand=True)),
                ft.Tab(text="Vitals", icon=ft.Icons.FAVORITE,
                      content=self._build_vitals_history_tab()),
                ft.Tab(text="Investigations", icon=ft.Icons.SCIENCE,
                      content=self._build_investigations_tab()),
                ft.Tab(text="Trends", icon=ft.Icons.TRENDING_UP, content=self.trends_container),
                ft.Tab(text="Procedures", icon=ft.Icons.MEDICAL_SERVICES,
                      content=self._build_procedures_tab()),
                ft.Tab(text="Flowsheets", icon=ft.Icons.MONITOR_HEART,
                      content=self.flowsheets_container),
            ],
            expand=True,
        )

        return ft.Column([
            self.patient_header.build(),
            ft.Container(content=self.tabs, expand=True),
        ], spacing=0, expand=True)

    def _build_investigations_tab(self) -> ft.Container:
        """Build investigations tab with add button."""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Investigations", size=16, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton("Add Investigation", icon=ft.Icons.ADD,
                        on_click=self._add_investigation,
                        style=ft.ButtonStyle(bgcolor=Colors.PRIMARY_600, color=Colors.NEUTRAL_0)),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Container(content=self.investigations_list, expand=True),
            ], spacing=10, expand=True),
            padding=10, expand=True,
        )

    def _build_procedures_tab(self) -> ft.Container:
        """Build procedures tab with add button."""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Procedures", size=16, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton("Add Procedure", icon=ft.Icons.ADD,
                        on_click=self._add_procedure,
                        style=ft.ButtonStyle(bgcolor=Colors.PRIMARY_600, color=Colors.NEUTRAL_0)),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Container(content=self.procedures_list, expand=True),
            ], spacing=10, expand=True),
            padding=10, expand=True,
        )

    def _build_vitals_history_tab(self) -> ft.Container:
        """Build vitals history tab."""
        return ft.Container(
            content=ft.Column([
                ft.Text("Vitals History", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Container(content=self.vitals_history_list, expand=True),
            ], spacing=10, expand=True),
            padding=10, expand=True,
        )

    # ================== Patient Management ==================

    def set_patient(self, patient: Patient):
        """Set the current patient."""
        self.current_patient = patient
        self.current_prescription = None
        self.editing_visit_id = None

        # Update header
        self.patient_header.set_patient(patient)

        # Setup vitals form
        last_height = self.db.get_last_height(patient.id)
        self.vitals_form.set_patient(patient.id, last_height)

        # Enable actions
        self.action_bar.enable_patient_actions()

        # Clear notes
        self.clinical_notes.clear()
        self.prescription_view.clear()

        # Load tab data
        self.investigations = self.db.get_patient_investigations(patient.id)
        self.procedures = self.db.get_patient_procedures(patient.id)
        self._refresh_all_tabs()

        if self.tabs and self.tabs.page:
            self.tabs.page.update()

    def set_visits(self, visits: List[Visit]):
        """Set visits for history tab."""
        self.visits = visits
        self._refresh_history()

    def _refresh_all_tabs(self):
        """Refresh all tab contents."""
        self._refresh_investigations()
        self._refresh_procedures()
        self._refresh_vitals_history()
        self._refresh_trends()
        self._refresh_flowsheets()

    # ================== Dialogs ==================

    def _show_audit_history(self, e):
        if self.current_patient and e.page:
            self.audit_dialog.show(e.page, self.current_patient)

    def _show_reminder_settings(self, e):
        if self.current_patient and e.page:
            show_reminder_settings(e.page, self.db, self.current_patient.id, self.current_patient.name)

    def _show_snackbar(self, message: str, error: bool = False):
        if self.tabs and self.tabs.page:
            self.tabs.page.open(ft.SnackBar(
                content=ft.Text(message),
                bgcolor=Colors.ERROR_MAIN if error else Colors.SUCCESS_MAIN,
            ))

    # ================== Prescription Actions ==================

    def _on_templates_click(self, e):
        if e.page:
            self.template_browser.show(e.page)

    def _on_template_applied(self, prescription_data: dict):
        try:
            self.current_prescription = Prescription(**prescription_data)
            self.prescription_view.display(self.current_prescription)
            self.action_bar.enable_prescription_actions()
            if self.tabs and self.tabs.page:
                self.tabs.page.update()
            self._show_snackbar("Template applied successfully")
        except Exception as ex:
            self._show_snackbar(f"Error applying template: {str(ex)}", error=True)

    def _on_generate_click(self, e):
        notes = self.clinical_notes.get_notes()
        if not notes:
            self._show_snackbar("Please enter clinical notes first", error=True)
            return

        self.action_bar.set_loading(True)

        def callback(success: bool, prescription: Optional[Prescription], raw: str):
            self.action_bar.set_loading(False)
            if success and prescription:
                self.current_prescription = prescription
                self.prescription_view.display(prescription)
                self.action_bar.enable_prescription_actions()
            else:
                self.prescription_view.show_error(f"Error: {raw}")
            if e.page:
                e.page.update()

        self.on_generate_rx(notes, callback)

    def _on_save_click(self, e):
        if not self.current_patient or not self.current_prescription:
            return

        diagnosis = ", ".join(self.current_prescription.diagnosis) if self.current_prescription.diagnosis else ""
        visit_data = {
            "chief_complaint": self.clinical_notes.get_complaint(),
            "clinical_notes": self.clinical_notes.get_notes(),
            "diagnosis": diagnosis,
            "prescription_json": self.current_prescription.model_dump_json(),
        }

        # Save vitals if entered
        if self.vitals_form.has_data():
            try:
                self.db.add_vitals(self.vitals_form.get_data())
                self._refresh_vitals_history()
                last_height = self.db.get_last_height(self.current_patient.id)
                self.vitals_form.set_patient(self.current_patient.id, last_height)
            except Exception as ex:
                self._show_snackbar(f"Warning: Failed to save vitals: {str(ex)}", error=True)

        if self.editing_visit_id:
            visit = Visit(id=self.editing_visit_id, patient_id=self.current_patient.id, **visit_data)
            if self.db.update_visit(visit):
                self._show_snackbar("Visit updated successfully")
                self.editing_visit_id = None
                self.action_bar.set_save_mode(False)
                self.visits = self.db.get_patient_visits(self.current_patient.id)
                self._refresh_history()
            else:
                self._show_snackbar("Failed to update visit", error=True)
        else:
            if self.on_save_visit(visit_data):
                self._show_snackbar("Visit saved successfully")
                self.action_bar.disable_save()
                self._offer_schedule_followup(e.page)
        e.page.update()

    def _offer_schedule_followup(self, page):
        if not self.current_patient or not self.current_prescription:
            return
        suggested_days = 14
        if self.current_prescription.follow_up:
            fu = self.current_prescription.follow_up.lower()
            if "1 week" in fu: suggested_days = 7
            elif "2 week" in fu: suggested_days = 14
            elif "1 month" in fu: suggested_days = 30
        show_schedule_followup(page, self.db, self.current_patient, suggested_days)

    def _on_print_click(self, e):
        if not self.current_prescription:
            return
        filepath = self.on_print_pdf(self.current_prescription, self.clinical_notes.get_complaint())
        if filepath:
            self._show_snackbar(f"PDF saved: {filepath}")
            self._last_pdf_path = filepath
        else:
            self._show_snackbar("Failed to generate PDF", error=True)

    def _on_whatsapp_click(self, e):
        if not self.current_prescription or not self.current_patient:
            return
        show_whatsapp_share(e.page, self.current_patient, self.current_prescription,
                          getattr(self, '_last_pdf_path', None),
                          lambda: self._show_snackbar("Prescription shared via WhatsApp"))

    def _on_save_template_click(self, e):
        if not self.current_prescription:
            self._show_snackbar("No prescription to save", error=True)
            return
        save_dialog = SaveTemplateDialog(
            db=self.db,
            prescription_dict=self.current_prescription.model_dump(),
            on_save=lambda tid: self._show_snackbar("Template saved successfully!")
        )
        if e.page:
            save_dialog.show(e.page)

    # ================== History Tab ==================

    def _refresh_history(self):
        self.history_list.controls.clear()
        if not self.visits:
            self.history_list.controls.append(
                ft.Text("No previous visits", color=Colors.NEUTRAL_500, italic=True))
        else:
            for visit in self.visits:
                self.history_list.controls.append(self._create_visit_card(visit))
        if self.history_list.page:
            self.history_list.update()

    def _create_visit_card(self, visit: Visit) -> ft.Control:
        parts = []
        if visit.chief_complaint:
            parts.append(ft.Text(f"CC: {visit.chief_complaint}", size=13, weight=ft.FontWeight.W_500))
        if visit.diagnosis:
            parts.append(ft.Text(f"Dx: {visit.diagnosis}", size=12, color=Colors.PRIMARY_700))
        if visit.prescription_json:
            try:
                rx = json.loads(visit.prescription_json)
                meds = rx.get("medications", [])[:3]
                if meds:
                    names = [m.get("drug_name", "") for m in meds]
                    parts.append(ft.Text(f"Rx: {', '.join(names)}{'...' if len(rx.get('medications',[])) > 3 else ''}",
                                        size=12, color=Colors.NEUTRAL_600))
            except: pass

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(str(visit.visit_date) if visit.visit_date else "Unknown",
                           size=12, weight=ft.FontWeight.BOLD, color=Colors.NEUTRAL_700),
                    ft.Row([
                        ft.IconButton(icon=ft.Icons.COPY, icon_size=16, tooltip="Load",
                                     on_click=lambda e, v=visit: self._load_visit(v)),
                        ft.IconButton(icon=ft.Icons.EDIT, icon_size=16, tooltip="Edit",
                                     on_click=lambda e, v=visit: self._edit_visit(v)),
                        ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_size=16, tooltip="Delete",
                                     icon_color=Colors.ERROR_MAIN,
                                     on_click=lambda e, v=visit: self._delete_visit(e, v)),
                    ], spacing=0),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                *parts,
            ], spacing=5),
            padding=15, bgcolor=Colors.NEUTRAL_0, border_radius=Radius.MD,
            border=ft.border.all(1, Colors.NEUTRAL_300),
        )

    def _load_visit(self, visit: Visit):
        self.clinical_notes.set_complaint(visit.chief_complaint or "")
        self.clinical_notes.set_notes(visit.clinical_notes or "")
        self.editing_visit_id = None
        if visit.prescription_json:
            try:
                self.current_prescription = Prescription(**json.loads(visit.prescription_json))
                self.prescription_view.display(self.current_prescription)
                self.action_bar.enable_prescription_actions()
            except: pass
        self.tabs.selected_index = 0
        if self.tabs.page:
            self.tabs.page.update()

    def _edit_visit(self, visit: Visit):
        self.editing_visit_id = visit.id
        self._load_visit(visit)
        self.action_bar.set_save_mode(True)
        self._show_snackbar(f"Editing visit from {visit.visit_date}")

    def _delete_visit(self, e, visit: Visit):
        def confirm():
            if self.db.delete_visit(visit.id):
                self._show_snackbar("Visit deleted")
                if self.current_patient:
                    self.visits = self.db.get_patient_visits(self.current_patient.id)
                    self._refresh_history()
            else:
                self._show_snackbar("Failed to delete visit", error=True)
        ConfirmationDialog.show(e.page, "Delete Visit?",
            f"Delete visit from {visit.visit_date}? This is recoverable from backups.", confirm)

    # ================== Investigations Tab ==================

    def _refresh_investigations(self):
        self.investigations_list.controls.clear()
        if not self.investigations:
            self.investigations_list.controls.append(
                ft.Text("No investigations recorded", color=Colors.NEUTRAL_500, italic=True))
        else:
            for inv in self.investigations:
                self.investigations_list.controls.append(self._create_investigation_card(inv))
        if self.investigations_list.page:
            self.investigations_list.update()

    def _create_investigation_card(self, inv: Investigation) -> ft.Control:
        result_text = f"{inv.result} {inv.unit}" if inv.result else "Pending"
        if inv.is_abnormal:
            result_text += " (ABNORMAL)"
        trend = self._calculate_trend(inv.test_name)

        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Row([
                        ft.Text(inv.test_name, size=14, weight=ft.FontWeight.W_500),
                        ft.Text(trend, size=14) if trend != "→" else ft.Container(),
                        ft.IconButton(icon=ft.Icons.SHOW_CHART, icon_size=16, tooltip="View trend",
                            icon_color=Colors.PRIMARY_700, on_click=lambda e, i=inv: self._show_trend(e, i)),
                    ], spacing=5),
                    ft.Row([
                        ft.Text(str(inv.test_date) if inv.test_date else "", size=11, color=Colors.NEUTRAL_600),
                        ft.Text(result_text, size=12, weight=ft.FontWeight.BOLD,
                               color=Colors.ERROR_MAIN if inv.is_abnormal else Colors.SUCCESS_MAIN),
                    ], spacing=15),
                    ft.Text(f"Ref: {inv.reference_range}" if inv.reference_range else "",
                           size=11, color=Colors.NEUTRAL_500),
                ], spacing=3, expand=True),
                ft.Row([
                    ft.IconButton(icon=ft.Icons.EDIT, icon_size=18, tooltip="Edit",
                        on_click=lambda e, i=inv: self._edit_investigation(e, i)),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_size=18, tooltip="Delete",
                        icon_color=Colors.ERROR_MAIN, on_click=lambda e, i=inv: self._delete_investigation(e, i)),
                ], spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15, bgcolor=Colors.NEUTRAL_0, border_radius=Radius.MD,
            border=ft.border.all(1, Colors.NEUTRAL_300),
        )

    def _calculate_trend(self, test_name: str) -> str:
        test_invs = [i for i in self.investigations if i.test_name.lower() == test_name.lower() and i.result]
        if len(test_invs) < 2:
            return "→"
        try:
            values = [float(i.result) for i in test_invs[-3:]]
            return calculate_trend(values)
        except ValueError:
            return "→"

    def _show_trend(self, e, inv: Investigation):
        if not e.page or not self.current_patient:
            return
        test_invs = [i for i in self.investigations if i.test_name.lower() == inv.test_name.lower()]
        LabTrendsDialog(inv.test_name, test_invs, self.investigations).show(e.page)

    def _add_investigation(self, e):
        if not self.current_patient:
            return
        def save(data):
            if self.db.add_investigation(Investigation(**data)):
                self._show_snackbar("Investigation added")
                self.investigations = self.db.get_patient_investigations(self.current_patient.id)
                self._refresh_investigations()
                self._refresh_trends()
            else:
                self._show_snackbar("Failed to add investigation", error=True)
        EditInvestigationDialog.show(e.page, None, self.current_patient.id, save)

    def _edit_investigation(self, e, inv: Investigation):
        def save(data):
            if self.db.update_investigation(Investigation(**data)):
                self._show_snackbar("Investigation updated")
                self.investigations = self.db.get_patient_investigations(self.current_patient.id)
                self._refresh_investigations()
                self._refresh_trends()
            else:
                self._show_snackbar("Failed to update investigation", error=True)
        inv_dict = {"id": inv.id, "patient_id": inv.patient_id, "test_name": inv.test_name,
                    "result": inv.result or "", "unit": inv.unit or "",
                    "reference_range": inv.reference_range or "", "test_date": inv.test_date,
                    "is_abnormal": inv.is_abnormal}
        EditInvestigationDialog.show(e.page, inv_dict, inv.patient_id, save)

    def _delete_investigation(self, e, inv: Investigation):
        def confirm():
            if self.db.delete_investigation(inv.id):
                self._show_snackbar("Investigation deleted")
                self.investigations = self.db.get_patient_investigations(self.current_patient.id)
                self._refresh_investigations()
                self._refresh_trends()
            else:
                self._show_snackbar("Failed to delete investigation", error=True)
        ConfirmationDialog.show(e.page, "Delete Investigation?",
            f"Delete {inv.test_name} from {inv.test_date}?", confirm)

    # ================== Procedures Tab ==================

    def _refresh_procedures(self):
        self.procedures_list.controls.clear()
        if not self.procedures:
            self.procedures_list.controls.append(
                ft.Text("No procedures recorded", color=Colors.NEUTRAL_500, italic=True))
        else:
            for proc in self.procedures:
                self.procedures_list.controls.append(self._create_procedure_card(proc))
        if self.procedures_list.page:
            self.procedures_list.update()

    def _create_procedure_card(self, proc: Procedure) -> ft.Control:
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(proc.procedure_name, size=14, weight=ft.FontWeight.W_500),
                    ft.Text(str(proc.procedure_date) if proc.procedure_date else "",
                           size=11, color=Colors.NEUTRAL_600),
                    ft.Text(proc.details if proc.details else "", size=12, color=Colors.NEUTRAL_700,
                           max_lines=2, overflow=ft.TextOverflow.ELLIPSIS) if proc.details else ft.Container(),
                ], spacing=3, expand=True),
                ft.Row([
                    ft.IconButton(icon=ft.Icons.EDIT, icon_size=18, tooltip="Edit",
                        on_click=lambda e, p=proc: self._edit_procedure(e, p)),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_size=18, tooltip="Delete",
                        icon_color=Colors.ERROR_MAIN, on_click=lambda e, p=proc: self._delete_procedure(e, p)),
                ], spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15, bgcolor=Colors.NEUTRAL_0, border_radius=Radius.MD,
            border=ft.border.all(1, Colors.NEUTRAL_300),
        )

    def _add_procedure(self, e):
        if not self.current_patient:
            return
        def save(data):
            if self.db.add_procedure(Procedure(**data)):
                self._show_snackbar("Procedure added")
                self.procedures = self.db.get_patient_procedures(self.current_patient.id)
                self._refresh_procedures()
            else:
                self._show_snackbar("Failed to add procedure", error=True)
        EditProcedureDialog.show(e.page, None, self.current_patient.id, save)

    def _edit_procedure(self, e, proc: Procedure):
        def save(data):
            if self.db.update_procedure(Procedure(**data)):
                self._show_snackbar("Procedure updated")
                self.procedures = self.db.get_patient_procedures(self.current_patient.id)
                self._refresh_procedures()
            else:
                self._show_snackbar("Failed to update procedure", error=True)
        proc_dict = {"id": proc.id, "patient_id": proc.patient_id, "procedure_name": proc.procedure_name,
                     "details": proc.details or "", "procedure_date": proc.procedure_date,
                     "notes": proc.notes or ""}
        EditProcedureDialog.show(e.page, proc_dict, proc.patient_id, save)

    def _delete_procedure(self, e, proc: Procedure):
        def confirm():
            if self.db.delete_procedure(proc.id):
                self._show_snackbar("Procedure deleted")
                self.procedures = self.db.get_patient_procedures(self.current_patient.id)
                self._refresh_procedures()
            else:
                self._show_snackbar("Failed to delete procedure", error=True)
        ConfirmationDialog.show(e.page, "Delete Procedure?",
            f"Delete {proc.procedure_name} from {proc.procedure_date}?", confirm)

    # ================== Vitals History Tab ==================

    def _refresh_vitals_history(self):
        if not self.vitals_history_list or not self.current_patient:
            return
        self.vitals_history_list.controls.clear()
        vitals_list = self.db.get_patient_vitals(self.current_patient.id, limit=50)

        if not vitals_list:
            self.vitals_history_list.controls.append(
                ft.Text("No vitals recorded", color=Colors.NEUTRAL_500, italic=True))
        else:
            # Header row
            self.vitals_history_list.controls.append(ft.Container(
                content=ft.Row([
                    ft.Text("Date", size=12, weight=ft.FontWeight.BOLD, width=120),
                    ft.Text("BP", size=12, weight=ft.FontWeight.BOLD, width=80),
                    ft.Text("Pulse", size=12, weight=ft.FontWeight.BOLD, width=60),
                    ft.Text("SpO2", size=12, weight=ft.FontWeight.BOLD, width=60),
                    ft.Text("Weight", size=12, weight=ft.FontWeight.BOLD, width=70),
                    ft.Text("BMI", size=12, weight=ft.FontWeight.BOLD, width=60),
                    ft.Text("Sugar", size=12, weight=ft.FontWeight.BOLD, width=100),
                ]),
                padding=10, bgcolor=Colors.NEUTRAL_200, border_radius=Radius.MD,
            ))
            for v in vitals_list:
                bp = f"{v.get('bp_systolic','')}/{v.get('bp_diastolic','')}" if v.get('bp_systolic') else ""
                bp_color = Colors.ERROR_MAIN if v.get('bp_systolic',0)>=140 or v.get('bp_diastolic',0)>=90 else None
                spo2 = f"{v['spo2']}%" if v.get('spo2') else ""
                spo2_color = Colors.ERROR_MAIN if v.get('spo2',100)<95 else None
                bmi_color = Colors.ERROR_MAIN if v.get('bmi',0)>=30 else Colors.WARNING_MAIN if v.get('bmi',0)>=25 else Colors.SUCCESS_MAIN if v.get('bmi') else None

                self.vitals_history_list.controls.append(ft.Container(
                    content=ft.Row([
                        ft.Text(v.get('recorded_at','')[:16], size=11, width=120),
                        ft.Text(bp, size=11, width=80, color=bp_color),
                        ft.Text(str(v.get('pulse','')) if v.get('pulse') else "", size=11, width=60),
                        ft.Text(spo2, size=11, width=60, color=spo2_color),
                        ft.Text(f"{v['weight']} kg" if v.get('weight') else "", size=11, width=70),
                        ft.Text(str(v.get('bmi','')) if v.get('bmi') else "", size=11, width=60, color=bmi_color),
                        ft.Text(f"{v.get('blood_sugar','')} {v.get('sugar_type','')}" if v.get('blood_sugar') else "", size=11, width=100),
                    ]),
                    padding=10, bgcolor=Colors.NEUTRAL_0, border=ft.border.all(1, Colors.NEUTRAL_300),
                    border_radius=Radius.SM,
                ))
        if self.vitals_history_list.page:
            self.vitals_history_list.update()

    # ================== Trends Tab ==================

    def _refresh_trends(self):
        if not self.trends_container:
            return
        panels = []
        for panel_name, test_names in TREND_PANELS.items():
            items = []
            for test_name in test_names:
                test_invs = [i for i in self.investigations if i.test_name.lower()==test_name.lower() and i.result]
                if not test_invs:
                    continue
                latest = test_invs[-1]
                try:
                    value_str = f"{float(latest.result):.1f} {latest.unit}"
                except ValueError:
                    value_str = latest.result
                trend = "→"
                if len(test_invs) >= 2:
                    try:
                        trend = calculate_trend([float(i.result) for i in test_invs[-3:]])
                    except ValueError:
                        pass
                trend_color = Colors.WARNING_MAIN if trend=="↑" else Colors.INFO_MAIN if trend=="↓" else Colors.NEUTRAL_500
                items.append(ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(test_name, size=12, weight=ft.FontWeight.W_500),
                            ft.Text(value_str, size=11, color=Colors.NEUTRAL_600),
                        ], spacing=2, expand=True),
                        ft.Row([
                            ft.Text(trend, size=16, color=trend_color),
                            ft.IconButton(icon=ft.Icons.SHOW_CHART, icon_size=14, tooltip="View",
                                icon_color=Colors.PRIMARY_700,
                                on_click=lambda e, tn=test_name: self._show_trend_panel(e, tn)),
                        ], spacing=0),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=8, bgcolor=Colors.ERROR_LIGHT if latest.is_abnormal else Colors.NEUTRAL_0,
                    border_radius=Radius.SM,
                ))
            if items:
                panels.append(ft.Container(
                    content=ft.Column([
                        ft.Text(f"{panel_name.upper()} PANEL", size=12, weight=ft.FontWeight.BOLD, color=Colors.PRIMARY_700),
                        ft.Column(items, spacing=5),
                    ], spacing=10),
                    padding=15, bgcolor=Colors.NEUTRAL_50, border_radius=Radius.MD,
                    border=ft.border.all(1, Colors.NEUTRAL_300), width=250,
                ))
        if not panels:
            self.trends_container.content = ft.Text("No investigation data for trends",
                size=14, color=Colors.NEUTRAL_500, italic=True)
        else:
            rows = [ft.Row(panels[i:i+3], spacing=15, wrap=True) for i in range(0, len(panels), 3)]
            self.trends_container.content = ft.Column(rows, spacing=15, scroll=ft.ScrollMode.AUTO)
        if self.trends_container.page:
            self.trends_container.update()

    def _show_trend_panel(self, e, test_name: str):
        if not e.page or not self.current_patient:
            return
        test_invs = [i for i in self.investigations if i.test_name.lower()==test_name.lower()]
        if test_invs:
            LabTrendsDialog(test_name, test_invs, self.investigations).show(e.page)

    # ================== Flowsheets Tab ==================

    def _refresh_flowsheets(self):
        if not self.flowsheets_container or not self.current_patient:
            return
        manager = ConditionManager(db=self.db, patient_id=self.current_patient.id)
        self.flowsheets_container.content = manager.build()
        if self.flowsheets_container.page:
            self.flowsheets_container.update()
