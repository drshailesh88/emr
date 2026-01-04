"""
Main Flet application with premium 3-panel layout.

Uses design tokens from tokens.py for consistent, premium styling.
"""

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
from ..models.schemas import Patient, Visit, Prescription

from .patient_panel import PatientPanel
from .central_panel import CentralPanel
from .agent_panel import AgentPanel
from .backup_dialog import show_backup_dialog

# Import premium design system
from .themes import (
    get_light_theme,
    get_dark_theme,
    get_panel_colors,
    get_alert_colors,
    get_button_style,
    Colors,
    Typography,
    Spacing,
    Radius,
    Shadows,
)

logger = logging.getLogger(__name__)


class DocAssistApp:
    """Main application class with premium UI."""

    def __init__(self):
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

        self.current_patient: Optional[Patient] = None
        self.page: Optional[ft.Page] = None
        self.is_dark_mode: bool = False

        # UI components (initialized in build)
        self.patient_panel: Optional[PatientPanel] = None
        self.central_panel: Optional[CentralPanel] = None
        self.agent_panel: Optional[AgentPanel] = None
        self.status_bar: Optional[ft.Text] = None

    def main(self, page: ft.Page):
        """Main entry point for Flet app."""
        self.page = page
        page.title = "DocAssist EMR"

        # Apply premium theme
        page.theme = get_light_theme()
        page.dark_theme = get_dark_theme()
        page.theme_mode = ft.ThemeMode.LIGHT

        page.padding = 0
        page.spacing = 0

        # Set window size
        page.window.width = 1400
        page.window.height = 800
        page.window.min_width = 1000
        page.window.min_height = 600

        # Set close handler
        page.on_close = self._on_app_close

        # Check LLM status in background
        self._check_llm_status()

        # Build UI
        page.add(self._build_ui())
        page.update()

        # Load patients
        self._load_patients()

        # Start backup scheduler
        if self.scheduler:
            self.scheduler.start()

    def _get_colors(self):
        """Get current theme colors."""
        return get_panel_colors(self.is_dark_mode)

    def _build_ui(self) -> ft.Control:
        """Build the premium main UI layout."""
        colors = self._get_colors()

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

        # Premium status bar
        self.status_bar = ft.Text(
            "Ready",
            size=Typography.BODY_SMALL.size,
            color=colors['status_text'],
            weight=ft.FontWeight.W_400,
        )

        # Premium header with subtle shadow
        header = ft.Container(
            content=ft.Row(
                [
                    # Logo and title
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.LOCAL_HOSPITAL,
                                color=Colors.PRIMARY_500,
                                size=24,
                            ),
                            padding=Spacing.XS,
                            border_radius=Radius.SM,
                            bgcolor=Colors.PRIMARY_50,
                        ),
                        ft.Text(
                            "DocAssist",
                            size=Typography.HEADLINE_MEDIUM.size,
                            weight=ft.FontWeight.W_600,
                            color=Colors.NEUTRAL_900,
                        ),
                        ft.Text(
                            "EMR",
                            size=Typography.HEADLINE_MEDIUM.size,
                            weight=ft.FontWeight.W_300,
                            color=Colors.NEUTRAL_500,
                        ),
                    ], spacing=Spacing.SM),

                    # Right side: status and actions
                    ft.Row([
                        # Status indicator
                        ft.Container(
                            content=self.status_bar,
                            padding=ft.padding.symmetric(
                                horizontal=Spacing.SM,
                                vertical=Spacing.XXS
                            ),
                            border_radius=Radius.SM,
                            bgcolor=Colors.NEUTRAL_100,
                        ),

                        # Action buttons with premium styling
                        ft.IconButton(
                            icon=ft.Icons.BACKUP_OUTLINED,
                            icon_color=Colors.NEUTRAL_600,
                            icon_size=20,
                            tooltip="Backup & Restore",
                            on_click=self._on_backup_click,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                                overlay_color=Colors.HOVER_OVERLAY,
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS_OUTLINED,
                            icon_color=Colors.NEUTRAL_600,
                            icon_size=20,
                            tooltip="Settings",
                            on_click=self._on_settings_click,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                                overlay_color=Colors.HOVER_OVERLAY,
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.HELP_OUTLINE,
                            icon_color=Colors.NEUTRAL_600,
                            icon_size=20,
                            tooltip="Help",
                            on_click=self._on_help_click,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                                overlay_color=Colors.HOVER_OVERLAY,
                            ),
                        ),
                    ], spacing=Spacing.XXS),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(
                horizontal=Spacing.LG,
                vertical=Spacing.SM
            ),
            bgcolor=colors['header_bg'],
            border=ft.border.only(
                bottom=ft.BorderSide(1, colors['header_border'])
            ),
            shadow=ft.BoxShadow(
                blur_radius=8,
                spread_radius=0,
                offset=ft.Offset(0, 2),
                color="rgba(0,0,0,0.04)",
            ),
        )

        # Main content with premium 3-panel layout
        main_content = ft.Row(
            [
                # Left panel - Patients (fixed width)
                ft.Container(
                    content=self.patient_panel.build(),
                    width=280,
                    bgcolor=colors['patient_panel_bg'],
                    border=ft.border.only(
                        right=ft.BorderSide(1, colors['patient_panel_border'])
                    ),
                ),
                # Center panel - Main content (expandable)
                ft.Container(
                    content=self.central_panel.build(),
                    expand=True,
                    bgcolor=colors['central_panel_bg'],
                ),
                # Right panel - AI Agent (fixed width)
                ft.Container(
                    content=self.agent_panel.build(),
                    width=350,
                    bgcolor=colors['agent_panel_bg'],
                    border=ft.border.only(
                        left=ft.BorderSide(1, colors['divider'])
                    ),
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
            try:
                if self.llm.is_available():
                    model_info = self.llm.get_model_info()
                    logger.info(f"LLM available: {model_info['model']}, RAM: {model_info['ram_gb']:.1f}GB")
                    self._update_status(f"AI: {model_info['model']} | {model_info['ram_gb']:.1f}GB")
                else:
                    logger.warning("Ollama not running - AI features disabled")
                    self._update_status("Ollama not running", error=True)
            except Exception as e:
                logger.error(f"Error checking LLM status: {e}", exc_info=True)
                self._update_status("LLM error", error=True)

        threading.Thread(target=check, daemon=True).start()

    def _update_status(self, message: str, error: bool = False):
        """Update status bar with premium styling."""
        if self.status_bar and self.page:
            colors = self._get_colors()
            self.status_bar.value = message
            self.status_bar.color = colors['status_error'] if error else colors['status_text']
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
            try:
                summary = self.db.get_patient_summary(patient_id)
                if summary:
                    self.rag.index_patient_summary(patient_id, summary)

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
            patients = self.db.search_patients_basic(query)

            if not patients and len(query.split()) > 2:
                results = self.rag.search_patients(query, n_results=10)
                if results:
                    patient_ids = [r[0] for r in results]
                    patients = [self.db.get_patient(pid) for pid in patient_ids if self.db.get_patient(pid)]

            self.patient_panel.set_patients(patients)
            logger.info(f"Patient search returned {len(patients)} results")
        except Exception as e:
            logger.error(f"Error during patient search: {e}", exc_info=True)
            self._update_status("Search error", error=True)

    def _on_new_patient(self, patient_data: dict):
        """Handle new patient creation."""
        try:
            patient = Patient(**patient_data)
            saved_patient = self.db.add_patient(patient)
            logger.info(f"Created new patient: {saved_patient.name} (ID: {saved_patient.id})")

            summary = f"Patient: {saved_patient.name}. UHID: {saved_patient.uhid}"
            if saved_patient.age:
                summary += f". Age: {saved_patient.age}"
            if saved_patient.gender:
                summary += f". Gender: {saved_patient.gender}"
            self.rag.index_patient_summary(saved_patient.id, summary)

            self._load_patients()
            self._on_patient_selected(saved_patient)
            self._update_status(f"Created: {saved_patient.name}")
        except Exception as e:
            logger.error(f"Error creating new patient: {e}", exc_info=True)
            self._update_status("Creation error", error=True)

    def _on_generate_prescription(self, clinical_notes: str, callback):
        """Handle prescription generation."""
        if not self.llm.is_available():
            logger.warning("Prescription generation attempted but Ollama not available")
            callback(False, None, "Ollama is not running. Please start Ollama first.")
            return

        self._update_status("Generating Rx...")
        logger.debug("Starting prescription generation")

        def generate():
            try:
                success, prescription, raw = self.llm.generate_prescription(clinical_notes)
                if success:
                    logger.info("Prescription generated successfully")
                else:
                    logger.error(f"Prescription generation failed: {raw[:100]}")
                if self.page:
                    self.page.run_thread_safe(lambda: callback(success, prescription, raw))
                    self.page.run_thread_safe(lambda: self._update_status(
                        "Rx generated" if success else "Rx error", error=not success
                    ))
            except Exception as e:
                logger.error(f"Error during prescription generation: {e}", exc_info=True)
                if self.page:
                    self.page.run_thread_safe(lambda: callback(False, None, str(e)))
                    self.page.run_thread_safe(lambda: self._update_status("Rx error", error=True))

        threading.Thread(target=generate, daemon=True).start()

    def _on_save_visit(self, visit_data: dict):
        """Handle saving a visit."""
        if not self.current_patient:
            logger.warning("Save visit attempted without current patient")
            return False

        try:
            visit = Visit(patient_id=self.current_patient.id, **visit_data)
            saved_visit = self.db.add_visit(visit)
            logger.info(f"Visit saved for patient {self.current_patient.id} (Visit ID: {saved_visit.id})")

            self._index_patient_for_rag(self.current_patient.id)
            self._update_status(f"Saved visit for {self.current_patient.name}")
            return True
        except Exception as e:
            logger.error(f"Error saving visit: {e}", exc_info=True)
            self._update_status("Save error", error=True)
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
                doctor_name="Dr. ",
                clinic_name="",
                clinic_address=""
            )

            if filepath:
                logger.info(f"PDF generated: {filepath}")
                self._update_status("PDF saved")
            else:
                logger.warning("PDF generation returned no filepath")
            return filepath
        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            self._update_status("PDF error", error=True)
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

        self._update_status("Searching...")
        logger.debug(f"RAG query for patient {self.current_patient.id}: {question}")

        def query():
            try:
                context = self.rag.query_patient_context(
                    patient_id=self.current_patient.id,
                    query=question,
                    n_results=5
                )
                success, answer = self.llm.query_patient_records(context, question)

                if success:
                    logger.info("RAG query completed successfully")
                else:
                    logger.error(f"RAG query failed: {answer}")

                if self.page:
                    self.page.run_thread_safe(lambda: callback(success, answer))
                    self.page.run_thread_safe(lambda: self._update_status("Ready"))
            except Exception as e:
                logger.error(f"Error during RAG query: {e}", exc_info=True)
                if self.page:
                    self.page.run_thread_safe(lambda: callback(False, f"Error: {str(e)}"))
                    self.page.run_thread_safe(lambda: self._update_status("Query error", error=True))

        threading.Thread(target=query, daemon=True).start()

    def _on_backup_click(self, e):
        """Handle backup button click."""
        show_backup_dialog(self.page, self.backup, self.scheduler, self.settings)

    def _on_settings_click(self, e):
        """Handle settings click with premium dialog."""
        colors = self._get_colors()
        model_info = self.llm.get_model_info()

        dialog = ft.AlertDialog(
            title=ft.Text(
                "Settings",
                size=Typography.HEADLINE_SMALL.size,
                weight=ft.FontWeight.W_500,
            ),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        f"Model: {model_info['model']}",
                        size=Typography.BODY_MEDIUM.size,
                    ),
                    ft.Text(
                        f"System RAM: {model_info['ram_gb']:.1f} GB",
                        size=Typography.BODY_MEDIUM.size,
                    ),
                    ft.Text(
                        f"Ollama: {'Connected' if model_info['ollama_available'] else 'Not Running'}",
                        size=Typography.BODY_MEDIUM.size,
                        color=Colors.SUCCESS_MAIN if model_info['ollama_available'] else Colors.ERROR_MAIN,
                    ),
                    ft.Divider(height=Spacing.MD),
                    ft.Text(
                        "Model configuration is in src/services/llm.py",
                        size=Typography.BODY_SMALL.size,
                        color=colors['text_secondary'],
                    ),
                ], tight=True, spacing=Spacing.SM),
                padding=Spacing.SM,
            ),
            actions=[
                ft.TextButton(
                    "Close",
                    on_click=lambda e: self._close_dialog(dialog),
                    style=get_button_style("ghost"),
                ),
            ],
            shape=ft.RoundedRectangleBorder(radius=Radius.DIALOG),
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _on_help_click(self, e):
        """Handle help click with premium dialog."""
        colors = self._get_colors()

        dialog = ft.AlertDialog(
            title=ft.Text(
                "Quick Start Guide",
                size=Typography.HEADLINE_SMALL.size,
                weight=ft.FontWeight.W_500,
            ),
            content=ft.Container(
                content=ft.Column([
                    # Getting Started
                    ft.Text(
                        "Getting Started",
                        weight=ft.FontWeight.W_600,
                        size=Typography.TITLE_SMALL.size,
                    ),
                    ft.Text("1. Add a patient using the + button", size=Typography.BODY_SMALL.size),
                    ft.Text("2. Select a patient from the list", size=Typography.BODY_SMALL.size),
                    ft.Text("3. Enter clinical notes in the center panel", size=Typography.BODY_SMALL.size),
                    ft.Text("4. Click 'Generate Rx' to create prescription", size=Typography.BODY_SMALL.size),
                    ft.Text("5. Save and print as PDF", size=Typography.BODY_SMALL.size),

                    ft.Divider(height=Spacing.MD),

                    # AI Assistant
                    ft.Text(
                        "AI Assistant",
                        weight=ft.FontWeight.W_600,
                        size=Typography.TITLE_SMALL.size,
                    ),
                    ft.Text(
                        "Ask questions about patient history",
                        size=Typography.BODY_SMALL.size,
                    ),
                    ft.Container(
                        content=ft.Text(
                            '"What was his last creatinine?"',
                            size=Typography.BODY_SMALL.size,
                            italic=True,
                        ),
                        padding=ft.padding.only(left=Spacing.SM),
                    ),

                    ft.Divider(height=Spacing.MD),

                    # Search
                    ft.Text(
                        "Smart Search",
                        weight=ft.FontWeight.W_600,
                        size=Typography.TITLE_SMALL.size,
                    ),
                    ft.Text(
                        "Search by name or natural language",
                        size=Typography.BODY_SMALL.size,
                    ),
                    ft.Container(
                        content=ft.Text(
                            '"Ram who had PCI to LAD"',
                            size=Typography.BODY_SMALL.size,
                            italic=True,
                        ),
                        padding=ft.padding.only(left=Spacing.SM),
                    ),
                ], tight=True, spacing=Spacing.XS, scroll=ft.ScrollMode.AUTO),
                padding=Spacing.SM,
                width=320,
            ),
            actions=[
                ft.TextButton(
                    "Got it",
                    on_click=lambda e: self._close_dialog(dialog),
                    style=get_button_style("primary"),
                ),
            ],
            shape=ft.RoundedRectangleBorder(radius=Radius.DIALOG),
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
            self.scheduler.backup_on_close()
            self.scheduler.stop()


def run_app():
    """Run the DocAssist EMR application."""
    app = DocAssistApp()
    ft.app(target=app.main)
