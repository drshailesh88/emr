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
from ..services.simple_backup import SimpleBackupService
from ..services.settings import SettingsService
from ..services.scheduler import BackupScheduler
from ..services.integration.service_registry import ServiceRegistry, get_registry
from ..services.integration.event_bus import EventBus, EventType, get_event_bus
from ..services.integration.clinical_flow import ClinicalFlow
from ..models.schemas import Patient, Visit, Prescription

from .main_layout import MainLayout
from .backup_dialog import show_backup_dialog
from .simple_backup_dialog import show_simple_backup_dialog
from .setup_wizard import SetupWizard
from .components.tutorial_overlay import show_tutorial_overlay
from .keyboard_shortcuts import KeyboardShortcutHandler

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
        self.simple_backup = SimpleBackupService()  # Simple local backup without encryption
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
        self.setup_wizard: Optional[SetupWizard] = None
        self.showing_wizard: bool = False
        self.showing_tutorial: bool = False
        self.tutorial_overlay: Optional[ft.Stack] = None
        self.keyboard_shortcuts: Optional[KeyboardShortcutHandler] = None

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

        # Check if this is first run
        if self.settings.is_first_run():
            logger.info("First run detected - showing setup wizard")
            self.showing_wizard = True
            self._show_setup_wizard()
        else:
            # Normal app flow
            self._show_main_app()

    def _show_setup_wizard(self):
        """Show the first-run setup wizard."""
        self.page.clean()

        # Create and show wizard
        self.setup_wizard = SetupWizard(
            page=self.page,
            settings_service=self.settings,
            on_complete=self._on_wizard_complete
        )

        self.page.add(self.setup_wizard.build())
        self.page.update()

    def _on_wizard_complete(self):
        """Handle wizard completion."""
        logger.info("Setup wizard completed - showing main app")
        self.showing_wizard = False

        # Apply theme from settings
        app_settings = self.settings.load()
        self.page.theme_mode = ft.ThemeMode.DARK if app_settings.theme == "dark" else ft.ThemeMode.LIGHT

        # Show main app
        self._show_main_app()

        # Show tutorial if not completed
        if not self.settings.is_tutorial_completed():
            logger.info("First run - showing tutorial overlay")
            self._show_tutorial_overlay()

    def _show_main_app(self):
        """Show the main application UI."""
        self.page.clean()

        # Check for database corruption and offer to restore
        self._check_database_integrity()

        # Check LLM status in background
        self._check_llm_status()

        # Build UI with MainLayout
        self.page.add(self._build_ui())
        self.page.update()

        # Initialize keyboard shortcuts (after page is set up)
        self._setup_keyboard_shortcuts()

        # Update backup status indicator
        self._update_backup_status()

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

        # Show tutorial if not completed and not just finished wizard
        # (wizard completion handler shows tutorial separately)
        if not self.showing_wizard and not self.settings.is_tutorial_completed():
            logger.info("First run detected - showing tutorial overlay")
            self._show_tutorial_overlay()

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
            # Get doctor settings
            doctor_settings = self.settings.get_doctor_settings()

            filepath = self.pdf.generate_prescription_pdf(
                patient=self.current_patient,
                prescription=prescription,
                chief_complaint=chief_complaint,
                doctor_name=doctor_settings.doctor_name or "Dr. ",
                doctor_qualifications=doctor_settings.qualifications or "",
                clinic_name=doctor_settings.clinic_name or "",
                clinic_address=doctor_settings.clinic_address or ""
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
        # Use simple backup dialog for better UX
        show_simple_backup_dialog(self.page, self.simple_backup)

        # Update backup status after dialog closes
        if self.main_layout:
            last_backup = self.simple_backup.get_last_backup_time()
            self.main_layout.update_backup_status(last_backup)

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
                ft.Divider(),
                ft.Text("Keyboard Shortcuts:", weight=ft.FontWeight.BOLD),
                ft.Text("Press F1 or Ctrl+/ to see all shortcuts", size=12),
                ft.Text("Quick access: Ctrl+N (new), Ctrl+S (save), Ctrl+F (search)", size=12),
                ft.Divider(),
                ft.Container(
                    content=ft.Row([
                        ft.TextButton(
                            "Show Tutorial Again",
                            icon=ft.Icons.SCHOOL_ROUNDED,
                            on_click=lambda e: self._retrigger_tutorial(dialog),
                        ),
                        ft.TextButton(
                            "View All Shortcuts",
                            icon=ft.Icons.KEYBOARD,
                            on_click=lambda e: self._show_shortcuts_from_help(dialog),
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                ),
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
        # Perform simple backup on close
        backup_settings = self.settings.get_backup_settings()
        if backup_settings.backup_on_close:
            logger.info("Creating backup on app close...")
            try:
                backup_path = self.simple_backup.create_backup()
                if backup_path:
                    logger.info(f"Auto-backup created on close: {backup_path}")
                else:
                    logger.warning("Auto-backup on close failed")
            except Exception as ex:
                logger.error(f"Error creating auto-backup on close: {ex}", exc_info=True)

        # Stop scheduler if running
        if self.scheduler:
            # Perform backup on close if enabled
            self.scheduler.backup_on_close()
            # Stop the scheduler
            self.scheduler.stop()

    def _check_database_integrity(self):
        """Check database integrity and offer to restore if corrupted."""
        import sqlite3
        from pathlib import Path

        db_path = Path("data/clinic.db")
        if not db_path.exists():
            logger.info("Database does not exist yet - first run")
            return

        try:
            # Try to open and query the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM patients")
            cursor.fetchone()
            conn.close()
            logger.info("Database integrity check passed")
        except Exception as e:
            logger.error(f"Database integrity check failed: {e}", exc_info=True)

            # Check if backups exist
            backups = self.simple_backup.list_backups()
            if backups:
                # Show restore dialog
                self._show_restore_offer_dialog(backups[0])
            else:
                logger.error("Database corrupted and no backups available!")

    def _show_restore_offer_dialog(self, latest_backup):
        """Show dialog offering to restore from backup.

        Args:
            latest_backup: Latest backup info
        """
        def on_restore(e):
            dialog.open = False
            self.page.update()

            # Restore in background
            def restore():
                try:
                    success = self.simple_backup.restore_backup(latest_backup.path)
                    if success:
                        logger.info("Database restored successfully!")
                        # Reload the app
                        if self.page:
                            self.page.run_thread_safe(lambda: self.page.window_close())
                    else:
                        logger.error("Database restore failed")
                except Exception as ex:
                    logger.error(f"Restore error: {ex}", exc_info=True)

            threading.Thread(target=restore, daemon=True).start()

        def on_skip(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_700),
                ft.Text("Database Issue Detected"),
            ], spacing=10),
            content=ft.Column([
                ft.Text(
                    "The database appears to be corrupted or inaccessible.",
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                ft.Text(f"A backup is available from:"),
                ft.Text(
                    f"{latest_backup.created_at.strftime('%Y-%m-%d %H:%M')}",
                    size=14,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Text(
                    f"Contains: {latest_backup.patient_count} patients, {latest_backup.visit_count} visits",
                    size=12,
                ),
                ft.Divider(),
                ft.Text(
                    "Would you like to restore from this backup?",
                    size=13,
                ),
            ], tight=True, spacing=5),
            actions=[
                ft.TextButton("Skip", on_click=on_skip),
                ft.ElevatedButton(
                    "Restore Backup",
                    on_click=on_restore,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.ORANGE_700,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _update_backup_status(self):
        """Update backup status indicator with latest backup time."""
        if self.main_layout:
            last_backup = self.simple_backup.get_last_backup_time()
            self.main_layout.update_backup_status(last_backup)
            logger.info(f"Backup status updated - last backup: {last_backup}")

    def _show_tutorial_overlay(self):
        """Show the tutorial overlay."""
        if self.showing_tutorial:
            logger.warning("Tutorial already showing")
            return

        self.showing_tutorial = True

        # Get current theme
        app_settings = self.settings.load()
        is_dark = app_settings.theme == "dark"

        # Create tutorial overlay
        self.tutorial_overlay = show_tutorial_overlay(
            page=self.page,
            on_complete=self._on_tutorial_complete,
            on_skip=self._on_tutorial_skip,
            is_dark=is_dark,
        )

        # Add tutorial as overlay
        self.page.overlay.append(self.tutorial_overlay)
        self.page.update()

    def _on_tutorial_complete(self):
        """Handle tutorial completion."""
        logger.info("Tutorial completed by user")

        # Mark tutorial as completed in settings
        self.settings.mark_tutorial_completed()

        # Remove tutorial overlay
        self._hide_tutorial_overlay()

    def _on_tutorial_skip(self):
        """Handle tutorial skip."""
        logger.info("Tutorial skipped by user")

        # Mark tutorial as completed (so it doesn't show again)
        self.settings.mark_tutorial_completed()

        # Remove tutorial overlay
        self._hide_tutorial_overlay()

    def _hide_tutorial_overlay(self):
        """Hide the tutorial overlay."""
        if self.tutorial_overlay and self.tutorial_overlay in self.page.overlay:
            self.page.overlay.remove(self.tutorial_overlay)
            self.tutorial_overlay = None
            self.showing_tutorial = False
            self.page.update()

    def _retrigger_tutorial(self, help_dialog):
        """Re-trigger the tutorial from help menu.

        Args:
            help_dialog: The help dialog to close
        """
        # Close help dialog first
        self._close_dialog(help_dialog)

        # Reset and show tutorial
        self.settings.reset_tutorial()
        self._show_tutorial_overlay()

    def _show_shortcuts_from_help(self, help_dialog):
        """Show keyboard shortcuts help from help menu.

        Args:
            help_dialog: The help dialog to close
        """
        # Close help dialog first
        self._close_dialog(help_dialog)

        # Show shortcuts help overlay
        if self.keyboard_shortcuts:
            self.keyboard_shortcuts._show_help_overlay()

    def _setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts."""
        # Initialize keyboard shortcuts handler
        self.keyboard_shortcuts = KeyboardShortcutHandler(self.page)

        # Wire up callbacks
        self.keyboard_shortcuts.on_new_patient = self._shortcut_new_patient
        self.keyboard_shortcuts.on_save = self._shortcut_save
        self.keyboard_shortcuts.on_focus_search = self._shortcut_focus_search
        self.keyboard_shortcuts.on_print_pdf = self._shortcut_print_pdf
        self.keyboard_shortcuts.on_toggle_voice = self._shortcut_toggle_voice
        self.keyboard_shortcuts.on_submit = self._shortcut_submit
        self.keyboard_shortcuts.on_switch_tab = self._shortcut_switch_tab
        self.keyboard_shortcuts.on_backup = self._shortcut_backup
        self.keyboard_shortcuts.on_refresh_patients = self._shortcut_refresh_patients
        self.keyboard_shortcuts.on_navigate_patient = self._shortcut_navigate_patient
        self.keyboard_shortcuts.on_generate_rx = self._shortcut_generate_rx
        self.keyboard_shortcuts.on_settings = self._shortcut_settings
        self.keyboard_shortcuts.on_help = self._shortcut_help

        logger.info("Keyboard shortcuts initialized and wired up")

    # Keyboard shortcut action handlers
    def _shortcut_new_patient(self):
        """Handle new patient keyboard shortcut."""
        if self.main_layout and self.main_layout.patient_panel:
            # Trigger the new patient dialog
            self.main_layout.patient_panel._on_add_patient_click(None)
            logger.debug("Keyboard shortcut: New patient triggered")

    def _shortcut_save(self):
        """Handle save keyboard shortcut."""
        if self.main_layout and self.main_layout.central_panel:
            # Trigger save visit
            self.main_layout.central_panel._on_save_click(None)
            logger.debug("Keyboard shortcut: Save triggered")

    def _shortcut_focus_search(self):
        """Handle focus search keyboard shortcut."""
        if self.main_layout and self.main_layout.patient_panel:
            # Focus the search field
            if hasattr(self.main_layout.patient_panel, 'search_field'):
                search_field = self.main_layout.patient_panel.search_field
                if search_field:
                    search_field.focus()
                    self.page.update()
                    logger.debug("Keyboard shortcut: Search focused")

    def _shortcut_print_pdf(self):
        """Handle print PDF keyboard shortcut."""
        if self.main_layout and self.main_layout.central_panel:
            # Trigger print PDF
            if hasattr(self.main_layout.central_panel, 'print_btn'):
                print_btn = self.main_layout.central_panel.print_btn
                if print_btn and not print_btn.disabled:
                    self.main_layout.central_panel._on_print_click(None)
                    logger.debug("Keyboard shortcut: Print PDF triggered")

    def _shortcut_toggle_voice(self):
        """Handle toggle voice keyboard shortcut."""
        if self.main_layout and self.main_layout.central_panel:
            # Toggle voice recording
            if hasattr(self.main_layout.central_panel, 'voice_btn'):
                voice_btn = self.main_layout.central_panel.voice_btn
                if voice_btn and hasattr(voice_btn, '_toggle_recording'):
                    voice_btn._toggle_recording(None)
                    self.page.update()
                    logger.debug("Keyboard shortcut: Voice toggle triggered")

    def _shortcut_submit(self):
        """Handle submit keyboard shortcut."""
        # Same as save for now - could be different based on context
        self._shortcut_save()

    def _shortcut_switch_tab(self, tab_index: int):
        """Handle tab switch keyboard shortcut."""
        if self.main_layout and self.main_layout.tab_navigation:
            # Switch to the specified tab
            self.main_layout._switch_to_tab(tab_index)
            logger.debug(f"Keyboard shortcut: Switched to tab {tab_index}")

    def _shortcut_backup(self):
        """Handle backup keyboard shortcut."""
        # Trigger backup dialog
        self._on_backup_click(None)
        logger.debug("Keyboard shortcut: Backup triggered")

    def _shortcut_refresh_patients(self):
        """Handle refresh patients keyboard shortcut."""
        # Reload patient list
        self._load_patients()
        logger.debug("Keyboard shortcut: Patients refreshed")

    def _shortcut_navigate_patient(self, direction: str):
        """Handle patient navigation keyboard shortcut."""
        if self.main_layout and self.main_layout.patient_panel:
            if hasattr(self.main_layout.patient_panel, 'navigate_patient'):
                self.main_layout.patient_panel.navigate_patient(direction)
                logger.debug(f"Keyboard shortcut: Navigate patient {direction}")

    def _shortcut_generate_rx(self):
        """Handle generate prescription keyboard shortcut."""
        if self.main_layout and self.main_layout.central_panel:
            # Trigger prescription generation
            if hasattr(self.main_layout.central_panel, 'generate_btn'):
                generate_btn = self.main_layout.central_panel.generate_btn
                if generate_btn and not generate_btn.disabled:
                    self.main_layout.central_panel._on_generate_click(None)
                    logger.debug("Keyboard shortcut: Generate Rx triggered")

    def _shortcut_settings(self):
        """Handle settings keyboard shortcut."""
        # Trigger settings dialog
        self._on_settings_click(None)
        logger.debug("Keyboard shortcut: Settings triggered")

    def _shortcut_help(self):
        """Handle help keyboard shortcut."""
        # Trigger help dialog
        self._on_help_click(None)
        logger.debug("Keyboard shortcut: Help triggered")


def run_app():
    """Run the DocAssist EMR application."""
    app = DocAssistApp()
    ft.app(target=app.main)
