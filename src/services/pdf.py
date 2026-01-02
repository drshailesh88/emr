"""PDF generation service for prescriptions."""

from fpdf import FPDF
from pathlib import Path
from datetime import date
from typing import Optional
import json
import os

from ..models.schemas import Patient, Prescription


class PDFService:
    """Generates prescription PDFs."""

    def __init__(self, output_dir: Optional[str] = None):
        if output_dir is None:
            output_dir = os.getenv("DOCASSIST_PDF_DIR", "data/prescriptions")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_prescription_pdf(
        self,
        patient: Patient,
        prescription: Prescription,
        chief_complaint: str = "",
        doctor_name: str = "Dr. ",
        clinic_name: str = "",
        clinic_address: str = ""
    ) -> Optional[str]:
        """Generate a prescription PDF.

        Returns:
            Path to generated PDF file, or None if failed
        """
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Header
            pdf.set_font("Helvetica", "B", 16)
            if clinic_name:
                pdf.cell(0, 10, clinic_name, ln=True, align="C")
            if clinic_address:
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 5, clinic_address, ln=True, align="C")

            pdf.ln(5)

            # Doctor name
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, doctor_name, ln=True, align="C")

            # Line separator
            pdf.set_draw_color(0, 0, 0)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            # Patient Info
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, "PATIENT DETAILS", ln=True)
            pdf.set_font("Helvetica", "", 10)

            patient_info = f"Name: {patient.name}"
            if patient.age:
                patient_info += f"  |  Age: {patient.age}"
            if patient.gender:
                patient_info += f"  |  Gender: {patient.gender}"
            if patient.uhid:
                patient_info += f"  |  UHID: {patient.uhid}"

            pdf.cell(0, 5, patient_info, ln=True)
            pdf.cell(0, 5, f"Date: {date.today().strftime('%d-%b-%Y')}", ln=True)

            pdf.ln(3)

            # Chief Complaint
            if chief_complaint:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, "Chief Complaint:", ln=True)
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(0, 5, chief_complaint)
                pdf.ln(2)

            # Diagnosis
            if prescription.diagnosis:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, "Diagnosis:", ln=True)
                pdf.set_font("Helvetica", "", 10)
                for dx in prescription.diagnosis:
                    pdf.cell(0, 5, f"  - {dx}", ln=True)
                pdf.ln(2)

            # Line separator
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)

            # Rx Symbol
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 8, "Rx", ln=True)

            # Medications
            pdf.set_font("Helvetica", "", 10)
            for i, med in enumerate(prescription.medications, 1):
                med_line = f"{i}. {med.drug_name}"
                if med.strength:
                    med_line += f" {med.strength}"
                if med.form and med.form != "tablet":
                    med_line += f" ({med.form})"

                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, med_line, ln=True)

                dosage_line = f"   {med.dose} {med.frequency}"
                if med.duration:
                    dosage_line += f" x {med.duration}"
                if med.instructions:
                    dosage_line += f" - {med.instructions}"

                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 5, dosage_line, ln=True)

            pdf.ln(3)

            # Investigations
            if prescription.investigations:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, "Investigations Advised:", ln=True)
                pdf.set_font("Helvetica", "", 10)
                for inv in prescription.investigations:
                    pdf.cell(0, 5, f"  - {inv}", ln=True)
                pdf.ln(2)

            # Advice
            if prescription.advice:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, "Advice:", ln=True)
                pdf.set_font("Helvetica", "", 10)
                for adv in prescription.advice:
                    pdf.cell(0, 5, f"  - {adv}", ln=True)
                pdf.ln(2)

            # Follow-up
            if prescription.follow_up:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, f"Follow-up: {prescription.follow_up}", ln=True)
                pdf.ln(2)

            # Red Flags
            if prescription.red_flags:
                pdf.ln(3)
                pdf.set_fill_color(255, 240, 240)
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, "RED FLAGS - Seek immediate attention if:", ln=True, fill=True)
                pdf.set_font("Helvetica", "", 10)
                for flag in prescription.red_flags:
                    pdf.cell(0, 5, f"  ! {flag}", ln=True, fill=True)

            # Footer
            pdf.ln(10)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            pdf.set_font("Helvetica", "I", 8)
            pdf.cell(0, 5, "This is a computer-generated prescription.", ln=True, align="C")

            # Generate filename
            safe_name = "".join(c for c in patient.name if c.isalnum() or c in " -_")[:30]
            filename = f"Rx_{safe_name}_{date.today().strftime('%Y%m%d')}.pdf"
            filepath = self.output_dir / filename

            pdf.output(str(filepath))
            return str(filepath)

        except Exception as e:
            print(f"PDF generation error: {e}")
            return None

    def prescription_to_text(self, patient: Patient, prescription: Prescription) -> str:
        """Convert prescription to plain text format."""
        lines = []
        lines.append(f"PRESCRIPTION - {date.today().strftime('%d-%b-%Y')}")
        lines.append("=" * 40)
        lines.append(f"Patient: {patient.name}")
        if patient.age:
            lines.append(f"Age: {patient.age} | Gender: {patient.gender or 'N/A'}")
        if patient.uhid:
            lines.append(f"UHID: {patient.uhid}")
        lines.append("")

        if prescription.diagnosis:
            lines.append("DIAGNOSIS:")
            for dx in prescription.diagnosis:
                lines.append(f"  - {dx}")
            lines.append("")

        lines.append("Rx")
        lines.append("-" * 20)
        for i, med in enumerate(prescription.medications, 1):
            med_str = f"{i}. {med.drug_name}"
            if med.strength:
                med_str += f" {med.strength}"
            lines.append(med_str)
            dosage = f"   {med.dose} {med.frequency}"
            if med.duration:
                dosage += f" x {med.duration}"
            if med.instructions:
                dosage += f" ({med.instructions})"
            lines.append(dosage)
        lines.append("")

        if prescription.investigations:
            lines.append("INVESTIGATIONS:")
            for inv in prescription.investigations:
                lines.append(f"  - {inv}")
            lines.append("")

        if prescription.advice:
            lines.append("ADVICE:")
            for adv in prescription.advice:
                lines.append(f"  - {adv}")
            lines.append("")

        if prescription.follow_up:
            lines.append(f"FOLLOW-UP: {prescription.follow_up}")

        if prescription.red_flags:
            lines.append("")
            lines.append("!! RED FLAGS !!")
            for flag in prescription.red_flags:
                lines.append(f"  - {flag}")

        return "\n".join(lines)
