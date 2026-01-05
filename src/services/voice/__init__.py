"""Voice capture and speech-to-text services for ambient clinical intelligence"""

from .voice_capture import VoiceCaptureEngine, AudioConfig
from .speech_to_text import SpeechToText
from .language_detector import LanguageDetector
from .whisper_manager import WhisperManager, get_whisper_manager
from .audio_processor import AudioProcessor, get_audio_processor, AudioFormat

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
]
