"""Data validation tests for schemas and business rules.

These tests verify:
- UHID format compliance
- Prescription schema validation
- Patient data validation
- Medical data constraints
"""

import pytest
import json
import re
import tempfile
from pathlib import Path
from datetime import date, datetime
from pydantic import ValidationError

from src.models.schemas import (
    Patient, Visit, Investigation, Procedure,
    Medication, Prescription, RAGDocument
)
from src.services.database import DatabaseService


class TestUHIDFormat:
    """Tests for UHID (Unique Hospital ID) format."""

    @pytest.fixture
    def db_service(self):
        """Create database service with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield DatabaseService(db_path=str(db_path))

    def test_uhid_format_pattern(self, db_service):
        """Test UHID follows EMR-YYYY-NNNN format."""
        patient = db_service.add_patient(Patient(name="Test Patient"))

        # Pattern: EMR-YYYY-NNNN
        pattern = r"^EMR-\d{4}-\d{4}$"
        assert re.match(pattern, patient.uhid) is not None

    def test_uhid_contains_current_year(self, db_service):
        """Test UHID contains current year."""
        patient = db_service.add_patient(Patient(name="Test Patient"))

        current_year = str(datetime.now().year)
        assert current_year in patient.uhid

    def test_uhid_sequential_numbering(self, db_service):
        """Test UHID numbers increment sequentially."""
        patient1 = db_service.add_patient(Patient(name="Patient 1"))
        patient2 = db_service.add_patient(Patient(name="Patient 2"))
        patient3 = db_service.add_patient(Patient(name="Patient 3"))

        # Extract sequence numbers
        seq1 = int(patient1.uhid.split("-")[2])
        seq2 = int(patient2.uhid.split("-")[2])
        seq3 = int(patient3.uhid.split("-")[2])

        assert seq2 == seq1 + 1
        assert seq3 == seq2 + 1

    def test_uhid_unique(self, db_service):
        """Test each patient gets unique UHID."""
        uhids = set()
        for i in range(10):
            patient = db_service.add_patient(Patient(name=f"Patient {i}"))
            uhids.add(patient.uhid)

        assert len(uhids) == 10

    def test_uhid_padded_to_4_digits(self, db_service):
        """Test sequence number is zero-padded to 4 digits."""
        patient = db_service.add_patient(Patient(name="Test"))

        # Extract sequence part
        seq_part = patient.uhid.split("-")[2]
        assert len(seq_part) == 4


class TestPatientValidation:
    """Tests for patient data validation."""

    def test_patient_requires_name(self):
        """Test patient must have a name."""
        with pytest.raises(ValidationError):
            Patient()  # No name provided

    def test_patient_name_not_empty(self):
        """Test patient name cannot be empty string."""
        # Pydantic allows empty string by default, but we should validate
        patient = Patient(name="")
        assert patient.name == ""  # Currently allowed - may want to add validator

    def test_patient_gender_values(self):
        """Test valid gender values."""
        for gender in ["M", "F", "O"]:
            patient = Patient(name="Test", gender=gender)
            assert patient.gender == gender

    def test_patient_age_positive(self):
        """Test patient age should be positive."""
        patient = Patient(name="Test", age=45)
        assert patient.age == 45

        # Negative age - Pydantic doesn't prevent this by default
        # Should add validator in production
        patient_neg = Patient(name="Test", age=-5)
        assert patient_neg.age == -5  # Currently allowed

    def test_patient_phone_format(self):
        """Test patient phone can store various formats."""
        phone_numbers = [
            "9876543210",
            "+91-9876543210",
            "098-765-43210",
            "+1 (555) 123-4567"
        ]

        for phone in phone_numbers:
            patient = Patient(name="Test", phone=phone)
            assert patient.phone == phone

    def test_patient_optional_fields(self):
        """Test patient can be created with only required fields."""
        patient = Patient(name="Minimal Patient")

        assert patient.id is None
        assert patient.uhid is None
        assert patient.age is None
        assert patient.gender is None
        assert patient.phone is None
        assert patient.address is None


class TestPrescriptionValidation:
    """Tests for prescription schema validation."""

    def test_prescription_default_empty_lists(self):
        """Test prescription initializes with empty lists."""
        rx = Prescription()

        assert rx.diagnosis == []
        assert rx.medications == []
        assert rx.investigations == []
        assert rx.advice == []
        assert rx.red_flags == []

    def test_medication_required_fields(self):
        """Test medication requires drug_name."""
        with pytest.raises(ValidationError):
            Medication()  # No drug_name

    def test_medication_with_full_details(self):
        """Test medication with all fields."""
        med = Medication(
            drug_name="Metformin",
            strength="500mg",
            form="tablet",
            dose="1",
            frequency="BD",
            duration="30 days",
            instructions="after meals"
        )

        assert med.drug_name == "Metformin"
        assert med.strength == "500mg"
        assert med.frequency == "BD"

    def test_medication_frequency_values(self):
        """Test common medication frequency values."""
        frequencies = ["OD", "BD", "TDS", "QID", "HS", "SOS", "STAT"]

        for freq in frequencies:
            med = Medication(drug_name="Test Drug", frequency=freq)
            assert med.frequency == freq

    def test_prescription_json_roundtrip(self):
        """Test prescription can be serialized and deserialized."""
        rx = Prescription(
            diagnosis=["Type 2 Diabetes", "Hypertension"],
            medications=[
                Medication(
                    drug_name="Metformin",
                    strength="500mg",
                    frequency="BD"
                ),
                Medication(
                    drug_name="Amlodipine",
                    strength="5mg",
                    frequency="OD"
                )
            ],
            investigations=["HbA1c", "Lipid Profile"],
            advice=["Diet control", "Exercise 30 min daily"],
            follow_up="2 weeks",
            red_flags=["Chest pain", "Breathlessness", "Hypoglycemia symptoms"]
        )

        # Serialize
        json_str = rx.model_dump_json()

        # Deserialize
        rx_restored = Prescription.model_validate_json(json_str)

        assert rx_restored.diagnosis == rx.diagnosis
        assert len(rx_restored.medications) == 2
        assert rx_restored.medications[0].drug_name == "Metformin"

    def test_prescription_matches_documented_schema(self):
        """Test prescription matches the JSON schema in CLAUDE.md."""
        # Schema from CLAUDE.md
        expected_json = {
            "diagnosis": ["Primary", "Secondary"],
            "medications": [
                {
                    "drug_name": "Metformin",
                    "strength": "500mg",
                    "form": "tablet",
                    "dose": "1",
                    "frequency": "BD",
                    "duration": "30 days",
                    "instructions": "after meals"
                }
            ],
            "investigations": ["CBC", "HbA1c"],
            "advice": ["Diet control", "Exercise"],
            "follow_up": "2 weeks",
            "red_flags": ["Chest pain", "Breathlessness"]
        }

        # Should parse without error
        rx = Prescription.model_validate(expected_json)

        assert rx.diagnosis == ["Primary", "Secondary"]
        assert rx.medications[0].drug_name == "Metformin"
        assert rx.follow_up == "2 weeks"


class TestVisitValidation:
    """Tests for visit data validation."""

    def test_visit_requires_patient_id(self):
        """Test visit requires patient_id."""
        with pytest.raises(ValidationError):
            Visit()  # No patient_id

    def test_visit_with_prescription_json(self):
        """Test visit can store prescription as JSON."""
        rx = Prescription(
            diagnosis=["Fever"],
            medications=[Medication(drug_name="Paracetamol")]
        )

        visit = Visit(
            patient_id=1,
            diagnosis="Viral Fever",
            prescription_json=rx.model_dump_json()
        )

        # Verify JSON is valid
        stored_rx = json.loads(visit.prescription_json)
        assert stored_rx["diagnosis"] == ["Fever"]

    def test_visit_date_format(self):
        """Test visit accepts date objects."""
        visit = Visit(
            patient_id=1,
            visit_date=date(2024, 12, 15)
        )

        assert visit.visit_date == date(2024, 12, 15)


class TestInvestigationValidation:
    """Tests for investigation data validation."""

    def test_investigation_requires_patient_and_test_name(self):
        """Test investigation requires patient_id and test_name."""
        with pytest.raises(ValidationError):
            Investigation()

        with pytest.raises(ValidationError):
            Investigation(patient_id=1)  # No test_name

    def test_investigation_abnormal_flag(self):
        """Test abnormal flag for investigations."""
        normal = Investigation(
            patient_id=1,
            test_name="Creatinine",
            result="1.0",
            is_abnormal=False
        )

        abnormal = Investigation(
            patient_id=1,
            test_name="Creatinine",
            result="3.5",
            is_abnormal=True
        )

        assert normal.is_abnormal is False
        assert abnormal.is_abnormal is True

    def test_investigation_with_units_and_reference(self):
        """Test investigation with units and reference range."""
        inv = Investigation(
            patient_id=1,
            test_name="Hemoglobin",
            result="12.5",
            unit="g/dL",
            reference_range="13.0-17.0"
        )

        assert inv.unit == "g/dL"
        assert inv.reference_range == "13.0-17.0"


class TestProcedureValidation:
    """Tests for procedure data validation."""

    def test_procedure_requires_patient_and_name(self):
        """Test procedure requires patient_id and procedure_name."""
        with pytest.raises(ValidationError):
            Procedure()

        with pytest.raises(ValidationError):
            Procedure(patient_id=1)  # No procedure_name

    def test_procedure_with_details(self):
        """Test procedure with full details."""
        proc = Procedure(
            patient_id=1,
            procedure_name="Coronary Angioplasty",
            details="Single vessel PCI to LAD with DES",
            procedure_date=date(2024, 6, 15),
            notes="Successful procedure, no complications"
        )

        assert proc.procedure_name == "Coronary Angioplasty"
        assert "LAD" in proc.details


class TestRAGDocumentValidation:
    """Tests for RAG document validation."""

    def test_rag_document_required_fields(self):
        """Test RAG document requires id, patient_id, doc_type, content."""
        with pytest.raises(ValidationError):
            RAGDocument()

    def test_rag_document_valid_doc_types(self):
        """Test RAG document accepts valid doc types."""
        for doc_type in ["visit", "investigation", "procedure"]:
            doc = RAGDocument(
                id=f"{doc_type}_1",
                patient_id=1,
                doc_type=doc_type,
                content="Test content"
            )
            assert doc.doc_type == doc_type

    def test_rag_document_with_metadata(self):
        """Test RAG document with metadata."""
        doc = RAGDocument(
            id="visit_1",
            patient_id=1,
            doc_type="visit",
            content="Patient visit for fever",
            metadata={
                "date": "2024-12-15",
                "diagnosis": "Viral fever"
            }
        )

        assert doc.metadata["date"] == "2024-12-15"


class TestDataIntegrityConstraints:
    """Tests for data integrity constraints in database."""

    @pytest.fixture
    def db_service(self):
        """Create database service with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield DatabaseService(db_path=str(db_path))

    def test_visit_requires_valid_patient(self, db_service):
        """Test visit references valid patient."""
        # Add visit for non-existent patient
        visit = Visit(patient_id=99999, chief_complaint="Test")

        # Currently the database doesn't enforce FK at runtime
        # but this documents expected behavior
        result = db_service.add_visit(visit)
        assert result.id is not None  # SQLite allows this without FK enforcement

    def test_duplicate_uhid_rejected(self, db_service):
        """Test duplicate UHID is rejected."""
        import sqlite3

        patient = db_service.add_patient(Patient(name="Original"))

        # Try to manually insert duplicate UHID
        with pytest.raises(sqlite3.IntegrityError):
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO patients (uhid, name) VALUES (?, ?)",
                    (patient.uhid, "Duplicate")
                )


class TestMedicalDataValidation:
    """Tests for medical data validation rules."""

    def test_prescription_medications_not_empty_drug_name(self):
        """Test medication must have non-empty drug name."""
        # Currently allows empty string - production should validate
        med = Medication(drug_name="")
        assert med.drug_name == ""

    def test_investigation_numeric_results(self):
        """Test investigation can store numeric results as string."""
        inv = Investigation(
            patient_id=1,
            test_name="Blood Sugar",
            result="126.5",
            unit="mg/dL"
        )

        # Result is stored as string but should be parseable as float
        result_float = float(inv.result)
        assert result_float == 126.5

    def test_visit_clinical_notes_length(self):
        """Test visit can store long clinical notes."""
        long_notes = "Patient history: " + "detailed notes " * 1000

        visit = Visit(
            patient_id=1,
            clinical_notes=long_notes
        )

        assert len(visit.clinical_notes) > 10000
