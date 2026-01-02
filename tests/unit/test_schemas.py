"""Unit tests for Pydantic schemas."""

import pytest
from datetime import date, datetime
from pydantic import ValidationError

from src.models.schemas import (
    Patient, Visit, Investigation, Procedure,
    Medication, Prescription, RAGDocument
)


class TestPatientSchema:
    """Tests for Patient schema."""

    def test_patient_minimal(self):
        """Test patient with only required fields."""
        patient = Patient(name="John Doe")
        assert patient.name == "John Doe"
        assert patient.id is None
        assert patient.uhid is None

    def test_patient_full(self):
        """Test patient with all fields."""
        patient = Patient(
            id=1,
            uhid="EMR-2024-0001",
            name="Ram Lal",
            age=65,
            gender="M",
            phone="9876543210",
            address="Delhi",
            created_at=datetime.now()
        )
        assert patient.name == "Ram Lal"
        assert patient.age == 65
        assert patient.gender == "M"

    def test_patient_invalid_missing_name(self):
        """Test that patient without name fails validation."""
        with pytest.raises(ValidationError):
            Patient()


class TestMedicationSchema:
    """Tests for Medication schema."""

    def test_medication_minimal(self):
        """Test medication with only drug name."""
        med = Medication(drug_name="Paracetamol")
        assert med.drug_name == "Paracetamol"
        assert med.form == "tablet"
        assert med.frequency == "OD"

    def test_medication_full(self):
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
        assert med.instructions == "after meals"


class TestPrescriptionSchema:
    """Tests for Prescription schema."""

    def test_prescription_empty(self):
        """Test empty prescription."""
        rx = Prescription()
        assert rx.diagnosis == []
        assert rx.medications == []
        assert rx.investigations == []
        assert rx.advice == []
        assert rx.follow_up == ""
        assert rx.red_flags == []

    def test_prescription_with_medications(self):
        """Test prescription with medications."""
        rx = Prescription(
            diagnosis=["Hypertension"],
            medications=[
                Medication(drug_name="Amlodipine", strength="5mg")
            ],
            follow_up="1 month"
        )
        assert len(rx.medications) == 1
        assert rx.medications[0].drug_name == "Amlodipine"
        assert rx.diagnosis == ["Hypertension"]

    def test_prescription_complex(self, sample_prescription):
        """Test complex prescription with all fields."""
        assert len(sample_prescription.diagnosis) == 2
        assert len(sample_prescription.medications) == 2
        assert len(sample_prescription.investigations) == 3
        assert len(sample_prescription.advice) == 3
        assert sample_prescription.follow_up == "2 weeks"
        assert len(sample_prescription.red_flags) == 3


class TestVisitSchema:
    """Tests for Visit schema."""

    def test_visit_minimal(self):
        """Test visit with minimal fields."""
        visit = Visit(patient_id=1)
        assert visit.patient_id == 1
        assert visit.chief_complaint == ""
        assert visit.clinical_notes == ""

    def test_visit_full(self, sample_visit):
        """Test visit with all fields."""
        assert sample_visit.patient_id is not None
        assert sample_visit.chief_complaint == "Chest pain x 2 days"
        assert sample_visit.diagnosis == "Acute Coronary Syndrome"
        assert isinstance(sample_visit.visit_date, date)

    def test_visit_invalid_missing_patient_id(self):
        """Test visit without patient_id fails."""
        with pytest.raises(ValidationError):
            Visit()


class TestInvestigationSchema:
    """Tests for Investigation schema."""

    def test_investigation_minimal(self):
        """Test investigation with required fields."""
        inv = Investigation(patient_id=1, test_name="CBC")
        assert inv.patient_id == 1
        assert inv.test_name == "CBC"
        assert inv.is_abnormal is False

    def test_investigation_full(self, sample_investigation):
        """Test investigation with all fields."""
        assert sample_investigation.test_name == "Creatinine"
        assert sample_investigation.result == "1.4"
        assert sample_investigation.unit == "mg/dL"
        assert sample_investigation.is_abnormal is True

    def test_investigation_abnormal_flag(self):
        """Test abnormal flag handling."""
        inv = Investigation(
            patient_id=1,
            test_name="Glucose",
            result="250",
            is_abnormal=True
        )
        assert inv.is_abnormal is True


class TestProcedureSchema:
    """Tests for Procedure schema."""

    def test_procedure_minimal(self):
        """Test procedure with required fields."""
        proc = Procedure(patient_id=1, procedure_name="Blood draw")
        assert proc.patient_id == 1
        assert proc.procedure_name == "Blood draw"

    def test_procedure_full(self, sample_procedure):
        """Test procedure with all fields."""
        assert sample_procedure.procedure_name == "PCI to LAD"
        assert "drug-eluting stent" in sample_procedure.details
        assert sample_procedure.notes == "Procedure successful, patient stable"


class TestRAGDocumentSchema:
    """Tests for RAGDocument schema."""

    def test_rag_document_minimal(self):
        """Test RAG document with required fields."""
        doc = RAGDocument(
            id="visit_123",
            patient_id=1,
            doc_type="visit",
            content="Patient visit notes"
        )
        assert doc.id == "visit_123"
        assert doc.patient_id == 1
        assert doc.doc_type == "visit"
        assert doc.metadata == {}

    def test_rag_document_with_metadata(self):
        """Test RAG document with metadata."""
        doc = RAGDocument(
            id="inv_456",
            patient_id=2,
            doc_type="investigation",
            content="Lab results",
            metadata={"date": "2024-01-15", "test": "CBC"}
        )
        assert doc.metadata["date"] == "2024-01-15"
        assert doc.metadata["test"] == "CBC"
