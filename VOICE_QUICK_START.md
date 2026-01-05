# Voice Integration - Quick Start Guide

**5-Minute Integration Guide** for adding Whisper voice input to DocAssist EMR.

## Prerequisites

```bash
pip install faster-whisper sounddevice numpy
```

## 1. Add Voice Status to Toolbar (30 seconds)

```python
# In your main app.py or main_layout.py
from src.ui.components import VoiceStatusBadge, show_voice_status_dialog

# Add to toolbar
voice_badge = VoiceStatusBadge(
    on_click=lambda e: show_voice_status_dialog(page)
)

# Add to your toolbar row
toolbar = ft.Row([
    # ... other toolbar items ...
    voice_badge,
])
```

## 2. Add Voice Button to Notes Field (1 minute)

```python
# In central_panel.py or wherever clinical notes are
from src.ui.components import VoiceInputButtonEnhanced

# Your existing notes field
notes_field = ft.TextField(
    label="Clinical Notes",
    multiline=True,
    min_lines=8,
)

# Voice text handler
def on_voice_text(text: str):
    """Handle transcribed text."""
    current = notes_field.value or ""
    if current and not current.endswith((' ', '\n', '.')):
        text = " " + text
    notes_field.value = current + text
    notes_field.update()

# Voice button
voice_button = VoiceInputButtonEnhanced(
    on_text=on_voice_text,
    size=48,
    show_waveform=True,
)

# Layout (notes field + voice button)
notes_row = ft.Row([
    ft.Container(content=notes_field, expand=True),
    ft.Container(
        content=voice_button,
        alignment=ft.alignment.top_center,
        padding=ft.padding.only(top=5),
    ),
])
```

## 3. Optional: Add Preview Dialog (2 minutes)

```python
# Replace simple on_voice_text with preview version
from src.ui.components import TranscriptionPreviewDialog

def on_voice_text_with_preview(text: str):
    """Show preview before inserting."""

    def insert_text(edited_text: str):
        current = notes_field.value or ""
        if current and not current.endswith((' ', '\n', '.')):
            edited_text = " " + edited_text
        notes_field.value = current + edited_text
        notes_field.update()

        # Optional: Show success message
        page.open(ft.SnackBar(
            content=ft.Text("Transcription inserted"),
            bgcolor=ft.Colors.GREEN_700,
        ))

    # Show preview dialog
    preview = TranscriptionPreviewDialog(
        transcribed_text=text,
        on_insert=insert_text,
    )
    preview.show(page)

# Use this instead
voice_button = VoiceInputButtonEnhanced(
    on_text=on_voice_text_with_preview,
    size=48,
    show_waveform=True,
)
```

## 4. Optional: Preload Model on Startup (1 minute)

```python
# In your app initialization (main.py or app.py)
from src.services.voice import get_whisper_manager
import threading

def preload_voice_model():
    """Preload voice model in background."""
    manager = get_whisper_manager()
    if manager.is_available():
        manager.preload_model_async("base")

# Call during app startup
threading.Thread(target=preload_voice_model, daemon=True).start()
```

## 5. Test It!

1. Run your app
2. Check voice status badge (should show green if ready)
3. Click microphone button
4. Speak: "Patient presents with chest pain radiating to left arm"
5. Click microphone again to stop
6. Review transcription in preview dialog
7. Edit if needed, click "Insert"
8. Text appears in clinical notes

## Complete Example

Here's everything together in one place:

```python
import flet as ft
from src.ui.components import (
    VoiceInputButtonEnhanced,
    VoiceStatusBadge,
    TranscriptionPreviewDialog,
    show_voice_status_dialog,
)
from src.services.voice import get_whisper_manager

def build_clinical_notes_panel(page: ft.Page) -> ft.Control:
    """Build clinical notes panel with voice input."""

    # Notes field
    notes_field = ft.TextField(
        label="Clinical Notes",
        hint_text="Enter findings or use voice input...",
        multiline=True,
        min_lines=8,
        max_lines=12,
    )

    # Voice text handler with preview
    def on_voice_text(text: str):
        def insert_text(edited_text: str):
            current = notes_field.value or ""
            if current and not current.endswith((' ', '\n', '.')):
                edited_text = " " + edited_text
            notes_field.value = current + edited_text
            notes_field.update()

            page.open(ft.SnackBar(
                content=ft.Text("Transcription inserted"),
                bgcolor=ft.Colors.GREEN_700,
            ))

        preview = TranscriptionPreviewDialog(
            transcribed_text=text,
            on_insert=insert_text,
        )
        preview.show(page)

    # Voice button
    voice_button = VoiceInputButtonEnhanced(
        on_text=on_voice_text,
        size=48,
        show_waveform=True,
    )

    # Layout
    return ft.Row([
        ft.Container(content=notes_field, expand=True),
        ft.Container(
            content=voice_button,
            alignment=ft.alignment.top_center,
            padding=ft.padding.only(top=5),
        ),
    ])


def build_toolbar(page: ft.Page) -> ft.Control:
    """Build toolbar with voice status."""

    voice_badge = VoiceStatusBadge(
        on_click=lambda e: show_voice_status_dialog(page)
    )

    return ft.Row([
        ft.Text("DocAssist EMR", size=20, weight=ft.FontWeight.BOLD),
        # ... other toolbar items ...
        voice_badge,
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)


def main(page: ft.Page):
    """Main app."""
    page.title = "DocAssist EMR"

    # Preload voice model in background
    def preload():
        manager = get_whisper_manager()
        if manager.is_available():
            manager.preload_model_async("base")

    import threading
    threading.Thread(target=preload, daemon=True).start()

    # Build UI
    toolbar = build_toolbar(page)
    notes_panel = build_clinical_notes_panel(page)

    page.add(
        ft.Column([
            toolbar,
            ft.Divider(),
            notes_panel,
        ], expand=True)
    )


if __name__ == "__main__":
    ft.app(target=main)
```

## Troubleshooting

### "Voice Not Available" Error

```bash
pip install faster-whisper sounddevice numpy
```

### "No Microphone Detected"

Check system permissions:
- **macOS**: System Preferences → Security & Privacy → Microphone
- **Windows**: Settings → Privacy → Microphone
- **Linux**: Ensure user in `audio` group

### "Model Download Failed"

1. Check internet connection
2. Ensure 200MB free disk space
3. Try manual download:
   ```python
   from src.services.voice import get_whisper_manager
   manager = get_whisper_manager()
   manager.preload_model_async("base")
   ```

### Poor Transcription Quality

1. Use better microphone (USB recommended)
2. Reduce background noise
3. Position mic 6-12 inches from mouth
4. Use `small` model for better accuracy:
   ```python
   manager.load_model("small")
   ```

## Advanced Configuration

### Custom Model Size

```python
# In voice button initialization
from src.services.voice import get_whisper_manager

# Load specific model first
manager = get_whisper_manager()
manager.load_model("small")  # or "tiny", "medium"

# Then create button
voice_button = VoiceInputButtonEnhanced(...)
```

### Custom Audio Settings

```python
from src.services.voice import AudioProcessor, AudioFormat

# Custom audio format
custom_format = AudioFormat(
    sample_rate=16000,
    channels=1,
    chunk_duration_s=5.0,  # 5 second chunks
)

processor = AudioProcessor(custom_format)
```

### Disable Waveform (for performance)

```python
voice_button = VoiceInputButtonEnhanced(
    on_text=on_voice_text,
    size=48,
    show_waveform=False,  # Disable waveform
)
```

## Performance Tips

1. **Preload model on startup** - Reduces first-use delay
2. **Use `base` model** - Best balance of speed/accuracy
3. **Close other apps** - Free up RAM for transcription
4. **USB microphone** - Better audio quality = better accuracy

## Next Steps

- Read full documentation: `docs/VOICE_INTEGRATION.md`
- Run example: `flet run examples/voice_integration_example.py`
- Run tests: `pytest tests/test_voice_integration.py -v`

**That's it! Voice input is now integrated. 🎉**
