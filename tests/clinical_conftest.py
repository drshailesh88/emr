"""Enhanced pytest configuration and fixtures for clinical workflow testing.

This module provides comprehensive fixtures for testing the complete clinical
consultation workflow, including mocked services and realistic test data.
"""

import asyncio
import json
import pytest
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import tempfile
import sqlite3

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.schemas import (
    Patient, Visit, Investigation, Medication, Prescription,
    PatientSnapshot, SafetyAlert, PrescriptionDraft
)
from src.services.database import DatabaseService
from src.services.safety import PrescriptionSafetyChecker
from src.services.clinical_rules import check_critical_value


# ============== MOCK SERVICES ==============

@pytest.fixture
def mock_database():
    """In-memory SQLite database for testing."""
    temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = temp_db_file.name
    temp_db_file.close()

    db = DatabaseService(db_path=db_path)
    db.init_db()

    yield db

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def mock_llm_service():
    """Mock LLM service that returns predefined responses."""
    mock_llm = Mock()

    # Mock prescription generation
    def generate_prescription_mock(clinical_notes, patient_context=None):
        prescription = {
            "diagnosis": ["Viral Fever"],
            "medications": [
                {
                    "drug_name": "Paracetamol",
                    "strength": "500mg",
                    "form": "tablet",
                    "dose": "1",
                    "frequency": "TDS",
                    "duration": "3 days",
                    "instructions": "after meals"
                }
            ],
            "investigations": ["CBC"],
            "advice": ["Rest", "Plenty of fluids"],
            "follow_up": "3 days if symptoms persist",
            "red_flags": ["High fever >103F", "Severe headache"]
        }
        return True, Prescription(**prescription), json.dumps(prescription)

    mock_llm.generate_prescription = Mock(side_effect=generate_prescription_mock)

    # Mock RAG query
    def query_patient_records_mock(context, query):
        return True, "The last creatinine level was 1.4 mg/dL on 2024-01-10."

    mock_llm.query_patient_records = Mock(side_effect=query_patient_records_mock)

    return mock_llm


@pytest.fixture
def mock_whatsapp_client():
    """Mock WhatsApp client that logs instead of sending."""
    mock_client = Mock()
    sent_messages = []

    async def send_prescription_mock(phone, prescription, patient_name=None):
        sent_messages.append({
            "phone": phone,
            "prescription": prescription,
            "patient_name": patient_name,
            "timestamp": datetime.now()
        })
        return True

    mock_client.send_prescription = AsyncMock(side_effect=send_prescription_mock)
    mock_client.sent_messages = sent_messages

    return mock_client


@pytest.fixture
def mock_speech_to_text():
    """Mock speech-to-text service."""
    mock_stt = Mock()

    async def transcribe_mock(audio_bytes):
        # Return different transcriptions based on audio length
        if len(audio_bytes) < 100:
            return "Patient has fever and headache for two days."
        else:
            return "Patient complains of chest pain radiating to left arm, shortness of breath, and sweating. Started 30 minutes ago."

    mock_stt.transcribe = AsyncMock(side_effect=transcribe_mock)

    return mock_stt


@pytest.fixture
def mock_clinical_nlp():
    """Mock clinical NLP service for entity extraction."""
    mock_nlp = Mock()

    async def extract_entities_mock(text):
        entities = {
            "symptoms": [],
            "medications": [],
            "investigations": [],
            "vitals": {}
        }

        # Simple keyword matching
        text_lower = text.lower()

        if "fever" in text_lower:
            entities["symptoms"].append("Fever")
        if "headache" in text_lower:
            entities["symptoms"].append("Headache")
        if "chest pain" in text_lower:
            entities["symptoms"].append("Chest pain")
        if "shortness of breath" in text_lower:
            entities["symptoms"].append("Dyspnea")

        if "paracetamol" in text_lower:
            entities["medications"].append("Paracetamol")
        if "aspirin" in text_lower:
            entities["medications"].append("Aspirin")

        return entities

    mock_nlp.extract_entities = AsyncMock(side_effect=extract_entities_mock)

    return mock_nlp


@pytest.fixture
def mock_red_flag_detector():
    """Mock red flag detector service."""
    mock_detector = Mock()

    async def check_text_mock(text, patient_data=None):
        red_flags = []
        text_lower = text.lower()

        # Check for cardiac red flags
        cardiac_keywords = ["chest pain", "shortness of breath", "sweating", "radiating to arm"]
        if any(keyword in text_lower for keyword in cardiac_keywords):
            red_flags.append({
                "type": "cardiac",
                "severity": "critical",
                "message": "⚠️ CARDIAC RED FLAG: Consider acute coronary syndrome",
                "recommended_actions": [
                    "ECG immediately",
                    "Cardiac enzymes (Troponin I/T)",
                    "Aspirin 325mg stat if no contraindications"
                ]
            })

        # Check for neurological red flags
        if "severe headache" in text_lower or "worst headache" in text_lower:
            red_flags.append({
                "type": "neurological",
                "severity": "high",
                "message": "⚠️ NEURO RED FLAG: Rule out subarachnoid hemorrhage",
                "recommended_actions": [
                    "Neurological examination",
                    "Consider CT head if sudden onset"
                ]
            })

        return red_flags

    mock_detector.check_text = AsyncMock(side_effect=check_text_mock)

    return mock_detector


@pytest.fixture
def mock_audit_logger():
    """Mock audit logger that stores events in memory."""
    mock_logger = Mock()
    audit_events = []

    async def log_event_mock(event_type, user_id, patient_id=None, metadata=None):
        audit_events.append({
            "event_type": event_type,
            "user_id": user_id,
            "patient_id": patient_id,
            "metadata": metadata,
            "timestamp": datetime.now()
        })
        return True

    mock_logger.log_event = AsyncMock(side_effect=log_event_mock)
    mock_logger.audit_events = audit_events

    return mock_logger


# ============== TEST DATA FIXTURES ==============

@pytest.fixture
def sample_patient(mock_database):
    """Sample patient for testing."""
    patient = Patient(
        name="Ram Lal",
        age=65,
        gender="M",
        phone="9876543210",
        address="Delhi"
    )
    return mock_database.add_patient(patient)


@pytest.fixture
def sample_patient_snapshot():
    """Sample patient clinical snapshot."""
    return PatientSnapshot(
        patient_id=1,
        uhid="EMR-2024-0001",
        demographics="Ram Lal, 65M",
        active_problems=["Type 2 Diabetes Mellitus", "Hypertension"],
        current_medications=[
            Medication(
                drug_name="Metformin",
                strength="500mg",
                dose="1",
                frequency="BD",
                duration="ongoing"
            ),
            Medication(
                drug_name="Ramipril",
                strength="5mg",
                dose="1",
                frequency="OD",
                duration="ongoing"
            )
        ],
        allergies=["Penicillin"],
        key_labs={
            "creatinine": {"value": 1.2, "date": "2024-01-01", "unit": "mg/dL"},
            "hba1c": {"value": 7.5, "date": "2023-12-15", "unit": "%"},
            "potassium": {"value": 4.2, "date": "2024-01-01", "unit": "mEq/L"}
        },
        vitals={
            "BP": "140/90",
            "Weight": "72kg",
            "BMI": "26.5"
        },
        blood_group="B+",
        code_status="FULL",
        on_anticoagulation=False,
        last_visit_date=date(2024, 1, 1),
        major_events=["Started on insulin - 2023-06-15"]
    )


@pytest.fixture
def sample_visit():
    """Sample visit data."""
    return Visit(
        patient_id=1,
        visit_date=date.today(),
        chief_complaint="Fever and headache for 2 days",
        clinical_notes="Patient presents with fever up to 101F, headache, body aches. No cough or respiratory symptoms.",
        diagnosis="Viral Fever"
    )


@pytest.fixture
def sample_prescription():
    """Sample prescription."""
    return Prescription(
        diagnosis=["Viral Fever"],
        medications=[
            Medication(
                drug_name="Paracetamol",
                strength="500mg",
                form="tablet",
                dose="1",
                frequency="TDS",
                duration="3 days",
                instructions="after meals"
            ),
            Medication(
                drug_name="Cetirizine",
                strength="10mg",
                form="tablet",
                dose="1",
                frequency="OD",
                duration="3 days",
                instructions="at bedtime"
            )
        ],
        investigations=["CBC"],
        advice=["Rest", "Plenty of fluids", "Light diet"],
        follow_up="3 days if fever persists",
        red_flags=["High fever >103F", "Severe headache", "Difficulty breathing"]
    )


@pytest.fixture
def sample_prescription_with_interaction():
    """Sample prescription with drug interaction."""
    return Prescription(
        diagnosis=["Atrial Fibrillation"],
        medications=[
            Medication(
                drug_name="Warfarin",
                strength="5mg",
                dose="1",
                frequency="OD",
                duration="ongoing"
            ),
            Medication(
                drug_name="Aspirin",
                strength="75mg",
                dose="1",
                frequency="OD",
                duration="ongoing"
            )
        ],
        investigations=["INR"],
        advice=["Regular INR monitoring"],
        follow_up="1 week"
    )


@pytest.fixture
def sample_diabetic_patient():
    """Sample diabetic patient snapshot."""
    return PatientSnapshot(
        patient_id=2,
        uhid="EMR-2024-0002",
        demographics="Sita Devi, 58F",
        active_problems=["Type 2 Diabetes Mellitus", "Diabetic Neuropathy"],
        current_medications=[
            Medication(
                drug_name="Metformin",
                strength="1000mg",
                dose="1",
                frequency="BD"
            ),
            Medication(
                drug_name="Glimepiride",
                strength="2mg",
                dose="1",
                frequency="OD"
            )
        ],
        allergies=[],
        key_labs={
            "hba1c": {"value": 9.2, "date": "2024-01-10", "unit": "%"},
            "fbs": {"value": 180, "date": "2024-01-15", "unit": "mg/dL"},
            "creatinine": {"value": 0.9, "date": "2024-01-10", "unit": "mg/dL"}
        },
        vitals={
            "BP": "130/80",
            "Weight": "68kg",
            "BMI": "28.3"
        },
        blood_group="O+",
        on_anticoagulation=False
    )


# ============== SERVICE REGISTRY FIXTURES ==============

@pytest.fixture
def service_registry(
    mock_database,
    mock_llm_service,
    mock_whatsapp_client,
    mock_speech_to_text,
    mock_clinical_nlp,
    mock_red_flag_detector,
    mock_audit_logger
):
    """Pre-populated service registry for testing."""
    from src.services.integration.service_registry import ServiceRegistry

    registry = ServiceRegistry()

    # Register all services
    registry.register("database", mock_database)
    registry.register("llm", mock_llm_service)
    registry.register("whatsapp_client", mock_whatsapp_client)
    registry.register("speech_to_text", mock_speech_to_text)
    registry.register("clinical_nlp", mock_clinical_nlp)
    registry.register("red_flag_detector", mock_red_flag_detector)
    registry.register("audit_logger", mock_audit_logger)

    # Add mock implementations for other services
    registry.register("interaction_checker", create_mock_interaction_checker())
    registry.register("dose_calculator", create_mock_dose_calculator())
    registry.register("patient_summarizer", create_mock_patient_summarizer())
    registry.register("care_gap_detector", create_mock_care_gap_detector())
    registry.register("reminder_service", create_mock_reminder_service())
    registry.register("practice_analytics", create_mock_practice_analytics())

    return registry


def create_mock_interaction_checker():
    """Create mock interaction checker."""
    mock = Mock()

    async def check_interactions_mock(medications, patient_id):
        interactions = []

        # Check for warfarin + aspirin
        med_names = [m.get("drug_name", "").lower() for m in medications]
        if "warfarin" in med_names and "aspirin" in med_names:
            interactions.append({
                "severity": "HIGH",
                "drugs": ["Warfarin", "Aspirin"],
                "message": "Increased bleeding risk with concurrent use",
                "action": "WARN"
            })

        return interactions

    mock.check_interactions = AsyncMock(side_effect=check_interactions_mock)
    return mock


def create_mock_dose_calculator():
    """Create mock dose calculator."""
    mock = Mock()

    async def check_dose_mock(medication, patient_data):
        warnings = []

        # Simple dose checking
        if medication.get("drug_name", "").lower() == "paracetamol":
            # Check if dose exceeds 4000mg/day
            pass

        return {
            "warnings": warnings,
            "recommended_dose": None
        }

    mock.check_dose = AsyncMock(side_effect=check_dose_mock)
    return mock


def create_mock_patient_summarizer():
    """Create mock patient summarizer."""
    mock = Mock()

    async def get_patient_timeline_mock(patient_id):
        return [
            {
                "date": "2024-01-15",
                "type": "visit",
                "summary": "Routine checkup - BP controlled"
            },
            {
                "date": "2024-01-10",
                "type": "lab",
                "summary": "HbA1c: 7.5%"
            }
        ]

    mock.get_patient_timeline = AsyncMock(side_effect=get_patient_timeline_mock)
    return mock


def create_mock_care_gap_detector():
    """Create mock care gap detector."""
    mock = Mock()

    async def check_patient_gaps_mock(patient_id):
        return [
            {
                "gap_type": "screening",
                "message": "HbA1c due (last done 3 months ago)",
                "priority": "medium"
            }
        ]

    mock.check_patient_gaps = AsyncMock(side_effect=check_patient_gaps_mock)
    return mock


def create_mock_reminder_service():
    """Create mock reminder service."""
    mock = Mock()

    async def get_pending_reminders_mock(patient_id):
        return []

    async def schedule_reminder_mock(patient_id, reminder_type, scheduled_date, message):
        return {
            "id": 1,
            "patient_id": patient_id,
            "type": reminder_type,
            "scheduled_date": scheduled_date,
            "message": message
        }

    mock.get_pending_reminders = AsyncMock(side_effect=get_pending_reminders_mock)
    mock.schedule_reminder = AsyncMock(side_effect=schedule_reminder_mock)

    return mock


def create_mock_practice_analytics():
    """Create mock practice analytics service."""
    mock = Mock()

    async def record_consultation_mock(consultation_id, patient_id, doctor_id, **kwargs):
        return True

    mock.record_consultation = AsyncMock(side_effect=record_consultation_mock)

    return mock


@pytest.fixture
def clinical_flow(service_registry):
    """Initialized ClinicalFlow with all mocked services."""
    from src.services.integration.clinical_flow import ClinicalFlow
    from src.services.integration.context_manager import ContextManager
    from src.services.integration.event_bus import EventBus

    context_manager = ContextManager()
    event_bus = EventBus()

    flow = ClinicalFlow(
        services=None,
        context_manager=context_manager,
        event_bus=event_bus,
        service_registry=service_registry
    )

    return flow


# ============== PYTEST CONFIGURATION ==============

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_collection_modifyitems(config, items):
    """Automatically mark async tests."""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
