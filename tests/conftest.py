"""Shared pytest fixtures for DocAssist EMR tests."""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import date, datetime
from unittest.mock import Mock, patch

from src.services.database import DatabaseService
from src.services.llm import LLMService
from src.services.rag import RAGService
from src.services.pdf import PDFService
from src.models.schemas import Patient, Visit, Investigation, Procedure, Prescription, Medication


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_db(temp_dir):
    """Create a fresh SQLite database for each test."""
    db_path = Path(temp_dir) / "test_clinic.db"
    db_service = DatabaseService(db_path=str(db_path))
    yield db_service
    # Cleanup handled by temp_dir fixture


@pytest.fixture
def temp_rag(temp_dir):
    """Create a fresh ChromaDB instance for each test."""
    chroma_path = Path(temp_dir) / "test_chroma"
    rag_service = RAGService(persist_directory=str(chroma_path))
    yield rag_service
    # Cleanup handled by temp_dir fixture


@pytest.fixture
def temp_pdf(temp_dir):
    """Create a PDF service with temporary output directory."""
    pdf_path = Path(temp_dir) / "test_pdfs"
    pdf_service = PDFService(output_dir=str(pdf_path))
    yield pdf_service
    # Cleanup handled by temp_dir fixture


@pytest.fixture
def mock_ollama_available():
    """Mock Ollama to appear available."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen2.5:1.5b"},
                {"name": "qwen2.5:3b"},
                {"name": "qwen2.5:7b"}
            ]
        }
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_ollama_generate():
    """Mock Ollama generate endpoint."""
    def _mock_generate(response_text, json_response=None):
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            if json_response:
                mock_response.json.return_value = {"response": json.dumps(json_response)}
            else:
                mock_response.json.return_value = {"response": response_text}
            mock_post.return_value = mock_response
            yield mock_post
    return _mock_generate


@pytest.fixture
def mock_llm_service(temp_dir):
    """Create LLM service with mocked Ollama."""
    with patch('psutil.virtual_memory') as mock_mem:
        # Mock 8GB RAM to select qwen2.5:3b
        mock_mem.return_value = Mock(total=8 * 1024**3)

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": [{"name": "qwen2.5:3b"}]}
            mock_get.return_value = mock_response

            llm_service = LLMService()
            yield llm_service


@pytest.fixture
def sample_patient():
    """Create a sample patient for testing."""
    return Patient(
        name="Ram Lal",
        age=65,
        gender="M",
        phone="9876543210",
        address="123 Main Street, Delhi"
    )


@pytest.fixture
def sample_patient_data(temp_db, sample_patient):
    """Create a sample patient in the database."""
    patient = temp_db.add_patient(sample_patient)
    return patient


@pytest.fixture
def sample_visit(sample_patient_data):
    """Create a sample visit for testing."""
    return Visit(
        patient_id=sample_patient_data.id,
        visit_date=date(2024, 1, 15),
        chief_complaint="Chest pain x 2 days",
        clinical_notes="Patient presents with substernal chest pain, radiating to left arm. History of hypertension.",
        diagnosis="Acute Coronary Syndrome"
    )


@pytest.fixture
def sample_visit_data(temp_db, sample_visit):
    """Create a sample visit in the database."""
    visit = temp_db.add_visit(sample_visit)
    return visit


@pytest.fixture
def sample_investigation(sample_patient_data):
    """Create a sample investigation for testing."""
    return Investigation(
        patient_id=sample_patient_data.id,
        test_name="Creatinine",
        result="1.4",
        unit="mg/dL",
        reference_range="0.7-1.3",
        test_date=date(2024, 1, 10),
        is_abnormal=True
    )


@pytest.fixture
def sample_procedure(sample_patient_data):
    """Create a sample procedure for testing."""
    return Procedure(
        patient_id=sample_patient_data.id,
        procedure_name="PCI to LAD",
        details="Primary PCI performed, drug-eluting stent placed in LAD",
        procedure_date=date(2023, 12, 15),
        notes="Procedure successful, patient stable"
    )


@pytest.fixture
def sample_prescription():
    """Create a sample prescription for testing."""
    return Prescription(
        diagnosis=["Type 2 Diabetes Mellitus", "Hypertension"],
        medications=[
            Medication(
                drug_name="Metformin",
                strength="500mg",
                form="tablet",
                dose="1",
                frequency="BD",
                duration="30 days",
                instructions="after meals"
            ),
            Medication(
                drug_name="Amlodipine",
                strength="5mg",
                form="tablet",
                dose="1",
                frequency="OD",
                duration="30 days",
                instructions="morning"
            )
        ],
        investigations=["HbA1c", "Lipid Profile", "Renal Function Test"],
        advice=["Low salt diet", "Regular exercise 30 min daily", "Monitor blood sugar"],
        follow_up="2 weeks",
        red_flags=["Severe chest pain", "Breathlessness", "Excessive sweating"]
    )


@pytest.fixture
def mock_prescription_response():
    """Mock LLM response for prescription generation."""
    return {
        "diagnosis": ["Acute Gastroenteritis"],
        "medications": [
            {
                "drug_name": "ORS",
                "strength": "1 sachet",
                "form": "powder",
                "dose": "1",
                "frequency": "after each loose stool",
                "duration": "3 days",
                "instructions": "dissolve in 1L water"
            },
            {
                "drug_name": "Ondansetron",
                "strength": "4mg",
                "form": "tablet",
                "dose": "1",
                "frequency": "TDS",
                "duration": "3 days",
                "instructions": "before meals"
            }
        ],
        "investigations": ["Stool routine", "CBC if fever persists"],
        "advice": ["Plenty of fluids", "Avoid spicy food", "Hand hygiene"],
        "follow_up": "3 days or if symptoms worsen",
        "red_flags": ["Bloody stools", "High fever >102F", "Severe dehydration"]
    }


@pytest.fixture
def mock_rag_context():
    """Mock RAG context for patient queries."""
    return """[VISIT - 2024-01-10]
Visit on 2024-01-10: Chief complaint: Routine checkup. Notes: Patient doing well, BP controlled. Diagnosis: Hypertension - controlled.

[INVESTIGATION - 2024-01-10]
Investigation on 2024-01-10: Creatinine = 1.4 mg/dL (ABNORMAL)

[INVESTIGATION - 2024-01-10]
Investigation on 2024-01-10: HbA1c = 6.8 %"""


@pytest.fixture
def load_fixture_json():
    """Helper to load JSON fixture files."""
    def _load(filename):
        fixture_path = Path(__file__).parent / "fixtures" / filename
        with open(fixture_path, 'r') as f:
            return json.load(f)
    return _load
