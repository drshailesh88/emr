"""Ambient Panel - Real-time voice capture with SOAP note extraction."""

import flet as ft
from typing import Optional, Callable, Dict, Any
import time
from dataclasses import dataclass
from enum import Enum


class AmbientState(Enum):
    """States for ambient voice capture."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


@dataclass
class SOAPNote:
    """SOAP note structure extracted from conversation."""
    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""


class AmbientPanel(ft.UserControl):
    """Real-time voice capture panel with live transcription and SOAP extraction.

    Features:
    - Waveform visualization during recording
    - Live transcript display
    - AI-extracted SOAP notes in editable cards
    - Language detection (Hindi/English/Mixed)
    - One-click accept/edit/reject
    - Premium UX with smooth animations
    """

    def __init__(
        self,
        on_accept: Optional[Callable[[SOAPNote], None]] = None,
        on_reject: Optional[Callable] = None,
        is_dark: bool = False,
    ):
        """Initialize ambient panel.

        Args:
            on_accept: Callback when SOAP note is accepted
            on_reject: Callback when user rejects the note
            is_dark: Whether dark mode is active
        """
        super().__init__()
        self.on_accept = on_accept
        self.on_reject = on_reject
        self.is_dark = is_dark

        self.state = AmbientState.IDLE
        self.current_transcript = ""
        self.detected_language = "English"
        self.soap_note = SOAPNote()

        # UI components
        self.state_indicator: Optional[ft.Container] = None
        self.mic_button: Optional[ft.Container] = None
        self.waveform: Optional[ft.Row] = None
        self.transcript_view: Optional[ft.Container] = None
        self.language_badge: Optional[ft.Container] = None
        self.soap_cards: Dict[str, ft.Container] = {}
        self.action_buttons: Optional[ft.Row] = None

    def build(self):
        """Build the ambient panel UI."""
        # Header with state indicator
        header = self._build_header()

        # Microphone button with waveform
        mic_section = self._build_mic_section()

        # Live transcript display
        transcript_section = self._build_transcript_section()

        # SOAP note cards
        soap_section = self._build_soap_section()

        # Action buttons
        actions = self._build_actions()

        return ft.Container(
            content=ft.Column([
                header,
                ft.Divider(height=1, color=ft.Colors.GREY_800 if self.is_dark else ft.Colors.GREY_300),
                mic_section,
                transcript_section,
                soap_section,
                actions,
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20,
            bgcolor="#1A2332" if self.is_dark else ft.Colors.BLUE_50,
            expand=True,
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )

    def _build_header(self) -> ft.Container:
        """Build header with state indicator and language badge."""
        self.state_indicator = ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.CIRCLE,
                    size=12,
                    color=self._get_state_color(),
                ),
                ft.Text(
                    self._get_state_text(),
                    size=14,
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.WHITE if self.is_dark else ft.Colors.GREY_900,
                ),
            ], spacing=8),
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
        )

        self.language_badge = ft.Container(
            content=ft.Text(
                self.detected_language,
                size=12,
                color=ft.Colors.WHITE,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            bgcolor=ft.Colors.BLUE_700,
            border_radius=12,
            visible=self.state != AmbientState.IDLE,
        )

        return ft.Container(
            content=ft.Row([
                ft.Text(
                    "Ambient Capture",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE if self.is_dark else ft.Colors.GREY_900,
                ),
                ft.Container(expand=True),
                self.state_indicator,
                self.language_badge,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        )

    def _build_mic_section(self) -> ft.Container:
        """Build microphone button with waveform visualization."""
        # Animated waveform bars
        waveform_bars = []
        for i, height in enumerate([30, 45, 35, 50, 40, 55, 35, 45, 30]):
            bar = ft.Container(
                width=4,
                height=height,
                bgcolor=ft.Colors.BLUE_400 if self.is_dark else ft.Colors.BLUE_600,
                border_radius=2,
                animate=ft.animation.Animation(500 + i * 100, ft.AnimationCurve.EASE_IN_OUT),
            )
            waveform_bars.append(bar)

        self.waveform = ft.Row(
            waveform_bars,
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
            visible=False,
        )

        # Microphone button
        self.mic_button = ft.Container(
            content=ft.Icon(
                ft.Icons.MIC,
                color=ft.Colors.WHITE,
                size=48,
            ),
            width=100,
            height=100,
            bgcolor=ft.Colors.BLUE_700,
            border_radius=50,
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.3, ft.Colors.BLUE_700),
                offset=ft.Offset(0, 4),
            ),
            ink=True,
            on_click=self._toggle_recording,
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
            animate_scale=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
        )

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=self.mic_button,
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=15),
                self.waveform,
                ft.Container(height=10),
                ft.Text(
                    "Tap to start listening",
                    size=14,
                    color=ft.Colors.GREY_400 if self.is_dark else ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=20,
        )

    def _build_transcript_section(self) -> ft.Container:
        """Build live transcript display."""
        self.transcript_view = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SUBTITLES, size=16, color=ft.Colors.BLUE_400),
                    ft.Text(
                        "Live Transcript",
                        size=14,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.WHITE if self.is_dark else ft.Colors.GREY_900,
                    ),
                ], spacing=8),
                ft.Container(height=10),
                ft.Text(
                    self.current_transcript or "Transcript will appear here as you speak...",
                    size=13,
                    color=ft.Colors.GREY_400 if self.is_dark else ft.Colors.GREY_700,
                    selectable=True,
                ),
            ], spacing=5),
            padding=15,
            bgcolor="#2D2D2D" if self.is_dark else ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_800 if self.is_dark else ft.Colors.GREY_300),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            visible=False,
        )

        return self.transcript_view

    def _build_soap_section(self) -> ft.Container:
        """Build SOAP note cards (editable)."""
        soap_sections = [
            ("Subjective", "subjective", ft.Icons.PERSON, "Chief complaint, history"),
            ("Objective", "objective", ft.Icons.SCIENCE, "Vitals, examination findings"),
            ("Assessment", "assessment", ft.Icons.ANALYTICS, "Diagnoses, differential"),
            ("Plan", "plan", ft.Icons.ASSIGNMENT, "Medications, investigations, advice"),
        ]

        cards = []
        for title, key, icon, placeholder in soap_sections:
            card = self._create_soap_card(title, key, icon, placeholder)
            self.soap_cards[key] = card
            cards.append(card)

        return ft.Container(
            content=ft.Column(cards, spacing=12),
            visible=False,
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )

    def _create_soap_card(
        self,
        title: str,
        key: str,
        icon: str,
        placeholder: str
    ) -> ft.Container:
        """Create individual SOAP card."""
        text_field = ft.TextField(
            value="",
            multiline=True,
            min_lines=2,
            max_lines=5,
            hint_text=placeholder,
            border_color=ft.Colors.GREY_700 if self.is_dark else ft.Colors.GREY_400,
            focused_border_color=ft.Colors.BLUE_400,
            text_size=13,
            bgcolor="#1E1E1E" if self.is_dark else ft.Colors.GREY_50,
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, size=18, color=ft.Colors.BLUE_400),
                    ft.Text(
                        title,
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE if self.is_dark else ft.Colors.GREY_900,
                    ),
                ], spacing=8),
                ft.Container(height=8),
                text_field,
            ], spacing=0),
            padding=15,
            bgcolor="#2D2D2D" if self.is_dark else ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_800 if self.is_dark else ft.Colors.GREY_300),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            data={"key": key, "text_field": text_field},
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
        )

    def _build_actions(self) -> ft.Container:
        """Build action buttons (Accept/Edit/Reject)."""
        self.action_buttons = ft.Row([
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.CLOSE, size=18),
                    ft.Text("Reject", size=14),
                ], spacing=5),
                bgcolor=ft.Colors.RED_700,
                color=ft.Colors.WHITE,
                on_click=self._handle_reject,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                ),
            ),
            ft.Container(expand=True),
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=18),
                    ft.Text("Accept & Save", size=14, weight=ft.FontWeight.BOLD),
                ], spacing=5),
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
                on_click=self._handle_accept,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.padding.symmetric(horizontal=24, vertical=12),
                ),
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, visible=False)

        return ft.Container(
            content=self.action_buttons,
            padding=ft.padding.only(top=10),
        )

    def _toggle_recording(self, e):
        """Toggle recording on/off."""
        if self.state == AmbientState.IDLE:
            self._start_listening()
        elif self.state == AmbientState.LISTENING:
            self._stop_listening()

    def _start_listening(self):
        """Start voice capture."""
        self.state = AmbientState.LISTENING
        self.current_transcript = ""

        # Update UI
        self._update_mic_button(listening=True)
        self.waveform.visible = True
        self.transcript_view.visible = True
        self.language_badge.visible = True

        self._update_state_indicator()
        self._animate_waveform(True)

        if self.page:
            self.update()

    def _stop_listening(self):
        """Stop voice capture and process."""
        self.state = AmbientState.PROCESSING

        # Update UI
        self._update_mic_button(listening=False)
        self.waveform.visible = False
        self._update_state_indicator()

        if self.page:
            self.update()

        # Simulate processing (replace with actual LLM call)
        import threading
        threading.Thread(target=self._process_transcript, daemon=True).start()

    def _process_transcript(self):
        """Process transcript to extract SOAP notes (mock implementation)."""
        # Simulate LLM processing delay
        time.sleep(2)

        # Mock SOAP extraction (replace with actual LLM service)
        self.soap_note = SOAPNote(
            subjective="Patient complains of chest pain for 2 days, radiating to left arm. No breathlessness.",
            objective="BP: 140/90 mmHg, HR: 88 bpm, Chest: clear to auscultation",
            assessment="1. Angina pectoris - stable\n2. Hypertension - controlled",
            plan="1. Tab. Aspirin 75mg OD\n2. Tab. Atorvastatin 40mg OD\n3. ECG, Troponin I\n4. Follow-up in 1 week"
        )

        # Update UI on main thread
        if self.page:
            self.page.run_task(self._show_soap_results)

    def _show_soap_results(self):
        """Display extracted SOAP notes."""
        self.state = AmbientState.READY

        # Populate SOAP cards
        for key in ["subjective", "objective", "assessment", "plan"]:
            value = getattr(self.soap_note, key, "")
            card = self.soap_cards.get(key)
            if card:
                text_field = card.data["text_field"]
                text_field.value = value

        # Show SOAP section and action buttons
        for card in self.soap_cards.values():
            card.visible = True
        self.action_buttons.visible = True

        self._update_state_indicator()

        if self.page:
            self.update()

    def _handle_accept(self, e):
        """Accept SOAP note and save."""
        # Collect edited values
        for key in ["subjective", "objective", "assessment", "plan"]:
            card = self.soap_cards.get(key)
            if card:
                text_field = card.data["text_field"]
                setattr(self.soap_note, key, text_field.value or "")

        if self.on_accept:
            self.on_accept(self.soap_note)

        self._reset()

    def _handle_reject(self, e):
        """Reject SOAP note."""
        if self.on_reject:
            self.on_reject()

        self._reset()

    def _reset(self):
        """Reset to idle state."""
        self.state = AmbientState.IDLE
        self.current_transcript = ""
        self.soap_note = SOAPNote()

        # Hide UI elements
        self.transcript_view.visible = False
        self.language_badge.visible = False
        for card in self.soap_cards.values():
            card.visible = False
        self.action_buttons.visible = False

        self._update_mic_button(listening=False)
        self._update_state_indicator()

        if self.page:
            self.update()

    def _update_mic_button(self, listening: bool):
        """Update microphone button appearance."""
        if not self.mic_button:
            return

        if listening:
            self.mic_button.bgcolor = ft.Colors.RED_700
            self.mic_button.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.5, ft.Colors.RED_700),
                offset=ft.Offset(0, 4),
            )
            # Add pulsing animation
            self.mic_button.scale = 1.1
        else:
            self.mic_button.bgcolor = ft.Colors.BLUE_700
            self.mic_button.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.3, ft.Colors.BLUE_700),
                offset=ft.Offset(0, 4),
            )
            self.mic_button.scale = 1.0

        if self.mic_button.page:
            self.mic_button.update()

    def _animate_waveform(self, active: bool):
        """Animate waveform bars."""
        if not self.waveform:
            return

        # Simple animation toggle (in production, use audio levels)
        for bar in self.waveform.controls:
            if active:
                bar.opacity = 1.0
            else:
                bar.opacity = 0.3

    def _update_state_indicator(self):
        """Update state indicator."""
        if not self.state_indicator:
            return

        icon = self.state_indicator.content.controls[0]
        text = self.state_indicator.content.controls[1]

        icon.color = self._get_state_color()
        text.value = self._get_state_text()

        if self.state_indicator.page:
            self.state_indicator.update()

    def _get_state_color(self) -> str:
        """Get color for current state."""
        return {
            AmbientState.IDLE: ft.Colors.GREY_500,
            AmbientState.LISTENING: ft.Colors.RED_500,
            AmbientState.PROCESSING: ft.Colors.ORANGE_500,
            AmbientState.READY: ft.Colors.GREEN_500,
            AmbientState.ERROR: ft.Colors.RED_700,
        }.get(self.state, ft.Colors.GREY_500)

    def _get_state_text(self) -> str:
        """Get text for current state."""
        return {
            AmbientState.IDLE: "Ready",
            AmbientState.LISTENING: "Listening...",
            AmbientState.PROCESSING: "Processing...",
            AmbientState.READY: "Ready to Save",
            AmbientState.ERROR: "Error",
        }.get(self.state, "Unknown")

    def update_transcript(self, text: str):
        """Update live transcript (call from voice service).

        Args:
            text: Transcribed text to append
        """
        self.current_transcript = text

        if self.transcript_view:
            text_widget = self.transcript_view.content.controls[2]
            text_widget.value = text

            if self.transcript_view.page:
                text_widget.update()

    def set_language(self, language: str):
        """Set detected language.

        Args:
            language: Detected language name
        """
        self.detected_language = language

        if self.language_badge:
            badge_text = self.language_badge.content
            badge_text.value = language

            if self.language_badge.page:
                self.language_badge.update()
