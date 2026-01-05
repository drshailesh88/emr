"""Voice capture and speech-to-text services for ambient clinical intelligence."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Optional, Callable

from .voice_capture import VoiceCaptureEngine, AudioConfig
from .speech_to_text import SpeechToText
from .language_detector import LanguageDetector
from .whisper_manager import WhisperManager, get_whisper_manager
from .audio_processor import AudioProcessor, get_audio_processor, AudioFormat

logger = logging.getLogger(__name__)


class _NoOpVoiceService:
    """Safe fallback when voice dependencies or models are unavailable."""

    def start_recording(
        self,
        on_transcription: Optional[Callable[[str], None]] = None,
        on_status_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        if on_status_change:
            on_status_change("Voice input not available")

    def stop_recording(self) -> None:
        return


class VoiceInputService:
    """Minimal voice input service used by the UI."""

    def __init__(self, model_size: str = "tiny") -> None:
        self.model_size = model_size
        self._capture: Optional[VoiceCaptureEngine] = None
        self._stt: Optional[SpeechToText] = None
        self._lock = threading.Lock()

    def _ensure_ready(self) -> None:
        with self._lock:
            if self._capture is None:
                self._capture = VoiceCaptureEngine()
            if self._stt is None:
                self._stt = SpeechToText(model_size=self.model_size)

    def start_recording(
        self,
        on_transcription: Optional[Callable[[str], None]] = None,
        on_status_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        try:
            self._ensure_ready()
        except Exception as exc:
            logger.warning("Voice input unavailable: %s", exc)
            if on_status_change:
                on_status_change("Voice input not available")
            return

        if on_status_change:
            on_status_change("Listening...")

        def handle_speech(audio_bytes: bytes) -> None:
            if not self._stt:
                return
            text = self._stt.transcribe(audio_bytes)
            if on_transcription and text:
                on_transcription(text)

        self._capture.on_speech_detected(handle_speech)
        self._capture.start_listening()

    def stop_recording(self) -> None:
        if self._capture:
            self._capture.stop_listening()


_voice_service: Optional[VoiceInputService] = None
_voice_available: Optional[bool] = None


def _audio_backend_available() -> bool:
    try:
        import pyaudio  # noqa: F401
        return True
    except Exception:
        try:
            import sounddevice  # noqa: F401
            return True
        except Exception:
            return False


def _model_available(model_size: str) -> bool:
    try:
        model_name = SpeechToText.MODELS.get(model_size, SpeechToText.MODELS["tiny"])
    except Exception:
        return False
    model_path = Path("models") / model_name
    return model_path.exists()


def get_voice_service(model_size: str = "tiny") -> VoiceInputService:
    """Return a safe voice service (no-op when unavailable)."""
    global _voice_service, _voice_available

    if _voice_service is None:
        if _audio_backend_available() and _model_available(model_size):
            try:
                _voice_service = VoiceInputService(model_size=model_size)
                _voice_available = True
            except Exception as exc:
                logger.warning("Voice service init failed: %s", exc)
                _voice_service = _NoOpVoiceService()
                _voice_available = False
        else:
            _voice_service = _NoOpVoiceService()
            _voice_available = False

    return _voice_service


def is_voice_available() -> bool:
    """Check if voice input is available without initializing the service."""
    global _voice_available
    if _voice_available is None:
        _voice_available = _audio_backend_available() and _model_available("tiny")
    return _voice_available


__all__ = [
    "VoiceCaptureEngine",
    "AudioConfig",
    "SpeechToText",
    "LanguageDetector",
    "WhisperManager",
    "get_whisper_manager",
    "AudioProcessor",
    "get_audio_processor",
    "AudioFormat",
    "VoiceInputService",
    "get_voice_service",
    "is_voice_available",
]
