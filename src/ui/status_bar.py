"""Status Bar Component - Sync status, patient info, and consultation timer."""

import flet as ft
from typing import Optional, Callable
from datetime import datetime, timedelta
import threading


class StatusBar(ft.UserControl):
    """
    Status bar component displaying:
    - Sync status indicator (synced/syncing/offline)
    - Current patient name
    - Consultation timer
    - Ambient listening indicator
    - Connection status (Ollama, backup service)
    """

    def __init__(
        self,
        on_sync_click: Optional[Callable] = None,
        is_dark: bool = False,
    ):
        """Initialize status bar.

        Args:
            on_sync_click: Callback when sync status is clicked
            is_dark: Whether dark mode is active
        """
        super().__init__()
        self.on_sync_click = on_sync_click
        self.is_dark = is_dark

        # State
        self.sync_status = "synced"  # "synced", "syncing", "offline"
        self.current_patient_name = None
        self.consultation_started_at = None
        self.is_ambient_listening = False
        self.ollama_connected = False
        self.backup_service_connected = False

        # Timer thread
        self._timer_thread = None
        self._timer_running = False
        self.elapsed_time = timedelta(0)

        # UI components
        self.sync_indicator: Optional[ft.Container] = None
        self.patient_name_text: Optional[ft.Text] = None
        self.timer_text: Optional[ft.Text] = None
        self.ambient_indicator: Optional[ft.Container] = None
        self.connection_status: Optional[ft.Row] = None

    def build(self):
        """Build the status bar UI."""
        # Sync status indicator
        self.sync_indicator = ft.Container(
            content=ft.Row([
                ft.Icon(
                    self._get_sync_icon(),
                    size=16,
                    color=self._get_sync_color(),
                    animate_rotation=ft.animation.Animation(
                        1000, ft.AnimationCurve.LINEAR
                    ) if self.sync_status == "syncing" else None,
                ),
                ft.Text(
                    self._get_sync_text(),
                    size=12,
                    color=self._get_sync_color(),
                    weight=ft.FontWeight.W_500,
                ),
            ], spacing=5),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border_radius=12,
            bgcolor=self._get_sync_bg_color(),
            ink=True,
            on_click=lambda e: self.on_sync_click() if self.on_sync_click else None,
            tooltip="Click to view sync details",
        )

        # Current patient name
        self.patient_name_text = ft.Text(
            self.current_patient_name or "No patient selected",
            size=13,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE if self.is_dark else ft.Colors.GREY_900,
        )

        # Consultation timer
        self.timer_text = ft.Text(
            self._format_elapsed_time(),
            size=12,
            color=ft.Colors.GREY_400 if self.is_dark else ft.Colors.GREY_600,
            visible=self.consultation_started_at is not None,
        )

        # Ambient listening indicator
        self.ambient_indicator = ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.MIC,
                    size=14,
                    color=ft.Colors.RED_400,
                ),
                ft.Text(
                    "Listening...",
                    size=11,
                    color=ft.Colors.RED_400,
                    weight=ft.FontWeight.BOLD,
                ),
            ], spacing=4),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.RED_400),
            border_radius=10,
            visible=self.is_ambient_listening,
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=ft.animation.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        )

        # Connection status icons
        self.connection_status = ft.Row([
            # Ollama status
            ft.Container(
                content=ft.Icon(
                    ft.Icons.PSYCHOLOGY if self.ollama_connected else ft.Icons.PSYCHOLOGY_OUTLINED,
                    size=16,
                    color=ft.Colors.GREEN_400 if self.ollama_connected else ft.Colors.GREY_600,
                ),
                tooltip="Ollama LLM: " + ("Connected" if self.ollama_connected else "Disconnected"),
            ),
            # Backup service status
            ft.Container(
                content=ft.Icon(
                    ft.Icons.CLOUD_DONE if self.backup_service_connected else ft.Icons.CLOUD_OFF,
                    size=16,
                    color=ft.Colors.BLUE_400 if self.backup_service_connected else ft.Colors.GREY_600,
                ),
                tooltip="Backup Service: " + ("Connected" if self.backup_service_connected else "Offline"),
            ),
        ], spacing=8)

        return ft.Container(
            content=ft.Row([
                # Left section - Sync status
                self.sync_indicator,
                ft.VerticalDivider(width=1, color=ft.Colors.GREY_700 if self.is_dark else ft.Colors.GREY_300),
                # Middle section - Patient info and timer
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, size=16, color=ft.Colors.BLUE_400),
                    self.patient_name_text,
                    ft.Container(width=10),
                    ft.Icon(ft.Icons.TIMER, size=14, color=ft.Colors.GREY_500, visible=self.consultation_started_at is not None),
                    self.timer_text,
                ], spacing=5),
                ft.Container(expand=True),
                # Right section - Ambient indicator and connections
                self.ambient_indicator,
                self.connection_status,
            ], spacing=15, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=15, vertical=8),
            bgcolor="#1A2332" if self.is_dark else ft.Colors.GREY_100,
            border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_700 if self.is_dark else ft.Colors.GREY_300)),
        )

    def set_sync_status(self, status: str):
        """Set sync status.

        Args:
            status: "synced", "syncing", or "offline"
        """
        self.sync_status = status

        if self.sync_indicator:
            icon = self.sync_indicator.content.controls[0]
            text = self.sync_indicator.content.controls[1]

            icon.name = self._get_sync_icon()
            icon.color = self._get_sync_color()
            text.value = self._get_sync_text()
            text.color = self._get_sync_color()
            self.sync_indicator.bgcolor = self._get_sync_bg_color()

            # Enable rotation animation for syncing
            if status == "syncing":
                icon.rotate = ft.transform.Rotate(0, alignment=ft.alignment.center)
                icon.animate_rotation = ft.animation.Animation(1000, ft.AnimationCurve.LINEAR)
            else:
                icon.rotate = None
                icon.animate_rotation = None

            self.update()

    def set_patient(self, patient_name: Optional[str]):
        """Set current patient name.

        Args:
            patient_name: Patient name or None
        """
        self.current_patient_name = patient_name

        if self.patient_name_text:
            self.patient_name_text.value = patient_name or "No patient selected"
            self.update()

    def start_consultation(self):
        """Start consultation timer."""
        self.consultation_started_at = datetime.now()
        self.elapsed_time = timedelta(0)

        if self.timer_text:
            self.timer_text.visible = True

        # Start timer thread
        self._timer_running = True
        self._timer_thread = threading.Thread(target=self._update_timer, daemon=True)
        self._timer_thread.start()

        self.update()

    def stop_consultation(self):
        """Stop consultation timer."""
        self._timer_running = False
        self.consultation_started_at = None
        self.elapsed_time = timedelta(0)

        if self.timer_text:
            self.timer_text.visible = False

        self.update()

    def set_ambient_listening(self, is_listening: bool):
        """Set ambient listening status.

        Args:
            is_listening: Whether ambient listening is active
        """
        self.is_ambient_listening = is_listening

        if self.ambient_indicator:
            self.ambient_indicator.visible = is_listening
            self.update()

    def set_ollama_status(self, connected: bool):
        """Set Ollama connection status.

        Args:
            connected: Whether Ollama is connected
        """
        self.ollama_connected = connected

        if self.connection_status:
            ollama_icon = self.connection_status.controls[0].content
            ollama_icon.name = ft.Icons.PSYCHOLOGY if connected else ft.Icons.PSYCHOLOGY_OUTLINED
            ollama_icon.color = ft.Colors.GREEN_400 if connected else ft.Colors.GREY_600
            self.connection_status.controls[0].tooltip = "Ollama LLM: " + ("Connected" if connected else "Disconnected")
            self.update()

    def set_backup_status(self, connected: bool):
        """Set backup service connection status.

        Args:
            connected: Whether backup service is connected
        """
        self.backup_service_connected = connected

        if self.connection_status:
            backup_icon = self.connection_status.controls[1].content
            backup_icon.name = ft.Icons.CLOUD_DONE if connected else ft.Icons.CLOUD_OFF
            backup_icon.color = ft.Colors.BLUE_400 if connected else ft.Colors.GREY_600
            self.connection_status.controls[1].tooltip = "Backup Service: " + ("Connected" if connected else "Offline")
            self.update()

    def _update_timer(self):
        """Background thread to update timer."""
        while self._timer_running and self.consultation_started_at:
            self.elapsed_time = datetime.now() - self.consultation_started_at

            if self.timer_text and self.page:
                self.page.run_task(self._update_timer_ui)

            threading.Event().wait(1)  # Update every second

    def _update_timer_ui(self):
        """Update timer UI (called from main thread)."""
        if self.timer_text:
            self.timer_text.value = self._format_elapsed_time()
            self.timer_text.update()

    def _format_elapsed_time(self) -> str:
        """Format elapsed time for display.

        Returns:
            Formatted time string (e.g., "05:23")
        """
        if not self.consultation_started_at:
            return "00:00"

        total_seconds = int(self.elapsed_time.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _get_sync_icon(self) -> str:
        """Get icon for sync status."""
        return {
            "synced": ft.Icons.CHECK_CIRCLE,
            "syncing": ft.Icons.SYNC,
            "offline": ft.Icons.CLOUD_OFF,
        }.get(self.sync_status, ft.Icons.HELP)

    def _get_sync_text(self) -> str:
        """Get text for sync status."""
        return {
            "synced": "Synced",
            "syncing": "Syncing...",
            "offline": "Offline",
        }.get(self.sync_status, "Unknown")

    def _get_sync_color(self) -> str:
        """Get color for sync status."""
        return {
            "synced": ft.Colors.GREEN_600,
            "syncing": ft.Colors.BLUE_600,
            "offline": ft.Colors.ORANGE_600,
        }.get(self.sync_status, ft.Colors.GREY_600)

    def _get_sync_bg_color(self) -> str:
        """Get background color for sync status."""
        if self.is_dark:
            return {
                "synced": ft.Colors.with_opacity(0.2, ft.Colors.GREEN_600),
                "syncing": ft.Colors.with_opacity(0.2, ft.Colors.BLUE_600),
                "offline": ft.Colors.with_opacity(0.2, ft.Colors.ORANGE_600),
            }.get(self.sync_status, ft.Colors.GREY_800)
        else:
            return {
                "synced": ft.Colors.GREEN_50,
                "syncing": ft.Colors.BLUE_50,
                "offline": ft.Colors.ORANGE_50,
            }.get(self.sync_status, ft.Colors.GREY_200)
