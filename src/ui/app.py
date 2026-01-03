"""Main Flet application with 3-panel layout."""

import flet as ft
from typing import Optional
import threading

from ..services.database import DatabaseService
from ..services.llm import LLMService
from ..services.rag import RAGService
from ..services.pdf import PDFService
from ..services.backup import BackupService
from ..models.schemas import Patient, Visit, Prescription

from .patient_panel import PatientPanel
from .central_panel import CentralPanel
from .agent_panel import AgentPanel
from .backup_dialog import show_backup_dialog


class DocAssistApp:
    """Main application class."""

    def __init__(self):
        self.db = DatabaseService()
        self.llm = LLMService()
        self.rag = RAGService()
        self.pdf = PDFService()
        self.backup = BackupService()

        self.current_patient: Optional[Patient] = None
        self.page: Optional[ft.Page] = None

        # UI components (initialized in build)
        self.patient_panel: Optional[PatientPanel] = None
        self.central_panel: Optional[CentralPanel] = None
        self.agent_panel: Optional[AgentPanel] = None
        self.status_bar: Optional[ft.Text] = None

    def main(self, page: ft.Page):
        """Main entry point for Flet app."""
        self.page = page
        page.title = "DocAssist EMR"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.spacing = 0

        # Set window size
        page.window.width = 1400
        page.window.height = 800
        page.window.min_width = 1000
        page.window.min_height = 600

        # Check LLM status in background
        self._check_llm_status()

        # Build UI
        page.add(self._build_ui())
        page.update()

        # Load patients
        self._load_patients()

    def _build_ui(self) -> ft.Control:
        """Build the main UI layout."""

        # Initialize panels
        self.patient_panel = PatientPanel(
            on_patient_selected=self._on_patient_selected,
            on_search=self._on_patient_search,
            on_new_patient=self._on_new_patient,
            db=self.db,
            rag=self.rag
        )

        self.central_panel = CentralPanel(
            on_generate_rx=self._on_generate_prescription,
            on_save_visit=self._on_save_visit,
            on_print_pdf=self._on_print_pdf,
            llm=self.llm
        )

        self.agent_panel = AgentPanel(
            on_query=self._on_rag_query,
            llm=self.llm,
            rag=self.rag
        )

        # Status bar
        self.status_bar = ft.Text(
            "Ready",
            size=12,
            color=ft.Colors.GREY_600
        )

        # Header
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.LOCAL_HOSPITAL, color=ft.Colors.BLUE_700, size=28),
                        ft.Text("DocAssist EMR", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                    ], spacing=10),
                    ft.Row([
                        self.status_bar,
                        ft.IconButton(
                            icon=ft.Icons.BACKUP,
                            tooltip="Backup & Restore",
                            on_click=self._on_backup_click
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS,
                            tooltip="Settings",
                            on_click=self._on_settings_click
                        ),
                        ft.IconButton(
                            icon=ft.Icons.HELP_OUTLINE,
                            tooltip="Help",
                            on_click=self._on_help_click
                        ),
                    ], spacing=5),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
        )

        # Main content with 3 panels
        main_content = ft.Row(
            [
                # Left panel - Patients (fixed width)
                ft.Container(
                    content=self.patient_panel.build(),
                    width=280,
                    bgcolor=ft.Colors.GREY_50,
                    border=ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_300)),
                ),
                # Center panel - Main content (expandable)
                ft.Container(
                    content=self.central_panel.build(),
                    expand=True,
                    bgcolor=ft.Colors.WHITE,
                ),
                # Right panel - AI Agent (fixed width)
                ft.Container(
                    content=self.agent_panel.build(),
                    width=350,
                    bgcolor=ft.Colors.BLUE_50,
                    border=ft.border.only(left=ft.BorderSide(1, ft.Colors.GREY_300)),
                ),
            ],
            spacing=0,
            expand=True,
        )

        return ft.Column(
            [header, main_content],
            spacing=0,
            expand=True,
        )

    def _check_llm_status(self):
        """Check LLM availability in background."""
        def check():
            if self.llm.is_available():
                model_info = self.llm.get_model_info()
                self._update_status(f"LLM: {model_info['model']} | RAM: {model_info['ram_gb']:.1f}GB")
            else:
                self._update_status("Ollama not running - AI features disabled", error=True)

        threading.Thread(target=check, daemon=True).start()

    def _update_status(self, message: str, error: bool = False):
        """Update status bar."""
        if self.status_bar and self.page:
            self.status_bar.value = message
            self.status_bar.color = ft.Colors.RED_600 if error else ft.Colors.GREY_600
            self.page.update()

    def _load_patients(self):
        """Load all patients into the list."""
        patients = self.db.get_all_patients()
        if self.patient_panel:
            self.patient_panel.set_patients(patients)

    def _on_patient_selected(self, patient: Patient):
        """Handle patient selection."""
        self.current_patient = patient
        self.central_panel.set_patient(patient)
        self.agent_panel.set_patient(patient)

        # Load visits for this patient
        visits = self.db.get_patient_visits(patient.id)
        self.central_panel.set_visits(visits)

        # Index patient documents for RAG in background
        self._index_patient_for_rag(patient.id)

        self._update_status(f"Selected: {patient.name} ({patient.uhid})")

    def _index_patient_for_rag(self, patient_id: int):
        """Index patient documents for RAG in background."""
        def index():
            # Get patient summary
            summary = self.db.get_patient_summary(patient_id)
            if summary:
                self.rag.index_patient_summary(patient_id, summary)

            # Get all documents
            documents = self.db.get_patient_documents_for_rag(patient_id)
            if documents:
                self.rag.index_patient_documents(patient_id, documents)

        threading.Thread(target=index, daemon=True).start()

    def _on_patient_search(self, query: str):
        """Handle patient search."""
        if not query.strip():
            self._load_patients()
            return

        # First try basic search
        patients = self.db.search_patients_basic(query)

        # If no results and query looks like natural language, try RAG search
        if not patients and len(query.split()) > 2:
            results = self.rag.search_patients(query, n_results=10)
            if results:
                patient_ids = [r[0] for r in results]
                patients = [self.db.get_patient(pid) for pid in patient_ids if self.db.get_patient(pid)]

        self.patient_panel.set_patients(patients)

    def _on_new_patient(self, patient_data: dict):
        """Handle new patient creation."""
        patient = Patient(**patient_data)
        saved_patient = self.db.add_patient(patient)

        # Index for RAG
        summary = f"Patient: {saved_patient.name}. UHID: {saved_patient.uhid}"
        if saved_patient.age:
            summary += f". Age: {saved_patient.age}"
        if saved_patient.gender:
            summary += f". Gender: {saved_patient.gender}"
        self.rag.index_patient_summary(saved_patient.id, summary)

        self._load_patients()
        self._on_patient_selected(saved_patient)
        self._update_status(f"Created patient: {saved_patient.name}")

    def _on_generate_prescription(self, clinical_notes: str, callback):
        """Handle prescription generation."""
        if not self.llm.is_available():
            callback(False, None, "Ollama is not running. Please start Ollama first.")
            return

        self._update_status("Generating prescription...")

        def generate():
            success, prescription, raw = self.llm.generate_prescription(clinical_notes)
            if self.page:
                self.page.run_thread_safe(lambda: callback(success, prescription, raw))
                self.page.run_thread_safe(lambda: self._update_status(
                    "Prescription generated" if success else f"Error: {raw[:50]}"
                ))

        threading.Thread(target=generate, daemon=True).start()

    def _on_save_visit(self, visit_data: dict):
        """Handle saving a visit."""
        if not self.current_patient:
            return False

        visit = Visit(
            patient_id=self.current_patient.id,
            **visit_data
        )
        saved_visit = self.db.add_visit(visit)

        # Reindex patient for RAG
        self._index_patient_for_rag(self.current_patient.id)

        self._update_status(f"Visit saved for {self.current_patient.name}")
        return True

    def _on_print_pdf(self, prescription: Prescription, chief_complaint: str) -> Optional[str]:
        """Handle PDF generation."""
        if not self.current_patient or not prescription:
            return None

        filepath = self.pdf.generate_prescription_pdf(
            patient=self.current_patient,
            prescription=prescription,
            chief_complaint=chief_complaint,
            doctor_name="Dr. ",  # TODO: Get from settings
            clinic_name="",
            clinic_address=""
        )

        if filepath:
            self._update_status(f"PDF saved: {filepath}")
        return filepath

    def _on_rag_query(self, question: str, callback):
        """Handle RAG query."""
        if not self.current_patient:
            callback(False, "Please select a patient first.")
            return

        if not self.llm.is_available():
            callback(False, "Ollama is not running. Please start Ollama first.")
            return

        self._update_status("Searching patient records...")

        def query():
            # Get relevant context
            context = self.rag.query_patient_context(
                patient_id=self.current_patient.id,
                query=question,
                n_results=5
            )

            # Generate answer
            success, answer = self.llm.query_patient_records(context, question)

            if self.page:
                self.page.run_thread_safe(lambda: callback(success, answer))
                self.page.run_thread_safe(lambda: self._update_status("Query complete"))

        threading.Thread(target=query, daemon=True).start()

    def _on_backup_click(self, e):
        """Handle backup button click."""
        show_backup_dialog(self.page, self.backup)

    def _on_settings_click(self, e):
        """Handle settings click."""
        model_info = self.llm.get_model_info()

        dialog = ft.AlertDialog(
            title=ft.Text("Settings"),
            content=ft.Column([
                ft.Text(f"Model: {model_info['model']}", size=14),
                ft.Text(f"System RAM: {model_info['ram_gb']:.1f} GB", size=14),
                ft.Text(f"Ollama Status: {'Connected' if model_info['ollama_available'] else 'Not Running'}", size=14),
                ft.Divider(),
                ft.Text("To change models or configure Ollama,", size=12),
                ft.Text("edit the model selection in src/services/llm.py", size=12),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog)),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _on_help_click(self, e):
        """Handle help click."""
        dialog = ft.AlertDialog(
            title=ft.Text("DocAssist EMR - Help"),
            content=ft.Column([
                ft.Text("Quick Start:", weight=ft.FontWeight.BOLD),
                ft.Text("1. Add a patient using the + button", size=12),
                ft.Text("2. Select a patient from the list", size=12),
                ft.Text("3. Enter clinical notes in the center panel", size=12),
                ft.Text("4. Click 'Generate Rx' to create prescription", size=12),
                ft.Text("5. Save and print as PDF", size=12),
                ft.Divider(),
                ft.Text("AI Assistant:", weight=ft.FontWeight.BOLD),
                ft.Text("Ask questions about the patient's history", size=12),
                ft.Text("Example: 'What was his last creatinine?'", size=12),
                ft.Divider(),
                ft.Text("Search:", weight=ft.FontWeight.BOLD),
                ft.Text("Search patients by name or natural language", size=12),
                ft.Text("Example: 'Ram who had PCI to LAD'", size=12),
            ], tight=True, spacing=5, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog)),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _close_dialog(self, dialog):
        """Close a dialog."""
        dialog.open = False
        self.page.update()


def run_app():
    """Run the DocAssist EMR application."""
    app = DocAssistApp()
    ft.app(target=app.main)
