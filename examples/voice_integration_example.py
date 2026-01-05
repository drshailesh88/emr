"""Example of integrating voice input into DocAssist EMR.

This example demonstrates:
1. Voice status indicator
2. Enhanced voice input button with waveform
3. Transcription preview dialog
4. Integration with clinical notes field
"""

import flet as ft
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.components.voice_status_indicator import VoiceStatusIndicator, VoiceStatusBadge, show_voice_status_dialog
from src.ui.components.voice_input_button_enhanced import VoiceInputButtonEnhanced, TranscriptionPreviewDialog


def main(page: ft.Page):
    """Main app with voice integration example."""
    page.title = "Voice Integration Example - DocAssist EMR"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20

    # Clinical notes field (simulating central_panel notes field)
    notes_field = ft.TextField(
        label="Clinical Notes",
        hint_text="Enter clinical findings or use voice input...",
        multiline=True,
        min_lines=8,
        max_lines=12,
        expand=True,
    )

    # Transcription counter
    transcription_count = ft.Text("Transcriptions: 0", size=12, color=ft.Colors.GREY_600)
    count = [0]

    def on_voice_text(text: str):
        """Handle transcribed text from voice input."""
        # Show preview dialog
        def insert_text(edited_text: str):
            # Insert into notes field
            current = notes_field.value or ""
            if current and not current.endswith((' ', '\n', '.')):
                edited_text = " " + edited_text
            notes_field.value = current + edited_text
            notes_field.update()

            # Update counter
            count[0] += 1
            transcription_count.value = f"Transcriptions: {count[0]}"
            transcription_count.update()

            # Show success snackbar
            page.open(
                ft.SnackBar(
                    content=ft.Text("Transcription inserted"),
                    bgcolor=ft.Colors.GREEN_700,
                )
            )

        # Show preview dialog
        preview = TranscriptionPreviewDialog(
            transcribed_text=text,
            on_insert=insert_text,
        )
        preview.show(page)

    # Voice status indicator
    voice_status = VoiceStatusIndicator(
        on_settings_click=lambda: show_voice_status_dialog(page),
        auto_check=True,
    )

    # Enhanced voice input button
    voice_button = VoiceInputButtonEnhanced(
        on_text=on_voice_text,
        size=56,
        tooltip="Click to record, click again to stop (Ctrl+M)",
        show_waveform=True,
    )

    # Voice status badge for toolbar
    voice_badge = VoiceStatusBadge(
        on_click=lambda e: show_voice_status_dialog(page)
    )

    # Header with voice status
    header = ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    "DocAssist EMR - Voice Integration Demo",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                voice_badge,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=10,
        bgcolor=ft.Colors.BLUE_50,
        border_radius=8,
    )

    # Voice status panel
    status_panel = ft.Container(
        content=ft.Column(
            [
                ft.Text("Voice Status", size=14, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                voice_status,
            ],
            spacing=10,
        ),
        padding=15,
        bgcolor=ft.Colors.GREY_50,
        border_radius=8,
        width=300,
    )

    # Notes panel with voice button
    notes_panel = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Clinical Notes", size=14, weight=ft.FontWeight.BOLD),
                        transcription_count,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(height=1),
                ft.Row(
                    [
                        ft.Container(content=notes_field, expand=True),
                        ft.Container(
                            content=voice_button,
                            alignment=ft.alignment.top_center,
                            padding=ft.padding.only(top=10),
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            spacing=10,
            expand=True,
        ),
        padding=15,
        bgcolor=ft.Colors.WHITE,
        border_radius=8,
        border=ft.border.all(1, ft.Colors.GREY_300),
        expand=True,
    )

    # Instructions
    instructions = ft.Container(
        content=ft.Column(
            [
                ft.Text("How to Use:", size=13, weight=ft.FontWeight.BOLD),
                ft.Text("1. Check voice status in the top-right badge", size=12),
                ft.Text("2. If model needs downloading, click 'Download' in status panel", size=12),
                ft.Text("3. Click the microphone button to start recording", size=12),
                ft.Text("4. Speak your clinical notes", size=12),
                ft.Text("5. Click again to stop and transcribe", size=12),
                ft.Text("6. Review and edit the transcription before inserting", size=12),
            ],
            spacing=5,
        ),
        padding=15,
        bgcolor=ft.Colors.BLUE_50,
        border_radius=8,
    )

    # Main layout
    page.add(
        ft.Column(
            [
                header,
                ft.Container(height=10),
                instructions,
                ft.Container(height=10),
                ft.Row(
                    [
                        notes_panel,
                        status_panel,
                    ],
                    spacing=10,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
