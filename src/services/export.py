"""Data export service for EMR data."""

import csv
import json
import os
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List
from fpdf import FPDF

from ..models.schemas import Patient, Visit, Investigation, Procedure
from .database import DatabaseService
from .pdf import PDFService


class ExportService:
    """Handles data export in various formats (PDF, CSV, JSON)."""

    def __init__(self, db: DatabaseService, pdf_service: PDFService,
                 output_dir: Optional[str] = None):
        """Initialize export service.

        Args:
            db: Database service instance
            pdf_service: PDF service instance
            output_dir: Output directory for exports (default: data/exports/)
        """
        self.db = db
        self.pdf_service = pdf_service

        if output_dir is None:
            output_dir = os.getenv("DOCASSIST_EXPORT_DIR", "data/exports")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, name: str, max_length: int = 30) -> str:
        """Sanitize a string for use in filename."""
        safe = "".join(c for c in name if c.isalnum() or c in " -_")
        return safe[:max_length].strip()

    def _get_timestamp(self) -> str:
        """Get timestamp string for filenames."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    # ============== PATIENT SUMMARY PDF ==============

    def export_patient_summary_pdf(self, patient_id: int,
                                   output_path: Optional[Path] = None) -> Path:
        """Export complete patient history as PDF.

        Includes: demographics, all visits, all investigations, all procedures.

        Args:
            patient_id: ID of patient to export
            output_path: Optional custom output path

        Returns:
            Path to generated PDF file

        Raises:
            ValueError: If patient not found
        """
        patient = self.db.get_patient(patient_id)
        if not patient:
            raise ValueError(f"Patient with ID {patient_id} not found")

        # Get all patient data
        visits = self.db.get_patient_visits(patient_id)
        investigations = self.db.get_patient_investigations(patient_id)
        procedures = self.db.get_patient_procedures(patient_id)

        # Generate filename if not provided
        if output_path is None:
            safe_name = self._sanitize_filename(patient.name)
            timestamp = self._get_timestamp()
            filename = f"PatientSummary_{safe_name}_{timestamp}.pdf"
            output_path = self.output_dir / filename

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Header
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 10, "PATIENT SUMMARY", ln=True, align="C")
        pdf.ln(5)

        # Patient Demographics
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Patient Information", ln=True)
        pdf.set_draw_color(0, 0, 0)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Name: {patient.name}", ln=True)
        if patient.uhid:
            pdf.cell(0, 6, f"UHID: {patient.uhid}", ln=True)
        if patient.age:
            pdf.cell(0, 6, f"Age: {patient.age} years", ln=True)
        if patient.gender:
            gender_full = {"M": "Male", "F": "Female", "O": "Other"}.get(
                patient.gender, patient.gender)
            pdf.cell(0, 6, f"Gender: {gender_full}", ln=True)
        if patient.phone:
            pdf.cell(0, 6, f"Phone: {patient.phone}", ln=True)
        if patient.address:
            pdf.multi_cell(0, 6, f"Address: {patient.address}")

        pdf.ln(5)

        # Visit History
        if visits:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Visit History", ln=True)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            for i, visit in enumerate(visits, 1):
                pdf.set_font("Helvetica", "B", 10)
                visit_date_str = str(visit.visit_date) if visit.visit_date else "Unknown"
                pdf.cell(0, 6, f"Visit {i} - {visit_date_str}", ln=True)

                pdf.set_font("Helvetica", "", 10)
                if visit.chief_complaint:
                    pdf.multi_cell(0, 5, f"  Chief Complaint: {visit.chief_complaint}")
                if visit.diagnosis:
                    pdf.multi_cell(0, 5, f"  Diagnosis: {visit.diagnosis}")
                if visit.clinical_notes:
                    pdf.multi_cell(0, 5, f"  Notes: {visit.clinical_notes}")

                # Parse prescription if available
                if visit.prescription_json:
                    try:
                        rx = json.loads(visit.prescription_json)
                        if rx.get("medications"):
                            pdf.cell(0, 5, "  Medications:", ln=True)
                            for med in rx["medications"]:
                                med_str = f"    - {med.get('drug_name', '')}"
                                if med.get('strength'):
                                    med_str += f" {med['strength']}"
                                pdf.cell(0, 5, med_str, ln=True)
                    except json.JSONDecodeError:
                        pass

                pdf.ln(3)

            pdf.ln(5)

        # Investigations
        if investigations:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Investigation Results", ln=True)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            # Table header
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(30, 6, "Date", border=1)
            pdf.cell(50, 6, "Test", border=1)
            pdf.cell(30, 6, "Result", border=1)
            pdf.cell(40, 6, "Reference", border=1)
            pdf.cell(20, 6, "Status", border=1, ln=True)

            # Table rows
            pdf.set_font("Helvetica", "", 9)
            for inv in investigations:
                test_date_str = str(inv.test_date) if inv.test_date else "N/A"
                result_str = f"{inv.result} {inv.unit}".strip() if inv.result else "N/A"
                ref_str = inv.reference_range or "N/A"
                status = "ABNORMAL" if inv.is_abnormal else "Normal"

                pdf.cell(30, 6, test_date_str, border=1)
                pdf.cell(50, 6, inv.test_name[:25], border=1)
                pdf.cell(30, 6, result_str[:15], border=1)
                pdf.cell(40, 6, ref_str[:20], border=1)
                pdf.cell(20, 6, status, border=1, ln=True)

            pdf.ln(5)

        # Procedures
        if procedures:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Procedures", ln=True)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            for i, proc in enumerate(procedures, 1):
                pdf.set_font("Helvetica", "B", 10)
                proc_date_str = str(proc.procedure_date) if proc.procedure_date else "Unknown"
                pdf.cell(0, 6, f"{i}. {proc.procedure_name} - {proc_date_str}", ln=True)

                pdf.set_font("Helvetica", "", 10)
                if proc.details:
                    pdf.multi_cell(0, 5, f"   Details: {proc.details}")
                if proc.notes:
                    pdf.multi_cell(0, 5, f"   Notes: {proc.notes}")

                pdf.ln(2)

        # Footer
        pdf.ln(10)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 4, f"Generated on: {datetime.now().strftime('%d-%b-%Y %H:%M')}", ln=True, align="C")
        pdf.cell(0, 4, "This is a computer-generated document.", ln=True, align="C")

        # Save PDF
        pdf.output(str(output_path))
        return output_path

    # ============== PATIENT JSON EXPORT ==============

    def export_patient_json(self, patient_id: int,
                           output_path: Optional[Path] = None) -> Path:
        """Export patient data as JSON file.

        Args:
            patient_id: ID of patient to export
            output_path: Optional custom output path

        Returns:
            Path to generated JSON file

        Raises:
            ValueError: If patient not found
        """
        patient = self.db.get_patient(patient_id)
        if not patient:
            raise ValueError(f"Patient with ID {patient_id} not found")

        # Get all patient data
        visits = self.db.get_patient_visits(patient_id)
        investigations = self.db.get_patient_investigations(patient_id)
        procedures = self.db.get_patient_procedures(patient_id)

        # Generate filename if not provided
        if output_path is None:
            safe_name = self._sanitize_filename(patient.name)
            timestamp = self._get_timestamp()
            filename = f"Patient_{safe_name}_{timestamp}.json"
            output_path = self.output_dir / filename

        # Build export data
        export_data = {
            "export_version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "patient": patient.model_dump(mode="json"),
            "visits": [v.model_dump(mode="json") for v in visits],
            "investigations": [i.model_dump(mode="json") for i in investigations],
            "procedures": [p.model_dump(mode="json") for p in procedures],
        }

        # Write JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

        return output_path

    # ============== CSV EXPORTS ==============

    def export_all_patients_csv(self, output_path: Optional[Path] = None) -> Path:
        """Export all patients to CSV file.

        Args:
            output_path: Optional custom output path

        Returns:
            Path to generated CSV file
        """
        if output_path is None:
            timestamp = self._get_timestamp()
            filename = f"Patients_{timestamp}.csv"
            output_path = self.output_dir / filename

        patients = self.db.get_all_patients()

        # Write CSV with UTF-8 BOM for Excel compatibility
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "uhid", "name", "age", "gender", "phone", "address", "created_at"
            ])

            # Data rows
            for p in patients:
                writer.writerow([
                    p.uhid or "",
                    p.name,
                    p.age or "",
                    p.gender or "",
                    p.phone or "",
                    p.address or "",
                    str(p.created_at) if p.created_at else "",
                ])

        return output_path

    def export_all_visits_csv(self, output_path: Optional[Path] = None) -> Path:
        """Export all visits to CSV file.

        Args:
            output_path: Optional custom output path

        Returns:
            Path to generated CSV file
        """
        if output_path is None:
            timestamp = self._get_timestamp()
            filename = f"Visits_{timestamp}.csv"
            output_path = self.output_dir / filename

        # Get all patients and their visits
        patients = self.db.get_all_patients()
        all_visits = []

        for patient in patients:
            visits = self.db.get_patient_visits(patient.id)
            for visit in visits:
                all_visits.append({
                    "patient_uhid": patient.uhid,
                    "patient_name": patient.name,
                    "visit": visit
                })

        # Write CSV with UTF-8 BOM for Excel compatibility
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "patient_uhid", "patient_name", "visit_date", "chief_complaint",
                "diagnosis", "clinical_notes", "created_at"
            ])

            # Data rows
            for item in all_visits:
                v = item["visit"]
                writer.writerow([
                    item["patient_uhid"] or "",
                    item["patient_name"],
                    str(v.visit_date) if v.visit_date else "",
                    v.chief_complaint or "",
                    v.diagnosis or "",
                    v.clinical_notes or "",
                    str(v.created_at) if v.created_at else "",
                ])

        return output_path

    def export_all_investigations_csv(self, output_path: Optional[Path] = None) -> Path:
        """Export all investigations to CSV file.

        Args:
            output_path: Optional custom output path

        Returns:
            Path to generated CSV file
        """
        if output_path is None:
            timestamp = self._get_timestamp()
            filename = f"Investigations_{timestamp}.csv"
            output_path = self.output_dir / filename

        # Get all patients and their investigations
        patients = self.db.get_all_patients()
        all_investigations = []

        for patient in patients:
            investigations = self.db.get_patient_investigations(patient.id)
            for inv in investigations:
                all_investigations.append({
                    "patient_uhid": patient.uhid,
                    "patient_name": patient.name,
                    "investigation": inv
                })

        # Write CSV with UTF-8 BOM for Excel compatibility
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "patient_uhid", "patient_name", "test_date", "test_name",
                "result", "unit", "reference_range", "is_abnormal", "created_at"
            ])

            # Data rows
            for item in all_investigations:
                i = item["investigation"]
                writer.writerow([
                    item["patient_uhid"] or "",
                    item["patient_name"],
                    str(i.test_date) if i.test_date else "",
                    i.test_name,
                    i.result or "",
                    i.unit or "",
                    i.reference_range or "",
                    "Yes" if i.is_abnormal else "No",
                    str(i.created_at) if i.created_at else "",
                ])

        return output_path

    def export_all_procedures_csv(self, output_path: Optional[Path] = None) -> Path:
        """Export all procedures to CSV file.

        Args:
            output_path: Optional custom output path

        Returns:
            Path to generated CSV file
        """
        if output_path is None:
            timestamp = self._get_timestamp()
            filename = f"Procedures_{timestamp}.csv"
            output_path = self.output_dir / filename

        # Get all patients and their procedures
        patients = self.db.get_all_patients()
        all_procedures = []

        for patient in patients:
            procedures = self.db.get_patient_procedures(patient.id)
            for proc in procedures:
                all_procedures.append({
                    "patient_uhid": patient.uhid,
                    "patient_name": patient.name,
                    "procedure": proc
                })

        # Write CSV with UTF-8 BOM for Excel compatibility
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "patient_uhid", "patient_name", "procedure_date", "procedure_name",
                "details", "notes", "created_at"
            ])

            # Data rows
            for item in all_procedures:
                p = item["procedure"]
                writer.writerow([
                    item["patient_uhid"] or "",
                    item["patient_name"],
                    str(p.procedure_date) if p.procedure_date else "",
                    p.procedure_name,
                    p.details or "",
                    p.notes or "",
                    str(p.created_at) if p.created_at else "",
                ])

        return output_path

    # ============== FULL DATABASE JSON EXPORT ==============

    def export_full_database_json(self, output_path: Optional[Path] = None) -> Path:
        """Export entire database as JSON bundle.

        Args:
            output_path: Optional custom output path

        Returns:
            Path to generated JSON file
        """
        if output_path is None:
            timestamp = self._get_timestamp()
            filename = f"FullDatabase_{timestamp}.json"
            output_path = self.output_dir / filename

        # Get all data
        patients = self.db.get_all_patients()
        all_visits = []
        all_investigations = []
        all_procedures = []

        for patient in patients:
            all_visits.extend(self.db.get_patient_visits(patient.id))
            all_investigations.extend(self.db.get_patient_investigations(patient.id))
            all_procedures.extend(self.db.get_patient_procedures(patient.id))

        # Build export data
        export_data = {
            "export_version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "patient_count": len(patients),
            "visit_count": len(all_visits),
            "investigation_count": len(all_investigations),
            "procedure_count": len(all_procedures),
            "patients": [p.model_dump(mode="json") for p in patients],
            "visits": [v.model_dump(mode="json") for v in all_visits],
            "investigations": [i.model_dump(mode="json") for i in all_investigations],
            "procedures": [p.model_dump(mode="json") for p in all_procedures],
        }

        # Write JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

        return output_path
