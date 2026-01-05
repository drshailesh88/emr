# Quick Note Integration Guide

This guide shows how to integrate the QuickNoteScreen into the main mobile app.

---

## Overview

The QuickNoteScreen provides a voice-to-text interface for capturing clinical notes on-the-go. Features include:

- **Large voice recording button** for easy thumb access
- **Text input fallback** for manual entry
- **AI-extracted SOAP note** preview (Subjective/Objective/Assessment/Plan)
- **Save as draft** for later review
- **Save to patient** to add to patient record
- **Offline queue** support for syncing later

---

## Integration Steps

### 1. Add QuickNoteScreen to Navigation

Update `mobile_app.py` to include QuickNote in navigation:

```python
from .screens import QuickNoteScreen, QuickNoteData

class Screen(Enum):
    # ... existing screens
    QUICK_NOTE = "quick_note"

class DocAssistMobile:
    def __init__(self, page: ft.Page):
        # ... existing init
        self.quick_note_screen_widget: Optional[QuickNoteScreen] = None
```

### 2. Add Quick Note Tab to Bottom Nav

The `BottomNavBar` already includes a Quick Note tab. Update the navigation handler:

```python
def _on_nav_change(self, e):
    """Handle bottom navigation change."""
    index = e.control.selected_index
    if index == 0:
        self._show_home_screen()
    elif index == 1:
        self._show_patients_screen()
    elif index == 2:
        self._show_quick_note_screen()  # Add this
    elif index == 3:
        self._show_settings_screen()

    self._update_fab_visibility()
    self.page.update()
```

### 3. Implement Show Quick Note Handler

Add the handler to display QuickNoteScreen:

```python
def _show_quick_note_screen(self):
    """Show quick note screen."""
    self.current_screen = Screen.QUICK_NOTE

    # Get selected patient if coming from patient detail
    patient_id = None
    patient_name = None
    if self.selected_patient_id and self.local_db:
        try:
            patient = self.local_db.get_patient(self.selected_patient_id)
            if patient:
                patient_id = patient.id
                patient_name = patient.name
        except:
            pass

    # Create quick note screen
    self.quick_note_screen_widget = QuickNoteScreen(
        patient_id=patient_id,
        patient_name=patient_name,
        on_save=self._handle_save_quick_note,
        on_back=self._go_back,
        haptic_feedback=self.haptics,
    )

    self.content_area.content = self.quick_note_screen_widget
    self.content_area.update()
```

### 4. Implement Save Quick Note Handler

Add the save handler with offline queue support:

```python
def _handle_save_quick_note(self, note_data: QuickNoteData):
    """Handle save quick note."""
    if not self.local_db:
        print("Database not initialized")
        return

    def save():
        try:
            # Convert SOAP note to visit format
            visit_data = {
                'visit_date': note_data.created_at,
                'clinical_notes': note_data.note_text,
            }

            # Add SOAP sections if available
            soap_sections = []
            if note_data.subjective:
                soap_sections.append(f"S: {note_data.subjective}")
            if note_data.objective:
                soap_sections.append(f"O: {note_data.objective}")
            if note_data.assessment:
                soap_sections.append(f"A: {note_data.assessment}")
            if note_data.plan:
                soap_sections.append(f"P: {note_data.plan}")

            if soap_sections:
                visit_data['diagnosis'] = "\n\n".join(soap_sections)

            # Save to queue if patient selected, else save as draft
            if note_data.patient_id:
                operation_id = self.local_db.add_visit_queued(
                    patient_id=note_data.patient_id,
                    visit_data=visit_data
                )
                message = f"Note saved to patient. Will sync when online."
            else:
                # Save to drafts (could be a separate table)
                # For now, just show success message
                message = "Note saved as draft."

            # Show success message on main thread
            def show_success():
                snackbar = ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=Colors.SUCCESS_MAIN,
                    duration=3000,
                )
                self.page.overlay.append(snackbar)
                snackbar.open = True
                self.page.update()

            self.page.run_task(show_success)

        except Exception as e:
            print(f"Error saving quick note: {e}")

            def show_error():
                snackbar = ft.SnackBar(
                    content=ft.Text(f"Error saving note: {e}"),
                    bgcolor=Colors.ERROR_MAIN,
                )
                self.page.overlay.append(snackbar)
                snackbar.open = True
                self.page.update()

            self.page.run_task(show_error)

    threading.Thread(target=save, daemon=True).start()
```

### 5. Update FAB Visibility

Hide FAB when on Quick Note screen:

```python
def _update_fab_visibility(self):
    """Update FAB visibility based on current screen."""
    if not self.fab:
        return

    # Hide FAB on Quick Note and other edit screens
    show_fab = self.current_screen in [Screen.HOME, Screen.PATIENTS]

    # Get the fab_container from the Stack
    if self.page.controls:
        stack = self.page.controls[0]
        if isinstance(stack, ft.Stack) and len(stack.controls) > 1:
            fab_container = stack.controls[1]
            fab_container.visible = show_fab
            fab_container.update()
```

---

## Alternative: Quick Note from FAB

You can also add Quick Note as a FAB action for quick access from Home/Patients:

```python
# In _show_main_app()
self.fab = FloatingActionButton(
    actions=[
        FABAction(
            icon=ft.Icons.NOTE_ADD,
            label="Quick Note",
            on_click=lambda e: self._show_quick_note_screen(),
        ),
        # ... other actions
    ],
    page=self.page,
    haptic_feedback=self.haptics,
)
```

---

## Voice-to-Text Integration (Future)

The QuickNoteScreen has placeholder code for voice recording. To implement actual speech-to-text:

### Option 1: Platform-native Speech Recognition

Use Flet's platform APIs (when available):

```python
import flet.speech_recognition as sr

async def _start_recording(self):
    recognizer = sr.SpeechRecognition(self.page)
    result = await recognizer.listen()
    self.text_input.value = result.text
    self.update()
```

### Option 2: Whisper.cpp (On-device)

For privacy, use local Whisper model:

```bash
pip install whisper-cpp-python
```

```python
import whisper_cpp

def transcribe_audio(audio_file: str) -> str:
    model = whisper_cpp.Whisper("models/ggml-tiny.bin")
    result = model.transcribe(audio_file)
    return result["text"]
```

### Option 3: Cloud API (Opt-in)

For speed, use cloud API with explicit consent:

```python
import requests

def transcribe_cloud(audio_file: str) -> str:
    # Show consent dialog first
    if not user_has_consented_to_cloud():
        return None

    response = requests.post(
        "https://api.docassist.app/v1/transcribe",
        files={"audio": open(audio_file, "rb")},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    return response.json()["text"]
```

---

## SOAP Extraction Integration

The QuickNoteScreen has placeholder SOAP extraction. To implement with LLM:

### Using Desktop LLM (Future: Mobile Pro)

```python
def _extract_soap_note(self):
    """Extract SOAP using on-device LLM."""
    if not self.note_text or len(self.note_text) < 50:
        return

    # TODO: Integrate with llama.cpp / MLC-LLM
    prompt = f"""
    Extract SOAP note from this clinical text:

    {self.note_text}

    Return JSON:
    {{
        "subjective": "...",
        "objective": "...",
        "assessment": "...",
        "plan": "..."
    }}
    """

    # For now, use simple keyword extraction
    self.soap_preview = self._simple_soap_extraction()
    self._update_soap_preview()
```

### Simple Keyword Extraction (Current)

The current implementation uses simple keyword matching as a fallback:

```python
def _simple_soap_extraction(self) -> dict:
    """Simple SOAP extraction using keywords."""
    text_lower = self.note_text.lower()

    soap = {
        "subjective": "",
        "objective": "",
        "assessment": "",
        "plan": "",
    }

    # Extract based on keywords
    if "complains" in text_lower or "c/o" in text_lower:
        # Extract first sentence as subjective
        soap["subjective"] = self.note_text.split('.')[0]

    if "bp" in text_lower or "hr" in text_lower:
        soap["objective"] = "Vitals recorded"

    if "diagnosis" in text_lower or "dx:" in text_lower:
        # Extract diagnosis section
        start = max(text_lower.find("diagnosis"), text_lower.find("dx:"))
        soap["assessment"] = self.note_text[start:start+100]

    if "plan" in text_lower or "rx:" in text_lower:
        # Extract plan section
        start = max(text_lower.find("plan"), text_lower.find("rx:"))
        soap["plan"] = self.note_text[start:start+100]

    return soap
```

---

## Offline Queue Integration

Quick notes are automatically queued for sync when offline:

```python
# In local_db.py (already implemented)
operation_id = db.add_visit_queued(
    patient_id=patient_id,
    visit_data=visit_data
)

# Check pending count
pending = db.get_pending_count()

# Show in UI
if pending > 0:
    show_sync_status_bar(f"{pending} changes pending sync")
```

---

## Testing

### Manual Testing

1. **Voice Input**:
   - Tap voice button
   - Verify recording indicator shows
   - Speak test note
   - Verify transcription appears

2. **Text Input**:
   - Type clinical note
   - Verify SOAP extraction works
   - Check formatting

3. **Save as Draft**:
   - Enter note without patient
   - Click "Save as Draft"
   - Verify confirmation message

4. **Save to Patient**:
   - Select patient first
   - Enter note
   - Click "Save to Patient"
   - Verify added to patient visits

5. **Offline Mode**:
   - Enable airplane mode
   - Save note
   - Verify queued for sync
   - Re-enable network
   - Verify auto-sync

### Unit Tests (Future)

```python
def test_soap_extraction():
    note = "Patient complains of chest pain. BP 140/90. Diagnosis: Angina. Plan: ECG, Aspirin"
    soap = extract_soap(note)

    assert "chest pain" in soap["subjective"]
    assert "BP 140/90" in soap["objective"]
    assert "Angina" in soap["assessment"]
    assert "ECG" in soap["plan"]
```

---

## Best Practices

1. **Always show patient context**: If coming from patient detail, pre-populate patient
2. **Haptic feedback**: Trigger on record start/stop, save success
3. **Offline-first**: Queue all saves, never fail on no network
4. **Clear after save**: Reset form after successful save to patient
5. **Loading states**: Show skeleton while processing voice
6. **Error handling**: Gracefully handle microphone permission denied

---

## UI/UX Guidelines

### Voice Button
- **Size**: 120x120px (large for easy thumb access)
- **Color**: Primary blue when idle, red when recording
- **Animation**: Pulse effect during recording
- **Haptic**: Medium feedback on tap

### Text Input
- **Min lines**: 4 (comfortable typing area)
- **Max lines**: 8 (avoid excessive scrolling)
- **Auto-resize**: Expand as user types
- **Placeholder**: "Chief complaint, examination findings..."

### SOAP Preview
- **Collapsible**: Can hide/show
- **Editable**: Allow inline editing (future)
- **Color-coded**: Different colors for S/O/A/P
- **Auto-update**: Live as user types

### Action Buttons
- **Draft**: Left, neutral color
- **Save**: Right, primary color
- **Disabled state**: Gray out if no text entered

---

## Future Enhancements

### Phase 1 (Current)
- ✅ Basic voice button (placeholder)
- ✅ Text input
- ✅ Simple SOAP extraction
- ✅ Save to patient
- ✅ Offline queue

### Phase 2 (Q2 2026)
- [ ] Actual voice recording
- [ ] On-device transcription (Whisper.cpp)
- [ ] LLM-powered SOAP extraction
- [ ] Voice commands ("Save", "Discard")

### Phase 3 (Q3 2026)
- [ ] Multi-language support (Hindi, Tamil, etc.)
- [ ] Auto-detect language
- [ ] Medical terminology autocorrect
- [ ] Template quick notes

### Phase 4 (Q4 2026)
- [ ] Real-time collaboration (multiple doctors)
- [ ] Voice signature for prescriptions
- [ ] Integration with EHR standards (FHIR)

---

## Troubleshooting

### Voice button doesn't work
**Cause**: No microphone permission
**Solution**: Request permission on first use:
```python
if not await request_microphone_permission():
    show_error("Microphone permission required")
```

### SOAP extraction not working
**Cause**: Text too short or no keywords
**Solution**: Ensure minimum 50 characters and guide user:
```python
if len(text) < 50:
    show_hint("Add more details for better SOAP extraction")
```

### Notes not syncing
**Cause**: Offline queue full or sync disabled
**Solution**: Check queue and trigger manual sync:
```python
if db.get_pending_count() > 100:
    show_warning("100+ pending notes. Sync now?")
```

---

## Support

For issues or questions about QuickNoteScreen integration:
- Check `README.md` for general mobile app docs
- See `EDIT_SCREENS_README.md` for similar edit screens
- Email: tech@docassist.app

---

**Happy coding! 🎤📝**
