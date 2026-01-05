"""Main Flet application with revolutionary UI integration."""

import flet as ft
from typing import Optional
import threading
import logging

from ..services.database import DatabaseService
from ..services.llm import LLMService
from ..services.rag import RAGService
from ..services.pdf import PDFService
from ..services.backup import BackupService
from ..services.settings import SettingsService
from ..services.scheduler import BackupScheduler
from ..services.integration.service_registry import ServiceRegistry, get_registry
from ..services.integration.event_bus import EventBus, EventType, get_event_bus
from ..services.integration.clinical_flow import ClinicalFlow
from ..models.schemas import Patient, Visit, Prescription

from .main_layout import MainLayout
from .backup_dialog import show_backup_dialog

logger = logging.getLogger(__name__)


class DocAssistApp:
    """Main application class with revolutionary features integration."""

    def __init__(self):
        # Core services
        self.db = DatabaseService()
        self.llm = LLMService()
        self.rag = RAGService()
        self.pdf = PDFService()
        self.backup = BackupService()
        self.settings = SettingsService()

        # Initialize backup scheduler
        backup_settings_dict = self.settings.get_backup_settings().to_dict()
        self.scheduler = BackupScheduler(
            backup_service=self.backup,
            settings_dict=backup_settings_dict,
            database_service=self.db
        )

        # Integration layer - Service Registry
        self.service_registry = get_registry()
        self._register_services()

        # Integration layer - Event Bus
        self.event_bus = get_event_bus()
        self._setup_event_subscriptions()

        # Integration layer - Clinical Flow
        self.clinical_flow = ClinicalFlow(
            services={
                "database": self.db,
                "llm": self.llm,
                "rag": self.rag,
                "pdf": self.pdf,
                "backup": self.backup,
            },
            event_bus=self.event_bus,
            service_registry=self.service_registry,
        )

        self.current_patient: Optional[Patient] = None
        self.page: Optional[ft.Page] = None

        # UI components (initialized in build)
        self.main_layout: Optional[MainLayout] = None

    def _register_services(self):
        """Register services in the service registry."""
        self.service_registry.register("database", self.db)
        self.service_registry.register("llm", self.llm)
        self.service_registry.register("rag", self.rag)
        self.service_registry.register("pdf", self.pdf)
        self.service_registry.register("backup", self.backup)
        self.service_registry.register("settings", self.settings)
        logger.info("Services registered in ServiceRegistry")

    def _setup_event_subscriptions(self):
        """Setup event subscriptions for app-level handlers."""
        # Subscribe to consultation events
        self.event_bus.subscribe(
            EventType.CONSULTATION_STARTED,
            self._on_consultation_started_event,
        )
        self.event_bus.subscribe(
            EventType.PRESCRIPTION_SENT,
            self._on_prescription_sent_event,
        )
        logger.info("Event subscriptions set up")

    def _on_consultation_started_event(self, event):
        """Handle consultation started event."""
        logger.info(f"Consultation started event: {event.data}")

    def _on_prescription_sent_event(self, event):
        """Handle prescription sent event."""
        logger.info(f"Prescription sent event: {event.data}")

    def main(self, page: ft.Page):
        """Main entry point for Flet app."""
        self.page = page
        page.title = "DocAssist EMR - Revolutionary AI-Powered Practice"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.spacing = 0

        # Set window size
        page.window.width = 1600
        page.window.height = 900
        page.window.min_width = 1200
        page.window.min_height = 700

        # Set close handler
        page.on_close = self._on_app_close

        # Check LLM status in background
        self._check_llm_status()

        # Build UI with MainLayout
        page.add(self._build_ui())
        page.update()

        # Load patients
        self._load_patients()

        # Start backup scheduler
        if self.scheduler:
            self.scheduler.start()

        # Publish app started event
        self.event_bus.publish_sync(
            EventType.SERVICE_STARTED,
            {"service": "DocAssistApp"}
        )

    def _build_ui(self) -> ft.Control:
        """Build the main UI layout using MainLayout."""

        # Initialize main layout with all services and integration layer
        self.main_layout = MainLayout(
            # Services
            db_service=self.db,
            llm_service=self.llm,
            rag_service=self.rag,
            pdf_service=self.pdf,
            backup_service=self.backup,
            settings_service=self.settings,
            # Integration layer
            clinical_flow=self.clinical_flow,
            event_bus=self.event_bus,
            # Callbacks
            on_settings_click=self._on_settings_click,
            on_help_click=self._on_help_click,
            on_backup_click=self._on_backup_click,
            # Theme
            is_dark=False,
        )

        # Wire up MainLayout callbacks to app methods
        self.main_layout._on_new_patient = self._on_new_patient
        self.main_layout._on_generate_prescription = self._on_generate_prescription
        self.main_layout._on_save_visit = self._on_save_visit
        self.main_layout._on_print_pdf = self._on_print_pdf
        self.main_layout._on_rag_query = self._on_rag_query
        self.main_layout._on_patient_search = self._on_patient_search

        return self.main_layout.build()

    def _check_llm_status(self):
        """Check LLM availability in background."""
        def check():
            try:
                if self.llm.is_available():
                    model_info = self.llm.get_model_info()
                    logger.info(f"LLM available: {model_info['model']}, RAM: {model_info['ram_gb']:.1f}GB")

                    # Update MainLayout with LLM status
                    if self.main_layout and self.page:
                        self.page.run_task(lambda: self.main_layout.set_llm_status(True, model_info))
                else:
                    logger.warning("Ollama not running - AI features disabled")

                    if self.main_layout and self.page:
                        self.page.run_task(lambda: self.main_layout.set_llm_status(False))
            except Exception as e:
                logger.error(f"Error checking LLM status: {e}", exc_info=True)

                if self.main_layout and self.page:
                    self.page.run_task(lambda: self.main_layout.set_llm_status(False))

        threading.Thread(target=check, daemon=True).start()

    def _load_patients(self):
        """Load all patients into the list."""
        patients = self.db.get_all_patients()
        if self.main_layout and self.main_layout.patient_panel:
            self.main_layout.patient_panel.set_patients(patients)

    def _on_patient_selected(self, patient: Patient):
        """Handle patient selection (delegated from MainLayout)."""
        self.current_patient = patient

        # Index patient documents for RAG in background
        self._index_patient_for_rag(patient.id)

        # Note: MainLayout already handles UI updates
        logger.info(f"App: Patient selected - {patient.name} ({patient.uhid})")

    def _index_patient_for_rag(self, patient_id: int):
        """Index patient documents for RAG in background."""
        def index():
            try:
                # Get patient summary
                summary = self.db.get_patient_summary(patient_id)
                if summary:
                    self.rag.index_patient_summary(patient_id, summary)

                # Get all documents
                documents = self.db.get_patient_documents_for_rag(patient_id)
                if documents:
                    self.rag.index_patient_documents(patient_id, documents)
                logger.debug(f"Indexed patient {patient_id} for RAG")
            except Exception as e:
                logger.error(f"Error indexing patient {patient_id} for RAG: {e}", exc_info=True)

        threading.Thread(target=index, daemon=True).start()

    def _on_patient_search(self, query: str):
        """Handle patient search."""
        try:
            if not query.strip():
                self._load_patients()
                return

            logger.debug(f"Searching patients with query: {query}")
            # First try basic search
            patients = self.db.search_patients_basic(query)

            # If no results and query looks like natural language, try RAG search
            if not patients and len(query.split()) > 2:
                results = self.rag.search_patients(query, n_results=10)
                if results:
                    patient_ids = [r[0] for r in results]
                    patients = [self.db.get_patient(pid) for pid in patient_ids if self.db.get_patient(pid)]

            if self.main_layout and self.main_layout.patient_panel:
                self.main_layout.patient_panel.set_patients(patients)
            logger.info(f"Patient search returned {len(patients)} results")
        except Exception as e:
            logger.error(f"Error during patient search: {e}", exc_info=True)

    def _on_new_patient(self, patient_data: dict):
        """Handle new patient creation."""
        try:
            patient = Patient(**patient_data)
            saved_patient = self.db.add_patient(patient)
            logger.info(f"Created new patient: {saved_patient.name} (ID: {saved_patient.id})")

            # Index for RAG
            summary = f"Patient: {saved_patient.name}. UHID: {saved_patient.uhid}"
            if saved_patient.age:
                summary += f". Age: {saved_patient.age}"
            if saved_patient.gender:
                summary += f". Gender: {saved_patient.gender}"
            self.rag.index_patient_summary(saved_patient.id, summary)

            self._load_patients()

            # Select the new patient through MainLayout
            if self.main_layout:
                self.main_layout._on_patient_selected(saved_patient)

            # Publish event
            self.event_bus.publish_sync(
                EventType.PATIENT_CREATED,
                {"patient_id": saved_patient.id, "patient_name": saved_patient.name}
            )
        except Exception as e:
            logger.error(f"Error creating new patient: {e}", exc_info=True)

    def _on_generate_prescription(self, clinical_notes: str, callback):
        """Handle prescription generation."""
        if not self.llm.is_available():
            logger.warning("Prescription generation attempted but Ollama not available")
            callback(False, None, "Ollama is not running. Please start Ollama first.")
            return

        logger.debug("Starting prescription generation")

        def generate():
            try:
                success, prescription, raw = self.llm.generate_prescription(clinical_notes)
                if success:
                    logger.info("Prescription generated successfully")

                    # Publish event
                    self.event_bus.publish_sync(
                        EventType.PRESCRIPTION_CREATED,
                        {
                            "patient_id": self.current_patient.id if self.current_patient else None,
                            "prescription": prescription.to_dict() if prescription else None
                        }
                    )
                else:
                    logger.error(f"Prescription generation failed: {raw[:100]}")
                if self.page:
                    self.page.run_thread_safe(lambda: callback(success, prescription, raw))
            except Exception as e:
                logger.error(f"Error during prescription generation: {e}", exc_info=True)
                if self.page:
                    self.page.run_thread_safe(lambda: callback(False, None, str(e)))

        threading.Thread(target=generate, daemon=True).start()

    def _on_save_visit(self, visit_data: dict):
        """Handle saving a visit."""
        if not self.current_patient:
            logger.warning("Save visit attempted without current patient")
            return False

        try:
            visit = Visit(
                patient_id=self.current_patient.id,
                **visit_data
            )
            saved_visit = self.db.add_visit(visit)
            logger.info(f"Visit saved for patient {self.current_patient.id} (Visit ID: {saved_visit.id})")

            # Reindex patient for RAG
            self._index_patient_for_rag(self.current_patient.id)

            # Stop consultation timer
            if self.main_layout and self.main_layout.status_bar:
                self.main_layout.status_bar.stop_consultation()

            # Publish event
            self.event_bus.publish_sync(
                EventType.CONSULTATION_COMPLETED,
                {
                    "patient_id": self.current_patient.id,
                    "visit_id": saved_visit.id
                }
            )

            return True
        except Exception as e:
            logger.error(f"Error saving visit: {e}", exc_info=True)
            return False

    def _on_print_pdf(self, prescription: Prescription, chief_complaint: str) -> Optional[str]:
        """Handle PDF generation."""
        if not self.current_patient or not prescription:
            logger.warning("PDF generation attempted without patient or prescription")
            return None

        try:
            filepath = self.pdf.generate_prescription_pdf(
                patient=self.current_patient,
                prescription=prescription,
                chief_complaint=chief_complaint,
                doctor_name="Dr. ",  # TODO: Get from settings
                clinic_name="",
                clinic_address=""
            )

            if filepath:
                logger.info(f"PDF generated: {filepath}")
            else:
                logger.warning("PDF generation returned no filepath")
            return filepath
        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            return None

    def _on_rag_query(self, question: str, callback):
        """Handle RAG query."""
        if not self.current_patient:
            logger.warning("RAG query attempted without current patient")
            callback(False, "Please select a patient first.")
            return

        if not self.llm.is_available():
            logger.warning("RAG query attempted but Ollama not available")
            callback(False, "Ollama is not running. Please start Ollama first.")
            return

        logger.debug(f"RAG query for patient {self.current_patient.id}: {question}")

        def query():
            try:
                # Get relevant context
                context = self.rag.query_patient_context(
                    patient_id=self.current_patient.id,
                    query=question,
                    n_results=5
                )

                # Generate answer
                success, answer = self.llm.query_patient_records(context, question)

                if success:
                    logger.info("RAG query completed successfully")
                else:
                    logger.error(f"RAG query failed: {answer}")

                if self.page:
                    self.page.run_thread_safe(lambda: callback(success, answer))
            except Exception as e:
                logger.error(f"Error during RAG query: {e}", exc_info=True)
                if self.page:
                    self.page.run_thread_safe(lambda: callback(False, f"Error: {str(e)}"))

        threading.Thread(target=query, daemon=True).start()

    def _on_backup_click(self, e):
        """Handle backup button click."""
        show_backup_dialog(self.page, self.backup, self.scheduler, self.settings)

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

    def _on_app_close(self, e):
        """Handle app close event."""
        if self.scheduler:
            # Perform backup on close if enabled
            self.scheduler.backup_on_close()
            # Stop the scheduler
            self.scheduler.stop()


def run_app():
    """Run the DocAssist EMR application."""
    app = DocAssistApp()
    ft.app(target=app.main)
