"""Enhanced voice input button with waveform visualization and smooth animations."""

import flet as ft
from typing import Optional, Callable
import threading
import time
import numpy as np

from ...services.voice.whisper_manager import get_whisper_manager
from ...services.voice.audio_processor import get_audio_processor


class VoiceInputButtonEnhanced(ft.UserControl):
    """Enhanced microphone button with visual feedback and waveform."""

    def __init__(
        self,
        on_text: Callable[[str], None],
        size: int = 48,
        tooltip: str = "Voice dictation (Ctrl+M)",
        show_waveform: bool = True,
    ):
        """Initialize enhanced voice input button.

        Args:
            on_text: Callback with transcribed text
            size: Button size in pixels
            tooltip: Tooltip text
            show_waveform: Show waveform visualization
        """
        super().__init__()
        self.on_text = on_text
        self.size = size
        self.tooltip = tooltip
        self.show_waveform_viz = show_waveform

        # State
        self.state = "idle"  # idle, recording, processing, error
        self.is_recording = False

        # Services
        self.whisper_manager = get_whisper_manager()
        self.audio_processor = get_audio_processor()

        # UI components
        self.mic_button: Optional[ft.Container] = None
        self.status_text: Optional[ft.Text] = None
        self.waveform: Optional[ft.Row] = None
        self.waveform_bars: list = []
        self.pulse_animation_active = False

        # Audio level for visualization
        self.current_audio_level = 0.0
        self._audio_level_lock = threading.Lock()

    def build(self):
        """Build the voice input button UI."""
        # Check if voice is available
        if not self.whisper_manager.is_available() or not self.audio_processor.is_available():
            return self._build_unavailable()

        # Status text
        self.status_text = ft.Text(
            "",
            size=10,
            color=ft.Colors.GREY_600,
            visible=False,
            text_align=ft.TextAlign.CENTER,
        )

        # Waveform visualization (5 bars)
        if self.show_waveform_viz:
            self.waveform_bars = [
                ft.Container(
                    width=3,
                    height=8,
                    bgcolor=ft.Colors.BLUE_700,
                    border_radius=2,
                    animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
                )
                for _ in range(5)
            ]
            self.waveform = ft.Row(
                self.waveform_bars,
                spacing=2,
                alignment=ft.MainAxisAlignment.CENTER,
                visible=False,
            )
        else:
            self.waveform = ft.Container(visible=False)

        # Microphone button
        self.mic_button = ft.Container(
            content=ft.Icon(
                ft.Icons.MIC,
                color=ft.Colors.WHITE,
                size=self.size - 20,
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
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )

        return ft.Column(
            [
                self.mic_button,
                self.waveform,
                self.status_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        )

    def _build_unavailable(self) -> ft.Control:
        """Build UI for unavailable state."""
        return ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.MIC_OFF,
                icon_color=ft.Colors.GREY_400,
                icon_size=self.size - 20,
                tooltip="Voice input not available. Check Voice Status for details.",
                disabled=True,
            ),
            width=self.size,
            height=self.size,
        )

    def _toggle_recording(self, e):
        """Toggle recording on/off."""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Start voice recording."""
        self.is_recording = True
        self._update_state("recording", "Listening...")

        # Start recording in background
        threading.Thread(target=self._record_and_transcribe, daemon=True).start()

    def _stop_recording(self):
        """Stop voice recording."""
        if not self.is_recording:
            return

        self.is_recording = False
        self._update_state("idle", "")

    def _record_and_transcribe(self):
        """Record audio and transcribe in background."""
        try:
            # Ensure model is loaded
            if self.whisper_manager.current_model is None:
                self._update_state("processing", "Loading model...")

                success, model, error = self.whisper_manager.load_model()
                if not success:
                    self._update_state("error", f"Error: {error[:20]}...")
                    time.sleep(2)
                    self._update_state("idle", "")
                    self.is_recording = False
                    return

            # Collect audio chunks
            audio_chunks = []

            def on_audio_chunk(audio_data: np.ndarray):
                """Handle audio chunk."""
                if self.is_recording:
                    audio_chunks.append(audio_data)

                    # Update waveform visualization
                    level = self.audio_processor.calculate_audio_level(audio_data)
                    with self._audio_level_lock:
                        self.current_audio_level = level

            # Start audio capture
            self.audio_processor.start_recording(on_audio_chunk)

            # Start waveform animation
            if self.show_waveform_viz:
                threading.Thread(target=self._animate_waveform, daemon=True).start()

            # Wait for recording to stop
            while self.is_recording:
                time.sleep(0.1)

            # Stop audio capture
            self.audio_processor.stop_recording()

            # Stop waveform animation
            self.pulse_animation_active = False

            # Concatenate all chunks
            if not audio_chunks:
                self._update_state("idle", "")
                return

            full_audio = np.concatenate(audio_chunks)

            # Check if we have enough audio
            if len(full_audio) < self.audio_processor.format.sample_rate * 0.5:
                self._update_state("error", "Too short")
                time.sleep(1)
                self._update_state("idle", "")
                return

            # Transcribe
            self._update_state("processing", "Transcribing...")

            text = self.whisper_manager.transcribe(
                full_audio,
                language="en",
                on_progress=lambda s: self._update_state("processing", s),
            )

            # Emit transcribed text
            if text and self.on_text:
                self.on_text(text)
                self._update_state("idle", "")
            else:
                self._update_state("error", "No speech detected")
                time.sleep(1)
                self._update_state("idle", "")

        except Exception as e:
            self._update_state("error", f"Error: {str(e)[:20]}...")
            time.sleep(2)
            self._update_state("idle", "")
        finally:
            self.is_recording = False
            self.audio_processor.stop_recording()
            self.pulse_animation_active = False

    def _update_state(self, state: str, message: str):
        """Update button state and UI.

        Args:
            state: One of idle, recording, processing, error
            message: Status message to display
        """
        self.state = state

        if not self.mic_button or not self.mic_button.page:
            return

        # Update button appearance
        if state == "idle":
            self.mic_button.bgcolor = ft.Colors.BLUE_700
            self.mic_button.content.name = ft.Icons.MIC
            self.mic_button.content.color = ft.Colors.WHITE
            self.status_text.visible = False
            if self.waveform:
                self.waveform.visible = False

        elif state == "recording":
            self.mic_button.bgcolor = ft.Colors.RED_700
            self.mic_button.content.name = ft.Icons.MIC
            self.mic_button.content.color = ft.Colors.WHITE
            self.status_text.value = message
            self.status_text.color = ft.Colors.RED_700
            self.status_text.visible = True
            if self.waveform:
                self.waveform.visible = True

            # Start pulse animation
            self.pulse_animation_active = True

        elif state == "processing":
            self.mic_button.bgcolor = ft.Colors.BLUE_700
            self.mic_button.content.name = ft.Icons.HOURGLASS_EMPTY
            self.mic_button.content.color = ft.Colors.WHITE
            self.status_text.value = message
            self.status_text.color = ft.Colors.BLUE_700
            self.status_text.visible = True
            if self.waveform:
                self.waveform.visible = False

        elif state == "error":
            self.mic_button.bgcolor = ft.Colors.RED_700
            self.mic_button.content.name = ft.Icons.ERROR_OUTLINE
            self.mic_button.content.color = ft.Colors.WHITE
            self.status_text.value = message
            self.status_text.color = ft.Colors.RED_700
            self.status_text.visible = True
            if self.waveform:
                self.waveform.visible = False

        # Update UI
        self.mic_button.page.update()

    def _animate_waveform(self):
        """Animate waveform bars based on audio level."""
        if not self.waveform or not self.waveform_bars:
            return

        self.pulse_animation_active = True

        while self.pulse_animation_active and self.is_recording:
            try:
                # Get current audio level
                with self._audio_level_lock:
                    level = self.current_audio_level

                # Update bar heights based on level
                base_height = 8
                max_height = 32

                for i, bar in enumerate(self.waveform_bars):
                    # Each bar has a slight phase offset for wave effect
                    phase = i * 0.2
                    wave_factor = np.sin(time.time() * 3 + phase)

                    # Combine audio level with wave
                    height = base_height + (max_height - base_height) * level * (0.5 + 0.5 * wave_factor)
                    bar.height = int(height)

                if self.waveform.page:
                    self.waveform.page.update()

                time.sleep(0.05)  # 20 FPS

            except Exception as e:
                break

        # Reset bars
        for bar in self.waveform_bars:
            bar.height = 8

        if self.waveform.page:
            self.waveform.page.update()

    def set_enabled(self, enabled: bool):
        """Enable or disable the button."""
        if self.mic_button:
            self.mic_button.disabled = not enabled


class TranscriptionPreviewDialog:
    """Dialog to preview and edit transcription before inserting."""

    def __init__(
        self,
        transcribed_text: str,
        on_insert: Callable[[str], None],
        on_cancel: Optional[Callable] = None,
    ):
        """Initialize preview dialog.

        Args:
            transcribed_text: The transcribed text
            on_insert: Callback when user clicks Insert
            on_cancel: Callback when user clicks Cancel
        """
        self.transcribed_text = transcribed_text
        self.on_insert = on_insert
        self.on_cancel = on_cancel
        self.text_field: Optional[ft.TextField] = None
        self.dialog: Optional[ft.AlertDialog] = None

    def show(self, page: ft.Page):
        """Show the preview dialog."""
        self.text_field = ft.TextField(
            value=self.transcribed_text,
            multiline=True,
            min_lines=3,
            max_lines=8,
            autofocus=True,
        )

        def insert_clicked(e):
            text = self.text_field.value.strip()
            if text and self.on_insert:
                self.on_insert(text)
            page.close(self.dialog)

        def cancel_clicked(e):
            if self.on_cancel:
                self.on_cancel()
            page.close(self.dialog)

        self.dialog = ft.AlertDialog(
            title=ft.Text("Voice Transcription"),
            content=ft.Column(
                [
                    ft.Text(
                        "Review and edit the transcription before inserting:",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                    self.text_field,
                ],
                tight=True,
                spacing=10,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_clicked),
                ft.ElevatedButton(
                    "Insert",
                    on_click=insert_clicked,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_700,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
        )

        page.open(self.dialog)
