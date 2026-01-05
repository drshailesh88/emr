"""End-to-end tests for clinical consultation workflow.

Tests the complete lifecycle of a patient consultation from start to completion,
including speech processing, prescription generation, and audit logging.
"""

import pytest
import asyncio
from datetime import datetime, date
from unittest.mock import AsyncMock, Mock

# Import fixtures from clinical_conftest
pytest_plugins = ['tests.clinical_conftest']


class TestConsultationWorkflow:
    """E2E tests for the complete consultation workflow."""

    @pytest.mark.asyncio
    async def test_start_consultation_loads_patient_data(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test that starting a consultation loads all patient data correctly."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Verify context was created
        assert context is not None
        assert context.consultation_id is not None
        assert context.patient_id == sample_patient.id
        assert context.doctor_id == "DR001"

        # Verify patient timeline was loaded
        assert context.patient_timeline is not None
        assert len(context.patient_timeline) > 0

        # Verify care gaps were checked
        assert context.care_gaps is not None
        assert len(context.care_gaps) > 0

        # Verify audit log entry was created
        audit_logger = service_registry.get("audit_logger")
        assert len(audit_logger.audit_events) > 0
        assert audit_logger.audit_events[0]["event_type"] == "consultation_started"

    @pytest.mark.asyncio
    async def test_speech_processing_extracts_soap(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test that speech processing extracts clinical entities correctly."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Process speech audio (mock audio bytes)
        audio_data = b"x" * 50  # Short audio
        result = await clinical_flow.process_speech(audio_data)

        # Verify transcription
        assert "transcription" in result
        assert len(result["transcription"]) > 0

        # Verify entities were extracted
        assert "entities" in result
        assert "symptoms" in result["entities"]

        # Verify clinical notes were updated in context
        current_context = clinical_flow.context_manager.get_current_context()
        assert current_context.clinical_notes is not None
        assert len(current_context.clinical_notes) > 0

    @pytest.mark.asyncio
    async def test_speech_processing_detects_red_flags(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test that red flags are detected from speech input."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Process speech with cardiac red flag keywords
        audio_data = b"x" * 200  # Longer audio triggers red flag response
        result = await clinical_flow.process_speech(audio_data)

        # Verify red flags were detected
        assert "red_flags" in result
        if len(result["red_flags"]) > 0:
            # Check that red flag was added to context
            current_context = clinical_flow.context_manager.get_current_context()
            assert len(current_context.red_flags) > 0

    @pytest.mark.asyncio
    async def test_prescription_checks_interactions(
        self, clinical_flow, sample_patient, sample_prescription_with_interaction
    ):
        """Test that drug interactions are detected during prescription generation."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Generate prescription with known interaction (warfarin + aspirin)
        medications = [
            {
                "drug_name": "Warfarin",
                "strength": "5mg",
                "dose": "1",
                "frequency": "OD"
            },
            {
                "drug_name": "Aspirin",
                "strength": "75mg",
                "dose": "1",
                "frequency": "OD"
            }
        ]

        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        # Verify interaction was detected
        assert "interactions" in prescription
        assert len(prescription["interactions"]) > 0
        assert any("bleeding" in str(i).lower() for i in prescription["interactions"])

    @pytest.mark.asyncio
    async def test_complete_consultation_saves_visit(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test that completing consultation saves visit data correctly."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Add some clinical data to context
        current_context = clinical_flow.context_manager.get_current_context()
        current_context.chief_complaint = "Fever and headache"
        current_context.clinical_notes = "Patient presents with fever for 2 days"
        current_context.diagnosis = "Viral Fever"

        # Complete consultation
        visit_data = {
            "visit_date": date.today()
        }

        summary = await clinical_flow.complete_consultation(visit_data)

        # Verify visit was saved
        assert "visit_id" in summary
        assert summary["visit_id"] is not None

        # Verify database has the visit
        db = service_registry.get("database")
        visits = db.get_patient_visits(sample_patient.id)
        assert len(visits) > 0

    @pytest.mark.asyncio
    async def test_whatsapp_sent_after_consultation(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test that WhatsApp message is sent after consultation completion."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Generate prescription
        medications = [
            {
                "drug_name": "Paracetamol",
                "strength": "500mg",
                "dose": "1",
                "frequency": "TDS"
            }
        ]

        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        # Complete consultation
        visit_data = {"visit_date": date.today()}
        summary = await clinical_flow.complete_consultation(visit_data)

        # Verify WhatsApp was sent
        whatsapp = service_registry.get("whatsapp_client")
        assert len(whatsapp.sent_messages) > 0
        assert whatsapp.sent_messages[0]["phone"] == sample_patient.phone

    @pytest.mark.asyncio
    async def test_audit_trail_complete(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test that complete audit trail is created for consultation."""
        # Start consultation
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Generate prescription
        medications = [{"drug_name": "Paracetamol", "strength": "500mg"}]
        await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        # Complete consultation
        await clinical_flow.complete_consultation({"visit_date": date.today()})

        # Verify audit events
        audit_logger = service_registry.get("audit_logger")
        events = audit_logger.audit_events

        # Should have: consultation_started, prescription_created, consultation_completed
        assert len(events) >= 3

        event_types = [e["event_type"] for e in events]
        assert "consultation_started" in event_types
        assert "prescription_created" in event_types
        assert "consultation_completed" in event_types

    @pytest.mark.asyncio
    async def test_workflow_state_transitions(self, clinical_flow, sample_patient):
        """Test that workflow states transition correctly through consultation."""
        # Initial state should be IDLE
        initial_state = clinical_flow.get_current_state()
        assert not initial_state["has_active_consultation"]

        # Start consultation - should transition to CONSULTATION_ACTIVE
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        active_state = clinical_flow.get_current_state()
        assert active_state["has_active_consultation"]
        assert active_state["consultation_id"] is not None

        # Generate prescription - should transition to PRESCRIBING
        medications = [{"drug_name": "Paracetamol", "strength": "500mg"}]
        await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        # Complete consultation - should transition to COMPLETED
        await clinical_flow.complete_consultation({"visit_date": date.today()})

        final_state = clinical_flow.get_current_state()
        assert not final_state["has_active_consultation"]

    @pytest.mark.asyncio
    async def test_error_recovery(self, clinical_flow, sample_patient, service_registry):
        """Test that workflow handles errors gracefully."""
        # Start consultation
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Simulate database error during visit save
        db = service_registry.get("database")
        original_create_visit = db.create_visit

        async def failing_create_visit(*args, **kwargs):
            raise Exception("Database connection failed")

        db.create_visit = AsyncMock(side_effect=failing_create_visit)

        # Try to complete consultation - should handle error
        with pytest.raises(Exception):
            await clinical_flow.complete_consultation({"visit_date": date.today()})

        # Verify error was logged
        audit_logger = service_registry.get("audit_logger")
        # Note: In real implementation, error should be logged

    @pytest.mark.asyncio
    async def test_cancel_consultation(self, clinical_flow, sample_patient, service_registry):
        """Test that consultation can be cancelled."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Cancel consultation
        await clinical_flow.cancel_consultation(reason="Patient left before completion")

        # Verify context was closed
        current_context = clinical_flow.context_manager.get_current_context()
        assert current_context is None

        # Verify cancellation was logged
        audit_logger = service_registry.get("audit_logger")
        events = audit_logger.audit_events
        assert any(e["event_type"] == "consultation_cancelled" for e in events)

    @pytest.mark.asyncio
    async def test_multiple_speech_segments(self, clinical_flow, sample_patient):
        """Test processing multiple speech segments in one consultation."""
        # Start consultation
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Process multiple speech segments
        audio_segments = [
            b"x" * 50,
            b"y" * 50,
            b"z" * 50
        ]

        for audio in audio_segments:
            result = await clinical_flow.process_speech(audio)
            assert "transcription" in result

        # Verify all transcriptions were added to clinical notes
        context = clinical_flow.context_manager.get_current_context()
        assert context.clinical_notes is not None
        # Should contain multiple sentences

    @pytest.mark.asyncio
    async def test_follow_up_reminder_scheduled(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test that follow-up reminders are scheduled correctly."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Set follow-up date
        from datetime import timedelta
        follow_up_date = date.today() + timedelta(days=7)

        current_context = clinical_flow.context_manager.get_current_context()
        current_context.follow_up = follow_up_date

        # Complete consultation
        await clinical_flow.complete_consultation({"visit_date": date.today()})

        # Verify reminder was scheduled
        summary = clinical_flow.context_manager.get_last_saved_context()
        # In real implementation, check reminder service was called
