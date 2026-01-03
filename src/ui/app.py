"""Main Flet application with 3-panel layout."""

import flet as ft
from typing import Optional, List
import threading

from ..services.database import DatabaseService
from ..services.phonetic import MultiStrategySearch
from ..services.safety import PrescriptionSafetyChecker
from ..services.context_builder import ContextBuilder
from ..services.app_mode import (
    get_mode_manager,
    get_current_mode,
    get_capabilities,
    can_use_llm,
    can_use_rag,
    AppMode,
)
from ..models.schemas import Patient, Visit, Prescription, PatientSnapshot, SafetyAlert

# Optional imports based on availability
try:
    from ..services.llm import LLMService
except ImportError:
    LLMService = None

try:
    from ..services.rag import RAGService
except ImportError:
    RAGService = None

try:
    from ..services.pdf import PDFService
except ImportError:
    PDFService = None

from .patient_panel import PatientPanel
from .central_panel import CentralPanel
from .agent_panel import AgentPanel


class DocAssistApp:
    """Main application class."""

    def __init__(self):
        # Get app mode
        self.mode_manager = get_mode_manager()
        self.capabilities = get_capabilities()

        # Core services (always available)
        self.db = DatabaseService()
        self.phonetic_search = MultiStrategySearch(self.db)
        self.safety_checker = PrescriptionSafetyChecker()
        self.context_builder = ContextBuilder(self.db)

        # Optional services
        self.pdf = None
        if PDFService:
            try:
                self.pdf = PDFService()
            except Exception as e:
                print(f"PDF service unavailable: {e}")

        # Optional AI services (mode-dependent)
        self.llm = None
        self.rag = None

        if self.capabilities.llm_prescription and LLMService:
            try:
                self.llm = LLMService()
            except Exception as e:
                print(f"LLM service unavailable: {e}")

        if self.capabilities.vector_rag and RAGService:
            try:
                self.rag = RAGService()
            except Exception as e:
                print(f"RAG service unavailable: {e}")

        self.current_patient: Optional[Patient] = None
        self.current_snapshot: Optional[PatientSnapshot] = None
        self.page: Optional[ft.Page] = None

        # UI components (initialized in build)
        self.patient_panel: Optional[PatientPanel] = None
        self.central_panel: Optional[CentralPanel] = None
        self.agent_panel: Optional[AgentPanel] = None
        self.status_bar: Optional[ft.Text] = None
        self.mode_badge: Optional[ft.Container] = None

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
            phonetic_search=self.phonetic_search,
        )

        self.central_panel = CentralPanel(
            on_generate_rx=self._on_generate_prescription,
            on_save_visit=self._on_save_visit,
            on_print_pdf=self._on_print_pdf,
            llm=self.llm,
            safety_checker=self.safety_checker,
            capabilities=self.capabilities,
        )

        self.agent_panel = AgentPanel(
            on_query=self._on_rag_query,
            llm=self.llm,
            rag=self.rag,
            context_builder=self.context_builder,
            capabilities=self.capabilities,
        )

        # Status bar
        self.status_bar = ft.Text(
            "Ready",
            size=12,
            color=ft.Colors.GREY_600
        )

        # Mode badge
        mode_colors = {
            AppMode.LITE: (ft.Colors.GREY_700, "LITE"),
            AppMode.STANDARD: (ft.Colors.BLUE_700, "STD"),
            AppMode.FULL: (ft.Colors.GREEN_700, "FULL"),
        }
        mode_color, mode_text = mode_colors.get(
            self.mode_manager.mode,
            (ft.Colors.GREY_700, "???")
        )

        self.mode_badge = ft.Container(
            content=ft.Text(
                mode_text,
                size=10,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            ),
            bgcolor=mode_color,
            padding=ft.padding.symmetric(horizontal=8, vertical=2),
            border_radius=10,
            tooltip=self.mode_manager._get_mode_display_name(),
        )

        # Header
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.LOCAL_HOSPITAL, color=ft.Colors.BLUE_700, size=28),
                        ft.Text("DocAssist EMR", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                        self.mode_badge,
                    ], spacing=10),
                    ft.Row([
                        self.status_bar,
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
            if self.llm and self.llm.is_available():
                model_info = self.llm.get_model_info()
                self._update_status(
                    f"LLM: {model_info['model']} | RAM: {model_info['ram_available_gb']:.1f}GB"
                )
            elif self.capabilities.llm_prescription:
                self._update_status("Ollama not running - AI features disabled", error=True)
            else:
                self._update_status(f"Mode: {self.mode_manager.mode.value} (AI disabled)")

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

        # Get or compute patient snapshot
        self.current_snapshot = self.db.get_patient_snapshot(patient.id)
        if not self.current_snapshot:
            self.current_snapshot = self.db.compute_patient_snapshot(patient.id)

        self.central_panel.set_patient(patient, self.current_snapshot)
        self.agent_panel.set_patient(patient)

        # Load visits for this patient
        visits = self.db.get_patient_visits(patient.id)
        self.central_panel.set_visits(visits)

        # Index patient documents for RAG in background (if available)
        if self.rag:
            self._index_patient_for_rag(patient.id)

        self._update_status(f"Selected: {patient.name} ({patient.uhid})")

    def _index_patient_for_rag(self, patient_id: int):
        """Index patient documents for RAG in background."""
        if not self.rag:
            return

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
            except Exception as e:
                print(f"RAG indexing error: {e}")

        threading.Thread(target=index, daemon=True).start()

    def _on_patient_search(self, query: str):
        """Handle patient search."""
        if not query.strip():
            self._load_patients()
            return

        # Try FTS search first
        patients = self.db.fts_search_patients(query, limit=20)

        # Try phonetic search if FTS found nothing
        if not patients:
            all_patients = self.db.get_all_patients()
            results = self.phonetic_search.search(
                query,
                [(p.name, p) for p in all_patients],
                threshold=0.6,
                limit=20
            )
            patients = [p for _, _, p in results]

        # If still no results and RAG is available, try semantic search
        if not patients and self.rag and len(query.split()) > 2:
            try:
                results = self.rag.search_patients(query, n_results=10)
                if results:
                    patient_ids = [r[0] for r in results]
                    patients = [
                        self.db.get_patient(pid)
                        for pid in patient_ids
                        if self.db.get_patient(pid)
                    ]
            except Exception:
                pass

        self.patient_panel.set_patients(patients)

    def _on_new_patient(self, patient_data: dict):
        """Handle new patient creation."""
        patient = Patient(**patient_data)
        saved_patient = self.db.add_patient(patient)

        # Index for RAG if available
        if self.rag:
            summary = f"Patient: {saved_patient.name}. UHID: {saved_patient.uhid}"
            if saved_patient.age:
                summary += f". Age: {saved_patient.age}"
            if saved_patient.gender:
                summary += f". Gender: {saved_patient.gender}"
            try:
                self.rag.index_patient_summary(saved_patient.id, summary)
            except Exception:
                pass

        self._load_patients()
        self._on_patient_selected(saved_patient)
        self._update_status(f"Created patient: {saved_patient.name}")

    def _on_generate_prescription(
        self,
        clinical_notes: str,
        callback,
        patient_snapshot: Optional[PatientSnapshot] = None
    ):
        """Handle prescription generation."""
        if not self.llm:
            callback(False, None, [], "LLM not available in current mode.")
            return

        if not self.llm.is_available():
            callback(False, None, [], "Ollama is not running. Please start Ollama first.")
            return

        self._update_status("Generating prescription...")

        # Use current snapshot if not provided
        snapshot = patient_snapshot or self.current_snapshot

        def generate():
            success, prescription, raw = self.llm.generate_prescription(clinical_notes)

            # Run safety checks if prescription generated successfully
            safety_alerts: List[SafetyAlert] = []
            if success and prescription and snapshot:
                safety_alerts = self.safety_checker.validate_prescription(
                    prescription, snapshot
                )

            if self.page:
                self.page.run_thread_safe(
                    lambda: callback(success, prescription, safety_alerts, raw)
                )
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
        if self.rag:
            self._index_patient_for_rag(self.current_patient.id)

        # Update patient snapshot
        self.current_snapshot = self.db.compute_patient_snapshot(self.current_patient.id)

        self._update_status(f"Visit saved for {self.current_patient.name}")
        return True

    def _on_print_pdf(self, prescription: Prescription, chief_complaint: str) -> Optional[str]:
        """Handle PDF generation."""
        if not self.current_patient or not prescription:
            return None

        if not self.pdf:
            self._update_status("PDF generation not available", error=True)
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

        self._update_status("Searching patient records...")

        def query():
            # Try SQL-based context builder first (always available)
            context = self.context_builder.build_context(
                self.current_patient.id, question
            )

            # If we have vector RAG and the query needs semantic search, use it
            if self.rag and self.capabilities.semantic_search:
                try:
                    rag_context = self.rag.query_patient_context(
                        patient_id=self.current_patient.id,
                        query=question,
                        n_results=5
                    )
                    if rag_context:
                        context += "\n\n--- Vector Search Results ---\n" + rag_context
                except Exception as e:
                    print(f"RAG query error: {e}")

            # Generate answer with LLM if available
            if self.llm and self.llm.is_available():
                success, answer = self.llm.query_patient_records(context, question)
            else:
                # Return raw context without LLM interpretation
                success = True
                answer = f"[AI disabled - Raw data]\n\n{context}"

            if self.page:
                self.page.run_thread_safe(lambda: callback(success, answer))
                self.page.run_thread_safe(lambda: self._update_status("Query complete"))

        threading.Thread(target=query, daemon=True).start()

    def _on_settings_click(self, e):
        """Handle settings click."""
        mode_status = self.mode_manager.get_status()

        content_items = [
            ft.Text(f"Mode: {mode_status['mode_display']}", size=14, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text(f"RAM: {mode_status['ram_available_gb']} / {mode_status['ram_total_gb']} GB", size=13),
        ]

        # Add feature status
        content_items.append(ft.Text("Features:", size=13, weight=ft.FontWeight.W_500))
        for feature, enabled in mode_status['features'].items():
            icon = ft.Icons.CHECK_CIRCLE if enabled else ft.Icons.CANCEL
            color = ft.Colors.GREEN_600 if enabled else ft.Colors.GREY_400
            content_items.append(
                ft.Row([
                    ft.Icon(icon, size=16, color=color),
                    ft.Text(feature, size=12),
                ], spacing=5)
            )

        # Add LLM info if available
        if self.llm:
            content_items.append(ft.Divider())
            model_info = self.llm.get_model_info()
            content_items.append(ft.Text(f"LLM Model: {model_info['model']}", size=13))
            content_items.append(ft.Text(
                f"Ollama: {'Connected' if model_info['ollama_available'] else 'Not Running'}",
                size=13,
                color=ft.Colors.GREEN_600 if model_info['ollama_available'] else ft.Colors.RED_600
            ))

        # Add upgrade message if applicable
        upgrade_msg = self.mode_manager.get_upgrade_message()
        if upgrade_msg:
            content_items.append(ft.Divider())
            content_items.append(ft.Text(upgrade_msg, size=11, italic=True))

        dialog = ft.AlertDialog(
            title=ft.Text("Settings & Status"),
            content=ft.Column(content_items, tight=True, spacing=8, scroll=ft.ScrollMode.AUTO),
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
                ft.Text("Search patients by name (phonetic matching)", size=12),
                ft.Text("Example: 'Ram' matches 'Raam', 'Rama'", size=12),
                ft.Divider(),
                ft.Text("Safety Alerts:", weight=ft.FontWeight.BOLD),
                ft.Text("Prescriptions are checked for allergies,", size=12),
                ft.Text("drug interactions, and dose limits.", size=12),
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
