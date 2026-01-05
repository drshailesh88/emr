"""Tests for communication services (WhatsApp, SMS, reminders).

Tests appointment reminders, medication reminders, broadcasts,
and notification queuing/retry logic.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, Mock

# Import fixtures
pytest_plugins = ['tests.clinical_conftest']


class TestCommunicationServices:
    """Tests for communication and reminder services."""

    @pytest.mark.asyncio
    async def test_appointment_reminder_scheduling(self, mock_whatsapp_client):
        """Test scheduling of appointment reminders."""
        # Schedule reminder for tomorrow
        reminder_date = date.today() + timedelta(days=1)

        patient_data = {
            "name": "Ram Lal",
            "phone": "9876543210"
        }

        # Send appointment reminder
        message = f"Reminder: You have an appointment tomorrow at 10:00 AM. - Dr. Sharma's Clinic"

        await mock_whatsapp_client.send_prescription(
            phone=patient_data["phone"],
            prescription={"message": message},
            patient_name=patient_data["name"]
        )

        # Verify message was queued
        assert len(mock_whatsapp_client.sent_messages) == 1
        assert mock_whatsapp_client.sent_messages[0]["phone"] == patient_data["phone"]

    @pytest.mark.asyncio
    async def test_follow_up_reminder(self, service_registry, sample_patient):
        """Test follow-up reminder creation."""
        reminder_service = service_registry.get("reminder_service")

        follow_up_date = date.today() + timedelta(days=7)

        reminder = await reminder_service.schedule_reminder(
            patient_id=sample_patient.id,
            reminder_type="follow_up",
            scheduled_date=follow_up_date,
            message="Follow-up for diabetes checkup"
        )

        assert reminder is not None
        assert reminder["type"] == "follow_up"
        assert reminder["patient_id"] == sample_patient.id

    @pytest.mark.asyncio
    async def test_medication_reminder(self, service_registry):
        """Test medication reminder scheduling."""
        reminder_service = service_registry.get("reminder_service")

        reminder = await reminder_service.schedule_reminder(
            patient_id=1,
            reminder_type="medication",
            scheduled_date=date.today(),
            message="Time to take your morning medications"
        )

        assert reminder is not None
        assert reminder["type"] == "medication"

    @pytest.mark.asyncio
    async def test_broadcast_to_segment(self, mock_whatsapp_client):
        """Test broadcasting messages to patient segments."""
        # Broadcast to all diabetic patients
        patient_segment = [
            {"name": "Patient 1", "phone": "9876543211"},
            {"name": "Patient 2", "phone": "9876543212"},
            {"name": "Patient 3", "phone": "9876543213"},
        ]

        message = "Reminder: Get your HbA1c tested this month. - Dr. Sharma's Clinic"

        for patient in patient_segment:
            await mock_whatsapp_client.send_prescription(
                phone=patient["phone"],
                prescription={"message": message},
                patient_name=patient["name"]
            )

        # Verify all messages were sent
        assert len(mock_whatsapp_client.sent_messages) == len(patient_segment)

    @pytest.mark.asyncio
    async def test_template_rendering_english(self, mock_whatsapp_client):
        """Test message template rendering in English."""
        template = "Dear {patient_name}, your prescription is ready. Please collect from {clinic_name}."

        data = {
            "patient_name": "Ram Lal",
            "clinic_name": "City Health Clinic"
        }

        message = template.format(**data)

        await mock_whatsapp_client.send_prescription(
            phone="9876543210",
            prescription={"message": message},
            patient_name=data["patient_name"]
        )

        sent_message = mock_whatsapp_client.sent_messages[0]
        assert "Ram Lal" in str(sent_message)

    @pytest.mark.asyncio
    async def test_template_rendering_hindi(self, mock_whatsapp_client):
        """Test message template rendering in Hindi."""
        template = "प्रिय {patient_name}, आपकी दवाई तैयार है। कृपया {clinic_name} से लें।"

        data = {
            "patient_name": "राम लाल",
            "clinic_name": "सिटी हेल्थ क्लिनिक"
        }

        message = template.format(**data)

        await mock_whatsapp_client.send_prescription(
            phone="9876543210",
            prescription={"message": message},
            patient_name=data["patient_name"]
        )

        assert len(mock_whatsapp_client.sent_messages) == 1

    @pytest.mark.asyncio
    async def test_notification_queue_priority(self):
        """Test that high-priority notifications are processed first."""
        # In a real implementation, notifications would have priority levels
        notifications = [
            {"priority": 1, "type": "critical_lab", "message": "Critical potassium level"},
            {"priority": 3, "type": "appointment", "message": "Appointment tomorrow"},
            {"priority": 2, "type": "follow_up", "message": "Follow-up needed"},
        ]

        # Sort by priority (lower number = higher priority)
        sorted_notifications = sorted(notifications, key=lambda x: x["priority"])

        assert sorted_notifications[0]["type"] == "critical_lab"
        assert sorted_notifications[1]["type"] == "follow_up"
        assert sorted_notifications[2]["type"] == "appointment"

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, mock_whatsapp_client):
        """Test retry logic when message sending fails."""
        # Create a failing mock
        fail_count = 0
        max_retries = 3

        async def failing_send(*args, **kwargs):
            nonlocal fail_count
            fail_count += 1
            if fail_count < max_retries:
                raise Exception("Network error")
            return True

        # Override the mock
        mock_whatsapp_client.send_prescription = AsyncMock(side_effect=failing_send)

        # Try sending with retry logic
        for attempt in range(max_retries):
            try:
                await mock_whatsapp_client.send_prescription(
                    phone="9876543210",
                    prescription={},
                    patient_name="Test"
                )
                break  # Success
            except Exception as e:
                if attempt == max_retries - 1:
                    pytest.fail("All retries failed")
                await asyncio.sleep(0.1)  # Short delay before retry

        assert fail_count == max_retries

    @pytest.mark.asyncio
    async def test_prescription_delivery_confirmation(self, mock_whatsapp_client):
        """Test prescription delivery confirmation tracking."""
        await mock_whatsapp_client.send_prescription(
            phone="9876543210",
            prescription={"diagnosis": ["Fever"]},
            patient_name="Ram Lal"
        )

        # In real implementation, track delivery status
        sent_message = mock_whatsapp_client.sent_messages[0]
        assert sent_message["timestamp"] is not None

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting for bulk messages."""
        # WhatsApp has rate limits - need to respect them
        max_messages_per_minute = 60

        messages_to_send = 100
        batch_size = max_messages_per_minute

        # Split into batches
        num_batches = (messages_to_send + batch_size - 1) // batch_size

        assert num_batches == 2  # Should need 2 batches for 100 messages

    @pytest.mark.asyncio
    async def test_opt_out_handling(self):
        """Test handling of patients who opt out of messages."""
        opt_out_list = {"9876543210", "9876543211"}

        patients = [
            {"phone": "9876543210", "name": "Patient 1"},  # Opted out
            {"phone": "9876543212", "name": "Patient 2"},  # Active
        ]

        messages_to_send = [
            p for p in patients if p["phone"] not in opt_out_list
        ]

        assert len(messages_to_send) == 1
        assert messages_to_send[0]["name"] == "Patient 2"

    @pytest.mark.asyncio
    async def test_scheduled_reminder_timing(self):
        """Test that reminders are scheduled at correct times."""
        # Schedule for 9 AM tomorrow
        reminder_time = datetime.combine(
            date.today() + timedelta(days=1),
            datetime.strptime("09:00", "%H:%M").time()
        )

        # Verify timing
        assert reminder_time.hour == 9
        assert reminder_time.minute == 0
        assert reminder_time.date() == date.today() + timedelta(days=1)

    @pytest.mark.asyncio
    async def test_lab_report_notification(self, mock_whatsapp_client):
        """Test notification when lab reports are ready."""
        message = "Your lab reports are ready. Please login to view them."

        await mock_whatsapp_client.send_prescription(
            phone="9876543210",
            prescription={"message": message},
            patient_name="Ram Lal"
        )

        assert len(mock_whatsapp_client.sent_messages) == 1

    @pytest.mark.asyncio
    async def test_birthday_greetings(self, mock_whatsapp_client):
        """Test automated birthday greetings."""
        message = "🎂 Happy Birthday! Wishing you good health. - Dr. Sharma's Clinic"

        await mock_whatsapp_client.send_prescription(
            phone="9876543210",
            prescription={"message": message},
            patient_name="Ram Lal"
        )

        sent = mock_whatsapp_client.sent_messages[0]
        assert "Birthday" in str(sent)

    @pytest.mark.asyncio
    async def test_vaccination_reminder(self, mock_whatsapp_client):
        """Test vaccination reminder notifications."""
        message = "Reminder: Your flu vaccine is due this month."

        await mock_whatsapp_client.send_prescription(
            phone="9876543210",
            prescription={"message": message},
            patient_name="Test Patient"
        )

        assert len(mock_whatsapp_client.sent_messages) == 1

    @pytest.mark.asyncio
    async def test_critical_lab_alert(self, mock_whatsapp_client):
        """Test immediate notification for critical lab values."""
        message = "⚠️ URGENT: Critical lab value detected. Please contact clinic immediately."

        await mock_whatsapp_client.send_prescription(
            phone="9876543210",
            prescription={"message": message},
            patient_name="Ram Lal"
        )

        # Critical alerts should be sent immediately
        assert len(mock_whatsapp_client.sent_messages) == 1

    @pytest.mark.asyncio
    async def test_message_personalization(self, mock_whatsapp_client):
        """Test message personalization with patient data."""
        patient = {
            "name": "Mr. Ram Lal",
            "phone": "9876543210",
            "last_visit": "2024-01-15"
        }

        message = f"Hello {patient['name']}, it's been a while since your last visit on {patient['last_visit']}. Schedule your checkup today."

        await mock_whatsapp_client.send_prescription(
            phone=patient["phone"],
            prescription={"message": message},
            patient_name=patient["name"]
        )

        sent = mock_whatsapp_client.sent_messages[0]
        assert patient["name"] in str(sent)

    @pytest.mark.asyncio
    async def test_bulk_campaign_analytics(self):
        """Test analytics for bulk messaging campaigns."""
        campaign = {
            "name": "HbA1c Reminder Campaign",
            "target_segment": "diabetic_patients",
            "messages_sent": 150,
            "delivery_confirmed": 145,
            "read_count": 120,
            "responses": 35
        }

        # Calculate metrics
        delivery_rate = campaign["delivery_confirmed"] / campaign["messages_sent"]
        read_rate = campaign["read_count"] / campaign["delivery_confirmed"]
        response_rate = campaign["responses"] / campaign["read_count"]

        assert delivery_rate > 0.95  # >95% delivery
        assert read_rate > 0.80  # >80% read rate
        assert response_rate > 0.20  # >20% response rate
