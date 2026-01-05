"""Integration test fixtures for DocAssist EMR.

Provides real databases, mock services, and full service registry for end-to-end testing.
"""

import pytest
import sqlite3
import tempfile
import asyncio
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, Mock, MagicMock
import json
import os

from src.services.database import DatabaseService
from src.services.integration.service_registry import ServiceRegistry
from src.services.integration.context_manager import ContextManager
from src.services.integration.event_bus import EventBus
from src.services.integration.clinical_flow import ClinicalFlow
from src.models.schemas import Patient, Visit, Medication, Investigation, Procedure


# ============== DATABASE FIXTURES ==============

@pytest.fixture
def temp_db_path():
    """Create temporary database file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def real_db(temp_db_path):
    """Real SQLite database for integration tests."""
    db = DatabaseService(temp_db_path)
    db.init_db()
    yield db
    db.close()


# ============== MOCK SERVICE FIXTURES ==============

@pytest.fixture
def mock_llm_service():
    """Mock LLM service with realistic responses."""
    mock = AsyncMock()

    # Mock prescription generation
    async def mock_generate_prescription(clinical_notes: str, **kwargs):
        return {
            "diagnosis": ["Hypertension", "Type 2 Diabetes"],
            "medications": [
                {
                    "drug_name": "Metformin",
                    "strength": "500mg",
                    "form": "tablet",
                    "dose": "1",
                    "frequency": "BD",
                    "duration": "30 days",
                    "instructions": "after meals"
                },
                {
                    "drug_name": "Amlodipine",
                    "strength": "5mg",
                    "form": "tablet",
                    "dose": "1",
                    "frequency": "OD",
                    "duration": "30 days",
                    "instructions": "morning"
                }
            ],
            "investigations": ["HbA1c", "Lipid Profile", "Renal Function Test"],
            "advice": ["Low salt diet", "Regular exercise", "Monitor BP daily"],
            "follow_up": "2 weeks",
            "red_flags": ["Chest pain", "Breathlessness", "Confusion"]
        }

    mock.generate_prescription.side_effect = mock_generate_prescription

    # Mock SOAP extraction
    async def mock_extract_soap(text: str, **kwargs):
        return {
            "subjective": "Patient complains of headache and fever for 2 days",
            "objective": "Temp 101F, BP 130/80, Pulse 88/min",
            "assessment": "Likely viral fever",
            "plan": "Symptomatic treatment, rest, hydration"
        }

    mock.extract_soap.side_effect = mock_extract_soap

    return mock


@pytest.fixture
def mock_speech_to_text():
    """Mock speech-to-text service."""
    mock = AsyncMock()

    async def mock_transcribe(audio: bytes, language: str = "auto"):
        # Return different transcriptions based on audio length for variety
        if len(audio) < 1000:
            return "Patient has fever since two days"
        elif len(audio) < 2000:
            return "BP is 140 over 90, pulse is 88"
        else:
            return "Give tab Paracetamol 500mg three times daily for five days"

    mock.transcribe.side_effect = mock_transcribe
    return mock


@pytest.fixture
def mock_whatsapp_client():
    """Mock WhatsApp client that logs messages."""
    mock = AsyncMock()
    mock.sent_messages = []

    async def mock_send_text(to: str, message: str, **kwargs):
        mock.sent_messages.append({
            "to": to,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "status": "delivered"
        })
        return {
            "message_id": f"wa-{len(mock.sent_messages)}",
            "status": "sent",
            "timestamp": datetime.now().isoformat()
        }

    async def mock_send_document(to: str, document: bytes, filename: str, **kwargs):
        mock.sent_messages.append({
            "to": to,
            "type": "document",
            "filename": filename,
            "size": len(document),
            "timestamp": datetime.now().isoformat(),
            "status": "delivered"
        })
        return {
            "message_id": f"wa-doc-{len(mock.sent_messages)}",
            "status": "sent",
            "timestamp": datetime.now().isoformat()
        }

    async def mock_send_prescription(phone: str, prescription: dict, patient_name: str = None):
        mock.sent_messages.append({
            "to": phone,
            "type": "prescription",
            "patient_name": patient_name,
            "medications": len(prescription.get("medications", [])),
            "timestamp": datetime.now().isoformat(),
            "status": "delivered"
        })
        return {
            "message_id": f"wa-rx-{len(mock.sent_messages)}",
            "status": "sent",
            "timestamp": datetime.now().isoformat()
        }

    mock.send_text.side_effect = mock_send_text
    mock.send_document.side_effect = mock_send_document
    mock.send_prescription.side_effect = mock_send_prescription

    return mock


@pytest.fixture
def mock_voice_capture():
    """Mock voice capture that returns test audio."""
    mock = AsyncMock()

    async def mock_start_listening(consultation_id: str):
        return {"status": "listening", "consultation_id": consultation_id}

    async def mock_stop_listening():
        return {"status": "stopped"}

    async def mock_get_audio_chunk():
        # Return fake audio bytes
        return b'\x00' * 1024

    mock.start_listening.side_effect = mock_start_listening
    mock.stop_listening.side_effect = mock_stop_listening
    mock.get_audio_chunk.side_effect = mock_get_audio_chunk

    return mock


@pytest.fixture
def mock_interaction_checker():
    """Mock drug interaction checker."""
    mock = AsyncMock()

    async def mock_check_interactions(medications: List[Dict], patient_id: int):
        # Return interaction if Aspirin + Warfarin
        interactions = []
        drug_names = [m.get("drug_name", "").lower() for m in medications]

        if "aspirin" in drug_names and "warfarin" in drug_names:
            interactions.append({
                "severity": "high",
                "message": "Aspirin + Warfarin: Increased bleeding risk",
                "drugs": ["Aspirin", "Warfarin"],
                "recommendation": "Monitor INR closely"
            })

        return interactions

    mock.check_interactions.side_effect = mock_check_interactions
    return mock


@pytest.fixture
def mock_red_flag_detector():
    """Mock red flag detector."""
    mock = AsyncMock()

    async def mock_check_text(text: str, patient_data: dict):
        red_flags = []
        text_lower = text.lower()

        # Check for red flag keywords
        if "chest pain" in text_lower:
            red_flags.append({
                "severity": "critical",
                "message": "Chest pain detected - possible cardiac event",
                "action": "Consider ECG, Troponin, immediate evaluation"
            })

        if "breathlessness" in text_lower or "shortness of breath" in text_lower:
            red_flags.append({
                "severity": "high",
                "message": "Breathlessness - possible cardiac/respiratory emergency",
                "action": "Check SpO2, consider CXR"
            })

        return red_flags

    mock.check_text.side_effect = mock_check_text
    return mock


@pytest.fixture
def mock_care_gap_detector():
    """Mock care gap detector."""
    mock = AsyncMock()

    async def mock_check_patient_gaps(patient_id: int):
        # Return some sample care gaps
        return [
            {
                "type": "overdue_screening",
                "message": "HbA1c overdue (last done 4 months ago)",
                "recommendation": "Order HbA1c test",
                "priority": "medium"
            },
            {
                "type": "missing_vaccination",
                "message": "Flu vaccine not recorded this year",
                "recommendation": "Consider flu vaccination",
                "priority": "low"
            }
        ]

    mock.check_patient_gaps.side_effect = mock_check_patient_gaps
    return mock


@pytest.fixture
def mock_audit_logger():
    """Mock audit logger that stores events."""
    mock = AsyncMock()
    mock.events = []

    async def mock_log_event(event_type: str, user_id: str, patient_id: int = None, metadata: dict = None):
        event = {
            "event_type": event_type,
            "user_id": user_id,
            "patient_id": patient_id,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        mock.events.append(event)
        return event

    mock.log_event.side_effect = mock_log_event
    return mock


@pytest.fixture
def mock_practice_analytics():
    """Mock practice analytics service."""
    mock = AsyncMock()
    mock.consultations = []

    async def mock_record_consultation(consultation_id: str, patient_id: int,
                                      doctor_id: str, duration: float,
                                      medications_count: int, alerts_count: int):
        record = {
            "consultation_id": consultation_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "duration": duration,
            "medications_count": medications_count,
            "alerts_count": alerts_count,
            "timestamp": datetime.now().isoformat()
        }
        mock.consultations.append(record)
        return record

    mock.record_consultation.side_effect = mock_record_consultation
    return mock


@pytest.fixture
def mock_reminder_service():
    """Mock reminder service."""
    mock = AsyncMock()
    mock.reminders = []

    async def mock_schedule_reminder(patient_id: int, reminder_type: str,
                                     scheduled_date: date, message: str):
        reminder = {
            "id": len(mock.reminders) + 1,
            "patient_id": patient_id,
            "reminder_type": reminder_type,
            "scheduled_date": scheduled_date.isoformat() if isinstance(scheduled_date, date) else scheduled_date,
            "message": message,
            "status": "scheduled"
        }
        mock.reminders.append(reminder)
        return reminder

    async def mock_get_pending_reminders(patient_id: int):
        return [r for r in mock.reminders if r["patient_id"] == patient_id and r["status"] == "scheduled"]

    mock.schedule_reminder.side_effect = mock_schedule_reminder
    mock.get_pending_reminders.side_effect = mock_get_pending_reminders

    return mock


@pytest.fixture
def mock_patient_summarizer():
    """Mock patient summarizer."""
    mock = AsyncMock()

    async def mock_get_patient_timeline(patient_id: int):
        return [
            {
                "date": (datetime.now() - timedelta(days=30)).date().isoformat(),
                "event": "Visit",
                "description": "Annual checkup"
            },
            {
                "date": (datetime.now() - timedelta(days=60)).date().isoformat(),
                "event": "Lab",
                "description": "HbA1c: 7.2%"
            }
        ]

    mock.get_patient_timeline.side_effect = mock_get_patient_timeline
    return mock


@pytest.fixture
def mock_clinical_nlp():
    """Mock clinical NLP service."""
    mock = AsyncMock()

    async def mock_extract_entities(text: str):
        entities = {
            "symptoms": [],
            "medications": [],
            "investigations": [],
            "vitals": {}
        }

        text_lower = text.lower()

        # Extract symptoms
        if "fever" in text_lower:
            entities["symptoms"].append("fever")
        if "headache" in text_lower:
            entities["symptoms"].append("headache")
        if "cough" in text_lower:
            entities["symptoms"].append("cough")

        # Extract medications
        if "paracetamol" in text_lower:
            entities["medications"].append("Paracetamol")
        if "metformin" in text_lower:
            entities["medications"].append("Metformin")

        # Extract vitals
        import re
        bp_match = re.search(r'(\d{2,3})\s*[/over]\s*(\d{2,3})', text_lower)
        if bp_match:
            entities["vitals"]["bp"] = f"{bp_match.group(1)}/{bp_match.group(2)}"

        return entities

    mock.extract_entities.side_effect = mock_extract_entities
    return mock


@pytest.fixture
def mock_dose_calculator():
    """Mock dose calculator."""
    mock = AsyncMock()

    async def mock_check_dose(medication: dict, patient_data: dict):
        result = {
            "warnings": [],
            "recommended_dose": None
        }

        # Check for pediatric dosing
        age = patient_data.get("age", 0)
        if age < 12 and medication.get("drug_name") == "Aspirin":
            result["warnings"].append("Aspirin not recommended for children under 12")

        # Check for renal dosing
        if patient_data.get("renal_impairment") and medication.get("drug_name") == "Metformin":
            result["warnings"].append("Reduce dose in renal impairment")
            result["recommended_dose"] = "250mg"

        return result

    mock.check_dose.side_effect = mock_check_dose
    return mock


# ============== SERVICE REGISTRY FIXTURE ==============

@pytest.fixture
def full_service_registry(
    real_db,
    mock_llm_service,
    mock_speech_to_text,
    mock_whatsapp_client,
    mock_voice_capture,
    mock_interaction_checker,
    mock_red_flag_detector,
    mock_care_gap_detector,
    mock_audit_logger,
    mock_practice_analytics,
    mock_reminder_service,
    mock_patient_summarizer,
    mock_clinical_nlp,
    mock_dose_calculator
):
    """Full service registry with all services wired."""
    registry = ServiceRegistry()

    # Register all services
    registry.register("database", real_db)
    registry.register("llm", mock_llm_service)
    registry.register("speech_to_text", mock_speech_to_text)
    registry.register("whatsapp_client", mock_whatsapp_client)
    registry.register("voice_capture", mock_voice_capture)
    registry.register("interaction_checker", mock_interaction_checker)
    registry.register("red_flag_detector", mock_red_flag_detector)
    registry.register("care_gap_detector", mock_care_gap_detector)
    registry.register("audit_logger", mock_audit_logger)
    registry.register("practice_analytics", mock_practice_analytics)
    registry.register("reminder_service", mock_reminder_service)
    registry.register("patient_summarizer", mock_patient_summarizer)
    registry.register("clinical_nlp", mock_clinical_nlp)
    registry.register("dose_calculator", mock_dose_calculator)

    yield registry

    # Cleanup
    registry.reset()


# ============== CLINICAL FLOW FIXTURE ==============

@pytest.fixture
def clinical_flow(full_service_registry):
    """Clinical flow orchestrator with full service registry."""
    context_manager = ContextManager()
    event_bus = EventBus()

    flow = ClinicalFlow(
        service_registry=full_service_registry,
        context_manager=context_manager,
        event_bus=event_bus
    )

    yield flow

    # Cleanup
    if context_manager.get_current_context():
        context_manager.close_context()


# ============== TEST DATA FIXTURES ==============

@pytest.fixture
def sample_patient(real_db):
    """Create a sample patient in the database."""
    patient = Patient(
        name="Rajesh Kumar",
        age=45,
        gender="M",
        phone="9876543210",
        address="123 MG Road, Mumbai"
    )
    added = real_db.add_patient(patient)
    return added


@pytest.fixture
def diabetic_patient(real_db):
    """Create a diabetic patient with history."""
    patient = Patient(
        name="Priya Sharma",
        age=52,
        gender="F",
        phone="9876543211",
        address="456 Park Street, Delhi"
    )
    added = real_db.add_patient(patient)

    # Add previous visit with diabetes diagnosis
    visit = Visit(
        patient_id=added.id,
        visit_date=date.today() - timedelta(days=90),
        chief_complaint="Follow-up for diabetes",
        clinical_notes="HbA1c: 7.2%, BP: 140/90",
        diagnosis="Type 2 Diabetes Mellitus, Hypertension",
        prescription_json=json.dumps({
            "medications": [
                {
                    "drug_name": "Metformin",
                    "strength": "500mg",
                    "frequency": "BD"
                }
            ]
        })
    )
    real_db.add_visit(visit)

    return added


@pytest.fixture
def test_audio_bytes():
    """Generate test audio bytes."""
    # Return fake audio data
    return b'\x00' * 2048


@pytest.fixture
def test_prescription():
    """Sample prescription data."""
    return {
        "diagnosis": ["Viral Fever"],
        "medications": [
            {
                "drug_name": "Paracetamol",
                "strength": "500mg",
                "form": "tablet",
                "dose": "1",
                "frequency": "TDS",
                "duration": "5 days",
                "instructions": "after meals"
            }
        ],
        "investigations": ["CBC"],
        "advice": ["Rest", "Plenty of fluids"],
        "follow_up": "5 days",
        "red_flags": ["High fever >103F", "Severe headache"]
    }


# ============== ASYNC FIXTURES ==============

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============== HELPER FIXTURES ==============

@pytest.fixture
def assert_audit_logged(mock_audit_logger):
    """Helper to assert audit events were logged."""
    def _assert(event_type: str, patient_id: int = None):
        events = [e for e in mock_audit_logger.events if e["event_type"] == event_type]
        if patient_id:
            events = [e for e in events if e["patient_id"] == patient_id]
        assert len(events) > 0, f"Expected audit event '{event_type}' not found"
        return events[0]
    return _assert


@pytest.fixture
def assert_whatsapp_sent(mock_whatsapp_client):
    """Helper to assert WhatsApp messages were sent."""
    def _assert(to: str = None, message_type: str = None):
        messages = mock_whatsapp_client.sent_messages
        if to:
            messages = [m for m in messages if m.get("to") == to]
        if message_type:
            messages = [m for m in messages if m.get("type") == message_type]
        assert len(messages) > 0, f"Expected WhatsApp message not found"
        return messages[0]
    return _assert


@pytest.fixture
def assert_reminder_scheduled(mock_reminder_service):
    """Helper to assert reminders were scheduled."""
    def _assert(patient_id: int = None, reminder_type: str = None):
        reminders = mock_reminder_service.reminders
        if patient_id:
            reminders = [r for r in reminders if r["patient_id"] == patient_id]
        if reminder_type:
            reminders = [r for r in reminders if r["reminder_type"] == reminder_type]
        assert len(reminders) > 0, f"Expected reminder not found"
        return reminders[0]
    return _assert
