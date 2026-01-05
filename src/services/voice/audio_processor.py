"""Audio processor - handles microphone input and converts to Whisper format."""

import numpy as np
import logging
from typing import Optional, Callable
import threading
from queue import Queue, Empty
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AudioFormat:
    """Audio format specification."""

    sample_rate: int = 16000  # Whisper expects 16kHz
    channels: int = 1  # Mono
    dtype: str = "float32"  # Whisper expects float32
    chunk_duration_s: float = 3.0  # 3 seconds per chunk


class AudioProcessor:
    """Handles audio recording and format conversion for Whisper."""

    def __init__(self, audio_format: AudioFormat = None):
        """Initialize audio processor.

        Args:
            audio_format: Audio format specification
        """
        self.format = audio_format or AudioFormat()
        self.is_recording = False
        self.audio_queue = Queue()
        self.recording_thread: Optional[threading.Thread] = None
        self.on_audio_chunk: Optional[Callable[[np.ndarray], None]] = None
        self._stop_event = threading.Event()

        # Audio backend
        self.audio_backend = self._detect_audio_backend()

    def _detect_audio_backend(self) -> str:
        """Detect available audio backend."""
        # Try sounddevice first (cross-platform, recommended)
        try:
            import sounddevice as sd

            logger.info("Using sounddevice for audio capture")
            return "sounddevice"
        except ImportError:
            logger.debug("sounddevice not available")

        # Fall back to pyaudio
        try:
            import pyaudio

            logger.info("Using pyaudio for audio capture")
            return "pyaudio"
        except ImportError:
            logger.warning("No audio backend available")
            return None

    def is_available(self) -> bool:
        """Check if audio capture is available."""
        return self.audio_backend is not None

    def get_installation_instructions(self) -> str:
        """Get instructions for installing audio dependencies."""
        if self.audio_backend:
            return "Audio capture is available"

        return "Audio capture requires sounddevice. Install with: pip install sounddevice numpy"

    def start_recording(self, on_audio_chunk: Callable[[np.ndarray], None]):
        """Start recording audio.

        Args:
            on_audio_chunk: Callback with audio chunk (numpy float32 array, 16kHz, mono)
        """
        if self.is_recording:
            logger.warning("Already recording")
            return

        if not self.is_available():
            logger.error("Audio capture not available")
            return

        self.on_audio_chunk = on_audio_chunk
        self._stop_event.clear()
        self.is_recording = True

        # Start recording thread
        self.recording_thread = threading.Thread(
            target=self._recording_loop, daemon=True
        )
        self.recording_thread.start()

        logger.info("Started audio recording")

    def stop_recording(self):
        """Stop recording audio."""
        if not self.is_recording:
            return

        self._stop_event.set()
        self.is_recording = False

        # Wait for thread to finish
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)

        logger.info("Stopped audio recording")

    def _recording_loop(self):
        """Main recording loop."""
        if self.audio_backend == "sounddevice":
            self._record_sounddevice()
        elif self.audio_backend == "pyaudio":
            self._record_pyaudio()

    def _record_sounddevice(self):
        """Record using sounddevice."""
        try:
            import sounddevice as sd

            chunk_samples = int(self.format.sample_rate * self.format.chunk_duration_s)
            audio_buffer = []

            def audio_callback(indata, frames, time, status):
                """Called for each audio chunk."""
                if status:
                    logger.warning(f"Audio callback status: {status}")

                if not self._stop_event.is_set():
                    # Convert to mono if needed
                    if indata.shape[1] > 1:
                        mono = np.mean(indata, axis=1)
                    else:
                        mono = indata[:, 0]

                    audio_buffer.append(mono)

                    # Check if we have enough for a chunk
                    total_samples = sum(len(chunk) for chunk in audio_buffer)
                    if total_samples >= chunk_samples:
                        # Concatenate and emit
                        full_chunk = np.concatenate(audio_buffer)
                        audio_buffer.clear()

                        # Ensure correct format (float32, normalized to -1.0 to 1.0)
                        if full_chunk.dtype != np.float32:
                            full_chunk = full_chunk.astype(np.float32)

                        # Emit chunk
                        if self.on_audio_chunk:
                            try:
                                self.on_audio_chunk(full_chunk)
                            except Exception as e:
                                logger.error(f"Error in audio callback: {e}")

            # Open stream
            with sd.InputStream(
                samplerate=self.format.sample_rate,
                channels=self.format.channels,
                dtype=self.format.dtype,
                blocksize=chunk_samples,
                callback=audio_callback,
            ):
                # Wait until stop is requested
                while not self._stop_event.is_set():
                    sd.sleep(100)

                # Process remaining buffer
                if audio_buffer and self.on_audio_chunk:
                    remaining = np.concatenate(audio_buffer)
                    if len(remaining) > self.format.sample_rate:  # At least 1 second
                        if remaining.dtype != np.float32:
                            remaining = remaining.astype(np.float32)
                        self.on_audio_chunk(remaining)

        except Exception as e:
            logger.error(f"sounddevice recording error: {e}")

    def _record_pyaudio(self):
        """Record using pyaudio (fallback)."""
        try:
            import pyaudio

            p = pyaudio.PyAudio()

            # Calculate chunk size
            chunk_samples = int(self.format.sample_rate * self.format.chunk_duration_s)

            # Open stream
            stream = p.open(
                format=pyaudio.paFloat32,
                channels=self.format.channels,
                rate=self.format.sample_rate,
                input=True,
                frames_per_buffer=chunk_samples,
            )

            try:
                while not self._stop_event.is_set():
                    # Read chunk
                    data = stream.read(chunk_samples, exception_on_overflow=False)

                    # Convert bytes to numpy array
                    audio_array = np.frombuffer(data, dtype=np.float32)

                    # Emit chunk
                    if self.on_audio_chunk:
                        try:
                            self.on_audio_chunk(audio_array)
                        except Exception as e:
                            logger.error(f"Error in audio callback: {e}")

            finally:
                stream.stop_stream()
                stream.close()
                p.terminate()

        except Exception as e:
            logger.error(f"pyaudio recording error: {e}")

    def convert_to_whisper_format(self, audio_data: np.ndarray) -> np.ndarray:
        """Convert audio to Whisper-compatible format.

        Args:
            audio_data: Input audio (any format)

        Returns:
            Audio as float32, 16kHz, mono, normalized to -1.0 to 1.0
        """
        # Ensure float32
        if audio_data.dtype != np.float32:
            if audio_data.dtype == np.int16:
                # Convert int16 to float32 (-1.0 to 1.0)
                audio_data = audio_data.astype(np.float32) / 32768.0
            else:
                audio_data = audio_data.astype(np.float32)

        # Ensure mono
        if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Normalize if needed
        max_val = np.abs(audio_data).max()
        if max_val > 1.0:
            audio_data = audio_data / max_val

        return audio_data

    def calculate_audio_level(self, audio_data: np.ndarray) -> float:
        """Calculate audio level for visualization.

        Args:
            audio_data: Audio array

        Returns:
            Audio level from 0.0 to 1.0
        """
        try:
            # Calculate RMS
            rms = np.sqrt(np.mean(audio_data**2))
            # Normalize (assuming max reasonable RMS is 0.3)
            level = min(1.0, rms / 0.3)
            return level
        except Exception as e:
            logger.error(f"Error calculating audio level: {e}")
            return 0.0

    def has_speech(self, audio_data: np.ndarray, threshold: float = 0.01) -> bool:
        """Simple energy-based speech detection.

        Args:
            audio_data: Audio array
            threshold: Energy threshold for speech detection

        Returns:
            True if audio likely contains speech
        """
        try:
            energy = np.sqrt(np.mean(audio_data**2))
            return energy > threshold
        except Exception as e:
            logger.error(f"Error in speech detection: {e}")
            return False

    def test_microphone(self) -> dict:
        """Test microphone and return info.

        Returns:
            Dictionary with test results
        """
        if not self.is_available():
            return {
                "available": False,
                "error": self.get_installation_instructions(),
            }

        try:
            if self.audio_backend == "sounddevice":
                import sounddevice as sd

                devices = sd.query_devices()
                default_input = sd.query_devices(kind="input")

                return {
                    "available": True,
                    "backend": "sounddevice",
                    "default_device": default_input["name"],
                    "sample_rate": default_input["default_samplerate"],
                    "channels": default_input["max_input_channels"],
                }
            elif self.audio_backend == "pyaudio":
                import pyaudio

                p = pyaudio.PyAudio()
                try:
                    default_input = p.get_default_input_device_info()
                    return {
                        "available": True,
                        "backend": "pyaudio",
                        "default_device": default_input["name"],
                        "sample_rate": default_input["defaultSampleRate"],
                        "channels": default_input["maxInputChannels"],
                    }
                finally:
                    p.terminate()

        except Exception as e:
            return {
                "available": False,
                "error": str(e),
            }

    def list_devices(self) -> list:
        """List available audio input devices.

        Returns:
            List of device info dictionaries
        """
        if not self.is_available():
            return []

        try:
            if self.audio_backend == "sounddevice":
                import sounddevice as sd

                devices = sd.query_devices()
                return [
                    {
                        "index": i,
                        "name": dev["name"],
                        "channels": dev["max_input_channels"],
                    }
                    for i, dev in enumerate(devices)
                    if dev["max_input_channels"] > 0
                ]
            elif self.audio_backend == "pyaudio":
                import pyaudio

                p = pyaudio.PyAudio()
                try:
                    device_list = []
                    for i in range(p.get_device_count()):
                        dev = p.get_device_info_by_index(i)
                        if dev["maxInputChannels"] > 0:
                            device_list.append(
                                {
                                    "index": i,
                                    "name": dev["name"],
                                    "channels": dev["maxInputChannels"],
                                }
                            )
                    return device_list
                finally:
                    p.terminate()

        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            return []


# Global instance
_audio_processor: Optional[AudioProcessor] = None


def get_audio_processor() -> AudioProcessor:
    """Get global AudioProcessor instance."""
    global _audio_processor
    if _audio_processor is None:
        _audio_processor = AudioProcessor()
    return _audio_processor
