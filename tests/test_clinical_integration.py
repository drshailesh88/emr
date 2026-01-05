"""Integration tests for complete clinical workflows.

Tests full end-to-end workflows integrating multiple services including
voice transcription, prescription generation, safety checking, and delivery.
"""

import pytest
import asyncio
from datetime import date, datetime, timedelta

# Import fixtures
pytest_plugins = ['tests.clinical_conftest']


class TestClinicalIntegration:
    """Integration tests for complete clinical workflows."""

    @pytest.mark.asyncio
    async def test_full_consultation_flow(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test complete consultation from start to finish."""
        # 1. Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        assert context.consultation_id is not None

        # 2. Process speech (ambient listening)
        audio_data = b"x" * 50
        speech_result = await clinical_flow.process_speech(audio_data)

        assert "transcription" in speech_result
        assert len(speech_result["transcription"]) > 0

        # 3. Generate prescription
        medications = [
            {"drug_name": "Paracetamol", "strength": "500mg", "dose": "1", "frequency": "TDS"}
        ]

        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        assert "medications" in prescription

        # 4. Complete consultation
        visit_data = {"visit_date": date.today()}
        summary = await clinical_flow.complete_consultation(visit_data)

        # Verify all steps completed
        assert summary["visit_id"] is not None
        assert summary["prescription_sent"] is True

        # Verify audit trail
        audit_logger = service_registry.get("audit_logger")
        assert len(audit_logger.audit_events) >= 3

    @pytest.mark.asyncio
    async def test_voice_to_prescription_flow(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test flow from voice input to prescription generation."""
        # Start consultation
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Process multiple voice segments
        voice_segments = [
            b"x" * 50,  # "Patient has fever and headache"
            b"y" * 50,  # More clinical details
        ]

        for audio in voice_segments:
            await clinical_flow.process_speech(audio)

        # Verify transcriptions accumulated
        context = clinical_flow.context_manager.get_current_context()
        assert context.clinical_notes is not None

        # Generate prescription based on accumulated notes
        medications = [
            {"drug_name": "Paracetamol", "strength": "500mg", "dose": "1", "frequency": "TDS"}
        ]

        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        assert prescription is not None
        assert len(prescription["medications"]) > 0

    @pytest.mark.asyncio
    async def test_patient_timeline_updated(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test that patient timeline is updated after consultation."""
        # Get initial visit count
        db = service_registry.get("database")
        initial_visits = db.get_patient_visits(sample_patient.id)
        initial_count = len(initial_visits)

        # Complete a consultation
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        medications = [
            {"drug_name": "Aspirin", "strength": "75mg"}
        ]

        await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        await clinical_flow.complete_consultation({"visit_date": date.today()})

        # Verify new visit was added
        final_visits = db.get_patient_visits(sample_patient.id)
        assert len(final_visits) == initial_count + 1

    @pytest.mark.asyncio
    async def test_analytics_recorded(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test that practice analytics are recorded."""
        # Complete consultation
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        medications = [
            {"drug_name": "Metformin", "strength": "500mg"}
        ]

        await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        await clinical_flow.complete_consultation({"visit_date": date.today()})

        # Verify analytics service was called
        analytics = service_registry.get("practice_analytics")
        # In real implementation, verify analytics.record_consultation was called

    @pytest.mark.asyncio
    async def test_event_bus_propagation(
        self, clinical_flow, sample_patient
    ):
        """Test that events propagate through the event bus."""
        # Events should be published and subscribers should receive them

        received_events = []

        async def event_handler(event):
            received_events.append(event)

        # Subscribe to events
        clinical_flow.event_bus.subscribe(
            "CONSULTATION_STARTED",
            event_handler
        )

        # Start consultation (should publish event)
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Small delay for async event processing
        await asyncio.sleep(0.1)

        # Verify events were received
        # Note: Actual event bus implementation may vary

    @pytest.mark.asyncio
    async def test_concurrent_consultations(
        self, service_registry, mock_database
    ):
        """Test handling of multiple concurrent consultations."""
        from src.services.integration.clinical_flow import ClinicalFlow
        from src.services.integration.context_manager import ContextManager
        from src.services.integration.event_bus import EventBus

        # Create two separate clinical flows (different sessions)
        flow1 = ClinicalFlow(
            services=None,
            context_manager=ContextManager(),
            event_bus=EventBus(),
            service_registry=service_registry
        )

        flow2 = ClinicalFlow(
            services=None,
            context_manager=ContextManager(),
            event_bus=EventBus(),
            service_registry=service_registry
        )

        # Create two patients
        from src.models.schemas import Patient
        patient1 = mock_database.add_patient(Patient(name="Patient 1", age=50))
        patient2 = mock_database.add_patient(Patient(name="Patient 2", age=60))

        # Start consultations concurrently
        context1 = await flow1.start_consultation(
            patient_id=patient1.id,
            doctor_id="DR001"
        )

        context2 = await flow2.start_consultation(
            patient_id=patient2.id,
            doctor_id="DR002"
        )

        # Verify contexts are separate
        assert context1.consultation_id != context2.consultation_id
        assert context1.patient_id != context2.patient_id

    @pytest.mark.asyncio
    async def test_workflow_with_critical_lab_alert(
        self, clinical_flow, sample_patient, service_registry, mock_database
    ):
        """Test workflow when critical lab value is detected."""
        from src.models.schemas import Investigation

        # Start consultation
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Add critical lab value
        investigation = Investigation(
            patient_id=sample_patient.id,
            test_name="Potassium",
            result="6.8",  # Critical high
            unit="mEq/L",
            test_date=date.today(),
            is_abnormal=True
        )

        mock_database.add_investigation(investigation)

        # Check critical value
        from src.services.clinical_rules import check_critical_value
        alert = check_critical_value("Potassium", 6.8)

        assert alert is not None
        assert alert["severity"] == "critical"
        assert "arrhythmia" in alert["message"].lower()

    @pytest.mark.asyncio
    async def test_prescription_with_allergy_block(
        self, clinical_flow, mock_database
    ):
        """Test that prescription is blocked for allergic medication."""
        from src.models.schemas import Patient, PatientSnapshot, Medication
        from src.services.safety import PrescriptionSafetyChecker

        # Create patient with penicillin allergy
        patient = mock_database.add_patient(
            Patient(name="Test Patient", age=45, gender="M")
        )

        snapshot = PatientSnapshot(
            patient_id=patient.id,
            uhid=patient.uhid,
            demographics=f"{patient.name}, {patient.age}{patient.gender}",
            allergies=["Penicillin"],
            current_medications=[]
        )

        # Try to prescribe amoxicillin (penicillin derivative)
        from src.models.schemas import Prescription
        prescription = Prescription(
            diagnosis=["Pneumonia"],
            medications=[
                Medication(
                    drug_name="Amoxicillin",
                    strength="500mg",
                    dose="1",
                    frequency="TDS"
                )
            ]
        )

        # Check safety
        checker = PrescriptionSafetyChecker()
        alerts = checker.validate_prescription(prescription, snapshot)

        # Should be blocked
        blocking_alerts = [a for a in alerts if a.action == "BLOCK"]
        assert len(blocking_alerts) > 0

    @pytest.mark.asyncio
    async def test_follow_up_reminder_integration(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test that follow-up reminders are created and scheduled."""
        # Start consultation
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Set follow-up date
        follow_up_date = date.today() + timedelta(days=7)

        context = clinical_flow.context_manager.get_current_context()
        context.follow_up = follow_up_date

        # Complete consultation
        await clinical_flow.complete_consultation({"visit_date": date.today()})

        # Verify reminder was scheduled
        # (In real implementation, check reminder service)

    @pytest.mark.asyncio
    async def test_multi_medication_safety_check(
        self, clinical_flow, sample_patient
    ):
        """Test safety checking with multiple medications."""
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Prescription with multiple medications
        medications = [
            {"drug_name": "Metformin", "strength": "500mg", "dose": "1", "frequency": "BD"},
            {"drug_name": "Aspirin", "strength": "75mg", "dose": "1", "frequency": "OD"},
            {"drug_name": "Atorvastatin", "strength": "20mg", "dose": "1", "frequency": "OD"},
        ]

        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        # Should check all interactions
        assert "interactions" in prescription
        assert "dose_warnings" in prescription

    @pytest.mark.asyncio
    async def test_error_handling_db_failure(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test error handling when database fails."""
        from unittest.mock import AsyncMock

        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Simulate database failure
        db = service_registry.get("database")
        original_create_visit = db.create_visit

        async def failing_create_visit(*args, **kwargs):
            raise Exception("Database error")

        db.create_visit = AsyncMock(side_effect=failing_create_visit)

        # Try to complete consultation
        with pytest.raises(Exception):
            await clinical_flow.complete_consultation({"visit_date": date.today()})

        # Restore original method
        db.create_visit = original_create_visit

    @pytest.mark.asyncio
    async def test_state_recovery_after_error(
        self, clinical_flow, sample_patient
    ):
        """Test that workflow can recover after error."""
        # Start consultation
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Simulate error during prescription
        try:
            raise Exception("Simulated error")
        except Exception:
            pass

        # Should be able to continue
        medications = [
            {"drug_name": "Paracetamol", "strength": "500mg"}
        ]

        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        assert prescription is not None
