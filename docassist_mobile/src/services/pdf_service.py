"""
PDF Service for Mobile - Generate and share prescription PDFs.

Handles:
- PDF generation from visit data
- Caching of generated PDFs
- Native share sheet integration
- Save to device downloads
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import date, datetime
from fpdf import FPDF
import logging

logger = logging.getLogger(__name__)


class MobilePDFService:
    """
    Mobile PDF service for prescription management.

    Usage:
        service = MobilePDFService()
        pdf_bytes = service.generate_prescription_pdf(visit_data)
        service.share_prescription(pdf_bytes, "Ram Lal")
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize PDF service.

        Args:
            cache_dir: Directory to cache generated PDFs (defaults to data/prescriptions)
        """
        if cache_dir is None:
            cache_dir = os.getenv("DOCASSIST_MOBILE_PDF_DIR", "data/prescriptions")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Doctor and clinic info (TODO: Load from settings/profile)
        self.doctor_name = os.getenv("DOCTOR_NAME", "Dr. ")
        self.doctor_qualifications = os.getenv("DOCTOR_QUALIFICATIONS", "")
        self.doctor_registration = os.getenv("DOCTOR_REGISTRATION", "")
        self.clinic_name = os.getenv("CLINIC_NAME", "")
        self.clinic_address = os.getenv("CLINIC_ADDRESS", "")
        self.clinic_phone = os.getenv("CLINIC_PHONE", "")
        self.clinic_email = os.getenv("CLINIC_EMAIL", "")

    def get_prescription_pdf(self, visit_id: int) -> Optional[bytes]:
        """
        Get prescription PDF from cache.

        Args:
            visit_id: Visit ID

        Returns:
            PDF as bytes, or None if not found
        """
        cache_path = self.cache_dir / f"prescription_{visit_id}.pdf"

        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading cached PDF: {e}")
                return None

        return None

    def generate_prescription_pdf(
        self,
        visit_data: Dict[str, Any],
        patient_data: Dict[str, Any],
    ) -> Optional[bytes]:
        """
        Generate prescription PDF from visit data.

        Args:
            visit_data: Visit information including prescription_json
            patient_data: Patient information

        Returns:
            PDF as bytes, or None if failed
        """
        try:
            # Check cache first
            visit_id = visit_data.get('id')
            if visit_id:
                cached = self.get_prescription_pdf(visit_id)
                if cached:
                    return cached

            # Parse prescription JSON
            prescription_json = visit_data.get('prescription_json')
            if not prescription_json:
                logger.warning("No prescription JSON found")
                return None

            if isinstance(prescription_json, str):
                prescription = json.loads(prescription_json)
            else:
                prescription = prescription_json

            # Generate PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Header
            self._add_header(pdf)

            # Patient Info
            self._add_patient_info(pdf, patient_data, visit_data)

            # Chief Complaint
            chief_complaint = visit_data.get('chief_complaint', '')
            if chief_complaint:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, "Chief Complaint:", ln=True)
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(0, 5, chief_complaint)
                pdf.ln(2)

            # Diagnosis
            diagnoses = prescription.get('diagnosis', [])
            if diagnoses:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, "Diagnosis:", ln=True)
                pdf.set_font("Helvetica", "", 10)
                for dx in diagnoses:
                    pdf.cell(0, 5, f"  - {dx}", ln=True)
                pdf.ln(2)

            # Line separator
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)

            # Rx Symbol
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 8, "Rx", ln=True)

            # Medications
            medications = prescription.get('medications', [])
            pdf.set_font("Helvetica", "", 10)
            for i, med in enumerate(medications, 1):
                med_line = f"{i}. {med.get('drug_name', 'Unknown')}"
                if med.get('strength'):
                    med_line += f" {med['strength']}"
                if med.get('form') and med['form'] != "tablet":
                    med_line += f" ({med['form']})"

                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, med_line, ln=True)

                dosage_line = f"   {med.get('dose', '')} {med.get('frequency', '')}"
                if med.get('duration'):
                    dosage_line += f" x {med['duration']}"
                if med.get('instructions'):
                    dosage_line += f" - {med['instructions']}"

                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 5, dosage_line, ln=True)

            pdf.ln(3)

            # Investigations
            investigations = prescription.get('investigations', [])
            if investigations:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, "Investigations Advised:", ln=True)
                pdf.set_font("Helvetica", "", 10)
                for inv in investigations:
                    pdf.cell(0, 5, f"  - {inv}", ln=True)
                pdf.ln(2)

            # Advice
            advice = prescription.get('advice', [])
            if advice:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, "Advice:", ln=True)
                pdf.set_font("Helvetica", "", 10)
                for adv in advice:
                    pdf.cell(0, 5, f"  - {adv}", ln=True)
                pdf.ln(2)

            # Follow-up
            follow_up = prescription.get('follow_up')
            if follow_up:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, f"Follow-up: {follow_up}", ln=True)
                pdf.ln(2)

            # Red Flags
            red_flags = prescription.get('red_flags', [])
            if red_flags:
                pdf.ln(3)
                pdf.set_fill_color(255, 240, 240)
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, "RED FLAGS - Seek immediate attention if:", ln=True, fill=True)
                pdf.set_font("Helvetica", "", 10)
                for flag in red_flags:
                    pdf.cell(0, 5, f"  ! {flag}", ln=True, fill=True)

            # Footer
            self._add_footer(pdf)

            # Generate PDF bytes
            pdf_bytes = pdf.output(dest='S').encode('latin1')

            # Cache the PDF
            if visit_id:
                cache_path = self.cache_dir / f"prescription_{visit_id}.pdf"
                try:
                    with open(cache_path, 'wb') as f:
                        f.write(pdf_bytes)
                except Exception as e:
                    logger.error(f"Error caching PDF: {e}")

            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF generation error: {e}", exc_info=True)
            return None

    def _add_header(self, pdf: FPDF):
        """Add clinic header to PDF."""
        # Header
        pdf.set_font("Helvetica", "B", 16)
        if self.clinic_name:
            pdf.cell(0, 10, self.clinic_name, ln=True, align="C")
        if self.clinic_address:
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 5, self.clinic_address, ln=True, align="C")

        pdf.ln(5)

        # Doctor name
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, self.doctor_name, ln=True, align="C")

        # Doctor qualifications
        if self.doctor_qualifications:
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 5, self.doctor_qualifications, ln=True, align="C")

        # Doctor registration
        if self.doctor_registration:
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, f"Reg. No: {self.doctor_registration}", ln=True, align="C")

        # Line separator
        pdf.set_draw_color(0, 0, 0)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    def _add_patient_info(self, pdf: FPDF, patient_data: Dict[str, Any], visit_data: Dict[str, Any]):
        """Add patient information to PDF."""
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, "PATIENT DETAILS", ln=True)
        pdf.set_font("Helvetica", "", 10)

        patient_info = f"Name: {patient_data.get('name', 'Unknown')}"
        if patient_data.get('age'):
            patient_info += f"  |  Age: {patient_data['age']}"
        if patient_data.get('gender'):
            patient_info += f"  |  Gender: {patient_data['gender']}"
        if patient_data.get('uhid'):
            patient_info += f"  |  UHID: {patient_data['uhid']}"

        pdf.cell(0, 5, patient_info, ln=True)

        # Visit date
        visit_date = visit_data.get('visit_date')
        if visit_date:
            if isinstance(visit_date, str):
                try:
                    visit_date_obj = date.fromisoformat(visit_date)
                    date_str = visit_date_obj.strftime('%d-%b-%Y')
                except:
                    date_str = visit_date
            else:
                date_str = visit_date.strftime('%d-%b-%Y')
        else:
            date_str = date.today().strftime('%d-%b-%Y')

        pdf.cell(0, 5, f"Date: {date_str}", ln=True)
        pdf.ln(3)

    def _add_footer(self, pdf: FPDF):
        """Add footer to PDF."""
        pdf.ln(10)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        pdf.set_font("Helvetica", "I", 8)

        # Clinic contact info in footer
        footer_parts = []
        if self.clinic_phone:
            footer_parts.append(f"Phone: {self.clinic_phone}")
        if self.clinic_email:
            footer_parts.append(f"Email: {self.clinic_email}")

        if footer_parts:
            pdf.cell(0, 4, " | ".join(footer_parts), ln=True, align="C")

        pdf.cell(0, 4, "This is a computer-generated prescription.", ln=True, align="C")

    def share_prescription(
        self,
        pdf_bytes: bytes,
        patient_name: str,
        page: Any = None,
    ) -> bool:
        """
        Trigger native share sheet for prescription PDF.

        Args:
            pdf_bytes: PDF file as bytes
            patient_name: Patient name for filename
            page: Flet page object (for share API)

        Returns:
            True if share was triggered, False otherwise
        """
        try:
            # Generate temporary file for sharing
            safe_name = "".join(c for c in patient_name if c.isalnum() or c in " -_")[:30]
            filename = f"Rx_{safe_name}_{date.today().strftime('%Y%m%d')}.pdf"
            temp_path = self.cache_dir / filename

            # Write PDF to temp file
            with open(temp_path, 'wb') as f:
                f.write(pdf_bytes)

            # Trigger native share
            # Note: Flet's share API may vary, this is a placeholder
            if page and hasattr(page, 'share'):
                page.share(str(temp_path))
                return True

            logger.info(f"PDF saved for sharing: {temp_path}")
            return True

        except Exception as e:
            logger.error(f"Error sharing prescription: {e}")
            return False

    def save_prescription(
        self,
        pdf_bytes: bytes,
        filename: str,
    ) -> Optional[str]:
        """
        Save prescription to device downloads.

        Args:
            pdf_bytes: PDF file as bytes
            filename: Filename to save as

        Returns:
            Path to saved file, or None if failed
        """
        try:
            # Save to cache directory
            # Note: On mobile, this should use platform-specific downloads folder
            filepath = self.cache_dir / filename

            with open(filepath, 'wb') as f:
                f.write(pdf_bytes)

            logger.info(f"PDF saved: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error saving prescription: {e}")
            return None

    def get_prescription_summary(self, prescription_json: str) -> Dict[str, Any]:
        """
        Extract summary from prescription JSON.

        Args:
            prescription_json: JSON string of prescription

        Returns:
            Dictionary with summary information
        """
        try:
            if isinstance(prescription_json, str):
                prescription = json.loads(prescription_json)
            else:
                prescription = prescription_json

            # Count medications
            med_count = len(prescription.get('medications', []))

            # Get primary diagnosis
            diagnoses = prescription.get('diagnosis', [])
            primary_diagnosis = diagnoses[0] if diagnoses else "No diagnosis"

            return {
                'diagnosis': primary_diagnosis,
                'medication_count': med_count,
                'has_investigations': len(prescription.get('investigations', [])) > 0,
                'has_follow_up': bool(prescription.get('follow_up')),
            }

        except Exception as e:
            logger.error(f"Error parsing prescription: {e}")
            return {
                'diagnosis': "Error parsing",
                'medication_count': 0,
                'has_investigations': False,
                'has_follow_up': False,
            }
