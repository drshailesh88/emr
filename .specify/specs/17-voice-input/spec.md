# Feature: Voice Input for Clinical Notes

> Hands-free dictation for clinical notes during patient examination

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

Doctors often examine patients while needing to document findings. Typing during examination breaks the patient connection. Voice dictation would allow hands-free documentation.

## User Stories

### Primary User Story
**As a** doctor
**I want to** dictate clinical notes using voice
**So that** I can document while examining the patient

### Additional Stories
- As a doctor, I want voice commands to navigate the app
- As a doctor, I want voice input to handle medical terminology
- As a doctor, I want to see text in real-time as I speak

## Requirements

### Functional Requirements

**Voice Dictation:**
1. **FR-1**: Microphone button to start/stop dictation
2. **FR-2**: Real-time transcription as doctor speaks
3. **FR-3**: Transcription appears in active text field
4. **FR-4**: Support for Indian English accent
5. **FR-5**: Medical terminology recognition

**Voice Commands:**
6. **FR-6**: "New line" / "Next line" - insert line break
7. **FR-7**: "Period" / "Full stop" - insert punctuation
8. **FR-8**: "Delete that" - remove last phrase
9. **FR-9**: "Stop listening" - end dictation

**Offline Speech Recognition:**
10. **FR-10**: Works without internet (local model)
11. **FR-11**: Vosk or Whisper for offline recognition
12. **FR-12**: Option to use online API for better accuracy

### Non-Functional Requirements
1. **NFR-1**: Latency < 500ms for transcription
2. **NFR-2**: Accuracy > 90% for medical terms
3. **NFR-3**: Works on low-end hardware
4. **NFR-4**: Microphone quality indication

## Acceptance Criteria

- [ ] Microphone button visible in notes field
- [ ] Clicking starts listening (visual indicator)
- [ ] Speech appears as text in real-time
- [ ] "Period" inserts full stop
- [ ] "New line" inserts line break
- [ ] Works offline with local model
- [ ] Medical terms transcribed correctly
- [ ] "Stop listening" or button click stops

## Technical Approach

### Option 1: Vosk (Offline, Recommended for MVP)
```python
from vosk import Model, KaldiRecognizer
import pyaudio

model = Model("vosk-model-small-en-in-0.4")  # Indian English
recognizer = KaldiRecognizer(model, 16000)

# Stream audio from microphone
# Process with recognizer
# Output text to UI
```

### Option 2: Whisper (Better accuracy, more RAM)
```python
import whisper
model = whisper.load_model("small")  # ~500MB
# Better accuracy but higher latency
```

### Option 3: Google Speech API (Online, best accuracy)
```python
# Requires internet - use as fallback
from google.cloud import speech
```

## UI Design

### Voice Input Button
```
┌──────────────────────────────────────────────────────────────────┐
│ Clinical Notes:                                                  │
├──────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Patient presents with chest pain radiating to left arm       │ │
│ │ since yesterday evening. Pain is 7/10 in intensity.|        │ │
│ │                                                              │ │
│ │                                                              │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                     [🎤 Start]   │
└──────────────────────────────────────────────────────────────────┘
```

### Listening State
```
┌──────────────────────────────────────────────────────────────────┐
│ Clinical Notes:                                    🔴 Listening  │
├──────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Patient presents with chest pain radiating to left arm       │ │
│ │ since yesterday evening. Pain is 7/10 in intensity.         │ │
│ │ No associated sweating or nausea|                            │ │
│ │                                 ↑ cursor                      │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                     [🛑 Stop]    │
└──────────────────────────────────────────────────────────────────┘
```

## Medical Vocabulary

Custom vocabulary file for common terms:
```
# Cardiology
tachycardia
bradycardia
arrhythmia
myocardial infarction
angina pectoris
hypertension

# Medications
metformin
amlodipine
atorvastatin
aspirin
clopidogrel

# Abbreviations
ECG
ECHO
CBC
LFT
RFT
HbA1c
```

## Out of Scope

- Voice-activated navigation ("Open patient Ram Lal")
- Multiple language support (Hindi dictation)
- Continuous ambient listening
- Transcription of recorded audio files

## Dependencies

- Vosk/Whisper model (~50-500MB)
- PyAudio for microphone access
- FFmpeg for audio processing

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Poor accuracy for accents | Unusable feature | Train on Indian English, allow corrections |
| High CPU/RAM usage | Slow system | Use smallest viable model |
| Microphone access issues | Feature fails | Clear error messages, permission guide |
| Ambient noise | Bad transcription | Noise cancellation, close-talk mic |

## Open Questions

- [x] Vosk vs Whisper? **Decision: Vosk for MVP (lighter), Whisper as upgrade**
- [x] Require internet? **Decision: No, offline-first with online option**
- [x] Model size? **Decision: Small model (~50MB) with option for larger**

---
*Spec created: 2026-01-02*
