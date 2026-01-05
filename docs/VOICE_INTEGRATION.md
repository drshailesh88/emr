# Voice Input Integration - DocAssist EMR

Complete guide to the Whisper-powered voice input system for DocAssist EMR.

## Overview

The voice input system provides **offline, local speech-to-text** for clinical documentation using OpenAI's Whisper model. All processing happens on-device with no cloud dependencies.

### Key Features

- ✅ **Offline & Private**: All transcription happens locally, no data sent to cloud
- ✅ **Medical Vocabulary**: Optimized for clinical terminology
- ✅ **Multiple Backends**: Supports faster-whisper (recommended) or openai-whisper
- ✅ **Visual Feedback**: Waveform visualization, pulsing animations
- ✅ **Model Management**: Automatic downloading with progress tracking
- ✅ **Error Handling**: Graceful fallbacks when dependencies unavailable

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Voice Input Flow                        │
└─────────────────────────────────────────────────────────────┘

    [Microphone]
         │
         ▼
  ┌──────────────┐
  │ AudioProcessor│  ← Handles recording, format conversion
  │ (sounddevice) │
  └──────┬───────┘
         │ (16kHz float32 mono audio)
         ▼
  ┌──────────────┐
  │WhisperManager│  ← Model loading, transcription
  │ (faster-whpr) │
  └──────┬───────┘
         │ (transcribed text)
         ▼
  ┌──────────────┐
  │   UI Button  │  ← Visual feedback, user interaction
  │  (Flet)      │
  └──────────────┘
```

## Components

### 1. WhisperManager (`src/services/voice/whisper_manager.py`)

Manages Whisper models with automatic downloading and caching.

**Features:**
- Auto-detects available backends (faster-whisper or openai-whisper)
- Downloads models on first use with progress callbacks
- Supports tiny, base, small, medium models
- Intelligent model caching
- Thread-safe model loading

**Usage:**
```python
from src.services.voice.whisper_manager import get_whisper_manager

# Get singleton instance
manager = get_whisper_manager()

# Check availability
if manager.is_available():
    # Load model with progress
    success, model, error = manager.load_model(
        "base",
        on_progress=lambda msg, pct: print(f"{msg}: {pct}%")
    )

    # Transcribe audio
    text = manager.transcribe(audio_array, language="en")
```

**Model Sizes:**
| Model  | Size  | RAM Usage | Speed | Accuracy |
|--------|-------|-----------|-------|----------|
| tiny   | 75MB  | ~1GB      | Fast  | Basic    |
| base   | 142MB | ~1.5GB    | Good  | Good     |
| small  | 466MB | ~2GB      | Slow  | Better   |
| medium | 1.5GB | ~5GB      | V.Slow| Best     |

**Recommendation**: Use `base` model for best balance.

### 2. AudioProcessor (`src/services/voice/audio_processor.py`)

Handles microphone input and audio format conversion.

**Features:**
- Cross-platform audio capture (sounddevice or pyaudio)
- Automatic format conversion to Whisper spec (16kHz, mono, float32)
- Audio level calculation for visualization
- Simple speech detection
- Device listing and testing

**Usage:**
```python
from src.services.voice.audio_processor import get_audio_processor

processor = get_audio_processor()

# Check if available
if processor.is_available():
    # Start recording
    def on_audio_chunk(audio: np.ndarray):
        print(f"Got audio: {len(audio)} samples")

    processor.start_recording(on_audio_chunk)

    # ... record for a while ...

    processor.stop_recording()
```

### 3. VoiceInputButtonEnhanced (`src/ui/components/voice_input_button_enhanced.py`)

Enhanced UI button with visual feedback.

**Features:**
- Pulsing animation during recording (red)
- Waveform visualization (5 animated bars)
- State management (idle, recording, processing, error)
- Automatic model loading
- Error handling with user feedback

**States:**
- **Idle** (gray): Ready to record
- **Recording** (red, pulsing): Actively recording with waveform
- **Processing** (blue): Transcribing audio
- **Error** (red): Error occurred

**Usage:**
```python
from src.ui.components import VoiceInputButtonEnhanced

def on_text_received(text: str):
    notes_field.value += " " + text
    notes_field.update()

voice_button = VoiceInputButtonEnhanced(
    on_text=on_text_received,
    size=56,
    tooltip="Voice input (Ctrl+M)",
    show_waveform=True,
)
```

### 4. VoiceStatusIndicator (`src/ui/components/voice_status_indicator.py`)

Shows voice availability and troubleshooting.

**Features:**
- Auto-checks voice system status
- Shows model download progress
- One-click installation instructions
- Download button for missing models
- Detailed status dialog

**Status States:**
- ✅ **Ready**: Voice input available, model loaded
- ⏳ **Loading**: Model is being loaded
- ⬇️ **Download Needed**: Model needs to be downloaded
- ❌ **Unavailable**: Dependencies not installed
- ⚠️ **Error**: Error occurred during setup

**Usage:**
```python
from src.ui.components import VoiceStatusIndicator, VoiceStatusBadge

# Full status indicator
status = VoiceStatusIndicator(
    on_settings_click=lambda: show_voice_status_dialog(page),
    auto_check=True,
)

# Compact badge for toolbar
badge = VoiceStatusBadge(
    on_click=lambda e: show_voice_status_dialog(page)
)
```

### 5. TranscriptionPreviewDialog

Preview and edit transcription before inserting.

**Features:**
- Shows transcribed text in editable field
- User can review and correct before inserting
- Cancel option
- Auto-focus on text field

**Usage:**
```python
from src.ui.components import TranscriptionPreviewDialog

preview = TranscriptionPreviewDialog(
    transcribed_text="Patient complains of chest pain",
    on_insert=lambda text: notes_field.value += text,
)
preview.show(page)
```

## Installation

### Required Dependencies

```bash
# Core voice dependencies
pip install faster-whisper sounddevice numpy

# OR use openai-whisper (slower but easier to install)
pip install openai-whisper sounddevice numpy
```

### Optional Dependencies

```bash
# For better VAD (Voice Activity Detection)
pip install webrtcvad

# For pyaudio backend (fallback)
pip install pyaudio
```

### System Requirements

**Minimum:**
- Python 3.11+
- 2GB RAM
- Microphone
- ~200MB disk space for base model

**Recommended:**
- 4GB RAM
- Good quality microphone
- 500MB disk space

## Integration Example

Complete example showing all components together:

```python
import flet as ft
from src.ui.components import (
    VoiceInputButtonEnhanced,
    VoiceStatusIndicator,
    VoiceStatusBadge,
    TranscriptionPreviewDialog,
)

def main(page: ft.Page):
    # Clinical notes field
    notes_field = ft.TextField(
        label="Clinical Notes",
        multiline=True,
        min_lines=8,
    )

    # Voice text handler
    def on_voice_text(text: str):
        def insert_text(edited_text: str):
            current = notes_field.value or ""
            if current and not current.endswith((' ', '\n')):
                edited_text = " " + edited_text
            notes_field.value = current + edited_text
            notes_field.update()

        # Show preview dialog
        preview = TranscriptionPreviewDialog(
            transcribed_text=text,
            on_insert=insert_text,
        )
        preview.show(page)

    # Components
    voice_button = VoiceInputButtonEnhanced(
        on_text=on_voice_text,
        size=56,
        show_waveform=True,
    )

    voice_status = VoiceStatusIndicator(auto_check=True)

    # Layout
    page.add(
        ft.Row([
            ft.Container(content=notes_field, expand=True),
            voice_button,
        ])
    )

ft.app(target=main)
```

## Usage Flow

### For Doctor

1. **First Time Setup**:
   - App checks voice status automatically
   - If model not downloaded, shows download button
   - One-click download with progress bar
   - Model cached locally (~142MB for base)

2. **During Consultation**:
   - Click microphone button (turns red)
   - Speak clinical notes naturally
   - Watch waveform animation (confirms recording)
   - Click again to stop (turns blue "Processing...")
   - Review transcription in preview dialog
   - Edit if needed, click "Insert"
   - Text appears in clinical notes field

3. **Keyboard Shortcut**:
   - Press `Ctrl+M` to toggle recording (if implemented)

## Troubleshooting

### "Voice Not Available" Error

**Possible causes:**
1. Missing dependencies
2. No microphone detected
3. Permissions not granted

**Solutions:**
```bash
# Install dependencies
pip install faster-whisper sounddevice numpy

# Check microphone
python -c "import sounddevice; print(sounddevice.query_devices())"

# Grant microphone permissions (macOS)
# System Preferences → Security & Privacy → Microphone
```

### "Model Download Failed" Error

**Solutions:**
1. Check internet connection
2. Ensure sufficient disk space (~200MB)
3. Try manual download:
   ```python
   from src.services.voice.whisper_manager import get_whisper_manager
   manager = get_whisper_manager()
   manager.preload_model_async("base")
   ```

### Poor Transcription Quality

**Improvements:**
1. Use better microphone (USB recommended)
2. Reduce background noise
3. Speak clearly and at moderate pace
4. Use `small` or `medium` model for better accuracy
5. Position mic 6-12 inches from mouth

### High Memory Usage

**Solutions:**
1. Use `tiny` model (uses ~1GB RAM)
2. Close other applications
3. Unload model after use:
   ```python
   manager.unload_model()
   ```

## Testing

Run integration tests:

```bash
# All tests
pytest tests/test_voice_integration.py -v

# Specific test
pytest tests/test_voice_integration.py::TestWhisperManager::test_model_loading -v

# Skip tests if dependencies unavailable
pytest tests/test_voice_integration.py -v --skip-missing
```

## Performance

### Benchmarks (base model on typical laptop)

| Metric | Value |
|--------|-------|
| Model load time | 2-5 seconds |
| Transcription speed | ~3x real-time |
| 10 second audio | ~3 seconds to transcribe |
| RAM usage | ~1.5GB |
| CPU usage | 50-80% during transcription |

### Optimization Tips

1. **Preload model on app start**:
   ```python
   # In app initialization
   manager = get_whisper_manager()
   manager.preload_model_async("base")
   ```

2. **Use faster-whisper**:
   - 2-3x faster than openai-whisper
   - Lower memory footprint
   - Better CPU optimization

3. **Adjust model size**:
   - Use `tiny` for faster transcription
   - Use `base` for good balance
   - Use `small` only if accuracy critical

## Privacy & Security

### Local Processing
- ✅ All audio processing happens on-device
- ✅ No audio data sent to cloud
- ✅ No internet connection required (after model download)
- ✅ Complete HIPAA/patient data compliance

### Data Storage
- Audio: Not stored (processed in RAM only)
- Models: Cached in `models/whisper/` directory
- Transcriptions: Stored in local SQLite database (encrypted at rest)

### Permissions
- Microphone: Required for recording
- Disk: Required for model caching
- Network: Only for initial model download (optional)

## Future Enhancements

### Planned Features
- [ ] Hindi/Hinglish language support
- [ ] Custom medical vocabulary fine-tuning
- [ ] Real-time streaming transcription
- [ ] Speaker diarization (identify speakers)
- [ ] Automatic punctuation and formatting
- [ ] Voice commands ("new line", "period", etc.) - partially implemented

### Advanced Features (Phase 2)
- [ ] GPU acceleration for faster transcription
- [ ] Multi-language detection and switching
- [ ] Medical abbreviation expansion
- [ ] ICD-10 code suggestions from voice
- [ ] Ambient listening mode (hands-free)

## Support

### Documentation
- Main README: `/README.md`
- Architecture: `/docs/ARCHITECTURE.md`
- This file: `/docs/VOICE_INTEGRATION.md`

### Example Code
- Basic example: `/examples/voice_integration_example.py`
- Tests: `/tests/test_voice_integration.py`

### Getting Help
1. Check troubleshooting section above
2. Run diagnostic:
   ```python
   from src.services.voice import get_whisper_manager, get_audio_processor

   wm = get_whisper_manager()
   print(wm.get_installation_instructions())

   ap = get_audio_processor()
   print(ap.test_microphone())
   ```
3. Open GitHub issue with diagnostic output

## Credits

- **Whisper**: OpenAI's speech recognition model
- **faster-whisper**: Optimized inference by Guillaume Klein
- **sounddevice**: PortAudio wrapper by Matthias Geier
- **Flet**: UI framework by Appveyor Systems Inc.
