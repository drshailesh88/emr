"""Voice status indicator - shows voice availability and model loading status."""

import flet as ft
from typing import Optional, Callable
import threading

from ...services.voice.whisper_manager import get_whisper_manager


class VoiceStatusIndicator(ft.UserControl):
    """Shows voice input availability and allows troubleshooting."""

    def __init__(
        self,
        on_settings_click: Optional[Callable] = None,
        auto_check: bool = True,
    ):
        """Initialize voice status indicator.

        Args:
            on_settings_click: Callback when user clicks to configure
            auto_check: Automatically check status on build
        """
        super().__init__()
        self.on_settings_click = on_settings_click
        self.auto_check = auto_check
        self.whisper_manager = get_whisper_manager()
        self.status_icon: Optional[ft.Icon] = None
        self.status_text: Optional[ft.Text] = None
        self.progress_bar: Optional[ft.ProgressBar] = None
        self.action_button: Optional[ft.TextButton] = None
        self.current_status: str = "unknown"

    def build(self):
        """Build the status indicator UI."""
        self.status_icon = ft.Icon(
            ft.Icons.MIC_OFF,
            color=ft.Colors.GREY_400,
            size=16,
        )

        self.status_text = ft.Text(
            "Checking voice...",
            size=11,
            color=ft.Colors.GREY_600,
        )

        self.progress_bar = ft.ProgressBar(
            width=100,
            height=2,
            visible=False,
        )

        self.action_button = ft.TextButton(
            "Setup",
            visible=False,
            on_click=self._on_action_click,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
            ),
        )

        container = ft.Container(
            content=ft.Row(
                [
                    self.status_icon,
                    ft.Column(
                        [
                            self.status_text,
                            self.progress_bar,
                        ],
                        spacing=2,
                    ),
                    self.action_button,
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=8,
            border_radius=8,
            bgcolor=ft.Colors.GREY_100,
        )

        # Check status on build
        if self.auto_check:
            threading.Thread(target=self._check_status, daemon=True).start()

        return container

    def _check_status(self):
        """Check voice input status in background."""
        # Check if Whisper is available
        if not self.whisper_manager.is_available():
            self._update_status(
                "unavailable",
                "Voice Not Available",
                ft.Icons.MIC_OFF,
                ft.Colors.RED_700,
                show_action=True,
            )
            return

        # Check if model is downloaded
        model_info = self.whisper_manager.get_model_info()

        if not model_info.get("downloaded"):
            self._update_status(
                "download_needed",
                f"Download {model_info.get('size_mb', 0)}MB model",
                ft.Icons.CLOUD_DOWNLOAD,
                ft.Colors.ORANGE_700,
                show_action=True,
            )
            return

        # Try to load model
        self._update_status(
            "loading",
            "Loading voice model...",
            ft.Icons.HOURGLASS_EMPTY,
            ft.Colors.BLUE_700,
            show_progress=True,
        )

        success, model, error = self.whisper_manager.load_model(
            on_progress=self._on_load_progress
        )

        if success:
            self._update_status(
                "ready",
                "Voice Ready",
                ft.Icons.MIC,
                ft.Colors.GREEN_700,
            )
        else:
            self._update_status(
                "error",
                f"Voice Error: {error[:30]}...",
                ft.Icons.ERROR,
                ft.Colors.RED_700,
                show_action=True,
            )

    def _update_status(
        self,
        status: str,
        message: str,
        icon: str,
        color: str,
        show_action: bool = False,
        show_progress: bool = False,
    ):
        """Update the status display."""
        self.current_status = status

        if self.status_icon and self.status_icon.page:
            self.status_icon.name = icon
            self.status_icon.color = color
            self.status_text.value = message
            self.status_text.color = color
            self.action_button.visible = show_action
            self.progress_bar.visible = show_progress

            if show_action:
                if status == "unavailable":
                    self.action_button.text = "Install"
                elif status == "download_needed":
                    self.action_button.text = "Download"
                elif status == "error":
                    self.action_button.text = "Retry"

            self.status_icon.page.update()

    def _on_load_progress(self, message: str, percent: float):
        """Handle model loading progress."""
        if self.progress_bar and self.progress_bar.page:
            self.progress_bar.value = percent / 100.0
            self.status_text.value = message
            self.progress_bar.page.update()

    def _on_action_click(self, e):
        """Handle action button click."""
        if self.current_status == "unavailable":
            self._show_installation_dialog(e.page)
        elif self.current_status == "download_needed":
            self._download_model(e.page)
        elif self.current_status == "error":
            # Retry loading
            threading.Thread(target=self._check_status, daemon=True).start()
        elif self.on_settings_click:
            self.on_settings_click()

    def _show_installation_dialog(self, page: ft.Page):
        """Show installation instructions."""
        instructions = self.whisper_manager.get_installation_instructions()

        dialog = ft.AlertDialog(
            title=ft.Text("Voice Input Setup"),
            content=ft.Column(
                [
                    ft.Text(
                        "Voice input requires additional packages:",
                        size=13,
                    ),
                    ft.Container(
                        content=ft.Text(
                            instructions,
                            size=12,
                            font_family="monospace",
                        ),
                        bgcolor=ft.Colors.GREY_100,
                        padding=10,
                        border_radius=5,
                    ),
                    ft.Text(
                        "After installation, restart the application.",
                        size=12,
                        italic=True,
                        color=ft.Colors.GREY_600,
                    ),
                ],
                spacing=10,
                tight=True,
            ),
            actions=[
                ft.TextButton("Copy Command", on_click=lambda e: self._copy_command(page)),
                ft.TextButton("Close", on_click=lambda e: page.close(dialog)),
            ],
        )

        page.open(dialog)

    def _copy_command(self, page: ft.Page):
        """Copy installation command to clipboard."""
        page.set_clipboard("pip install faster-whisper sounddevice numpy")
        page.open(
            ft.SnackBar(
                content=ft.Text("Installation command copied to clipboard"),
                bgcolor=ft.Colors.GREEN_700,
            )
        )

    def _download_model(self, page: ft.Page):
        """Download the model with progress."""
        self._update_status(
            "downloading",
            "Downloading model...",
            ft.Icons.CLOUD_DOWNLOAD,
            ft.Colors.BLUE_700,
            show_progress=True,
        )

        def on_progress(message: str, percent: float):
            if self.progress_bar and self.progress_bar.page:
                self.progress_bar.value = percent / 100.0
                self.status_text.value = f"{message} ({int(percent)}%)"
                self.progress_bar.page.update()

        def on_complete(success: bool, message: str):
            if success:
                self._update_status(
                    "ready",
                    "Voice Ready",
                    ft.Icons.MIC,
                    ft.Colors.GREEN_700,
                )
                if page:
                    page.open(
                        ft.SnackBar(
                            content=ft.Text("Voice model ready!"),
                            bgcolor=ft.Colors.GREEN_700,
                        )
                    )
            else:
                self._update_status(
                    "error",
                    f"Download failed",
                    ft.Icons.ERROR,
                    ft.Colors.RED_700,
                    show_action=True,
                )
                if page:
                    page.open(
                        ft.SnackBar(
                            content=ft.Text(f"Download failed: {message}"),
                            bgcolor=ft.Colors.RED_700,
                        )
                    )

        self.whisper_manager.preload_model_async(
            on_complete=on_complete,
            on_progress=on_progress,
        )

    def refresh_status(self):
        """Refresh the status check."""
        threading.Thread(target=self._check_status, daemon=True).start()

    def get_status(self) -> str:
        """Get current status.

        Returns:
            One of: unknown, unavailable, download_needed, loading, ready, error
        """
        return self.current_status


class VoiceStatusBadge(ft.UserControl):
    """Compact voice status badge for toolbar."""

    def __init__(self, on_click: Optional[Callable] = None):
        """Initialize badge.

        Args:
            on_click: Callback when badge is clicked
        """
        super().__init__()
        self.on_click = on_click
        self.whisper_manager = get_whisper_manager()
        self.badge_icon: Optional[ft.Icon] = None
        self.is_ready = False

    def build(self):
        """Build the badge."""
        # Check status
        is_available = self.whisper_manager.is_available()
        model_info = self.whisper_manager.get_model_info()
        is_downloaded = model_info.get("downloaded", False)

        if is_available and is_downloaded:
            icon = ft.Icons.MIC
            color = ft.Colors.GREEN_700
            tooltip = "Voice input ready"
            self.is_ready = True
        elif is_available:
            icon = ft.Icons.MIC_OFF
            color = ft.Colors.ORANGE_700
            tooltip = "Voice available - model download needed"
        else:
            icon = ft.Icons.MIC_NONE
            color = ft.Colors.GREY_400
            tooltip = "Voice input not available"

        self.badge_icon = ft.Icon(
            icon,
            color=color,
            size=20,
        )

        return ft.IconButton(
            content=self.badge_icon,
            tooltip=tooltip,
            on_click=self._handle_click,
            icon_size=20,
        )

    def _handle_click(self, e):
        """Handle badge click."""
        if self.on_click:
            self.on_click(e)


def show_voice_status_dialog(page: ft.Page):
    """Show detailed voice status in a dialog."""
    whisper_manager = get_whisper_manager()

    # Get status info
    is_available = whisper_manager.is_available()
    backend = whisper_manager.model_type
    models = whisper_manager.get_available_models()

    # Build content
    content_items = []

    if not is_available:
        content_items.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_700, size=48),
                        ft.Text(
                            "Voice Input Not Available",
                            weight=ft.FontWeight.BOLD,
                            size=16,
                        ),
                        ft.Text(
                            whisper_manager.get_installation_instructions(),
                            size=12,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=20,
            )
        )
    else:
        content_items.append(
            ft.Text(
                f"Backend: {backend}",
                size=12,
                weight=ft.FontWeight.BOLD,
            )
        )

        # Show available models
        for model_data in models:
            size = model_data["size"]
            info = model_data["info"]

            content_items.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE
                                if info.get("downloaded")
                                else ft.Icons.CLOUD_DOWNLOAD,
                                color=ft.Colors.GREEN_700
                                if info.get("downloaded")
                                else ft.Colors.GREY_400,
                                size=20,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        f"{size.upper()} ({info.get('size_mb')}MB)",
                                        size=13,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Text(
                                        info.get("description", ""),
                                        size=11,
                                        color=ft.Colors.GREY_600,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=10,
                    bgcolor=ft.Colors.GREY_50 if info.get("downloaded") else None,
                    border_radius=5,
                )
            )

    dialog = ft.AlertDialog(
        title=ft.Text("Voice Input Status"),
        content=ft.Column(
            content_items,
            spacing=10,
            tight=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        actions=[
            ft.TextButton("Close", on_click=lambda e: page.close(dialog)),
        ],
    )

    page.open(dialog)
