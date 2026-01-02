"""Main Flet application with 3-panel layout."""

import flet as ft
from typing import Optional
import threading
from datetime import datetime
import time
from pathlib import Path
import json

from ..services.database import DatabaseService
from ..services.llm import LLMService
from ..services.rag import RAGService
from ..services.pdf import PDFService
from ..services.settings import SettingsService
from ..services.backup import BackupService
from ..services.export import ExportService
from ..models.schemas import Patient, Visit, Prescription

from .patient_panel import PatientPanel
from .settings_dialog import SettingsDialog
from .central_panel import CentralPanel
from .agent_panel import AgentPanel
from .phrase_manager import PhraseManager
from .themes import LIGHT_THEME, DARK_THEME, get_panel_colors, get_alert_colors


class DocAssistApp:
    """Main application class."""

    def __init__(self):
        # Initialize settings first
        settings_path = Path("data/settings.json")
        self.settings_service = SettingsService(settings_path)
        self.settings_service.load()  # Load settings on startup

        self.db = DatabaseService()
        self.llm = LLMService()
        self.rag = RAGService()
        self.pdf = PDFService()
        self.backup = BackupService()
        self.export = ExportService(db=self.db, pdf_service=self.pdf)

        # Load initial templates if needed
        self._load_initial_templates()

        # Load initial drugs if needed
        self._load_initial_drugs()

        self.current_patient: Optional[Patient] = None
        self.page: Optional[ft.Page] = None

        # UI components (initialized in build)
        self.patient_panel: Optional[PatientPanel] = None
        self.central_panel: Optional[CentralPanel] = None
        self.agent_panel: Optional[AgentPanel] = None
        self.status_bar: Optional[ft.Text] = None

        # For managing open dialogs
        self.current_dialog: Optional[ft.AlertDialog] = None

        # Backup tracking
        self.last_backup_time: Optional[datetime] = None
        self.backup_timer_running = False
        self.backup_interval_hours = self.settings_service.settings.preferences.backup_frequency_hours

    def main(self, page: ft.Page):
        """Main entry point for Flet app."""
        self.page = page
        page.title = "DocAssist EMR"

        # Set custom themes
        page.theme = LIGHT_THEME
        page.dark_theme = DARK_THEME

        # Apply theme mode from settings
        theme = self.settings_service.settings.preferences.theme
        if theme == "system":
            page.theme_mode = ft.ThemeMode.SYSTEM
        elif theme == "dark":
            page.theme_mode = ft.ThemeMode.DARK
        else:
            page.theme_mode = ft.ThemeMode.LIGHT

        page.padding = 0
        page.spacing = 0

        # Set window size
        page.window.width = 1400
        page.window.height = 800
        page.window.min_width = 1000
        page.window.min_height = 600

        # Setup cleanup on close
        page.on_close = self._on_app_close

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Check LLM status in background
        self._check_llm_status()

        # Build UI
        page.add(self._build_ui())
        page.update()

        # Load patients
        self._load_patients()

        # Perform startup backup
        self._startup_backup()

        # Start periodic backup timer
        self._start_backup_timer()

    def _build_ui(self) -> ft.Control:
        """Build the main UI layout."""

        # Initialize panels
        self.patient_panel = PatientPanel(
            on_patient_selected=self._on_patient_selected,
            on_search=self._on_patient_search,
            on_new_patient=self._on_new_patient,
            on_patient_updated=self._on_patient_updated,
            db=self.db,
            rag=self.rag
        )

        self.central_panel = CentralPanel(
            on_generate_rx=self._on_generate_prescription,
            on_save_visit=self._on_save_visit,
            on_print_pdf=self._on_print_pdf,
            llm=self.llm,
            db=self.db
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
            color=ft.Colors.ON_SURFACE_VARIANT
        )

        # Theme toggle button (dynamic icon based on current theme)
        # Determine initial icon
        if self.page.theme_mode == ft.ThemeMode.SYSTEM:
            initial_icon = ft.Icons.BRIGHTNESS_AUTO
        elif self.page.theme_mode == ft.ThemeMode.DARK:
            initial_icon = ft.Icons.LIGHT_MODE
        else:
            initial_icon = ft.Icons.DARK_MODE

        self.theme_toggle_button = ft.IconButton(
            icon=initial_icon,
            tooltip="Toggle Theme",
            on_click=self._on_theme_toggle
        )

        # Header
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.LOCAL_HOSPITAL, color=ft.Colors.PRIMARY, size=28),
                        ft.Text("DocAssist EMR", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                    ], spacing=10),
                    ft.Row([
                        self.status_bar,
                        self.theme_toggle_button,
                        ft.IconButton(
                            icon=ft.Icons.TEXT_SNIPPET,
                            tooltip="Quick Phrases",
                            on_click=self._on_phrases_click
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS,
                            tooltip="Settings (Ctrl+,)",
                            on_click=self._on_settings_click
                        ),
                        ft.IconButton(
                            icon=ft.Icons.HELP_OUTLINE,
                            tooltip="Help (F1)",
                            on_click=self._show_shortcuts_help
                        ),
                    ], spacing=5),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            bgcolor=ft.Colors.SURFACE,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE)),
        )

        # Main content with 3 panels
        main_content = ft.Row(
            [
                # Left panel - Patients (fixed width)
                ft.Container(
                    content=self.patient_panel.build(),
                    width=280,
                    bgcolor=ft.Colors.SURFACE_VARIANT,
                    border=ft.border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE)),
                ),
                # Center panel - Main content (expandable)
                ft.Container(
                    content=self.central_panel.build(),
                    expand=True,
                    bgcolor=ft.Colors.BACKGROUND,
                ),
                # Right panel - AI Agent (fixed width)
                ft.Container(
                    content=self.agent_panel.build(),
                    width=350,
                    bgcolor=ft.Colors.SECONDARY_CONTAINER,
                    border=ft.border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE)),
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
            # Add backup time info if available
            backup_info = self._get_backup_status_text()
            if backup_info:
                message = f"{message} | {backup_info}"

            self.status_bar.value = message
            self.status_bar.color = ft.Colors.ERROR if error else ft.Colors.ON_SURFACE_VARIANT
            self.page.update()

    def _get_backup_status_text(self) -> str:
        """Get backup status text for status bar."""
        if self.last_backup_time:
            delta = datetime.now() - self.last_backup_time
            minutes = int(delta.total_seconds() / 60)

            if minutes < 1:
                return "Backup: just now"
            elif minutes < 60:
                return f"Backup: {minutes}m ago"
            else:
                hours = minutes // 60
                return f"Backup: {hours}h ago"
        return "Backup: none"

    def _load_initial_templates(self):
        """Load initial templates from JSON file if not already loaded."""
        try:
            # Get templates file path
            templates_file = Path(__file__).parent.parent / "data" / "initial_templates.json"

            if templates_file.exists():
                with open(templates_file, 'r') as f:
                    templates_data = json.load(f)

                # Load templates into database
                self.db.load_initial_templates(templates_data)
        except Exception as e:
            print(f"Warning: Could not load initial templates: {e}")

    def _load_patients(self):
        """Load all patients into the list."""
        if self.patient_panel:
            self.patient_panel.load_all_patients()

    def _on_patient_selected(self, patient: Patient):
        """Handle patient selection."""
        self.current_patient = patient
        self.central_panel.set_patient(patient)
        self.agent_panel.set_patient(patient)

        # Load visits for this patient
        visits = self.db.get_patient_visits(patient.id)
        self.central_panel.set_visits(visits)

        # Log patient access for recent patients tracking
        self.db.log_patient_access(patient.id)

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

    def _on_patient_updated(self):
        """Handle patient update or deletion - reload patient list."""
        self._load_patients()
        # If current patient was deleted, clear selection
        if self.current_patient:
            patient = self.db.get_patient(self.current_patient.id)
            if not patient:
                self.current_patient = None
                self._update_status("Patient deleted")
        # Re-index for RAG if needed
        if self.current_patient:
            self._index_patient_for_rag(self.current_patient.id)

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

        # Get settings
        settings = self.settings_service.settings

        filepath = self.pdf.generate_prescription_pdf(
            patient=self.current_patient,
            prescription=prescription,
            chief_complaint=chief_complaint,
            doctor_name=settings.doctor.name,
            doctor_qualifications=settings.doctor.qualifications,
            doctor_registration=settings.doctor.registration_number,
            clinic_name=settings.clinic.name,
            clinic_address=settings.clinic.address,
            clinic_phone=settings.clinic.phone,
            clinic_email=settings.clinic.email
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

    def _on_theme_toggle(self, e):
        """Cycle through light -> dark -> system themes."""
        # Cycle through theme modes
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            new_theme = "dark"
            self.theme_toggle_button.icon = ft.Icons.LIGHT_MODE
        elif self.page.theme_mode == ft.ThemeMode.DARK:
            self.page.theme_mode = ft.ThemeMode.SYSTEM
            new_theme = "system"
            self.theme_toggle_button.icon = ft.Icons.BRIGHTNESS_AUTO
        else:  # SYSTEM
            self.page.theme_mode = ft.ThemeMode.LIGHT
            new_theme = "light"
            self.theme_toggle_button.icon = ft.Icons.DARK_MODE

        # Save to settings
        self.settings_service.update_preferences(theme=new_theme)

        # Update the page
        self.page.update()
        self._update_status(f"Theme changed to {new_theme}")

    def _on_settings_click(self, e):
        """Handle settings click."""
        # Close any existing dialog
        if self.current_dialog:
            self._close_dialog(self.current_dialog)

        # Settings callback
        def on_save_settings(new_settings):
            # Save settings
            self.settings_service.save(new_settings)

            # Update backup interval
            self.backup_interval_hours = new_settings.preferences.backup_frequency_hours

            # Apply theme immediately if changed
            old_theme = self.settings_service.settings.preferences.theme
            new_theme = new_settings.preferences.theme
            if old_theme != new_theme:
                if new_theme == "system":
                    self.page.theme_mode = ft.ThemeMode.SYSTEM
                    self.theme_toggle_button.icon = ft.Icons.BRIGHTNESS_AUTO
                elif new_theme == "dark":
                    self.page.theme_mode = ft.ThemeMode.DARK
                    self.theme_toggle_button.icon = ft.Icons.LIGHT_MODE
                else:
                    self.page.theme_mode = ft.ThemeMode.LIGHT
                    self.theme_toggle_button.icon = ft.Icons.DARK_MODE
                self.page.update()

            self._update_status("Settings saved successfully")

            # Close current dialog and reopen to show backup tab
            time.sleep(0.3)
            self._close_current_dialog()
            self._on_settings_click(None)

        # Create settings dialog
        settings_dialog = SettingsDialog(
            page=self.page,
            current_settings=self.settings_service.settings,
            on_save=on_save_settings,
            backup_service=self.backup,
            last_backup_time=self.last_backup_time,
            on_backup=self._manual_backup,
            on_restore=self._confirm_restore,
            export_service=self.export,
            current_patient_id=self.current_patient.id if self.current_patient else None
        )

        model_info = self.llm.get_model_info()

        # Get backup info
        backups = self.backup.list_backups()
        backup_status_text = self._get_backup_status_text()

        # Create backup list items
        backup_list_items = []
        for backup in backups[:10]:  # Show last 10
            created_at = backup.get("created_at", "Unknown")
            try:
                dt = datetime.fromisoformat(created_at)
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                date_str = created_at[:16] if len(created_at) > 16 else created_at

            size_mb = backup.get("size_bytes", 0) / (1024 * 1024)
            patient_count = backup.get("patient_count", "?")

            backup_list_items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(date_str, size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{patient_count} patients | {size_mb:.1f} MB", size=11, color=ft.Colors.GREY_600),
                        ], spacing=2, tight=True),
                        ft.IconButton(
                            icon=ft.Icons.RESTORE,
                            tooltip="Restore this backup",
                            on_click=lambda e, b=backup: self._confirm_restore(b)
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=5,
                    border=ft.border.all(1, ft.Colors.OUTLINE),
                    border_radius=5,
                )
            )

        # Model & Backup tab
        model_backup_tab = ft.Container(
            content=ft.Column([
                # LLM Settings
                ft.Text("AI Model", weight=ft.FontWeight.BOLD, size=16),
                ft.Text(f"Model: {model_info['model']}", size=14),
                ft.Text(f"System RAM: {model_info['ram_gb']:.1f} GB", size=14),
                ft.Text(f"Ollama Status: {'Connected' if model_info['ollama_available'] else 'Not Running'}", size=14),

                ft.Divider(),

                # Backup Settings
                ft.Text("Backups", weight=ft.FontWeight.BOLD, size=16),
                ft.Text(backup_status_text, size=14),
                ft.ElevatedButton(
                    "Backup Now",
                    icon=ft.Icons.BACKUP,
                    on_click=lambda e: self._manual_backup()
                ),

                ft.Text("Recent Backups:", size=14, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column(
                        backup_list_items if backup_list_items else [
                            ft.Text("No backups found", size=12, color=ft.Colors.GREY_600)
                        ],
                        spacing=5,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    height=200,
                ),
            ], tight=True, spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=20,
        )

        # Create tabs
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="Doctor & Clinic",
                    icon=ft.Icons.SETTINGS,
                    content=settings_dialog.dialog.content.content,  # Use settings dialog content
                ),
                ft.Tab(
                    text="Model & Backup",
                    icon=ft.Icons.BACKUP,
                    content=model_backup_tab,
                ),
            ],
            expand=True,
        )

        dialog = ft.AlertDialog(
            title=ft.Text("Settings"),
            content=ft.Container(
                content=tabs,
                width=600,
                height=500,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog)),
            ],
        )
        self.current_dialog = dialog
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _on_phrases_click(self, e):
        """Handle quick phrases click."""
        def on_phrases_changed():
            """Callback when phrases are added/edited/deleted."""
            # Reload phrase cache in text fields
            if self.central_panel and hasattr(self.central_panel.complaint_field, 'reload_cache'):
                self.central_panel.complaint_field.reload_cache()
            if self.central_panel and hasattr(self.central_panel.notes_field, 'reload_cache'):
                self.central_panel.notes_field.reload_cache()

        phrase_manager = PhraseManager(self.db, on_phrases_changed=on_phrases_changed)
        phrase_manager.show(self.page)

    def _close_dialog(self, dialog):
        """Close a dialog."""
        dialog.open = False
        if dialog == self.current_dialog:
            self.current_dialog = None
        self.page.update()

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard event handlers."""
        def on_keyboard(e: ft.KeyboardEvent):
            # Handle Escape key
            if e.key == "Escape":
                self._close_current_dialog()
                return

            # Handle F1 key
            if e.key == "F1":
                e.page.run_thread_safe(self._show_shortcuts_help)
                return

            # Handle Ctrl key combinations
            if e.ctrl:
                if e.key == "Tab":
                    self._shortcut_quick_switch()
                elif e.key == "n" or e.key == "N":
                    self._shortcut_new_patient()
                elif e.key == "s" or e.key == "S":
                    self._shortcut_save()
                elif e.key == "p" or e.key == "P":
                    self._shortcut_print()
                elif e.key == "f" or e.key == "F":
                    self._shortcut_focus_search()
                elif e.key == "g" or e.key == "G":
                    self._shortcut_generate_rx()
                elif e.key == "b" or e.key == "B":
                    self._shortcut_backup_now()
                elif e.key == ",":
                    e.page.run_thread_safe(self._on_settings_click, None)
                elif e.key == "1":
                    self._shortcut_focus_patient_panel()
                elif e.key == "2":
                    self._shortcut_focus_central_panel()
                elif e.key == "3":
                    self._shortcut_focus_agent_panel()
                elif e.key == "l" or e.key == "L":
                    self._shortcut_clear_chat()
                # Ctrl+Enter is handled by the text field in agent panel

        self.page.on_keyboard_event = on_keyboard

    def _close_current_dialog(self):
        """Close the currently open dialog."""
        if self.current_dialog:
            self.current_dialog.open = False
            self.current_dialog = None
            if self.page:
                self.page.update()

    def _shortcut_new_patient(self):
        """Handle Ctrl+N - New Patient."""
        if self.patient_panel and self.page:
            # Create a dummy event with page
            class DummyEvent:
                def __init__(self, page):
                    self.page = page

            self.page.run_thread_safe(
                self.patient_panel._show_new_patient_dialog,
                DummyEvent(self.page)
            )

    def _shortcut_save(self):
        """Handle Ctrl+S - Save current."""
        if self.central_panel and self.page:
            # Only save if there's a prescription to save
            if self.current_patient and self.central_panel.current_prescription:
                class DummyEvent:
                    def __init__(self, page):
                        self.page = page

                self.page.run_thread_safe(
                    self.central_panel._on_save_click,
                    DummyEvent(self.page)
                )
            else:
                self._update_status("Nothing to save", error=True)

    def _shortcut_print(self):
        """Handle Ctrl+P - Print PDF."""
        if self.central_panel and self.page:
            if self.current_patient and self.central_panel.current_prescription:
                class DummyEvent:
                    def __init__(self, page):
                        self.page = page

                self.page.run_thread_safe(
                    self.central_panel._on_print_click,
                    DummyEvent(self.page)
                )
            else:
                self._update_status("No prescription to print", error=True)

    def _shortcut_focus_search(self):
        """Handle Ctrl+F - Focus patient search."""
        if self.patient_panel and self.patient_panel.search_field and self.page:
            self.page.run_thread_safe(lambda: self.patient_panel.search_field.focus())

    def _shortcut_generate_rx(self):
        """Handle Ctrl+G - Generate prescription."""
        if self.central_panel and self.page:
            if self.current_patient:
                class DummyEvent:
                    def __init__(self, page):
                        self.page = page

                self.page.run_thread_safe(
                    self.central_panel._on_generate_click,
                    DummyEvent(self.page)
                )
            else:
                self._update_status("Please select a patient first", error=True)

    def _shortcut_focus_patient_panel(self):
        """Handle Ctrl+1 - Focus patient panel."""
        if self.patient_panel and self.patient_panel.search_field and self.page:
            self.page.run_thread_safe(lambda: self.patient_panel.search_field.focus())

    def _shortcut_focus_central_panel(self):
        """Handle Ctrl+2 - Focus central panel."""
        if self.central_panel and self.central_panel.notes_field and self.page:
            self.page.run_thread_safe(lambda: self.central_panel.notes_field.focus())

    def _shortcut_focus_agent_panel(self):
        """Handle Ctrl+3 - Focus AI panel."""
        if self.agent_panel and self.agent_panel.query_field and self.page:
            self.page.run_thread_safe(lambda: self.agent_panel.query_field.focus())

    def _shortcut_clear_chat(self):
        """Handle Ctrl+L - Clear chat."""
        if self.agent_panel and self.page:
            self.page.run_thread_safe(self.agent_panel.clear_chat)

    def _shortcut_backup_now(self):
        """Handle Ctrl+B - Backup now."""
        if self.page:
            self.page.run_thread_safe(self._manual_backup)

    def _shortcut_quick_switch(self):
        """Handle Ctrl+Tab - Quick switch between recent patients."""
        if not self.page:
            return

        # Get last 5 recent patients
        recent_data = self.db.get_recent_patients(limit=5)
        if not recent_data:
            self._update_status("No recent patients", error=True)
            return

        recent_patients = [Patient(**data) for data in recent_data]

        def close_dialog(e):
            self._close_dialog(quick_switch_dialog)

        def select_patient(patient: Patient):
            self._close_dialog(quick_switch_dialog)
            self._on_patient_selected(patient)

        # Build patient list
        patient_tiles = []
        for i, patient in enumerate(recent_patients):
            is_current = self.current_patient and patient.id == self.current_patient.id

            subtitle_parts = []
            if patient.age:
                subtitle_parts.append(f"{patient.age}y")
            if patient.gender:
                subtitle_parts.append(patient.gender)
            if patient.uhid:
                subtitle_parts.append(patient.uhid)
            subtitle = " | ".join(subtitle_parts)

            tile = ft.Container(
                content=ft.Row([
                    ft.Icon(
                        ft.Icons.ARROW_RIGHT if is_current else ft.Icons.PERSON,
                        size=20,
                        color=ft.Colors.BLUE_700 if is_current else ft.Colors.GREY_600
                    ),
                    ft.Column([
                        ft.Text(
                            patient.name,
                            size=14,
                            weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL,
                            color=ft.Colors.BLUE_700 if is_current else ft.Colors.BLACK,
                        ),
                        ft.Text(subtitle, size=11, color=ft.Colors.GREY_600),
                    ], spacing=2, expand=True),
                ], spacing=10),
                padding=10,
                bgcolor=ft.Colors.BLUE_50 if is_current else ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.BLUE_700 if is_current else ft.Colors.GREY_300),
                border_radius=8,
                on_click=lambda e, p=patient: select_patient(p),
                ink=True,
            )
            patient_tiles.append(tile)

        quick_switch_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.SWAP_HORIZ, color=ft.Colors.BLUE_700),
                ft.Text("Quick Switch", weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column(patient_tiles, spacing=5, tight=True),
                width=400,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
            ],
        )

        self.current_dialog = quick_switch_dialog
        self.page.overlay.append(quick_switch_dialog)
        quick_switch_dialog.open = True
        self.page.update()

    def _show_shortcuts_help(self, e=None):
        """Show keyboard shortcuts help dialog."""
        # Close any existing dialog
        if self.current_dialog:
            self._close_dialog(self.current_dialog)

        def close_dialog(e):
            self._close_dialog(dialog)

        # Create shortcuts content
        shortcuts_content = ft.Column([
            # General section
            ft.Text("GENERAL", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.PRIMARY),
            ft.Container(height=5),
            self._shortcut_row("Ctrl+N", "New Patient"),
            self._shortcut_row("Ctrl+S", "Save Visit"),
            self._shortcut_row("Ctrl+P", "Print PDF"),
            self._shortcut_row("Ctrl+F", "Search Patients"),
            self._shortcut_row("Ctrl+G", "Generate Rx"),
            self._shortcut_row("Ctrl+B", "Backup Now"),
            self._shortcut_row("Ctrl+,", "Settings"),
            self._shortcut_row("F1", "This Help"),
            self._shortcut_row("Esc", "Close/Cancel"),

            ft.Container(height=15),

            # Navigation section
            ft.Text("NAVIGATION", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.PRIMARY),
            ft.Container(height=5),
            self._shortcut_row("Ctrl+Tab", "Quick Switch Patients"),
            self._shortcut_row("Ctrl+1", "Focus Patients Panel"),
            self._shortcut_row("Ctrl+2", "Focus Rx Panel"),
            self._shortcut_row("Ctrl+3", "Focus AI Panel"),
            self._shortcut_row("Tab", "Next Field"),
            self._shortcut_row("Shift+Tab", "Previous Field"),

            ft.Container(height=15),

            # AI Assistant section
            ft.Text("AI ASSISTANT", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.PRIMARY),
            ft.Container(height=5),
            self._shortcut_row("Enter", "Send Message (in AI chat)"),
            self._shortcut_row("Ctrl+L", "Clear Chat"),
        ], spacing=3, scroll=ft.ScrollMode.AUTO, tight=True)

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.KEYBOARD, color=ft.Colors.PRIMARY),
                ft.Text("Keyboard Shortcuts", weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Container(
                content=shortcuts_content,
                width=500,
                height=450,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
            ],
        )

        self.current_dialog = dialog
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _shortcut_row(self, key: str, description: str) -> ft.Control:
        """Create a row for a keyboard shortcut."""
        return ft.Row([
            ft.Container(
                content=ft.Text(
                    key,
                    size=12,
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.ON_PRIMARY_CONTAINER,
                ),
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=4,
                width=100,
            ),
            ft.Text(description, size=13),
        ], spacing=15)

    # ============== BACKUP METHODS ==============

    def _startup_backup(self):
        """Perform backup on app startup in background."""
        def do_backup():
            # Check last backup time first
            last_backup = self.backup.get_last_backup_time()
            if last_backup:
                self.last_backup_time = last_backup
                # Only backup if last backup was > 1 hour ago
                delta = datetime.now() - last_backup
                if delta.total_seconds() < 3600:
                    print(f"Skipping startup backup (last backup was {delta.total_seconds()/60:.0f} minutes ago)")
                    if self.page:
                        self.page.run_thread_safe(lambda: self._update_status("Ready"))
                    return

            print("Performing startup backup...")
            if self.page:
                self.page.run_thread_safe(lambda: self._update_status("Creating backup..."))

            if self.backup.auto_backup():
                self.last_backup_time = datetime.now()
                print("Startup backup completed")
                if self.page:
                    self.page.run_thread_safe(lambda: self._update_status("Ready"))
            else:
                print("Startup backup failed")

        threading.Thread(target=do_backup, daemon=True).start()

    def _on_app_close(self, e):
        """Handle app close event - perform final backup."""
        print("App closing, performing final backup...")
        self.backup_timer_running = False  # Stop the timer

        # Perform final backup (blocking since app is closing)
        try:
            self.backup.auto_backup()
            print("Final backup completed")
        except Exception as ex:
            print(f"Final backup failed: {ex}")

    def _start_backup_timer(self):
        """Start periodic backup timer (every N hours)."""
        def backup_timer():
            self.backup_timer_running = True
            interval_seconds = self.backup_interval_hours * 3600

            while self.backup_timer_running:
                # Sleep in small increments to allow quick exit
                for _ in range(int(interval_seconds)):
                    if not self.backup_timer_running:
                        return
                    time.sleep(1)

                # Perform periodic backup
                print(f"Performing periodic backup ({self.backup_interval_hours}h timer)...")
                if self.page:
                    self.page.run_thread_safe(lambda: self._update_status("Auto-backup in progress..."))

                if self.backup.auto_backup():
                    self.last_backup_time = datetime.now()
                    print("Periodic backup completed")
                    if self.page:
                        self.page.run_thread_safe(lambda: self._update_status("Ready"))

        threading.Thread(target=backup_timer, daemon=True).start()

    def _manual_backup(self):
        """Handle manual backup button click."""
        def do_backup():
            if self.page:
                self.page.run_thread_safe(lambda: self._update_status("Creating backup..."))

            if self.backup.auto_backup():
                self.last_backup_time = datetime.now()
                if self.page:
                    self.page.run_thread_safe(lambda: self._update_status("Backup completed"))
                    # Refresh settings dialog to show new backup
                    time.sleep(0.5)
                    self.page.run_thread_safe(lambda: self._close_current_dialog())
                    self.page.run_thread_safe(lambda: self._on_settings_click(None))
            else:
                if self.page:
                    self.page.run_thread_safe(lambda: self._update_status("Backup failed", error=True))

        threading.Thread(target=do_backup, daemon=True).start()

    def _confirm_restore(self, backup_info: dict):
        """Show confirmation dialog before restoring backup."""
        created_at = backup_info.get("created_at", "Unknown")
        try:
            dt = datetime.fromisoformat(created_at)
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            date_str = created_at

        patient_count = backup_info.get("patient_count", "?")
        visit_count = backup_info.get("visit_count", "?")

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Restore Backup?", weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Text("WARNING: This will replace all current data!",
                       color=ft.Colors.ERROR, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"Backup Date: {date_str}", size=14),
                ft.Text(f"Patients: {patient_count}", size=14),
                ft.Text(f"Visits: {visit_count}", size=14),
                ft.Divider(),
                ft.Text("Current data will be backed up before restore.", size=12, italic=True),
                ft.Text("Are you sure you want to continue?", size=14, weight=ft.FontWeight.BOLD),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(confirm_dialog)),
                ft.ElevatedButton(
                    "Restore",
                    bgcolor=ft.Colors.ERROR,
                    color=ft.Colors.ON_ERROR,
                    on_click=lambda e: self._do_restore(confirm_dialog, backup_info)
                ),
            ],
        )

        # Close settings dialog and show confirmation
        self._close_current_dialog()
        self.current_dialog = confirm_dialog
        self.page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        self.page.update()

    def _do_restore(self, dialog, backup_info: dict):
        """Perform the actual restore operation."""
        self._close_dialog(dialog)

        def do_restore():
            if self.page:
                self.page.run_thread_safe(lambda: self._update_status("Restoring backup..."))

            backup_path = backup_info.get("path")
            if self.backup.restore_backup(backup_path):
                if self.page:
                    self.page.run_thread_safe(lambda: self._update_status("Restore completed - please restart app", error=False))
                    # Show success message
                    self.page.run_thread_safe(lambda: self._show_restore_success())
            else:
                if self.page:
                    self.page.run_thread_safe(lambda: self._update_status("Restore failed", error=True))

        threading.Thread(target=do_restore, daemon=True).start()

    def _show_restore_success(self):
        """Show restore success message."""
        success_dialog = ft.AlertDialog(
            title=ft.Text("Restore Successful", color=ft.Colors.GREEN_700),
            content=ft.Column([
                ft.Text("Backup has been restored successfully.", size=14),
                ft.Text("Please restart the application to use the restored data.", size=14, weight=ft.FontWeight.BOLD),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("OK", on_click=lambda e: self._close_dialog(success_dialog)),
            ],
        )
        self.current_dialog = success_dialog
        self.page.overlay.append(success_dialog)
        success_dialog.open = True
        self.page.update()

    def _load_initial_templates(self):
        """Load initial prescription templates from JSON file."""
        try:
            import json
            templates_file = Path("src/data/initial_templates.json")
            if templates_file.exists():
                with open(templates_file, 'r') as f:
                    templates_data = json.load(f)
                self.db.load_initial_templates(templates_data)
        except Exception as e:
            print(f"Note: Could not load initial templates: {e}")

    def _load_initial_drugs(self):
        """Load initial drug database from JSON file."""
        try:
            import json
            drugs_file = Path("src/data/initial_drugs.json")
            if drugs_file.exists():
                with open(drugs_file, 'r') as f:
                    drugs_data = json.load(f)
                count = self.db.seed_initial_drugs(drugs_data)
                if count > 0:
                    print(f"Loaded {count} drugs into database")
        except Exception as e:
            print(f"Note: Could not load initial drugs: {e}")


def run_app():
    """Run the DocAssist EMR application."""
    app = DocAssistApp()
    ft.app(target=app.main)
