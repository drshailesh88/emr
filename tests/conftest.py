"""Shared pytest fixtures for DocAssist EMR tests."""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from datetime import date, datetime

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use lazy imports to avoid issues with missing dependencies
def _get_models():
    from src.models.schemas import Patient, Medication, Prescription, Visit, Investigation, Procedure
    return Patient, Medication, Prescription, Visit, Investigation, Procedure

def _get_database_service():
    from src.services.database import DatabaseService
    return DatabaseService

def _get_rag_service():
    from src.services.rag import RAGService
    return RAGService

def _get_pdf_service():
    from src.services.pdf import PDFService
    return PDFService

# For backwards compatibility, create aliases
Patient, Medication, Prescription, Visit, Investigation, Procedure = _get_models()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_db_path(temp_dir):
    """Create a temporary database path."""
    return os.path.join(temp_dir, "test_clinic.db")


@pytest.fixture
def db_service(temp_db_path):
    """Create a fresh DatabaseService for testing."""
    DatabaseService = _get_database_service()
    service = DatabaseService(db_path=temp_db_path)
    yield service


@pytest.fixture
def temp_chroma_dir(temp_dir):
    """Create a temporary ChromaDB directory."""
    return os.path.join(temp_dir, "test_chroma")


@pytest.fixture
def rag_service(temp_chroma_dir):
    """Create a fresh RAGService for testing."""
    RAGService = _get_rag_service()
    service = RAGService(persist_directory=temp_chroma_dir)
    yield service


@pytest.fixture
def temp_pdf_dir(temp_dir):
    """Create a temporary PDF output directory."""
    pdf_dir = os.path.join(temp_dir, "prescriptions")
    os.makedirs(pdf_dir, exist_ok=True)
    return pdf_dir


@pytest.fixture
def pdf_service(temp_pdf_dir):
    """Create a PDFService with temp output directory."""
    PDFService = _get_pdf_service()
    service = PDFService(output_dir=temp_pdf_dir)
    yield service


@pytest.fixture
def sample_patient():
    """Create a sample patient for testing."""
    return Patient(
        name="Ram Lal",
        age=65,
        gender="M",
        phone="9876543210",
        address="123 MG Road, Delhi"
    )


@pytest.fixture
def sample_patient_with_id():
    """Create a sample patient with ID and UHID."""
    return Patient(
        id=1,
        uhid="EMR-2024-0001",
        name="Ram Lal",
        age=65,
        gender="M",
        phone="9876543210",
        address="123 MG Road, Delhi",
        created_at=datetime.now()
    )


@pytest.fixture
def sample_medication():
    """Create a sample medication."""
    return Medication(
        drug_name="Metformin",
        strength="500mg",
        form="tablet",
        dose="1",
        frequency="BD",
        duration="30 days",
        instructions="after meals"
    )


@pytest.fixture
def sample_prescription(sample_medication):
    """Create a sample prescription."""
    return Prescription(
        diagnosis=["Type 2 Diabetes Mellitus", "Essential Hypertension"],
        medications=[sample_medication],
        investigations=["HbA1c", "Fasting Blood Sugar", "Lipid Profile"],
        advice=["Diet control", "Regular exercise", "Monitor blood sugar"],
        follow_up="1 month",
        red_flags=["Hypoglycemia symptoms", "Chest pain", "Breathlessness"]
    )


@pytest.fixture
def sample_visit():
    """Create a sample visit."""
    return Visit(
        patient_id=1,
        visit_date=date.today(),
        chief_complaint="Fever and headache for 2 days",
        clinical_notes="Patient presents with fever 101F, mild headache. No vomiting or rash.",
        diagnosis="Viral fever",
        prescription_json='{"diagnosis": ["Viral fever"], "medications": []}'
    )


@pytest.fixture
def sample_investigation():
    """Create a sample investigation."""
    return Investigation(
        patient_id=1,
        test_name="Creatinine",
        result="1.4",
        unit="mg/dL",
        reference_range="0.7-1.3",
        test_date=date.today(),
        is_abnormal=True
    )


@pytest.fixture
def sample_procedure():
    """Create a sample procedure."""
    return Procedure(
        patient_id=1,
        procedure_name="PCI to LAD",
        details="Drug-eluting stent placed",
        procedure_date=date.today(),
        notes="Successful procedure, no complications"
    )


@pytest.fixture
def populated_db(db_service, sample_patient, sample_visit, sample_investigation, sample_procedure):
    """Create a database with sample data."""
    # Add patient
    patient = db_service.add_patient(sample_patient)

    # Update visit with correct patient_id
    sample_visit.patient_id = patient.id
    sample_investigation.patient_id = patient.id
    sample_procedure.patient_id = patient.id

    # Add records
    db_service.add_visit(sample_visit)
    db_service.add_investigation(sample_investigation)
    db_service.add_procedure(sample_procedure)

    return db_service, patient
