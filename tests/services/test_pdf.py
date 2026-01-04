"""Tests for PDFService."""

import pytest
import os
from datetime import date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.pdf import PDFService
from src.models.schemas import Patient, Prescription, Medication


class TestPDFServiceInitialization:
    """Tests for PDFService initialization."""

    def test_creates_output_directory(self, temp_pdf_dir):
        """Test that output directory is created."""
        service = PDFService(output_dir=temp_pdf_dir)
        assert os.path.exists(temp_pdf_dir)

    def test_creates_nested_output_directory(self, temp_dir):
        """Test that nested output directory is created."""
        nested_path = os.path.join(temp_dir, "nested", "path", "pdfs")
        service = PDFService(output_dir=nested_path)
        assert os.path.exists(nested_path)

    def test_default_directory_from_env(self, temp_dir, monkeypatch):
        """Test default directory from environment variable."""
        test_path = os.path.join(temp_dir, "env_pdfs")
        monkeypatch.setenv("DOCASSIST_PDF_DIR", test_path)

        service = PDFService(output_dir=None)
        assert service.output_dir is not None


class TestGeneratePrescriptionPDF:
    """Tests for prescription PDF generation."""

    def test_generate_pdf_basic(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test basic PDF generation."""
        filepath = pdf_service.generate_prescription_pdf(
            patient=sample_patient_with_id,
            prescription=sample_prescription
        )

        assert filepath is not None
        assert os.path.exists(filepath)
        assert filepath.endswith(".pdf")

    def test_generate_pdf_with_all_options(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test PDF generation with all options."""
        filepath = pdf_service.generate_prescription_pdf(
            patient=sample_patient_with_id,
            prescription=sample_prescription,
            chief_complaint="Fever and body ache for 3 days",
            doctor_name="Dr. Sharma",
            clinic_name="City Heart Clinic",
            clinic_address="123 Main Street, Mumbai"
        )

        assert filepath is not None
        assert os.path.exists(filepath)

    def test_generate_pdf_filename_format(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test PDF filename format."""
        filepath = pdf_service.generate_prescription_pdf(
            patient=sample_patient_with_id,
            prescription=sample_prescription
        )

        filename = os.path.basename(filepath)
        assert filename.startswith("Rx_")
        assert date.today().strftime("%Y%m%d") in filename
        assert filename.endswith(".pdf")

    def test_generate_pdf_sanitizes_patient_name(self, pdf_service, sample_prescription):
        """Test that special characters in name are sanitized."""
        patient = Patient(
            id=1,
            name="Ram/Lal@Kumar#2024",
            uhid="EMR-2024-0001"
        )

        filepath = pdf_service.generate_prescription_pdf(
            patient=patient,
            prescription=sample_prescription
        )

        filename = os.path.basename(filepath)
        # Should not contain special characters
        assert "/" not in filename
        assert "@" not in filename
        assert "#" not in filename

    def test_generate_pdf_empty_prescription(self, pdf_service, sample_patient_with_id):
        """Test PDF generation with empty prescription."""
        prescription = Prescription()

        filepath = pdf_service.generate_prescription_pdf(
            patient=sample_patient_with_id,
            prescription=prescription
        )

        assert filepath is not None
        assert os.path.exists(filepath)

    def test_generate_pdf_multiple_medications(self, pdf_service, sample_patient_with_id):
        """Test PDF with multiple medications."""
        prescription = Prescription(
            diagnosis=["Type 2 DM", "HTN", "Dyslipidemia"],
            medications=[
                Medication(drug_name="Metformin", strength="500mg", frequency="BD"),
                Medication(drug_name="Telmisartan", strength="40mg", frequency="OD"),
                Medication(drug_name="Atorvastatin", strength="20mg", frequency="HS"),
                Medication(drug_name="Aspirin", strength="75mg", frequency="OD"),
            ],
            investigations=["HbA1c", "Lipid Profile", "KFT"],
            advice=["Diet control", "Exercise 30 min daily", "Avoid salt"],
            follow_up="1 month",
            red_flags=["Chest pain", "Breathlessness", "Hypoglycemia symptoms"]
        )

        filepath = pdf_service.generate_prescription_pdf(
            patient=sample_patient_with_id,
            prescription=prescription
        )

        assert filepath is not None
        assert os.path.exists(filepath)
        # Check file size > 0
        assert os.path.getsize(filepath) > 0

    def test_generate_pdf_with_chief_complaint(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test PDF includes chief complaint when provided."""
        filepath = pdf_service.generate_prescription_pdf(
            patient=sample_patient_with_id,
            prescription=sample_prescription,
            chief_complaint="Chest pain and breathlessness for 2 days"
        )

        assert filepath is not None
        assert os.path.exists(filepath)

    def test_generate_pdf_with_red_flags(self, pdf_service, sample_patient_with_id):
        """Test PDF with red flags section."""
        prescription = Prescription(
            diagnosis=["Acute MI"],
            medications=[Medication(drug_name="Aspirin", strength="325mg")],
            red_flags=[
                "Severe chest pain",
                "Breathlessness at rest",
                "Fainting",
                "Cold sweats"
            ]
        )

        filepath = pdf_service.generate_prescription_pdf(
            patient=sample_patient_with_id,
            prescription=prescription
        )

        assert filepath is not None
        assert os.path.exists(filepath)

    def test_generate_pdf_different_medication_forms(self, pdf_service, sample_patient_with_id):
        """Test PDF with different medication forms."""
        prescription = Prescription(
            medications=[
                Medication(drug_name="Paracetamol", form="tablet", strength="500mg"),
                Medication(drug_name="Amoxicillin", form="capsule", strength="500mg"),
                Medication(drug_name="Cough syrup", form="syrup", dose="5ml"),
                Medication(drug_name="Insulin", form="injection", dose="10 units"),
                Medication(drug_name="Betadine", form="cream"),
            ]
        )

        filepath = pdf_service.generate_prescription_pdf(
            patient=sample_patient_with_id,
            prescription=prescription
        )

        assert filepath is not None
        assert os.path.exists(filepath)

    def test_generate_pdf_patient_without_optional_fields(self, pdf_service, sample_prescription):
        """Test PDF with patient missing optional fields."""
        patient = Patient(
            id=1,
            name="Test Patient",
            uhid="EMR-2024-0001"
            # No age, gender, phone, address
        )

        filepath = pdf_service.generate_prescription_pdf(
            patient=patient,
            prescription=sample_prescription
        )

        assert filepath is not None
        assert os.path.exists(filepath)


class TestPrescriptionToText:
    """Tests for prescription to text conversion."""

    def test_prescription_to_text_basic(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test basic text conversion."""
        text = pdf_service.prescription_to_text(
            patient=sample_patient_with_id,
            prescription=sample_prescription
        )

        assert "PRESCRIPTION" in text
        assert sample_patient_with_id.name in text
        assert "Rx" in text

    def test_prescription_to_text_contains_diagnosis(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test text contains diagnosis."""
        text = pdf_service.prescription_to_text(
            patient=sample_patient_with_id,
            prescription=sample_prescription
        )

        assert "DIAGNOSIS" in text
        for dx in sample_prescription.diagnosis:
            assert dx in text

    def test_prescription_to_text_contains_medications(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test text contains medications."""
        text = pdf_service.prescription_to_text(
            patient=sample_patient_with_id,
            prescription=sample_prescription
        )

        for med in sample_prescription.medications:
            assert med.drug_name in text
            if med.strength:
                assert med.strength in text

    def test_prescription_to_text_contains_investigations(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test text contains investigations."""
        text = pdf_service.prescription_to_text(
            patient=sample_patient_with_id,
            prescription=sample_prescription
        )

        assert "INVESTIGATIONS" in text
        for inv in sample_prescription.investigations:
            assert inv in text

    def test_prescription_to_text_contains_advice(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test text contains advice."""
        text = pdf_service.prescription_to_text(
            patient=sample_patient_with_id,
            prescription=sample_prescription
        )

        assert "ADVICE" in text
        for adv in sample_prescription.advice:
            assert adv in text

    def test_prescription_to_text_contains_follow_up(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test text contains follow-up."""
        text = pdf_service.prescription_to_text(
            patient=sample_patient_with_id,
            prescription=sample_prescription
        )

        assert "FOLLOW-UP" in text
        assert sample_prescription.follow_up in text

    def test_prescription_to_text_contains_red_flags(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test text contains red flags."""
        text = pdf_service.prescription_to_text(
            patient=sample_patient_with_id,
            prescription=sample_prescription
        )

        assert "RED FLAGS" in text
        for flag in sample_prescription.red_flags:
            assert flag in text

    def test_prescription_to_text_patient_details(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test text contains patient details."""
        text = pdf_service.prescription_to_text(
            patient=sample_patient_with_id,
            prescription=sample_prescription
        )

        assert sample_patient_with_id.name in text
        assert str(sample_patient_with_id.age) in text
        assert sample_patient_with_id.uhid in text

    def test_prescription_to_text_empty_prescription(self, pdf_service, sample_patient_with_id):
        """Test text conversion with empty prescription."""
        prescription = Prescription()

        text = pdf_service.prescription_to_text(
            patient=sample_patient_with_id,
            prescription=prescription
        )

        assert "PRESCRIPTION" in text
        assert sample_patient_with_id.name in text
        assert "Rx" in text

    def test_prescription_to_text_date_format(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test text contains properly formatted date."""
        text = pdf_service.prescription_to_text(
            patient=sample_patient_with_id,
            prescription=sample_prescription
        )

        # Date should be in dd-Mon-YYYY format
        today = date.today().strftime('%d-%b-%Y')
        assert today in text


class TestPDFFileProperties:
    """Tests for PDF file properties."""

    def test_pdf_file_is_valid(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test that generated file is valid PDF."""
        filepath = pdf_service.generate_prescription_pdf(
            patient=sample_patient_with_id,
            prescription=sample_prescription
        )

        # Check PDF magic bytes
        with open(filepath, 'rb') as f:
            header = f.read(4)
            assert header == b'%PDF'

    def test_pdf_file_has_content(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test that PDF file has substantial content."""
        filepath = pdf_service.generate_prescription_pdf(
            patient=sample_patient_with_id,
            prescription=sample_prescription
        )

        file_size = os.path.getsize(filepath)
        # PDF should be at least 1KB
        assert file_size > 1024

    def test_multiple_pdfs_different_files(self, pdf_service, sample_patient_with_id, sample_prescription):
        """Test that multiple PDFs are saved to different files when patient name differs."""
        patient1 = sample_patient_with_id
        patient2 = Patient(id=2, name="Different Patient", uhid="EMR-2024-0002")

        filepath1 = pdf_service.generate_prescription_pdf(
            patient=patient1,
            prescription=sample_prescription
        )
        filepath2 = pdf_service.generate_prescription_pdf(
            patient=patient2,
            prescription=sample_prescription
        )

        assert filepath1 != filepath2
        assert os.path.exists(filepath1)
        assert os.path.exists(filepath2)
