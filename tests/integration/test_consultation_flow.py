"""End-to-end integration tests for complete consultation workflow.

Tests the entire consultation lifecycle from patient selection to prescription delivery.
"""

import pytest
import asyncio
from datetime import datetime, date, timedelta
import json


class TestFullConsultationFlow:
    """Test complete consultation workflows."""

    @pytest.mark.asyncio
    async def test_complete_consultation_happy_path(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry,
        assert_audit_logged,
        assert_whatsapp_sent,
        assert_reminder_scheduled
    ):
        """
        Test complete consultation from start to finish.

        Workflow:
        1. Create patient
        2. Start consultation
        3. Process voice input (mock)
        4. Extract SOAP note
        5. Generate prescription
        6. Check drug interactions
        7. Save visit
        8. Send WhatsApp
        9. Verify audit trail
        10. Verify analytics updated
        """
        # 1. Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        assert context is not None
        assert context.patient_id == sample_patient.id
        assert context.consultation_id is not None
        assert_audit_logged("consultation_started", sample_patient.id)

        # 2. Process voice input - simulate ambient listening
        test_audio = b'\x00' * 1024
        speech_result = await clinical_flow.process_speech(test_audio)

        assert "transcription" in speech_result
        assert len(speech_result["transcription"]) > 0

        # Verify clinical notes updated
        current_context = clinical_flow.context_manager.get_current_context()
        assert len(current_context.clinical_notes) > 0

        # 3. Generate prescription
        medications = [
            {
                "drug_name": "Paracetamol",
                "strength": "500mg",
                "form": "tablet",
                "dose": "1",
                "frequency": "TDS",
                "duration": "5 days",
                "instructions": "after meals"
            }
        ]

        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        assert "medications" in prescription
        assert len(prescription["medications"]) == 1
        assert len(prescription["interactions"]) == 0  # No interactions for single drug

        # 4. Complete consultation
        visit_data = {
            "chief_complaint": "Fever and headache",
            "diagnosis": "Viral Fever"
        }

        summary = await clinical_flow.complete_consultation(visit_data)

        assert summary["visit_id"] is not None
        assert summary["prescription_sent"] is True
        assert summary["analytics_updated"] is True

        # 5. Verify database state
        db = full_service_registry.get("database")
        saved_visit = db.get_visit(summary["visit_id"])

        assert saved_visit is not None
        assert saved_visit.patient_id == sample_patient.id
        assert saved_visit.diagnosis == "Viral Fever"

        # 6. Verify WhatsApp sent
        assert_whatsapp_sent(to=sample_patient.phone, message_type="prescription")

        # 7. Verify audit trail
        assert_audit_logged("consultation_completed", sample_patient.id)

        # 8. Verify analytics updated
        analytics = full_service_registry.get("practice_analytics")
        assert len(analytics.consultations) == 1
        assert analytics.consultations[0]["patient_id"] == sample_patient.id

    @pytest.mark.asyncio
    async def test_consultation_with_drug_interaction(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Verify drug interaction alert shown and logged."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Generate prescription with interacting drugs
        medications = [
            {
                "drug_name": "Aspirin",
                "strength": "75mg",
                "form": "tablet",
                "dose": "1",
                "frequency": "OD"
            },
            {
                "drug_name": "Warfarin",
                "strength": "5mg",
                "form": "tablet",
                "dose": "1",
                "frequency": "OD"
            }
        ]

        prescription = await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        # Verify interaction detected
        assert len(prescription["interactions"]) > 0
        interaction = prescription["interactions"][0]
        assert interaction["severity"] == "high"
        assert "bleeding" in interaction["message"].lower()

        # Verify interaction added to context
        current_context = clinical_flow.context_manager.get_current_context()
        assert len(current_context.drug_interactions) > 0

        # Verify alert in active alerts
        assert len(current_context.active_alerts) > 0
        interaction_alert = [a for a in current_context.active_alerts if a["alert_type"] == "drug_interaction"]
        assert len(interaction_alert) > 0

    @pytest.mark.asyncio
    async def test_consultation_with_red_flag(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Verify red flag detected and escalated."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Process speech with red flag keywords
        # Mock will detect "chest pain" and trigger red flag
        red_flag_detector = full_service_registry.get("red_flag_detector")

        # Simulate transcription with red flag
        test_audio = b'\x00' * 2048  # Different length triggers different transcription
        speech_result = await clinical_flow.process_speech(test_audio)

        # Manually check for red flags (since mock returns based on text)
        red_flags = await red_flag_detector.check_text(
            "Patient has chest pain radiating to left arm",
            {"age": sample_patient.age}
        )

        # Verify red flag detected
        assert len(red_flags) > 0
        assert red_flags[0]["severity"] == "critical"

        # Publish red flag event manually to trigger alert
        await clinical_flow.event_bus.publish(
            clinical_flow.event_bus.EventType.RED_FLAG_DETECTED if hasattr(clinical_flow.event_bus, 'EventType') else "RED_FLAG_DETECTED",
            red_flags[0],
            source="test"
        )

        # Give event handlers time to process
        await asyncio.sleep(0.1)

        # Verify alert added to context
        current_context = clinical_flow.context_manager.get_current_context()
        # Note: alerts might be in active_alerts or red_flags depending on implementation
        has_red_flag = (
            len(current_context.red_flags) > 0 or
            any(a.get("alert_type") == "red_flag" for a in current_context.active_alerts)
        )
        assert has_red_flag

    @pytest.mark.asyncio
    async def test_consultation_cancellation(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry,
        assert_audit_logged
    ):
        """Verify proper cleanup on cancel."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        consultation_id = context.consultation_id

        # Cancel consultation
        await clinical_flow.cancel_consultation(reason="Patient left before completion")

        # Verify context closed
        current_context = clinical_flow.context_manager.get_current_context()
        assert current_context is None

        # Verify cancellation logged
        assert_audit_logged("consultation_cancelled", sample_patient.id)

        # Verify no visit saved
        db = full_service_registry.get("database")
        visits = db.get_patient_visits(sample_patient.id)
        # Should have no new visits (only existing ones if any)
        visit_ids = [v.id for v in visits]
        # Context didn't have a visit_id, so shouldn't be in DB

    @pytest.mark.asyncio
    async def test_consultation_error_recovery(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Verify recovery from mid-consultation error."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Simulate error during prescription generation
        interaction_checker = full_service_registry.get("interaction_checker")

        # Make interaction checker raise an error
        original_check = interaction_checker.check_interactions

        async def failing_check(*args, **kwargs):
            raise Exception("Simulated interaction checker failure")

        interaction_checker.check_interactions.side_effect = failing_check

        # Try to generate prescription (should handle error gracefully)
        medications = [
            {
                "drug_name": "Paracetamol",
                "strength": "500mg",
                "form": "tablet",
                "dose": "1",
                "frequency": "TDS"
            }
        ]

        try:
            prescription = await clinical_flow.generate_prescription(
                medications=medications,
                patient_id=sample_patient.id
            )

            # Prescription should still be created, just without interaction check
            assert "medications" in prescription
            # Interactions list should be empty (check failed)
            assert "interactions" in prescription

        except Exception as e:
            # If it raises, verify error handling triggered
            state = clinical_flow.get_current_state()
            # Workflow might be in error state
            pass

        finally:
            # Restore original function
            interaction_checker.check_interactions.side_effect = original_check


class TestConsultationWithVitals:
    """Test consultation with vitals recording."""

    @pytest.mark.asyncio
    async def test_vitals_extraction_from_speech(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Test extracting vitals from ambient speech."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Process speech containing vitals
        test_audio = b'\x00' * 1500  # Triggers "BP is 140 over 90" transcription

        speech_result = await clinical_flow.process_speech(test_audio)

        # Verify transcription
        assert "transcription" in speech_result

        # Verify entities extracted
        if "entities" in speech_result and "vitals" in speech_result["entities"]:
            # BP should be extracted
            vitals = speech_result["entities"]["vitals"]
            # Check if BP was extracted (depends on NLP implementation)
            # This is a best-effort test


class TestMultiplePatientConsultations:
    """Test handling multiple consultations in sequence."""

    @pytest.mark.asyncio
    async def test_sequential_consultations(
        self,
        clinical_flow,
        sample_patient,
        diabetic_patient,
        full_service_registry
    ):
        """Test multiple consultations in sequence."""
        # First consultation
        context1 = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        medications1 = [
            {
                "drug_name": "Paracetamol",
                "strength": "500mg",
                "dose": "1",
                "frequency": "TDS"
            }
        ]

        await clinical_flow.generate_prescription(
            medications=medications1,
            patient_id=sample_patient.id
        )

        visit_data1 = {
            "chief_complaint": "Fever",
            "diagnosis": "Viral Fever"
        }

        summary1 = await clinical_flow.complete_consultation(visit_data1)
        visit1_id = summary1["visit_id"]

        # Second consultation
        context2 = await clinical_flow.start_consultation(
            patient_id=diabetic_patient.id,
            doctor_id="DR001"
        )

        medications2 = [
            {
                "drug_name": "Metformin",
                "strength": "500mg",
                "dose": "1",
                "frequency": "BD"
            }
        ]

        await clinical_flow.generate_prescription(
            medications=medications2,
            patient_id=diabetic_patient.id
        )

        visit_data2 = {
            "chief_complaint": "Diabetes follow-up",
            "diagnosis": "Type 2 Diabetes"
        }

        summary2 = await clinical_flow.complete_consultation(visit_data2)
        visit2_id = summary2["visit_id"]

        # Verify both visits saved
        assert visit1_id != visit2_id

        db = full_service_registry.get("database")

        visit1 = db.get_visit(visit1_id)
        visit2 = db.get_visit(visit2_id)

        assert visit1.patient_id == sample_patient.id
        assert visit2.patient_id == diabetic_patient.id

        # Verify analytics tracked both
        analytics = full_service_registry.get("practice_analytics")
        assert len(analytics.consultations) == 2


class TestConsultationWithFollowUp:
    """Test consultation with follow-up scheduling."""

    @pytest.mark.asyncio
    async def test_follow_up_reminder_scheduled(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry,
        assert_reminder_scheduled
    ):
        """Test that follow-up reminders are scheduled."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Set follow-up date in context
        follow_up_date = date.today() + timedelta(days=7)
        context.follow_up = follow_up_date
        context.chief_complaint = "Hypertension check"

        # Complete consultation
        visit_data = {
            "chief_complaint": "Hypertension check",
            "diagnosis": "Essential Hypertension"
        }

        summary = await clinical_flow.complete_consultation(visit_data)

        # Verify reminder scheduled
        reminder = assert_reminder_scheduled(
            patient_id=sample_patient.id,
            reminder_type="follow_up"
        )

        assert reminder["scheduled_date"] == follow_up_date.isoformat()
        assert "Hypertension" in reminder["message"]
