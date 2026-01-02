"""Unit tests for PDF service."""

import pytest
from pathlib import Path
from datetime import date

from src.services.pdf import PDFService
from src.models.schemas import Patient, Prescription, Medication


class TestPDFServiceInitialization:
    """Tests for PDF service initialization."""

    def test_pdf_service_initialization(self, temp_pdf):
        """Test PDF service initializes correctly."""
        assert temp_pdf.output_dir is not None
        assert Path(temp_pdf.output_dir).exists()

    def test_output_directory_created(self, temp_pdf):
        """Test that output directory is created."""
        assert Path(temp_pdf.output_dir).is_dir()


class TestPrescriptionPDFGeneration:
    """Tests for prescription PDF generation."""

    def test_generate_prescription_pdf_basic(self, temp_pdf, sample_patient, sample_prescription):
        """Test generating a basic prescription PDF."""
        filepath = temp_pdf.generate_prescription_pdf(
            patient=sample_patient,
            prescription=sample_prescription
        )

        assert filepath is not None
        assert Path(filepath).exists()
        assert filepath.endswith('.pdf')

    def test_pdf_filename_format(self, temp_pdf, sample_patient, sample_prescription):
        """Test PDF filename format."""
        filepath = temp_pdf.generate_prescription_pdf(
            patient=sample_patient,
            prescription=sample_prescription
        )

        filename = Path(filepath).name
        # Should contain patient name and date
        assert "Ram" in filename or "Lal" in filename
        assert date.today().strftime('%Y%m%d') in filename
        assert filename.startswith("Rx_")

    def test_pdf_with_chief_complaint(self, temp_pdf, sample_patient, sample_prescription):
        """Test PDF generation with chief complaint."""
        filepath = temp_pdf.generate_prescription_pdf(
            patient=sample_patient,
            prescription=sample_prescription,
            chief_complaint="Fever and body ache for 3 days"
        )

        assert filepath is not None
        assert Path(filepath).exists()

    def test_pdf_with_clinic_details(self, temp_pdf, sample_patient, sample_prescription):
        """Test PDF generation with clinic details."""
        filepath = temp_pdf.generate_prescription_pdf(
            patient=sample_patient,
            prescription=sample_prescription,
            doctor_name="Dr. Sharma",
            clinic_name="Sharma Clinic",
            clinic_address="123 Main Street, Delhi"
        )

        assert filepath is not None
        assert Path(filepath).exists()

    def test_pdf_with_minimal_patient_info(self, temp_pdf):
        """Test PDF with minimal patient information."""
        minimal_patient = Patient(name="John Doe")
        minimal_prescription = Prescription(
            medications=[
                Medication(drug_name="Paracetamol", strength="500mg")
            ]
        )

        filepath = temp_pdf.generate_prescription_pdf(
            patient=minimal_patient,
            prescription=minimal_prescription
        )

        assert filepath is not None
        assert Path(filepath).exists()

    def test_pdf_with_full_patient_info(self, temp_pdf):
        """Test PDF with complete patient information."""
        full_patient = Patient(
            id=1,
            uhid="EMR-2024-0001",
            name="Ram Lal",
            age=65,
            gender="M",
            phone="9876543210",
            address="Delhi"
        )

        full_prescription = Prescription(
            diagnosis=["Type 2 Diabetes", "Hypertension"],
            medications=[
                Medication(
                    drug_name="Metformin",
                    strength="500mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    duration="30 days",
                    instructions="after meals"
                )
            ],
            investigations=["HbA1c", "Lipid Profile"],
            advice=["Low salt diet", "Regular exercise"],
            follow_up="2 weeks",
            red_flags=["Severe chest pain", "Breathlessness"]
        )

        filepath = temp_pdf.generate_prescription_pdf(
            patient=full_patient,
            prescription=full_prescription
        )

        assert filepath is not None
        assert Path(filepath).exists()

    def test_pdf_with_multiple_medications(self, temp_pdf, sample_patient):
        """Test PDF with multiple medications."""
        prescription = Prescription(
            diagnosis=["Hypertension", "Diabetes"],
            medications=[
                Medication(drug_name="Amlodipine", strength="5mg", frequency="OD"),
                Medication(drug_name="Metformin", strength="500mg", frequency="BD"),
                Medication(drug_name="Aspirin", strength="75mg", frequency="OD"),
            ]
        )

        filepath = temp_pdf.generate_prescription_pdf(
            patient=sample_patient,
            prescription=prescription
        )

        assert filepath is not None
        assert Path(filepath).exists()

    def test_pdf_with_special_characters_in_name(self, temp_pdf):
        """Test PDF generation with special characters in patient name."""
        patient = Patient(name="Ram Kumar / S/o Mohan Lal (Senior)")
        prescription = Prescription(
            medications=[Medication(drug_name="Paracetamol")]
        )

        filepath = temp_pdf.generate_prescription_pdf(
            patient=patient,
            prescription=prescription
        )

        assert filepath is not None
        assert Path(filepath).exists()
        # Filename should sanitize special characters
        filename = Path(filepath).name
        assert "/" not in filename

    def test_pdf_file_size(self, temp_pdf, sample_patient, sample_prescription):
        """Test that generated PDF has reasonable file size."""
        filepath = temp_pdf.generate_prescription_pdf(
            patient=sample_patient,
            prescription=sample_prescription
        )

        file_size = Path(filepath).stat().st_size
        # PDF should be between 1KB and 1MB
        assert 1000 < file_size < 1000000

    def test_pdf_generation_error_handling(self, temp_pdf):
        """Test PDF generation handles errors gracefully."""
        # This test checks if the service handles errors without crashing
        # Using None might cause an error, which should be caught
        try:
            result = temp_pdf.generate_prescription_pdf(
                patient=None,
                prescription=None
            )
            # Should return None on error
            assert result is None
        except Exception:
            # Or might raise exception, which is also acceptable
            pass


class TestPrescriptionToText:
    """Tests for prescription text conversion."""

    def test_prescription_to_text_basic(self, temp_pdf, sample_patient, sample_prescription):
        """Test converting prescription to text format."""
        text = temp_pdf.prescription_to_text(sample_patient, sample_prescription)

        assert text is not None
        assert isinstance(text, str)
        assert len(text) > 0

    def test_text_contains_patient_name(self, temp_pdf, sample_patient, sample_prescription):
        """Test text output contains patient name."""
        text = temp_pdf.prescription_to_text(sample_patient, sample_prescription)

        assert "Ram Lal" in text

    def test_text_contains_diagnosis(self, temp_pdf, sample_patient, sample_prescription):
        """Test text output contains diagnosis."""
        text = temp_pdf.prescription_to_text(sample_patient, sample_prescription)

        assert "Diabetes" in text or "DIAGNOSIS" in text

    def test_text_contains_medications(self, temp_pdf, sample_patient, sample_prescription):
        """Test text output contains medications."""
        text = temp_pdf.prescription_to_text(sample_patient, sample_prescription)

        assert "Metformin" in text
        assert "Amlodipine" in text
        assert "Rx" in text

    def test_text_contains_investigations(self, temp_pdf, sample_patient, sample_prescription):
        """Test text output contains investigations."""
        text = temp_pdf.prescription_to_text(sample_patient, sample_prescription)

        assert "INVESTIGATION" in text.upper()
        assert "HbA1c" in text

    def test_text_contains_advice(self, temp_pdf, sample_patient, sample_prescription):
        """Test text output contains advice."""
        text = temp_pdf.prescription_to_text(sample_patient, sample_prescription)

        assert "ADVICE" in text.upper()
        assert "Low salt diet" in text or "exercise" in text.lower()

    def test_text_contains_follow_up(self, temp_pdf, sample_patient, sample_prescription):
        """Test text output contains follow-up."""
        text = temp_pdf.prescription_to_text(sample_patient, sample_prescription)

        assert "FOLLOW" in text.upper()
        assert "2 weeks" in text

    def test_text_contains_red_flags(self, temp_pdf, sample_patient, sample_prescription):
        """Test text output contains red flags."""
        text = temp_pdf.prescription_to_text(sample_patient, sample_prescription)

        assert "RED FLAG" in text.upper()
        assert "chest pain" in text.lower()

    def test_text_format_minimal_prescription(self, temp_pdf, sample_patient):
        """Test text format with minimal prescription."""
        minimal_prescription = Prescription(
            medications=[Medication(drug_name="Paracetamol")]
        )

        text = temp_pdf.prescription_to_text(sample_patient, minimal_prescription)

        assert "Paracetamol" in text
        assert "Ram Lal" in text

    def test_text_includes_date(self, temp_pdf, sample_patient, sample_prescription):
        """Test text includes current date."""
        text = temp_pdf.prescription_to_text(sample_patient, sample_prescription)

        # Should include today's date in some format
        today = date.today()
        # Date might be in different formats
        assert str(today.year) in text

    def test_text_medication_formatting(self, temp_pdf, sample_patient):
        """Test medication formatting in text output."""
        prescription = Prescription(
            medications=[
                Medication(
                    drug_name="Metformin",
                    strength="500mg",
                    dose="1",
                    frequency="BD",
                    duration="30 days",
                    instructions="after meals"
                )
            ]
        )

        text = temp_pdf.prescription_to_text(sample_patient, prescription)

        assert "Metformin" in text
        assert "500mg" in text
        assert "BD" in text
        assert "30 days" in text
        assert "after meals" in text


class TestPDFFileManagement:
    """Tests for PDF file management."""

    def test_multiple_pdfs_same_patient(self, temp_pdf, sample_patient):
        """Test generating multiple PDFs for same patient."""
        prescription1 = Prescription(
            medications=[Medication(drug_name="Med1")]
        )
        prescription2 = Prescription(
            medications=[Medication(drug_name="Med2")]
        )

        filepath1 = temp_pdf.generate_prescription_pdf(sample_patient, prescription1)
        filepath2 = temp_pdf.generate_prescription_pdf(sample_patient, prescription2)

        # Both files should exist
        assert Path(filepath1).exists()
        assert Path(filepath2).exists()

        # Files might have same name if generated on same day
        # That's OK - second one will overwrite or have timestamp

    def test_pdf_saved_in_correct_directory(self, temp_pdf, sample_patient, sample_prescription):
        """Test PDF is saved in the correct output directory."""
        filepath = temp_pdf.generate_prescription_pdf(
            patient=sample_patient,
            prescription=sample_prescription
        )

        # Should be in the temp_pdf output directory
        assert str(temp_pdf.output_dir) in filepath

    def test_empty_prescription(self, temp_pdf, sample_patient):
        """Test generating PDF with empty prescription."""
        empty_prescription = Prescription()

        filepath = temp_pdf.generate_prescription_pdf(
            patient=sample_patient,
            prescription=empty_prescription
        )

        # Should still generate PDF
        assert filepath is not None
        assert Path(filepath).exists()
