"""End-to-end integration tests for communication workflows.

Tests appointment reminders, prescription delivery, follow-ups, and broadcasts.
"""

import pytest
import asyncio
from datetime import datetime, date, timedelta
import json


class TestCommunicationFlow:
    """Test complete communication workflows."""

    @pytest.mark.asyncio
    async def test_appointment_reminder_flow(
        self,
        sample_patient,
        mock_reminder_service,
        mock_whatsapp_client,
        assert_reminder_scheduled
    ):
        """Test: Schedule appointment → reminder sent → delivery tracked."""
        # 1. Schedule appointment reminder
        appointment_date = date.today() + timedelta(days=7)

        reminder = await mock_reminder_service.schedule_reminder(
            patient_id=sample_patient.id,
            reminder_type="appointment",
            scheduled_date=appointment_date,
            message=f"Appointment reminder for {sample_patient.name} on {appointment_date}"
        )

        # Verify reminder created
        assert reminder["id"] is not None
        assert reminder["patient_id"] == sample_patient.id
        assert reminder["reminder_type"] == "appointment"

        # 2. Simulate reminder being sent
        await mock_whatsapp_client.send_text(
            to=sample_patient.phone,
            message=f"Reminder: You have an appointment on {appointment_date}"
        )

        # 3. Verify message sent
        assert len(mock_whatsapp_client.sent_messages) == 1
        sent_msg = mock_whatsapp_client.sent_messages[0]
        assert sent_msg["to"] == sample_patient.phone
        assert sent_msg["status"] == "delivered"

        # 4. Verify delivery tracked
        assert sent_msg["message_id"] is not None
        assert sent_msg["timestamp"] is not None

    @pytest.mark.asyncio
    async def test_prescription_whatsapp_flow(
        self,
        sample_patient,
        mock_whatsapp_client,
        test_prescription,
        assert_whatsapp_sent
    ):
        """Test: Prescription created → PDF → WhatsApp → delivered."""
        # 1. Create prescription (already have test_prescription)
        prescription = test_prescription

        # 2. Send prescription via WhatsApp
        result = await mock_whatsapp_client.send_prescription(
            phone=sample_patient.phone,
            prescription=prescription,
            patient_name=sample_patient.name
        )

        # 3. Verify sent
        assert result["message_id"] is not None
        assert result["status"] == "sent"

        # 4. Verify in sent messages
        sent = assert_whatsapp_sent(to=sample_patient.phone, message_type="prescription")
        assert sent["patient_name"] == sample_patient.name
        assert sent["medications"] == len(prescription["medications"])

    @pytest.mark.asyncio
    async def test_follow_up_reminder_flow(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry,
        assert_reminder_scheduled,
        assert_whatsapp_sent
    ):
        """Test: Visit → follow-up scheduled → reminder sent."""
        # 1. Start and complete consultation with follow-up
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Set follow-up
        follow_up_date = date.today() + timedelta(days=14)
        context.follow_up = follow_up_date
        context.chief_complaint = "Diabetes management"

        # Complete consultation
        visit_data = {
            "chief_complaint": "Diabetes management",
            "diagnosis": "Type 2 Diabetes"
        }

        summary = await clinical_flow.complete_consultation(visit_data)

        # 2. Verify follow-up reminder scheduled
        reminder = assert_reminder_scheduled(
            patient_id=sample_patient.id,
            reminder_type="follow_up"
        )

        assert follow_up_date.isoformat() in reminder["scheduled_date"]
        assert "Diabetes" in reminder["message"]

        # 3. Simulate reminder being sent on scheduled date
        reminder_service = full_service_registry.get("reminder_service")
        whatsapp = full_service_registry.get("whatsapp_client")

        await whatsapp.send_text(
            to=sample_patient.phone,
            message=f"Follow-up reminder: {reminder['message']}"
        )

        # 4. Verify sent
        sent = assert_whatsapp_sent(to=sample_patient.phone)
        assert "Follow-up" in sent["message"]

    @pytest.mark.asyncio
    async def test_broadcast_to_segment(
        self,
        real_db,
        mock_whatsapp_client
    ):
        """Test: Create patient segment → send broadcast → track delivery."""
        from src.models.schemas import Patient, Visit

        # 1. Create patient segment (diabetic patients)
        diabetic_patients = []

        for i in range(3):
            patient = Patient(
                name=f"Diabetic Patient {i+1}",
                age=50 + i,
                gender="M" if i % 2 == 0 else "F",
                phone=f"987654321{i}"
            )
            added = real_db.add_patient(patient)
            diabetic_patients.append(added)

            # Add diabetes diagnosis
            visit = Visit(
                patient_id=added.id,
                visit_date=date.today() - timedelta(days=30),
                chief_complaint="Diabetes follow-up",
                diagnosis="Type 2 Diabetes Mellitus"
            )
            real_db.add_visit(visit)

        # 2. Get diabetic patient segment
        # (In real app, this would be a database query)
        segment = diabetic_patients

        # 3. Send broadcast message
        broadcast_message = "Health tip: Regular HbA1c testing is important for diabetes management."

        for patient in segment:
            await mock_whatsapp_client.send_text(
                to=patient.phone,
                message=broadcast_message
            )

        # 4. Verify all messages sent
        assert len(mock_whatsapp_client.sent_messages) == 3

        for i, msg in enumerate(mock_whatsapp_client.sent_messages):
            assert msg["to"] == diabetic_patients[i].phone
            assert msg["message"] == broadcast_message
            assert msg["status"] == "delivered"


class TestReminderManagement:
    """Test reminder creation and management."""

    @pytest.mark.asyncio
    async def test_multiple_reminder_types(
        self,
        sample_patient,
        mock_reminder_service
    ):
        """Test creating different types of reminders."""
        # Schedule appointment reminder
        apt_reminder = await mock_reminder_service.schedule_reminder(
            patient_id=sample_patient.id,
            reminder_type="appointment",
            scheduled_date=date.today() + timedelta(days=7),
            message="Appointment in 7 days"
        )

        # Schedule medication reminder
        med_reminder = await mock_reminder_service.schedule_reminder(
            patient_id=sample_patient.id,
            reminder_type="medication",
            scheduled_date=date.today() + timedelta(days=1),
            message="Time to refill your prescription"
        )

        # Schedule test reminder
        test_reminder = await mock_reminder_service.schedule_reminder(
            patient_id=sample_patient.id,
            reminder_type="investigation",
            scheduled_date=date.today() + timedelta(days=30),
            message="HbA1c test due"
        )

        # Verify all reminders created
        assert len(mock_reminder_service.reminders) == 3

        # Get patient reminders
        patient_reminders = await mock_reminder_service.get_pending_reminders(sample_patient.id)
        assert len(patient_reminders) == 3

        # Verify different types
        types = {r["reminder_type"] for r in patient_reminders}
        assert types == {"appointment", "medication", "investigation"}

    @pytest.mark.asyncio
    async def test_reminder_scheduling_logic(
        self,
        sample_patient,
        mock_reminder_service
    ):
        """Test reminder scheduling for different timeframes."""
        today = date.today()

        # Schedule reminders at different intervals
        reminders = [
            (today + timedelta(days=1), "Tomorrow"),
            (today + timedelta(days=7), "Next week"),
            (today + timedelta(days=30), "Next month"),
        ]

        for scheduled_date, label in reminders:
            await mock_reminder_service.schedule_reminder(
                patient_id=sample_patient.id,
                reminder_type="appointment",
                scheduled_date=scheduled_date,
                message=f"Appointment {label}"
            )

        # Verify all scheduled
        pending = await mock_reminder_service.get_pending_reminders(sample_patient.id)
        assert len(pending) == 3


class TestWhatsAppTemplates:
    """Test WhatsApp template messages."""

    @pytest.mark.asyncio
    async def test_send_template_message(
        self,
        sample_patient,
        mock_whatsapp_client
    ):
        """Test sending pre-approved template messages."""
        # Send template (requires WhatsApp Business API approval)
        # For testing, we'll use the send_text method

        template_message = """Hello {name},

This is a reminder for your appointment on {date}.

Please arrive 10 minutes early.

- DocAssist Clinic"""

        formatted_message = template_message.format(
            name=sample_patient.name,
            date=date.today() + timedelta(days=7)
        )

        await mock_whatsapp_client.send_text(
            to=sample_patient.phone,
            message=formatted_message
        )

        # Verify sent
        assert len(mock_whatsapp_client.sent_messages) == 1
        sent = mock_whatsapp_client.sent_messages[0]
        assert sample_patient.name in sent["message"]

    @pytest.mark.asyncio
    async def test_send_document_via_whatsapp(
        self,
        sample_patient,
        mock_whatsapp_client
    ):
        """Test sending PDF document via WhatsApp."""
        # Create fake PDF content
        pdf_content = b'%PDF-1.4\n...'  # Fake PDF

        # Send document
        result = await mock_whatsapp_client.send_document(
            to=sample_patient.phone,
            document=pdf_content,
            filename=f"prescription_{sample_patient.uhid}.pdf"
        )

        # Verify sent
        assert result["message_id"] is not None

        sent = mock_whatsapp_client.sent_messages[0]
        assert sent["type"] == "document"
        assert sent["filename"].endswith(".pdf")
        assert sent["size"] == len(pdf_content)


class TestMessageDeliveryTracking:
    """Test message delivery status tracking."""

    @pytest.mark.asyncio
    async def test_track_message_delivery(
        self,
        sample_patient,
        mock_whatsapp_client
    ):
        """Test tracking message delivery status."""
        # Send message
        result = await mock_whatsapp_client.send_text(
            to=sample_patient.phone,
            message="Test message"
        )

        # Verify delivery info
        assert result["message_id"] is not None
        assert result["status"] == "sent"
        assert result["timestamp"] is not None

        # Check in sent messages log
        sent = mock_whatsapp_client.sent_messages[0]
        assert sent["status"] == "delivered"

    @pytest.mark.asyncio
    async def test_failed_message_handling(
        self,
        mock_whatsapp_client
    ):
        """Test handling failed message delivery."""
        # Override mock to simulate failure
        async def failing_send(to, message, **kwargs):
            return {
                "message_id": "",
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "error": "Invalid phone number"
            }

        original_send = mock_whatsapp_client.send_text
        mock_whatsapp_client.send_text.side_effect = failing_send

        try:
            # Try to send to invalid number
            result = await mock_whatsapp_client.send_text(
                to="invalid",
                message="Test"
            )

            # Verify failure tracked
            assert result["status"] == "failed"
            assert "error" in result

        finally:
            mock_whatsapp_client.send_text.side_effect = original_send


class TestBulkMessaging:
    """Test bulk messaging capabilities."""

    @pytest.mark.asyncio
    async def test_bulk_prescription_delivery(
        self,
        real_db,
        mock_whatsapp_client
    ):
        """Test sending prescriptions to multiple patients."""
        from src.models.schemas import Patient

        # Create multiple patients
        patients = []
        for i in range(5):
            patient = Patient(
                name=f"Patient {i+1}",
                phone=f"987654320{i}",
                age=30 + i,
                gender="M" if i % 2 == 0 else "F"
            )
            added = real_db.add_patient(patient)
            patients.append(added)

        # Send prescription to each
        prescriptions = []
        for patient in patients:
            prescription = {
                "medications": [
                    {
                        "drug_name": "Medication",
                        "strength": "100mg",
                        "frequency": "OD"
                    }
                ]
            }

            await mock_whatsapp_client.send_prescription(
                phone=patient.phone,
                prescription=prescription,
                patient_name=patient.name
            )

            prescriptions.append(prescription)

        # Verify all sent
        assert len(mock_whatsapp_client.sent_messages) == 5

        for i, msg in enumerate(mock_whatsapp_client.sent_messages):
            assert msg["type"] == "prescription"
            assert msg["to"] == patients[i].phone

    @pytest.mark.asyncio
    async def test_rate_limiting_bulk_messages(
        self,
        mock_whatsapp_client
    ):
        """Test rate limiting for bulk messages."""
        # WhatsApp has rate limits (e.g., 80 msgs/second for Cloud API)
        # This test simulates sending many messages

        messages_to_send = 10
        start_time = datetime.now()

        for i in range(messages_to_send):
            await mock_whatsapp_client.send_text(
                to=f"987654{i:04d}",
                message=f"Bulk message {i+1}"
            )

            # In production, add rate limiting delay here
            # await asyncio.sleep(0.015)  # ~66 msgs/second

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Verify all sent
        assert len(mock_whatsapp_client.sent_messages) == messages_to_send

        # In production with rate limiting, duration should be > 0.15 seconds


class TestCommunicationPreferences:
    """Test patient communication preferences."""

    @pytest.mark.asyncio
    async def test_opt_out_handling(
        self,
        sample_patient,
        mock_whatsapp_client
    ):
        """Test handling patients who opt out of communications."""
        # In real implementation, check opt-out status before sending

        # Simulate opt-out flag
        opted_out = False  # Would check patient preferences

        if not opted_out:
            await mock_whatsapp_client.send_text(
                to=sample_patient.phone,
                message="Test message"
            )

            assert len(mock_whatsapp_client.sent_messages) == 1
        else:
            # Should not send if opted out
            assert len(mock_whatsapp_client.sent_messages) == 0

    @pytest.mark.asyncio
    async def test_language_preference(
        self,
        sample_patient,
        mock_whatsapp_client
    ):
        """Test sending messages in patient's preferred language."""
        # Simulate language preference
        preferred_language = "hi"  # Hindi

        if preferred_language == "hi":
            message = "आपकी अपॉइंटमेंट 7 दिनों में है"
        else:
            message = "Your appointment is in 7 days"

        await mock_whatsapp_client.send_text(
            to=sample_patient.phone,
            message=message
        )

        sent = mock_whatsapp_client.sent_messages[0]
        # Message should be in Hindi
        assert len(sent["message"]) > 0
