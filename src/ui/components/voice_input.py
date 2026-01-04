"""Voice input component - mic button for dictation."""

import flet as ft
from typing import Optional, Callable
import threading

from ...services.voice import get_voice_service, is_voice_available


class VoiceInputButton(ft.UserControl):
    """Microphone button for voice dictation."""

    def __init__(
        self,
        on_text: Callable[[str], None],
        size: int = 36,
        tooltip: str = "Voice input (hold to dictate)"
    ):
        """Initialize voice input button.

        Args:
            on_text: Callback with transcribed text to insert
            size: Button size in pixels
            tooltip: Tooltip text
        """
        super().__init__()
        self.on_text = on_text
        self.size = size
        self.tooltip = tooltip
        self.is_recording = False
        self.mic_button: Optional[ft.Container] = None
        self.status_text: Optional[ft.Text] = None
        self.voice_service = get_voice_service()

    def build(self):
        # Check availability
        if not is_voice_available():
            return ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.MIC_OFF,
                    icon_color=ft.Colors.GREY_400,
                    icon_size=self.size - 12,
                    tooltip="Voice input not available. Install: pip install faster-whisper sounddevice numpy",
                    disabled=True,
                ),
                width=self.size,
                height=self.size,
            )

        self.status_text = ft.Text(
            "",
            size=10,
            color=ft.Colors.GREY_600,
            visible=False,
        )

        self.mic_button = ft.Container(
            content=ft.Icon(
                ft.Icons.MIC,
                color=ft.Colors.WHITE,
                size=self.size - 16,
            ),
            width=self.size,
            height=self.size,
            bgcolor=ft.Colors.BLUE_700,
            border_radius=self.size // 2,
            alignment=ft.alignment.center,
            tooltip=self.tooltip,
            ink=True,
            on_click=self._toggle_recording,
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
        )

        return ft.Column([
            self.mic_button,
            self.status_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)

    def _toggle_recording(self, e):
        """Toggle recording on/off."""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Start voice recording."""
        self.is_recording = True
        self._update_ui_recording(True)

        # Start recording in background
        self.voice_service.start_recording(
            on_transcription=self._on_transcription,
            on_status_change=self._on_status_change,
        )

    def _stop_recording(self):
        """Stop voice recording."""
        self.is_recording = False
        self.voice_service.stop_recording()
        self._update_ui_recording(False)

    def _on_transcription(self, text: str):
        """Handle transcribed text."""
        if text and self.on_text:
            self.on_text(text)

    def _on_status_change(self, status: str):
        """Handle status changes."""
        if self.status_text and self.status_text.page:
            self.status_text.value = status
            self.status_text.visible = bool(status)
            self.status_text.update()

    def _update_ui_recording(self, recording: bool):
        """Update UI for recording state."""
        if self.mic_button and self.mic_button.page:
            if recording:
                self.mic_button.bgcolor = ft.Colors.RED_700
                self.mic_button.content = ft.Icon(
                    ft.Icons.MIC,
                    color=ft.Colors.WHITE,
                    size=self.size - 16,
                )
                # Add pulsing animation
                self.mic_button.animate_scale = ft.animation.Animation(
                    500, ft.AnimationCurve.EASE_IN_OUT
                )
            else:
                self.mic_button.bgcolor = ft.Colors.BLUE_700
                self.mic_button.content = ft.Icon(
                    ft.Icons.MIC,
                    color=ft.Colors.WHITE,
                    size=self.size - 16,
                )
                self.status_text.visible = False

            self.mic_button.update()
            if self.status_text:
                self.status_text.update()


class VoiceInputOverlay(ft.UserControl):
    """Floating voice input overlay that can be shown over any text field."""

    def __init__(
        self,
        target_field: ft.TextField,
        on_close: Optional[Callable] = None
    ):
        """Initialize overlay.

        Args:
            target_field: TextField to insert text into
            on_close: Callback when overlay is closed
        """
        super().__init__()
        self.target_field = target_field
        self.on_close = on_close
        self.is_recording = False
        self.voice_service = get_voice_service()
        self.status_text: Optional[ft.Text] = None
        self.waveform: Optional[ft.Container] = None

    def build(self):
        self.status_text = ft.Text(
            "Tap to start listening...",
            size=14,
            color=ft.Colors.WHITE,
        )

        # Animated waveform indicator
        self.waveform = ft.Row([
            ft.Container(width=4, height=20, bgcolor=ft.Colors.WHITE, border_radius=2),
            ft.Container(width=4, height=30, bgcolor=ft.Colors.WHITE, border_radius=2),
            ft.Container(width=4, height=25, bgcolor=ft.Colors.WHITE, border_radius=2),
            ft.Container(width=4, height=35, bgcolor=ft.Colors.WHITE, border_radius=2),
            ft.Container(width=4, height=20, bgcolor=ft.Colors.WHITE, border_radius=2),
        ], spacing=3, alignment=ft.MainAxisAlignment.CENTER, visible=False)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Voice Input", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=ft.Colors.WHITE,
                        on_click=self._close,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=20),
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.MIC,
                        color=ft.Colors.WHITE,
                        size=48,
                    ),
                    width=80,
                    height=80,
                    bgcolor=ft.Colors.RED_700 if self.is_recording else ft.Colors.BLUE_700,
                    border_radius=40,
                    alignment=ft.alignment.center,
                    ink=True,
                    on_click=self._toggle_recording,
                ),
                ft.Container(height=10),
                self.waveform,
                ft.Container(height=10),
                self.status_text,
                ft.Container(height=10),
                ft.Text(
                    "Say 'new line' for ↵ | 'period' for . | 'stop listening' to end",
                    size=10,
                    color=ft.Colors.WHITE70,
                    text_align=ft.TextAlign.CENTER,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            bgcolor=ft.Colors.BLUE_900,
            border_radius=15,
            width=300,
        )

    def _toggle_recording(self, e):
        """Toggle recording."""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Start recording."""
        self.is_recording = True
        self.voice_service.start_recording(
            on_transcription=self._on_transcription,
            on_status_change=self._on_status_change,
        )
        self.waveform.visible = True
        if self.waveform.page:
            self.waveform.update()

    def _stop_recording(self):
        """Stop recording."""
        self.is_recording = False
        self.voice_service.stop_recording()
        self.waveform.visible = False
        if self.waveform.page:
            self.waveform.update()

    def _on_transcription(self, text: str):
        """Insert transcribed text into target field."""
        if text and self.target_field:
            current = self.target_field.value or ""
            # Add space if needed
            if current and not current.endswith((' ', '\n')):
                text = " " + text
            self.target_field.value = current + text
            if self.target_field.page:
                self.target_field.update()

    def _on_status_change(self, status: str):
        """Update status text."""
        if self.status_text and self.status_text.page:
            self.status_text.value = status
            self.status_text.update()

    def _close(self, e):
        """Close the overlay."""
        self._stop_recording()
        if self.on_close:
            self.on_close()


def show_voice_overlay(page: ft.Page, target_field: ft.TextField):
    """Show voice input overlay for a text field.

    Args:
        page: Flet page
        target_field: TextField to receive transcribed text
    """
    if not is_voice_available():
        page.open(ft.SnackBar(
            content=ft.Text("Voice input not available. Install: pip install faster-whisper sounddevice numpy"),
            bgcolor=ft.Colors.RED_700,
        ))
        return

    overlay = None

    def close_overlay():
        nonlocal overlay
        if overlay:
            page.overlay.remove(overlay)
            page.update()

    voice_input = VoiceInputOverlay(target_field, on_close=close_overlay)

    overlay = ft.Container(
        content=ft.Stack([
            # Semi-transparent backdrop
            ft.Container(
                bgcolor=ft.Colors.BLACK54,
                expand=True,
                on_click=lambda e: close_overlay(),
            ),
            # Centered voice input
            ft.Container(
                content=voice_input,
                alignment=ft.alignment.center,
                expand=True,
            ),
        ]),
        expand=True,
    )

    page.overlay.append(overlay)
    page.update()
