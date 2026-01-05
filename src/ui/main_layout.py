"""Main Layout - Orchestrates all UI panels and components."""

import flet as ft
from typing import Optional, Callable, Dict, Any
import logging

from .patient_panel import PatientPanel
from .central_panel import CentralPanel
from .agent_panel import AgentPanel
from .ambient.ambient_panel import AmbientPanel, SOAPNote
from .alerts.alert_banner import AlertBanner, Alert
from .timeline.patient_timeline import PatientTimeline
from .growth.growth_dashboard import GrowthDashboard
from .navigation import NavigationTab, TabNavigationBar
from .status_bar import StatusBar
from .components.backup_status import BackupStatusIndicator

from ..models.schemas import Patient, Visit, Prescription

logger = logging.getLogger(__name__)


class MainLayout(ft.UserControl):
    """
    Main layout that orchestrates all panels and components.

    Layout structure:
    - Top: Alert banner (floating, always visible)
    - Header: App title and controls
    - Main content:
      - Left: Patient list panel (fixed width)
      - Center left: Navigation tabs
      - Center: Tabbed content (Prescription/Timeline/Growth)
      - Right: AI Assistant with Ambient Panel
    - Bottom: Status bar
    """

    def __init__(
        self,
        # Service dependencies
        db_service,
        llm_service,
        rag_service,
        pdf_service,
        backup_service,
        settings_service,
        # Optional integration layer
        clinical_flow=None,
        event_bus=None,
        # Callbacks
        on_settings_click: Optional[Callable] = None,
        on_help_click: Optional[Callable] = None,
        on_backup_click: Optional[Callable] = None,
        # Theme
        is_dark: bool = False,
    ):
        """Initialize main layout.

        Args:
            db_service: Database service
            llm_service: LLM service
            rag_service: RAG service
            pdf_service: PDF service
            backup_service: Backup service
            settings_service: Settings service
            clinical_flow: Optional ClinicalFlow orchestrator
            event_bus: Optional EventBus
            on_settings_click: Settings button callback
            on_help_click: Help button callback
            on_backup_click: Backup button callback
            is_dark: Dark mode flag
        """
        super().__init__()

        # Services
        self.db = db_service
        self.llm = llm_service
        self.rag = rag_service
        self.pdf = pdf_service
        self.backup = backup_service
        self.settings = settings_service

        # Integration layer
        self.clinical_flow = clinical_flow
        self.event_bus = event_bus

        # Callbacks
        self.on_settings_click = on_settings_click
        self.on_help_click = on_help_click
        self.on_backup_click = on_backup_click

        # Theme
        self.is_dark = is_dark

        # State
        self.current_patient: Optional[Patient] = None
        self.current_tab = NavigationTab.PRESCRIPTION

        # UI Components (will be initialized in build)
        self.alert_banner: Optional[AlertBanner] = None
        self.patient_panel: Optional[PatientPanel] = None
        self.central_panel: Optional[CentralPanel] = None
        self.agent_panel: Optional[AgentPanel] = None
        self.ambient_panel: Optional[AmbientPanel] = None
        self.timeline: Optional[PatientTimeline] = None
        self.growth_dashboard: Optional[GrowthDashboard] = None
        self.tab_navigation: Optional[TabNavigationBar] = None
        self.status_bar: Optional[StatusBar] = None
        self.backup_status_indicator: Optional[BackupStatusIndicator] = None

        # Content container for tab switching
        self.content_container: Optional[ft.Container] = None

        # Subscribe to events if event bus is available
        if self.event_bus:
            self._setup_event_subscriptions()

    def build(self):
        """Build the main layout."""
        # Initialize all components
        self._init_components()

        # Alert banner (floating at top)
        alert_section = ft.Container(
            content=self.alert_banner.build(),
            padding=ft.padding.only(left=20, right=20, top=10),
        )

        # Header
        header = self._build_header()

        # Main content area
        main_content = ft.Row([
            # Left: Patient panel (fixed width)
            ft.Container(
                content=self.patient_panel.build(),
                width=280,
                bgcolor="#1A2332" if self.is_dark else ft.Colors.GREY_50,
                border=ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_700 if self.is_dark else ft.Colors.GREY_300)),
            ),
            # Center: Tabbed content area with navigation
            ft.Column([
                # Tab navigation
                self.tab_navigation.build(),
                # Content container (switches based on selected tab)
                self.content_container,
            ], spacing=0, expand=True),
            # Right: AI Assistant panel (fixed width)
            ft.Container(
                content=self._build_right_panel(),
                width=380,
                bgcolor="#1A2332" if self.is_dark else ft.Colors.BLUE_50,
                border=ft.border.only(left=ft.BorderSide(1, ft.Colors.GREY_700 if self.is_dark else ft.Colors.GREY_300)),
            ),
        ], spacing=0, expand=True)

        # Status bar
        status_section = self.status_bar.build()

        return ft.Column([
            alert_section,
            header,
            main_content,
            status_section,
        ], spacing=0, expand=True)

    def _init_components(self):
        """Initialize all UI components."""
        # Alert banner
        self.alert_banner = AlertBanner(
            on_alert_dismissed=self._on_alert_dismissed,
            on_override_requested=self._on_override_requested,
            is_dark=self.is_dark,
        )

        # Patient panel
        self.patient_panel = PatientPanel(
            on_patient_selected=self._on_patient_selected,
            on_search=self._on_patient_search,
            on_new_patient=self._on_new_patient,
            db=self.db,
            rag=self.rag,
        )

        # Central panel (Prescription)
        self.central_panel = CentralPanel(
            on_generate_rx=self._on_generate_prescription,
            on_save_visit=self._on_save_visit,
            on_print_pdf=self._on_print_pdf,
            llm=self.llm,
        )

        # Agent panel
        self.agent_panel = AgentPanel(
            on_query=self._on_rag_query,
            llm=self.llm,
            rag=self.rag,
        )

        # Ambient panel
        self.ambient_panel = AmbientPanel(
            on_accept=self._on_ambient_accept,
            on_reject=self._on_ambient_reject,
            is_dark=self.is_dark,
        )

        # Timeline
        self.timeline = PatientTimeline(
            patient_id=None,
            on_visit_click=self._on_timeline_visit_click,
            on_care_gap_action=self._on_care_gap_action,
        )

        # Growth dashboard
        self.growth_dashboard = GrowthDashboard(
            db_service=self.db,
            on_action_click=self._on_growth_action,
        )

        # Tab navigation
        self.tab_navigation = TabNavigationBar(
            on_tab_change=self._on_tab_change,
            initial_tab=NavigationTab.PRESCRIPTION,
            is_dark=self.is_dark,
        )

        # Status bar
        self.status_bar = StatusBar(
            on_sync_click=self._on_sync_click,
            is_dark=self.is_dark,
        )

        # Backup status indicator
        self.backup_status_indicator = BackupStatusIndicator(
            on_click=lambda e: self.on_backup_click(e) if self.on_backup_click else None,
            warning_threshold_hours=24,
        )

        # Content container (starts with prescription panel)
        self.content_container = ft.Container(
            content=self.central_panel.build(),
            expand=True,
            bgcolor=ft.Colors.WHITE if not self.is_dark else "#0F1419",
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
        )

    def _build_header(self) -> ft.Container:
        """Build app header."""
        return ft.Container(
            content=ft.Row([
                # Logo and title
                ft.Row([
                    ft.Icon(ft.Icons.LOCAL_HOSPITAL, color=ft.Colors.BLUE_700, size=28),
                    ft.Text(
                        "DocAssist EMR",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_700,
                    ),
                ], spacing=10),
                # Right controls
                ft.Row([
                    # Backup status indicator
                    self.backup_status_indicator.build() if self.backup_status_indicator else ft.Container(),
                    ft.Container(width=10),  # Spacer
                    ft.IconButton(
                        icon=ft.Icons.SETTINGS,
                        tooltip="Settings",
                        on_click=lambda e: self.on_settings_click(e) if self.on_settings_click else None,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.HELP_OUTLINE,
                        tooltip="Help",
                        on_click=lambda e: self.on_help_click(e) if self.on_help_click else None,
                    ),
                    # Dark mode toggle
                    ft.IconButton(
                        icon=ft.Icons.DARK_MODE if not self.is_dark else ft.Icons.LIGHT_MODE,
                        tooltip="Toggle dark mode",
                        on_click=self._toggle_dark_mode,
                    ),
                ], spacing=5),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            bgcolor="#1A2332" if self.is_dark else ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_700 if self.is_dark else ft.Colors.GREY_300)),
        )

    def _build_right_panel(self) -> ft.Column:
        """Build right panel with AI Assistant and Ambient Panel."""
        return ft.Column([
            # Ambient panel (collapsible)
            ft.Container(
                content=self.ambient_panel.build(),
                visible=False,  # Hidden by default, shown during consultation
            ),
            # Agent panel
            ft.Container(
                content=self.agent_panel.build(),
                expand=True,
            ),
        ], spacing=0, expand=True)

    def _on_tab_change(self, tab: NavigationTab):
        """Handle tab change.

        Args:
            tab: Selected tab
        """
        self.current_tab = tab
        logger.info(f"Tab changed to: {tab.value}")

        # Switch content based on tab
        if tab == NavigationTab.PRESCRIPTION:
            self.content_container.content = self.central_panel.build()
        elif tab == NavigationTab.TIMELINE:
            self.content_container.content = self.timeline.build()
            # Load timeline data for current patient
            if self.current_patient:
                self.timeline.patient_id = self.current_patient.id
                self.timeline.load_data()
        elif tab == NavigationTab.GROWTH:
            self.content_container.content = self.growth_dashboard.build()
        elif tab == NavigationTab.SETTINGS:
            # TODO: Create settings panel
            self.content_container.content = ft.Container(
                content=ft.Text("Settings panel coming soon...", size=18),
                padding=20,
            )

        self.update()

    def _on_patient_selected(self, patient: Patient):
        """Handle patient selection.

        Args:
            patient: Selected patient
        """
        self.current_patient = patient
        logger.info(f"Patient selected: {patient.name} ({patient.uhid})")

        # Update all panels
        self.central_panel.set_patient(patient)
        self.agent_panel.set_patient(patient)

        # Update timeline if on that tab
        if self.current_tab == NavigationTab.TIMELINE:
            self.timeline.patient_id = patient.id
            self.timeline.load_data()

        # Update status bar
        self.status_bar.set_patient(patient.name)

        # Load visits
        visits = self.db.get_patient_visits(patient.id)
        self.central_panel.set_visits(visits)

        # Start consultation timer
        self.status_bar.start_consultation()

        # Publish event if event bus available
        if self.event_bus:
            from ..services.integration.event_bus import EventType
            self.event_bus.publish_sync(
                EventType.CONSULTATION_STARTED,
                {"patient_id": patient.id, "patient_name": patient.name}
            )

        self.update()

    def _on_patient_search(self, query: str):
        """Handle patient search (delegated to patient panel)."""
        pass  # Handled by patient panel

    def _on_new_patient(self, patient_data: dict):
        """Handle new patient creation (delegated to app)."""
        pass  # Will be handled by app.py

    def _on_generate_prescription(self, clinical_notes: str, callback):
        """Handle prescription generation (delegated to app)."""
        pass  # Will be handled by app.py

    def _on_save_visit(self, visit_data: dict):
        """Handle visit save (delegated to app)."""
        pass  # Will be handled by app.py

    def _on_print_pdf(self, prescription: Prescription, chief_complaint: str):
        """Handle PDF generation (delegated to app)."""
        pass  # Will be handled by app.py

    def _on_rag_query(self, question: str, callback):
        """Handle RAG query (delegated to app)."""
        pass  # Will be handled by app.py

    def _on_ambient_accept(self, soap_note: SOAPNote):
        """Handle ambient SOAP note acceptance.

        Args:
            soap_note: Accepted SOAP note
        """
        logger.info("Ambient SOAP note accepted")

        # Populate prescription panel with SOAP data
        if self.central_panel:
            # Map SOAP to prescription fields
            clinical_notes = f"S: {soap_note.subjective}\n\nO: {soap_note.objective}\n\nA: {soap_note.assessment}\n\nP: {soap_note.plan}"
            # TODO: Set clinical notes in central panel
            # self.central_panel.set_clinical_notes(clinical_notes)

        # Switch to prescription tab
        self.tab_navigation.set_selected_tab(NavigationTab.PRESCRIPTION)
        self._on_tab_change(NavigationTab.PRESCRIPTION)

        self.update()

    def _on_ambient_reject(self):
        """Handle ambient SOAP note rejection."""
        logger.info("Ambient SOAP note rejected")

    def _on_timeline_visit_click(self, visit_id: int):
        """Handle timeline visit click.

        Args:
            visit_id: Visit ID
        """
        logger.info(f"Timeline visit clicked: {visit_id}")
        # TODO: Open visit details or switch to prescription tab with visit loaded

    def _on_care_gap_action(self, care_gap: Dict[str, Any]):
        """Handle care gap action.

        Args:
            care_gap: Care gap data
        """
        logger.info(f"Care gap action: {care_gap['title']}")
        # TODO: Handle care gap action (e.g., add investigation, create reminder)

    def _on_growth_action(self, recommendation: Dict[str, Any]):
        """Handle growth recommendation action.

        Args:
            recommendation: Recommendation data
        """
        logger.info(f"Growth action: {recommendation['title']}")
        # TODO: Handle recommendation action

    def _on_alert_dismissed(self, alert: Alert):
        """Handle alert dismissal.

        Args:
            alert: Dismissed alert
        """
        logger.info(f"Alert dismissed: {alert.title}")

    def _on_override_requested(self, alert: Alert):
        """Handle alert override request.

        Args:
            alert: Alert to override
        """
        logger.info(f"Override requested for alert: {alert.title}")
        # TODO: Show override reason dialog

    def _on_sync_click(self):
        """Handle sync status click."""
        logger.info("Sync status clicked")
        # TODO: Show sync details dialog

    def _toggle_dark_mode(self, e):
        """Toggle dark mode."""
        self.is_dark = not self.is_dark
        logger.info(f"Dark mode toggled: {self.is_dark}")
        # TODO: Apply dark mode to all components and rebuild
        # For now, just update the page theme
        if self.page:
            self.page.theme_mode = ft.ThemeMode.DARK if self.is_dark else ft.ThemeMode.LIGHT
            self.page.update()

    def _setup_event_subscriptions(self):
        """Setup event subscriptions for integration layer."""
        from ..services.integration.event_bus import EventType

        # Subscribe to alerts
        self.event_bus.subscribe(
            EventType.ALERT_TRIGGERED,
            self._handle_alert_event,
            priority=100
        )

        self.event_bus.subscribe(
            EventType.DRUG_INTERACTION_DETECTED,
            self._handle_drug_interaction_event,
            priority=100
        )

        self.event_bus.subscribe(
            EventType.RED_FLAG_DETECTED,
            self._handle_red_flag_event,
            priority=100
        )

        logger.info("Event subscriptions set up")

    def _handle_alert_event(self, event):
        """Handle alert event from event bus."""
        data = event.data
        self.alert_banner.show_info(
            title=data.get("title", "Alert"),
            message=data.get("message", "")
        )

    def _handle_drug_interaction_event(self, event):
        """Handle drug interaction event."""
        data = event.data
        self.alert_banner.show_interaction_alert(
            drug1=data.get("drug1", ""),
            drug2=data.get("drug2", ""),
            severity=data.get("severity", "moderate"),
            description=data.get("description", "")
        )

    def _handle_red_flag_event(self, event):
        """Handle red flag event."""
        data = event.data
        self.alert_banner.show_red_flag_alert(
            red_flag_type=data.get("type", ""),
            message=data.get("message", ""),
            action=data.get("action")
        )

    def set_llm_status(self, connected: bool, model_info: Optional[Dict] = None):
        """Update LLM connection status.

        Args:
            connected: Whether LLM is connected
            model_info: Optional model information
        """
        self.status_bar.set_ollama_status(connected)

    def set_backup_status(self, connected: bool):
        """Update backup service status.

        Args:
            connected: Whether backup service is connected
        """
        self.status_bar.set_backup_status(connected)

    def update_backup_status(self, last_backup_time):
        """Update backup status indicator.

        Args:
            last_backup_time: datetime of last backup or None
        """
        if self.backup_status_indicator:
            self.backup_status_indicator.update_status(last_backup_time)

    def show_ambient_panel(self):
        """Show ambient panel (for consultation mode)."""
        # TODO: Make ambient panel visible
        pass

    def hide_ambient_panel(self):
        """Hide ambient panel."""
        # TODO: Hide ambient panel
        pass
