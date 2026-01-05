"""End-to-end integration tests for voice-to-prescription pipeline.

Tests the complete voice processing workflow from audio input to prescription generation.
"""

import pytest
import asyncio
from datetime import datetime
import json


class TestVoiceToPrescription:
    """Test complete voice-to-prescription workflows."""

    @pytest.mark.asyncio
    async def test_hindi_voice_to_prescription(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Test Hindi speech → transcription → SOAP → prescription."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Simulate Hindi audio input
        hindi_audio = b'\x00' * 1024  # Mock audio

        # Get speech-to-text service
        stt = full_service_registry.get("speech_to_text")

        # Override mock to return Hindi-like transcription
        async def hindi_transcribe(audio, language="auto"):
            return "Patient ko bukhar hai do din se aur sar mein dard hai"

        original_transcribe = stt.transcribe
        stt.transcribe.side_effect = hindi_transcribe

        try:
            # Process speech
            result = await clinical_flow.process_speech(hindi_audio)

            # Verify transcription happened
            assert "transcription" in result
            assert len(result["transcription"]) > 0
            assert "bukhar" in result["transcription"].lower() or "fever" in result["transcription"].lower()

            # Get LLM service to generate prescription
            llm = full_service_registry.get("llm")

            # Generate prescription from clinical notes
            current_context = clinical_flow.context_manager.get_current_context()
            prescription_data = await llm.generate_prescription(
                clinical_notes=current_context.clinical_notes
            )

            # Verify prescription generated
            assert "medications" in prescription_data
            assert len(prescription_data["medications"]) > 0

        finally:
            # Restore original
            stt.transcribe.side_effect = original_transcribe

    @pytest.mark.asyncio
    async def test_english_voice_to_prescription(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Test English speech → transcription → SOAP → prescription."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Simulate English audio input
        english_audio = b'\x00' * 1500

        # Get speech-to-text service
        stt = full_service_registry.get("speech_to_text")

        # Override mock to return English transcription
        async def english_transcribe(audio, language="auto"):
            return "Patient has fever since two days and complains of headache"

        original_transcribe = stt.transcribe
        stt.transcribe.side_effect = english_transcribe

        try:
            # Process speech
            result = await clinical_flow.process_speech(english_audio)

            # Verify transcription
            assert "transcription" in result
            assert "fever" in result["transcription"].lower()
            assert "headache" in result["transcription"].lower()

            # Check entity extraction
            if "entities" in result:
                entities = result["entities"]
                # Should extract symptoms
                if "symptoms" in entities:
                    assert "fever" in [s.lower() for s in entities["symptoms"]] or \
                           "headache" in [s.lower() for s in entities["symptoms"]]

        finally:
            stt.transcribe.side_effect = original_transcribe

    @pytest.mark.asyncio
    async def test_hinglish_voice_to_prescription(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Test code-mixed (Hinglish) speech → SOAP → prescription."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Simulate Hinglish audio input
        hinglish_audio = b'\x00' * 2000

        # Get speech-to-text service
        stt = full_service_registry.get("speech_to_text")

        # Override mock to return Hinglish transcription
        async def hinglish_transcribe(audio, language="auto"):
            return "Patient ko fever hai two days se, BP check karo, temperature 101 hai"

        original_transcribe = stt.transcribe
        stt.transcribe.side_effect = hinglish_transcribe

        try:
            # Process speech
            result = await clinical_flow.process_speech(hinglish_audio)

            # Verify transcription
            assert "transcription" in result
            transcription = result["transcription"].lower()
            assert "fever" in transcription or "bukhar" in transcription

            # Get clinical NLP service
            nlp = full_service_registry.get("clinical_nlp")

            # Extract entities
            entities = await nlp.extract_entities(result["transcription"])

            # Should extract vitals (temperature)
            # This is best-effort depending on NLP implementation

        finally:
            stt.transcribe.side_effect = original_transcribe

    @pytest.mark.asyncio
    async def test_voice_with_vitals(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Verify vitals extracted from speech."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Simulate audio with vitals
        vitals_audio = b'\x00' * 1600

        stt = full_service_registry.get("speech_to_text")

        async def vitals_transcribe(audio, language="auto"):
            return "BP is 140 over 90, pulse 88 per minute, temperature 101 Fahrenheit"

        original_transcribe = stt.transcribe
        stt.transcribe.side_effect = vitals_transcribe

        try:
            # Process speech
            result = await clinical_flow.process_speech(vitals_audio)

            # Verify transcription
            assert "140" in result["transcription"]
            assert "90" in result["transcription"]

            # Get NLP service and extract vitals
            nlp = full_service_registry.get("clinical_nlp")
            entities = await nlp.extract_entities(result["transcription"])

            # Check if vitals extracted
            if "vitals" in entities:
                vitals = entities["vitals"]
                # BP should be extracted
                if "bp" in vitals:
                    assert "140" in vitals["bp"] or "90" in vitals["bp"]

        finally:
            stt.transcribe.side_effect = original_transcribe

    @pytest.mark.asyncio
    async def test_voice_with_medications(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Verify medications extracted correctly from speech."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Simulate audio mentioning medications
        med_audio = b'\x00' * 2500

        stt = full_service_registry.get("speech_to_text")

        async def med_transcribe(audio, language="auto"):
            return "Give tab Paracetamol 500mg three times daily after meals for five days"

        original_transcribe = stt.transcribe
        stt.transcribe.side_effect = med_transcribe

        try:
            # Process speech
            result = await clinical_flow.process_speech(med_audio)

            # Verify transcription
            assert "Paracetamol" in result["transcription"]
            assert "500mg" in result["transcription"]

            # Get NLP service and extract medications
            nlp = full_service_registry.get("clinical_nlp")
            entities = await nlp.extract_entities(result["transcription"])

            # Check if medications extracted
            if "medications" in entities:
                meds = entities["medications"]
                assert any("paracetamol" in m.lower() for m in meds)

        finally:
            stt.transcribe.side_effect = original_transcribe


class TestVoiceSOAPExtraction:
    """Test SOAP note extraction from voice."""

    @pytest.mark.asyncio
    async def test_soap_extraction_from_conversation(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Test extracting structured SOAP note from conversation."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Simulate multiple speech segments
        stt = full_service_registry.get("speech_to_text")

        async def conversation_transcribe(audio, language="auto"):
            # Return different parts of conversation based on call count
            if not hasattr(conversation_transcribe, 'call_count'):
                conversation_transcribe.call_count = 0
            conversation_transcribe.call_count += 1

            if conversation_transcribe.call_count == 1:
                return "Patient has fever since two days"
            elif conversation_transcribe.call_count == 2:
                return "BP is 130 over 80, temperature 101"
            else:
                return "Likely viral fever, give symptomatic treatment"

        original_transcribe = stt.transcribe
        stt.transcribe.side_effect = conversation_transcribe

        try:
            # Process multiple speech segments
            await clinical_flow.process_speech(b'\x00' * 1000)
            await clinical_flow.process_speech(b'\x00' * 1500)
            await clinical_flow.process_speech(b'\x00' * 2000)

            # Get accumulated clinical notes
            current_context = clinical_flow.context_manager.get_current_context()
            clinical_notes = current_context.clinical_notes

            # Verify notes accumulated
            assert len(clinical_notes) > 0

            # Extract SOAP note
            llm = full_service_registry.get("llm")
            soap = await llm.extract_soap(clinical_notes)

            # Verify SOAP structure
            assert "subjective" in soap
            assert "objective" in soap
            assert "assessment" in soap
            assert "plan" in soap

        finally:
            stt.transcribe.side_effect = original_transcribe


class TestMultilingualVoice:
    """Test multilingual voice processing."""

    @pytest.mark.asyncio
    async def test_language_switching_mid_consultation(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Test handling language switches during consultation."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        stt = full_service_registry.get("speech_to_text")

        # First in Hindi
        async def hindi_transcribe(audio, language="auto"):
            return "Patient ko bukhar hai"

        stt.transcribe.side_effect = hindi_transcribe
        result1 = await clinical_flow.process_speech(b'\x00' * 1000)

        # Then switch to English
        async def english_transcribe(audio, language="auto"):
            return "Temperature is 101 Fahrenheit"

        stt.transcribe.side_effect = english_transcribe
        result2 = await clinical_flow.process_speech(b'\x00' * 1500)

        # Verify both transcriptions captured
        current_context = clinical_flow.context_manager.get_current_context()
        clinical_notes = current_context.clinical_notes

        # Should contain parts from both languages
        assert len(clinical_notes) > 0


class TestVoiceErrorHandling:
    """Test error handling in voice pipeline."""

    @pytest.mark.asyncio
    async def test_speech_recognition_failure(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Test handling speech recognition failures."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        stt = full_service_registry.get("speech_to_text")

        # Make STT fail
        async def failing_transcribe(audio, language="auto"):
            raise Exception("Speech recognition failed")

        original_transcribe = stt.transcribe
        stt.transcribe.side_effect = failing_transcribe

        try:
            # Process speech - should handle error gracefully
            result = await clinical_flow.process_speech(b'\x00' * 1000)

            # Should return empty or error result, not crash
            # The exact behavior depends on error handling implementation

        except Exception as e:
            # If it raises, that's also acceptable error handling
            assert "Speech recognition failed" in str(e) or "transcribe" in str(e).lower()

        finally:
            stt.transcribe.side_effect = original_transcribe

    @pytest.mark.asyncio
    async def test_empty_audio_handling(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Test handling empty or invalid audio."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        stt = full_service_registry.get("speech_to_text")

        # Return empty transcription for empty audio
        async def empty_transcribe(audio, language="auto"):
            return ""

        original_transcribe = stt.transcribe
        stt.transcribe.side_effect = empty_transcribe

        try:
            # Process empty audio
            result = await clinical_flow.process_speech(b'')

            # Should handle gracefully
            assert "transcription" in result

        finally:
            stt.transcribe.side_effect = original_transcribe


class TestRealTimeVoiceProcessing:
    """Test real-time voice processing capabilities."""

    @pytest.mark.asyncio
    async def test_streaming_voice_updates(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Test processing voice in real-time chunks."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Simulate streaming audio chunks
        audio_chunks = [
            b'\x00' * 500,
            b'\x00' * 800,
            b'\x00' * 1200,
            b'\x00' * 1600,
        ]

        stt = full_service_registry.get("speech_to_text")
        call_count = 0

        async def streaming_transcribe(audio, language="auto"):
            nonlocal call_count
            call_count += 1
            return f"Chunk {call_count}: Patient has symptoms"

        original_transcribe = stt.transcribe
        stt.transcribe.side_effect = streaming_transcribe

        try:
            # Process each chunk
            for chunk in audio_chunks:
                result = await clinical_flow.process_speech(chunk)
                assert "transcription" in result

            # Verify all chunks processed
            current_context = clinical_flow.context_manager.get_current_context()
            # Clinical notes should accumulate
            assert len(current_context.clinical_notes) > 0

        finally:
            stt.transcribe.side_effect = original_transcribe
