"""Continuous voice capture with Voice Activity Detection"""
import threading
import numpy as np
from dataclasses import dataclass
from typing import Callable, Optional, List
from queue import Queue
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration_ms: int = 30
    vad_aggressiveness: int = 2
    silence_threshold_ms: int = 500


class VoiceCaptureEngine:
    """Ambient voice capture with VAD for speech detection"""

    def __init__(self, config: AudioConfig = None):
        """Initialize voice capture engine with VAD"""
        self.config = config or AudioConfig()
        self.is_running = False
        self.audio_queue = Queue()
        self.capture_thread: Optional[threading.Thread] = None
        self.speech_callback: Optional[Callable[[bytes], None]] = None

        # Audio level for visualization
        self.current_audio_level = 0.0
        self.level_lock = threading.Lock()

        # Speech detection state
        self.is_speech_active = False
        self.speech_frames = []
        self.silence_duration = 0

        # Lazy imports for audio capture
        self.pyaudio = None
        self.vad = None
        self.stream = None

        # Initialize components
        self._init_audio()
        self._init_vad()

    def _init_audio(self):
        """Initialize PyAudio for cross-platform audio capture"""
        try:
            import pyaudio
            self.pyaudio = pyaudio.PyAudio()
            logger.info("PyAudio initialized successfully")
        except ImportError:
            logger.warning("PyAudio not available, trying sounddevice as fallback")
            try:
                import sounddevice as sd
                self.sounddevice = sd
                logger.info("Sounddevice initialized successfully")
            except ImportError:
                logger.error("No audio library available (pyaudio or sounddevice)")
                raise RuntimeError("Audio capture requires pyaudio or sounddevice")

    def _init_vad(self):
        """Initialize WebRTC VAD for voice activity detection"""
        try:
            import webrtcvad
            self.vad = webrtcvad.Vad(self.config.vad_aggressiveness)
            logger.info(f"VAD initialized with aggressiveness={self.config.vad_aggressiveness}")
        except ImportError:
            logger.warning("webrtcvad not available, using energy-based detection")
            self.vad = None

    def start_listening(self):
        """Start ambient listening in background thread"""
        if self.is_running:
            logger.warning("Voice capture already running")
            return

        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info("Voice capture started")

    def stop_listening(self):
        """Stop listening and cleanup"""
        if not self.is_running:
            return

        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)

        # Cleanup audio stream
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None

        logger.info("Voice capture stopped")

    def on_speech_detected(self, callback: Callable[[bytes], None]):
        """Set callback for when speech segment is detected"""
        self.speech_callback = callback

    def get_audio_level(self) -> float:
        """Get current audio level for visualization (0.0-1.0)"""
        with self.level_lock:
            return self.current_audio_level

    def _capture_loop(self):
        """Main capture loop running in background thread"""
        try:
            # Calculate frame size
            chunk_size = int(self.config.sample_rate * self.config.chunk_duration_ms / 1000)

            if self.pyaudio:
                # Use PyAudio
                import pyaudio
                self.stream = self.pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=self.config.channels,
                    rate=self.config.sample_rate,
                    input=True,
                    frames_per_buffer=chunk_size
                )
            else:
                # Use sounddevice (fallback)
                logger.info("Using sounddevice for capture")

            while self.is_running:
                try:
                    # Read audio chunk
                    if self.pyaudio and self.stream:
                        audio_data = self.stream.read(chunk_size, exception_on_overflow=False)
                    else:
                        # Sounddevice fallback (simplified)
                        time.sleep(self.config.chunk_duration_ms / 1000)
                        continue

                    # Update audio level for visualization
                    self._update_audio_level(audio_data)

                    # Detect speech
                    is_speech = self._is_speech(audio_data)
                    self._handle_speech_detection(audio_data, is_speech)

                except Exception as e:
                    logger.error(f"Error in capture loop: {e}")
                    time.sleep(0.1)

        except Exception as e:
            logger.error(f"Failed to initialize audio capture: {e}")
        finally:
            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except:
                    pass

    def _update_audio_level(self, audio_data: bytes):
        """Update current audio level from raw audio data"""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            # Calculate RMS level
            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))

            # Normalize to 0.0-1.0 (assuming 16-bit audio)
            level = min(1.0, rms / 3000.0)

            with self.level_lock:
                self.current_audio_level = level
        except Exception as e:
            logger.error(f"Error updating audio level: {e}")

    def _is_speech(self, audio_data: bytes) -> bool:
        """Detect if audio frame contains speech"""
        if self.vad:
            try:
                # WebRTC VAD requires specific sample rates
                return self.vad.is_speech(audio_data, self.config.sample_rate)
            except Exception as e:
                logger.error(f"VAD error: {e}")
                return self._energy_based_detection(audio_data)
        else:
            # Fallback to energy-based detection
            return self._energy_based_detection(audio_data)

    def _energy_based_detection(self, audio_data: bytes) -> bool:
        """Simple energy-based speech detection as fallback"""
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            energy = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
            # Threshold for speech detection (tunable)
            return energy > 500
        except:
            return False

    def _handle_speech_detection(self, audio_data: bytes, is_speech: bool):
        """Handle speech detection state machine"""
        if is_speech:
            # Speech detected
            if not self.is_speech_active:
                logger.debug("Speech started")
                self.is_speech_active = True
                self.speech_frames = []

            self.speech_frames.append(audio_data)
            self.silence_duration = 0
        else:
            # Silence detected
            if self.is_speech_active:
                self.silence_duration += self.config.chunk_duration_ms

                # Continue collecting frames for a bit of trailing silence
                if self.silence_duration < self.config.silence_threshold_ms:
                    self.speech_frames.append(audio_data)
                else:
                    # End of speech segment
                    logger.debug(f"Speech ended ({len(self.speech_frames)} frames)")
                    self._emit_speech_segment()
                    self.is_speech_active = False
                    self.speech_frames = []
                    self.silence_duration = 0

    def _emit_speech_segment(self):
        """Emit collected speech segment to callback"""
        if self.speech_callback and self.speech_frames:
            try:
                # Concatenate all frames
                full_audio = b''.join(self.speech_frames)
                self.speech_callback(full_audio)
            except Exception as e:
                logger.error(f"Error in speech callback: {e}")

    def __del__(self):
        """Cleanup on deletion"""
        self.stop_listening()
        if self.pyaudio:
            try:
                self.pyaudio.terminate()
            except:
                pass
