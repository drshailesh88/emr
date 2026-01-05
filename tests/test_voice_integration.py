"""Integration tests for voice input system."""

import pytest
import numpy as np
import time
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.voice.whisper_manager import get_whisper_manager, WhisperManager
from src.services.voice.audio_processor import get_audio_processor, AudioProcessor, AudioFormat


class TestWhisperManager:
    """Test WhisperManager functionality."""

    def test_manager_initialization(self):
        """Test WhisperManager initializes correctly."""
        manager = WhisperManager()
        assert manager is not None
        assert manager.model_dir.exists()

    def test_backend_detection(self):
        """Test backend detection."""
        manager = WhisperManager()
        # Should detect one of the backends or none
        assert manager.model_type in [None, "faster_whisper", "openai_whisper"]

    def test_model_info(self):
        """Test getting model information."""
        manager = WhisperManager()
        info = manager.get_model_info("base")

        assert "size_mb" in info
        assert "description" in info
        assert "available" in info
        assert info["size_mb"] == 142

    def test_get_available_models(self):
        """Test getting list of available models."""
        manager = WhisperManager()
        models = manager.get_available_models()

        assert len(models) > 0
        assert any(m["size"] == "base" for m in models)
        assert any(m["size"] == "tiny" for m in models)

    @pytest.mark.skipif(
        get_whisper_manager().model_type is None,
        reason="Whisper not available"
    )
    def test_model_loading(self):
        """Test model loading (only if Whisper is available)."""
        manager = WhisperManager()

        if not manager.is_available():
            pytest.skip("Whisper backend not available")

        # Try to load tiny model (fastest)
        success, model, error = manager.load_model("tiny")

        # May fail if model needs downloading
        if success:
            assert model is not None
            assert manager.current_model is not None
        else:
            assert "download" in error.lower() or "not found" in error.lower()

    @pytest.mark.skipif(
        get_whisper_manager().model_type is None,
        reason="Whisper not available"
    )
    def test_transcription(self):
        """Test audio transcription."""
        manager = WhisperManager()

        if not manager.is_available():
            pytest.skip("Whisper backend not available")

        # Load model
        success, model, error = manager.load_model("tiny")
        if not success:
            pytest.skip("Model not available for testing")

        # Generate test audio (1 second of sine wave at 440Hz)
        sample_rate = 16000
        duration = 1.0
        frequency = 440

        t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
        audio = 0.5 * np.sin(2 * np.pi * frequency * t)

        # Transcribe (will probably return empty or gibberish for sine wave)
        text = manager.transcribe(audio, language="en")

        # Just check it doesn't crash
        assert isinstance(text, str)


class TestAudioProcessor:
    """Test AudioProcessor functionality."""

    def test_processor_initialization(self):
        """Test AudioProcessor initializes correctly."""
        processor = AudioProcessor()
        assert processor is not None
        assert processor.format.sample_rate == 16000
        assert processor.format.channels == 1

    def test_backend_detection(self):
        """Test audio backend detection."""
        processor = AudioProcessor()
        assert processor.audio_backend in [None, "sounddevice", "pyaudio"]

    def test_format_conversion_int16(self):
        """Test converting int16 to Whisper format."""
        processor = AudioProcessor()

        # Create test audio (int16)
        audio_int16 = np.array([0, 16384, 32767, -16384, -32768], dtype=np.int16)

        # Convert
        audio_float = processor.convert_to_whisper_format(audio_int16)

        # Check conversion
        assert audio_float.dtype == np.float32
        assert audio_float.max() <= 1.0
        assert audio_float.min() >= -1.0

    def test_format_conversion_stereo_to_mono(self):
        """Test converting stereo to mono."""
        processor = AudioProcessor()

        # Create stereo test audio
        audio_stereo = np.random.randn(100, 2).astype(np.float32)

        # Convert
        audio_mono = processor.convert_to_whisper_format(audio_stereo)

        # Check it's mono
        assert len(audio_mono.shape) == 1
        assert audio_mono.dtype == np.float32

    def test_audio_level_calculation(self):
        """Test audio level calculation."""
        processor = AudioProcessor()

        # Silence
        silence = np.zeros(1000, dtype=np.float32)
        level_silence = processor.calculate_audio_level(silence)
        assert level_silence == 0.0

        # Loud audio
        loud = np.ones(1000, dtype=np.float32) * 0.5
        level_loud = processor.calculate_audio_level(loud)
        assert level_loud > 0.5

    def test_speech_detection(self):
        """Test simple energy-based speech detection."""
        processor = AudioProcessor()

        # Silence should not be detected as speech
        silence = np.zeros(1000, dtype=np.float32)
        assert not processor.has_speech(silence)

        # Loud audio should be detected as speech
        audio = np.random.randn(1000).astype(np.float32) * 0.1
        # May or may not be detected depending on energy
        result = processor.has_speech(audio)
        assert isinstance(result, bool)

    @pytest.mark.skipif(
        get_audio_processor().audio_backend is None,
        reason="No audio backend available"
    )
    def test_microphone_test(self):
        """Test microphone availability."""
        processor = AudioProcessor()

        if not processor.is_available():
            pytest.skip("No audio backend available")

        test_result = processor.test_microphone()

        assert "available" in test_result
        if test_result["available"]:
            assert "backend" in test_result
            assert "default_device" in test_result

    @pytest.mark.skipif(
        get_audio_processor().audio_backend is None,
        reason="No audio backend available"
    )
    def test_list_devices(self):
        """Test listing audio devices."""
        processor = AudioProcessor()

        if not processor.is_available():
            pytest.skip("No audio backend available")

        devices = processor.list_devices()

        # Should return a list (may be empty on some systems)
        assert isinstance(devices, list)


class TestEndToEndVoiceFlow:
    """Test complete voice input flow."""

    @pytest.mark.skipif(
        get_whisper_manager().model_type is None or get_audio_processor().audio_backend is None,
        reason="Voice system not fully available"
    )
    def test_complete_flow_with_test_audio(self):
        """Test complete flow with synthetic audio."""
        whisper_manager = get_whisper_manager()
        audio_processor = get_audio_processor()

        if not whisper_manager.is_available() or not audio_processor.is_available():
            pytest.skip("Voice system not available")

        # Load model (tiny for speed)
        success, model, error = whisper_manager.load_model("tiny")
        if not success:
            pytest.skip(f"Model loading failed: {error}")

        # Generate test audio (1 second)
        sample_rate = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
        audio = 0.3 * np.sin(2 * np.pi * 440 * t)  # 440Hz sine wave

        # Convert to Whisper format
        audio_converted = audio_processor.convert_to_whisper_format(audio)

        # Transcribe
        text = whisper_manager.transcribe(audio_converted, language="en")

        # Should return something (probably empty for sine wave)
        assert isinstance(text, str)

    def test_audio_format_consistency(self):
        """Test that audio format is consistent through the pipeline."""
        audio_processor = get_audio_processor()

        # Create test audio in different formats
        formats = [
            (np.int16, 16384),  # int16 half scale
            (np.float32, 0.5),  # float32
            (np.float64, 0.5),  # float64
        ]

        for dtype, scale in formats:
            # Generate sine wave
            t = np.linspace(0, 1.0, 16000)
            if dtype == np.int16:
                audio = (scale * np.sin(2 * np.pi * 440 * t)).astype(dtype)
            else:
                audio = (scale * np.sin(2 * np.pi * 440 * t)).astype(dtype)

            # Convert
            converted = audio_processor.convert_to_whisper_format(audio)

            # Verify format
            assert converted.dtype == np.float32
            assert converted.max() <= 1.0
            assert converted.min() >= -1.0
            assert len(converted.shape) == 1  # Mono


class TestVoiceComponents:
    """Test voice UI components (basic structure)."""

    def test_whisper_manager_singleton(self):
        """Test WhisperManager singleton."""
        manager1 = get_whisper_manager()
        manager2 = get_whisper_manager()
        assert manager1 is manager2

    def test_audio_processor_singleton(self):
        """Test AudioProcessor singleton."""
        processor1 = get_audio_processor()
        processor2 = get_audio_processor()
        assert processor1 is processor2

    def test_installation_instructions(self):
        """Test getting installation instructions."""
        whisper_manager = get_whisper_manager()
        audio_processor = get_audio_processor()

        # Should return strings
        assert isinstance(whisper_manager.get_installation_instructions(), str)
        assert isinstance(audio_processor.get_installation_instructions(), str)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
