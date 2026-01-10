"""Voice capture and speech-to-text services for ambient clinical intelligence"""

from .voice_capture import VoiceCaptureEngine, AudioConfig
from .speech_to_text import SpeechToText
from .language_detector import LanguageDetector
from .whisper_manager import WhisperManager, get_whisper_manager
from .audio_processor import AudioProcessor, get_audio_processor, AudioFormat

# Voice availability check
_voice_available = False
try:
    import sounddevice
    _voice_available = True
except ImportError:
    pass

def is_voice_available() -> bool:
    """Check if voice input is available."""
    return _voice_available

# Lazy voice service singleton
_voice_service = None

def get_voice_service(model_size: str = "tiny"):
    """Get voice service - returns whisper manager for transcription."""
    global _voice_service
    if _voice_service is None:
        _voice_service = get_whisper_manager(model_size)
    return _voice_service

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
    "is_voice_available",
    "get_voice_service",
]
