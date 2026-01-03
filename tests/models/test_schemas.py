"""Tests for Pydantic models in schemas.py."""

import pytest
from datetime import date, datetime
from pydantic import ValidationError

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.schemas import (
    Patient, Medication, Prescription, Visit,
    Investigation, Procedure, RAGDocument
)


class TestPatientModel:
    """Tests for Patient model."""

    def test_patient_creation_with_required_fields(self):
        """Test patient can be created with only required name."""
        patient = Patient(name="John Doe")
        assert patient.name == "John Doe"
        assert patient.id is None
        assert patient.uhid is None
        assert patient.age is None
        assert patient.gender is None

    def test_patient_creation_with_all_fields(self):
        """Test patient with all fields populated."""
        now = datetime.now()
        patient = Patient(
            id=1,
            uhid="EMR-2024-0001",
            name="Ram Lal",
            age=65,
            gender="M",
            phone="9876543210",
            address="123 MG Road, Delhi",
            created_at=now
        )
        assert patient.id == 1
        assert patient.uhid == "EMR-2024-0001"
        assert patient.name == "Ram Lal"
        assert patient.age == 65
        assert patient.gender == "M"
        assert patient.phone == "9876543210"
        assert patient.address == "123 MG Road, Delhi"
        assert patient.created_at == now

    def test_patient_missing_name_raises_error(self):
        """Test that patient without name raises validation error."""
        with pytest.raises(ValidationError):
            Patient()

    def test_patient_gender_options(self):
        """Test different gender values."""
        for gender in ["M", "F", "O"]:
            patient = Patient(name="Test", gender=gender)
            assert patient.gender == gender

    def test_patient_model_dict(self):
        """Test patient can be converted to dict."""
        patient = Patient(name="Test", age=30)
        data = patient.model_dump()
        assert data["name"] == "Test"
        assert data["age"] == 30


class TestMedicationModel:
    """Tests for Medication model."""

    def test_medication_creation_required_only(self):
        """Test medication with only drug_name."""
        med = Medication(drug_name="Paracetamol")
        assert med.drug_name == "Paracetamol"
        assert med.strength == ""
        assert med.form == "tablet"
        assert med.dose == "1"
        assert med.frequency == "OD"

    def test_medication_creation_full(self):
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
        assert med.form == "tablet"
        assert med.dose == "1"
        assert med.frequency == "BD"
        assert med.duration == "30 days"
        assert med.instructions == "after meals"

    def test_medication_different_forms(self):
        """Test different medication forms."""
        forms = ["tablet", "capsule", "syrup", "injection", "cream", "drops"]
        for form in forms:
            med = Medication(drug_name="Test", form=form)
            assert med.form == form

    def test_medication_frequencies(self):
        """Test different dosing frequencies."""
        frequencies = ["OD", "BD", "TDS", "QID", "HS", "SOS", "stat"]
        for freq in frequencies:
            med = Medication(drug_name="Test", frequency=freq)
            assert med.frequency == freq


class TestPrescriptionModel:
    """Tests for Prescription model."""

    def test_empty_prescription(self):
        """Test empty prescription has correct defaults."""
        rx = Prescription()
        assert rx.diagnosis == []
        assert rx.medications == []
        assert rx.investigations == []
        assert rx.advice == []
        assert rx.follow_up == ""
        assert rx.red_flags == []

    def test_prescription_with_data(self):
        """Test prescription with full data."""
        med = Medication(drug_name="Aspirin", strength="75mg")
        rx = Prescription(
            diagnosis=["CAD", "HTN"],
            medications=[med],
            investigations=["ECG", "Lipid Profile"],
            advice=["Low salt diet", "Exercise"],
            follow_up="2 weeks",
            red_flags=["Chest pain", "Breathlessness"]
        )
        assert len(rx.diagnosis) == 2
        assert len(rx.medications) == 1
        assert rx.medications[0].drug_name == "Aspirin"
        assert len(rx.investigations) == 2
        assert rx.follow_up == "2 weeks"

    def test_prescription_multiple_medications(self):
        """Test prescription with multiple medications."""
        meds = [
            Medication(drug_name="Aspirin", strength="75mg"),
            Medication(drug_name="Atorvastatin", strength="40mg"),
            Medication(drug_name="Metoprolol", strength="25mg")
        ]
        rx = Prescription(medications=meds)
        assert len(rx.medications) == 3

    def test_prescription_json_serialization(self):
        """Test prescription can be serialized to JSON."""
        med = Medication(drug_name="Test")
        rx = Prescription(
            diagnosis=["Fever"],
            medications=[med]
        )
        json_str = rx.model_dump_json()
        assert "Fever" in json_str
        assert "Test" in json_str


class TestVisitModel:
    """Tests for Visit model."""

    def test_visit_creation_minimal(self):
        """Test visit with minimal fields."""
        visit = Visit(patient_id=1)
        assert visit.patient_id == 1
        assert visit.chief_complaint == ""
        assert visit.clinical_notes == ""
        assert visit.visit_date is None

    def test_visit_creation_full(self):
        """Test visit with all fields."""
        today = date.today()
        visit = Visit(
            id=1,
            patient_id=1,
            visit_date=today,
            chief_complaint="Chest pain",
            clinical_notes="Patient c/o chest pain x 2 days",
            diagnosis="Angina",
            prescription_json='{"diagnosis": ["Angina"]}'
        )
        assert visit.id == 1
        assert visit.patient_id == 1
        assert visit.visit_date == today
        assert visit.chief_complaint == "Chest pain"
        assert visit.diagnosis == "Angina"


class TestInvestigationModel:
    """Tests for Investigation model."""

    def test_investigation_creation_minimal(self):
        """Test investigation with minimal fields."""
        inv = Investigation(patient_id=1, test_name="CBC")
        assert inv.patient_id == 1
        assert inv.test_name == "CBC"
        assert inv.result == ""
        assert inv.is_abnormal is False

    def test_investigation_with_abnormal_flag(self):
        """Test investigation with abnormal flag."""
        inv = Investigation(
            patient_id=1,
            test_name="Creatinine",
            result="2.5",
            unit="mg/dL",
            reference_range="0.7-1.3",
            test_date=date.today(),
            is_abnormal=True
        )
        assert inv.is_abnormal is True
        assert inv.result == "2.5"
        assert inv.reference_range == "0.7-1.3"


class TestProcedureModel:
    """Tests for Procedure model."""

    def test_procedure_creation_minimal(self):
        """Test procedure with minimal fields."""
        proc = Procedure(patient_id=1, procedure_name="Colonoscopy")
        assert proc.patient_id == 1
        assert proc.procedure_name == "Colonoscopy"
        assert proc.details == ""
        assert proc.notes == ""

    def test_procedure_creation_full(self):
        """Test procedure with all fields."""
        today = date.today()
        proc = Procedure(
            id=1,
            patient_id=1,
            procedure_name="PCI to LAD",
            details="Drug-eluting stent placed",
            procedure_date=today,
            notes="Successful, no complications"
        )
        assert proc.id == 1
        assert proc.procedure_name == "PCI to LAD"
        assert proc.procedure_date == today


class TestRAGDocumentModel:
    """Tests for RAGDocument model."""

    def test_rag_document_creation(self):
        """Test RAG document creation."""
        doc = RAGDocument(
            id="doc_001",
            patient_id=1,
            doc_type="visit",
            content="Patient presented with fever",
            metadata={"date": "2024-01-15"}
        )
        assert doc.id == "doc_001"
        assert doc.patient_id == 1
        assert doc.doc_type == "visit"
        assert doc.metadata["date"] == "2024-01-15"

    def test_rag_document_default_metadata(self):
        """Test RAG document with default empty metadata."""
        doc = RAGDocument(
            id="doc_001",
            patient_id=1,
            doc_type="investigation",
            content="CBC normal"
        )
        assert doc.metadata == {}
