"""Whisper model manager with download, caching, and progress tracking."""

import os
import logging
from pathlib import Path
from typing import Optional, Callable, Tuple
import threading
import urllib.request
import hashlib

logger = logging.getLogger(__name__)


class WhisperManager:
    """Manages Whisper models with automatic downloading and caching."""

    # Model configurations
    MODELS = {
        "tiny": {
            "faster_whisper": "tiny",
            "openai_whisper": "tiny",
            "size_mb": 75,
            "description": "Fastest, least accurate",
        },
        "base": {
            "faster_whisper": "base",
            "openai_whisper": "base",
            "size_mb": 142,
            "description": "Good balance of speed and accuracy",
        },
        "small": {
            "faster_whisper": "small",
            "openai_whisper": "small",
            "size_mb": 466,
            "description": "More accurate, slower",
        },
        "medium": {
            "faster_whisper": "medium",
            "openai_whisper": "medium",
            "size_mb": 1500,
            "description": "High accuracy, much slower",
        },
    }

    def __init__(self, model_dir: str = "models/whisper", default_model: str = "base"):
        """Initialize Whisper manager.

        Args:
            model_dir: Directory to store models
            default_model: Default model size to use
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.default_model = default_model
        self.current_model = None
        self.model_type: Optional[str] = None  # 'faster_whisper' or 'openai_whisper'
        self._detect_available_backends()

    def _detect_available_backends(self):
        """Detect which Whisper backends are available."""
        # Try faster-whisper first (more efficient)
        try:
            import faster_whisper
            self.model_type = "faster_whisper"
            logger.info("Using faster-whisper backend")
            return
        except ImportError:
            logger.debug("faster-whisper not available")

        # Fall back to openai-whisper
        try:
            import whisper
            self.model_type = "openai_whisper"
            logger.info("Using openai-whisper backend")
            return
        except ImportError:
            logger.warning("No Whisper backend available")
            self.model_type = None

    def is_available(self) -> bool:
        """Check if any Whisper backend is available."""
        return self.model_type is not None

    def get_installation_instructions(self) -> str:
        """Get installation instructions for missing dependencies."""
        if self.model_type:
            return "Whisper is available"

        return (
            "Voice input requires Whisper. Install with:\n"
            "  pip install faster-whisper sounddevice numpy\n"
            "OR\n"
            "  pip install openai-whisper sounddevice numpy"
        )

    def is_model_downloaded(self, model_size: str = None) -> bool:
        """Check if a model is already downloaded and cached.

        Args:
            model_size: Model size to check (uses default if None)

        Returns:
            True if model is available locally
        """
        model_size = model_size or self.default_model

        if self.model_type == "faster_whisper":
            # faster-whisper downloads to cache automatically
            # Check if model cache exists
            cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
            if cache_dir.exists():
                # Look for model files
                model_files = list(cache_dir.glob(f"*{model_size}*"))
                return len(model_files) > 0
            return False
        elif self.model_type == "openai_whisper":
            # openai-whisper downloads to ~/.cache/whisper
            cache_dir = Path.home() / ".cache" / "whisper"
            if cache_dir.exists():
                model_files = list(cache_dir.glob(f"{model_size}.pt"))
                return len(model_files) > 0
            return False

        return False

    def load_model(
        self,
        model_size: str = None,
        on_progress: Optional[Callable[[str, float], None]] = None,
    ) -> Tuple[bool, Optional[object], str]:
        """Load Whisper model, downloading if necessary.

        Args:
            model_size: Model size to load (tiny, base, small, medium)
            on_progress: Callback(status_message, progress_percent)

        Returns:
            Tuple of (success, model_object, error_message)
        """
        model_size = model_size or self.default_model

        if not self.is_available():
            return False, None, self.get_installation_instructions()

        if model_size not in self.MODELS:
            return False, None, f"Invalid model size: {model_size}"

        try:
            if on_progress:
                on_progress(f"Loading {model_size} model...", 0)

            if self.model_type == "faster_whisper":
                model = self._load_faster_whisper(model_size, on_progress)
            else:
                model = self._load_openai_whisper(model_size, on_progress)

            self.current_model = model

            if on_progress:
                on_progress(f"Model {model_size} loaded successfully", 100)

            return True, model, ""

        except Exception as e:
            error_msg = f"Failed to load model: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def _load_faster_whisper(
        self,
        model_size: str,
        on_progress: Optional[Callable[[str, float], None]] = None,
    ) -> object:
        """Load model using faster-whisper."""
        from faster_whisper import WhisperModel

        # faster-whisper downloads automatically on first use
        if on_progress:
            on_progress(f"Initializing faster-whisper {model_size}...", 20)

        # Use int8 quantization for better CPU performance
        model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            download_root=str(self.model_dir),
        )

        if on_progress:
            on_progress(f"faster-whisper {model_size} ready", 100)

        logger.info(f"Loaded faster-whisper model: {model_size}")
        return model

    def _load_openai_whisper(
        self,
        model_size: str,
        on_progress: Optional[Callable[[str, float], None]] = None,
    ) -> object:
        """Load model using openai-whisper."""
        import whisper

        if on_progress:
            on_progress(f"Initializing openai-whisper {model_size}...", 20)

        # openai-whisper downloads automatically
        model = whisper.load_model(model_size, download_root=str(self.model_dir))

        if on_progress:
            on_progress(f"openai-whisper {model_size} ready", 100)

        logger.info(f"Loaded openai-whisper model: {model_size}")
        return model

    def transcribe(
        self,
        audio_data,
        language: str = "en",
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Transcribe audio using the loaded model.

        Args:
            audio_data: Audio array (numpy float32, 16kHz)
            language: Language code (en, hi, etc.)
            on_progress: Status callback

        Returns:
            Transcribed text
        """
        if self.current_model is None:
            logger.error("No model loaded")
            return ""

        try:
            if on_progress:
                on_progress("Transcribing...")

            if self.model_type == "faster_whisper":
                return self._transcribe_faster_whisper(audio_data, language)
            else:
                return self._transcribe_openai_whisper(audio_data, language)

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    def _transcribe_faster_whisper(self, audio_data, language: str) -> str:
        """Transcribe using faster-whisper."""
        segments, _ = self.current_model.transcribe(
            audio_data,
            language=language,
            beam_size=5,
            vad_filter=True,  # Filter silence
        )
        text = " ".join([segment.text for segment in segments])
        return text.strip()

    def _transcribe_openai_whisper(self, audio_data, language: str) -> str:
        """Transcribe using openai-whisper."""
        result = self.current_model.transcribe(
            audio_data,
            language=language,
            fp16=False,  # Use FP32 for CPU
        )
        return result["text"].strip()

    def get_model_info(self, model_size: str = None) -> dict:
        """Get information about a model.

        Args:
            model_size: Model size (uses default if None)

        Returns:
            Dictionary with model information
        """
        model_size = model_size or self.default_model

        if model_size not in self.MODELS:
            return {}

        info = self.MODELS[model_size].copy()
        info["downloaded"] = self.is_model_downloaded(model_size)
        info["backend"] = self.model_type
        info["available"] = self.is_available()

        return info

    def preload_model_async(
        self,
        model_size: str = None,
        on_complete: Optional[Callable[[bool, str], None]] = None,
        on_progress: Optional[Callable[[str, float], None]] = None,
    ):
        """Preload model in background thread.

        Args:
            model_size: Model to load
            on_complete: Callback(success, message)
            on_progress: Callback(status, percent)
        """

        def load_thread():
            success, model, error = self.load_model(model_size, on_progress)
            if on_complete:
                message = "Model loaded successfully" if success else error
                on_complete(success, message)

        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()

    def unload_model(self):
        """Unload current model to free memory."""
        if self.current_model:
            del self.current_model
            self.current_model = None
            logger.info("Model unloaded")

    def get_available_models(self) -> list:
        """Get list of available model sizes."""
        return [
            {
                "size": size,
                "info": self.get_model_info(size),
            }
            for size in self.MODELS.keys()
        ]


# Global instance
_whisper_manager: Optional[WhisperManager] = None


def get_whisper_manager(model_dir: str = "models/whisper") -> WhisperManager:
    """Get global WhisperManager instance."""
    global _whisper_manager
    if _whisper_manager is None:
        _whisper_manager = WhisperManager(model_dir)
    return _whisper_manager
