"""On-device Whisper integration for speech recognition"""
from typing import Generator, Optional, Callable
import numpy as np
import os
import logging
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


class SpeechToText:
    """On-device speech-to-text using Whisper"""

    MODELS = {
        "tiny": "ggml-tiny.bin",      # ~75MB, fastest
        "base": "ggml-base.bin",      # ~142MB, good balance
        "small": "ggml-small.bin",    # ~466MB, more accurate
    }

    MODEL_URLS = {
        "tiny": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
        "base": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
        "small": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
    }

    def __init__(self, model_size: str = "base", model_dir: str = "models"):
        """Initialize Whisper model - download if not present"""
        self.model_size = model_size
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.model_path = self.model_dir / self.MODELS[model_size]
        self.model = None
        self.whisper_cpp = None
        self.openai_whisper = None

        # Try to initialize model
        self._init_model()

    def _init_model(self):
        """Initialize Whisper model (try whisper.cpp first, fallback to openai-whisper)"""
        try:
            # Try whispercpp first (faster inference)
            from whispercpp import Whisper

            if not self.is_model_downloaded():
                logger.warning(f"Model {self.model_size} not found, will download on first use")
                return

            self.whisper_cpp = Whisper.from_pretrained(str(self.model_path))
            logger.info(f"Loaded whisper.cpp model: {self.model_size}")

        except ImportError:
            logger.warning("whispercpp not available, trying openai-whisper")
            try:
                import whisper

                # OpenAI Whisper uses model names differently
                model_name = self.model_size
                self.openai_whisper = whisper.load_model(model_name)
                logger.info(f"Loaded OpenAI Whisper model: {model_name}")

            except ImportError:
                logger.error("No Whisper implementation available (whispercpp or openai-whisper)")
                logger.info("Install with: pip install openai-whisper")

    def transcribe(self, audio: bytes, language: str = "auto") -> str:
        """Transcribe audio bytes to text"""
        if not self.whisper_cpp and not self.openai_whisper:
            logger.error("No Whisper model loaded")
            return "[Whisper model not available - install openai-whisper or whispercpp]"

        try:
            # Convert audio bytes to appropriate format
            if self.whisper_cpp:
                return self._transcribe_whispercpp(audio, language)
            else:
                return self._transcribe_openai(audio, language)
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return f"[Transcription error: {str(e)}]"

    def _transcribe_whispercpp(self, audio: bytes, language: str) -> str:
        """Transcribe using whisper.cpp"""
        try:
            # Convert bytes to numpy array (assuming 16-bit PCM)
            audio_array = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0

            # Whisper.cpp expects 16kHz mono
            result = self.whisper_cpp.transcribe(audio_array)
            return result.strip()
        except Exception as e:
            logger.error(f"whisper.cpp transcription error: {e}")
            return f"[Error: {str(e)}]"

    def _transcribe_openai(self, audio: bytes, language: str) -> str:
        """Transcribe using OpenAI Whisper"""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0

            # OpenAI Whisper expects float32 audio at 16kHz
            lang_code = None if language == "auto" else language

            result = self.openai_whisper.transcribe(
                audio_array,
                language=lang_code,
                fp16=False  # Use FP32 for CPU
            )

            return result["text"].strip()
        except Exception as e:
            logger.error(f"OpenAI Whisper transcription error: {e}")
            return f"[Error: {str(e)}]"

    def transcribe_streaming(self, audio_stream) -> Generator[str, None, None]:
        """Real-time transcription with streaming output"""
        # Note: True streaming requires more complex implementation
        # For now, we'll transcribe segments as they come
        logger.warning("Streaming transcription not fully implemented, using batch mode")

        for audio_chunk in audio_stream:
            text = self.transcribe(audio_chunk)
            if text and not text.startswith("["):
                yield text

    def detect_language(self, audio: bytes) -> str:
        """Detect spoken language (hi, en, or hi-en for code-mixed)"""
        if not self.openai_whisper:
            logger.warning("Language detection requires OpenAI Whisper")
            return "auto"

        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0

            # Detect language using Whisper's built-in detection
            audio_array = self.openai_whisper.pad_or_trim(audio_array)
            mel = self.openai_whisper.log_mel_spectrogram(audio_array).to(self.openai_whisper.device)
            _, probs = self.openai_whisper.detect_language(mel)

            detected_lang = max(probs, key=probs.get)

            # Check if it's code-mixed (both Hindi and English have reasonable probability)
            if detected_lang == "hi" and probs.get("en", 0) > 0.2:
                return "hi-en"
            elif detected_lang == "en" and probs.get("hi", 0) > 0.2:
                return "hi-en"

            return detected_lang
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return "auto"

    def is_model_downloaded(self) -> bool:
        """Check if model is available locally"""
        if self.openai_whisper:
            # OpenAI Whisper downloads automatically
            return True

        return self.model_path.exists() and self.model_path.stat().st_size > 1000000

    def download_model(self, progress_callback: Optional[Callable] = None):
        """Download model with progress callback"""
        if self.is_model_downloaded():
            logger.info("Model already downloaded")
            return

        try:
            import urllib.request

            url = self.MODEL_URLS[self.model_size]
            logger.info(f"Downloading {self.model_size} model from {url}")

            def report_progress(block_num, block_size, total_size):
                if progress_callback:
                    downloaded = block_num * block_size
                    percent = min(100, (downloaded / total_size) * 100)
                    progress_callback(percent, downloaded, total_size)

            urllib.request.urlretrieve(url, self.model_path, reporthook=report_progress)
            logger.info(f"Model downloaded to {self.model_path}")

            # Reinitialize model
            self._init_model()

        except Exception as e:
            logger.error(f"Error downloading model: {e}")
            raise
