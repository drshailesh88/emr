"""Voice input service using local Whisper for offline speech recognition."""

import threading
import queue
import tempfile
import os
from typing import Callable, Optional
from pathlib import Path

# Voice recognition state
_voice_available = False
_whisper_model = None
_audio_available = False

# Try to import required libraries
try:
    import numpy as np
    _numpy_available = True
except ImportError:
    _numpy_available = False

try:
    import sounddevice as sd
    _audio_available = True
except ImportError:
    _audio_available = False

try:
    # Try faster-whisper first (more efficient)
    from faster_whisper import WhisperModel
    _whisper_type = "faster"
    _voice_available = _audio_available and _numpy_available
except ImportError:
    try:
        # Fall back to openai-whisper
        import whisper
        _whisper_type = "openai"
        _voice_available = _audio_available and _numpy_available
    except ImportError:
        _whisper_type = None
        _voice_available = False


# Medical vocabulary for better recognition
MEDICAL_VOCABULARY = [
    # Cardiology
    "tachycardia", "bradycardia", "arrhythmia", "fibrillation", "flutter",
    "myocardial", "infarction", "angina", "pectoris", "hypertension",
    "hypotension", "cardiomyopathy", "pericarditis", "endocarditis",

    # Pulmonology
    "dyspnea", "tachypnea", "bradypnea", "pneumonia", "bronchitis",
    "asthma", "COPD", "emphysema", "pleurisy", "pneumothorax",

    # Gastroenterology
    "dyspepsia", "GERD", "hepatitis", "cirrhosis", "pancreatitis",
    "cholecystitis", "cholelithiasis", "jaundice", "ascites",

    # Neurology
    "headache", "migraine", "vertigo", "syncope", "seizure",
    "neuropathy", "paresthesia", "hemiplegia", "paraplegia",

    # Endocrinology
    "diabetes", "mellitus", "hypoglycemia", "hyperglycemia",
    "thyroid", "hypothyroid", "hyperthyroid", "HbA1c",

    # Common medications
    "metformin", "glimepiride", "insulin", "amlodipine", "telmisartan",
    "atorvastatin", "rosuvastatin", "aspirin", "clopidogrel", "warfarin",
    "omeprazole", "pantoprazole", "metoprolol", "atenolol", "losartan",
    "hydrochlorothiazide", "furosemide", "spironolactone",

    # Lab tests
    "CBC", "hemoglobin", "WBC", "platelet", "creatinine", "urea",
    "sodium", "potassium", "bilirubin", "SGOT", "SGPT", "alkaline",
    "phosphatase", "albumin", "globulin", "TSH", "T3", "T4",
    "ECG", "ECHO", "echocardiogram", "X-ray", "CT", "MRI", "USG",

    # Clinical terms
    "complains", "complaints", "presenting", "history", "examination",
    "inspection", "palpation", "percussion", "auscultation",
    "tenderness", "guarding", "rigidity", "rebound",
    "bilateral", "unilateral", "radiating", "referred",
    "acute", "chronic", "intermittent", "constant",
    "mild", "moderate", "severe", "progressive",

    # Abbreviations (spoken)
    "BP", "blood pressure", "PR", "pulse rate", "RR", "respiratory rate",
    "SpO2", "oxygen saturation", "BMI", "body mass index",
]

# Voice commands for text manipulation
VOICE_COMMANDS = {
    "new line": "\n",
    "next line": "\n",
    "period": ".",
    "full stop": ".",
    "comma": ",",
    "colon": ":",
    "semicolon": ";",
    "question mark": "?",
    "exclamation mark": "!",
    "open bracket": "(",
    "close bracket": ")",
    "hyphen": "-",
    "slash": "/",
}


class VoiceInputService:
    """Service for voice-to-text input using local Whisper."""

    def __init__(self, model_size: str = "tiny"):
        """Initialize voice service.

        Args:
            model_size: Whisper model size - "tiny", "base", "small", "medium"
                       Tiny uses ~75MB RAM, base ~150MB, small ~500MB
        """
        self.model_size = model_size
        self.model = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.processing_thread = None
        self.on_transcription: Optional[Callable[[str], None]] = None
        self.on_status_change: Optional[Callable[[str], None]] = None
        self.sample_rate = 16000
        self._stop_event = threading.Event()

    @property
    def is_available(self) -> bool:
        """Check if voice input is available."""
        return _voice_available

    def get_status_message(self) -> str:
        """Get status message about voice availability."""
        if not _numpy_available:
            return "Voice input requires numpy. Install with: pip install numpy"
        if not _audio_available:
            return "Voice input requires sounddevice. Install with: pip install sounddevice"
        if _whisper_type is None:
            return "Voice input requires whisper. Install with: pip install faster-whisper"
        return "Voice input ready"

    def load_model(self) -> bool:
        """Load the Whisper model. Returns True if successful."""
        global _whisper_model

        if not self.is_available:
            return False

        if _whisper_model is not None:
            self.model = _whisper_model
            return True

        try:
            if self.on_status_change:
                self.on_status_change("Loading voice model...")

            if _whisper_type == "faster":
                # faster-whisper uses different model loading
                self.model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8"  # Use int8 for better CPU performance
                )
            else:
                # openai-whisper
                import whisper
                self.model = whisper.load_model(self.model_size)

            _whisper_model = self.model

            if self.on_status_change:
                self.on_status_change("Voice model ready")

            return True

        except Exception as e:
            if self.on_status_change:
                self.on_status_change(f"Failed to load voice model: {str(e)}")
            return False

    def start_recording(
        self,
        on_transcription: Callable[[str], None],
        on_status_change: Optional[Callable[[str], None]] = None
    ):
        """Start recording and transcribing audio.

        Args:
            on_transcription: Callback with transcribed text
            on_status_change: Callback for status updates
        """
        if self.is_recording:
            return

        if not self.is_available:
            if on_status_change:
                on_status_change(self.get_status_message())
            return

        self.on_transcription = on_transcription
        self.on_status_change = on_status_change

        # Load model if not loaded
        if self.model is None:
            if not self.load_model():
                return

        self._stop_event.clear()
        self.is_recording = True

        # Start recording thread
        self.recording_thread = threading.Thread(target=self._record_audio, daemon=True)
        self.recording_thread.start()

        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_audio, daemon=True)
        self.processing_thread.start()

        if self.on_status_change:
            self.on_status_change("Listening...")

    def stop_recording(self):
        """Stop recording."""
        if not self.is_recording:
            return

        self._stop_event.set()
        self.is_recording = False

        # Clear the queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        if self.on_status_change:
            self.on_status_change("Stopped")

    def _record_audio(self):
        """Record audio from microphone in chunks."""
        try:
            chunk_duration = 3  # seconds per chunk
            chunk_samples = int(self.sample_rate * chunk_duration)

            def audio_callback(indata, frames, time, status):
                if not self._stop_event.is_set():
                    self.audio_queue.put(indata.copy())

            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                blocksize=chunk_samples,
                callback=audio_callback
            ):
                while not self._stop_event.is_set():
                    sd.sleep(100)

        except Exception as e:
            if self.on_status_change:
                self.on_status_change(f"Recording error: {str(e)}")
            self.is_recording = False

    def _process_audio(self):
        """Process audio chunks and transcribe."""
        audio_buffer = []
        min_audio_length = self.sample_rate * 1  # Minimum 1 second

        while not self._stop_event.is_set() or not self.audio_queue.empty():
            try:
                # Get audio chunk with timeout
                chunk = self.audio_queue.get(timeout=0.5)
                audio_buffer.append(chunk)

                # Concatenate buffer
                if audio_buffer:
                    audio_data = np.concatenate(audio_buffer, axis=0).flatten()

                    # Only transcribe if we have enough audio
                    if len(audio_data) >= min_audio_length:
                        # Transcribe
                        text = self._transcribe(audio_data)

                        if text and self.on_transcription:
                            # Process voice commands
                            processed_text = self._process_voice_commands(text)
                            self.on_transcription(processed_text)

                        # Clear buffer after transcription
                        audio_buffer = []

            except queue.Empty:
                # Process remaining buffer on timeout
                if audio_buffer and not self._stop_event.is_set():
                    audio_data = np.concatenate(audio_buffer, axis=0).flatten()
                    if len(audio_data) >= min_audio_length // 2:
                        text = self._transcribe(audio_data)
                        if text and self.on_transcription:
                            processed_text = self._process_voice_commands(text)
                            self.on_transcription(processed_text)
                    audio_buffer = []
            except Exception as e:
                if self.on_status_change:
                    self.on_status_change(f"Processing error: {str(e)}")

    def _transcribe(self, audio_data: np.ndarray) -> str:
        """Transcribe audio data to text."""
        try:
            if _whisper_type == "faster":
                # faster-whisper transcription
                segments, _ = self.model.transcribe(
                    audio_data,
                    language="en",
                    beam_size=5,
                    vad_filter=True,  # Filter out silence
                )
                text = " ".join([segment.text for segment in segments])
            else:
                # openai-whisper transcription
                result = self.model.transcribe(
                    audio_data,
                    language="en",
                    fp16=False,  # Use FP32 for CPU
                )
                text = result["text"]

            return text.strip()

        except Exception as e:
            if self.on_status_change:
                self.on_status_change(f"Transcription error: {str(e)}")
            return ""

    def _process_voice_commands(self, text: str) -> str:
        """Process voice commands in transcribed text."""
        result = text

        # Check for stop command
        lower_text = text.lower()
        if "stop listening" in lower_text or "stop dictation" in lower_text:
            self.stop_recording()
            # Remove the stop command from output
            result = lower_text.replace("stop listening", "").replace("stop dictation", "")

        # Replace voice commands with punctuation/formatting
        for command, replacement in VOICE_COMMANDS.items():
            # Case-insensitive replacement
            import re
            pattern = re.compile(re.escape(command), re.IGNORECASE)
            result = pattern.sub(replacement, result)

        return result.strip()


# Singleton instance
_voice_service: Optional[VoiceInputService] = None


def get_voice_service(model_size: str = "tiny") -> VoiceInputService:
    """Get the voice service singleton."""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceInputService(model_size)
    return _voice_service


def is_voice_available() -> bool:
    """Check if voice input is available."""
    return _voice_available
