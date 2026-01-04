#!/usr/bin/env python3
"""Test script for export functionality."""

from src.services.database import DatabaseService
from src.services.pdf import PDFService
from src.services.export import ExportService
from src.models.schemas import Patient, Visit, Investigation, Procedure
from datetime import date

def test_export():
    """Test export functionality with sample data."""

    # Initialize services
    db = DatabaseService()
    pdf = PDFService()
    export = ExportService(db=db, pdf_service=pdf)

    print("Export Service Test")
    print("=" * 50)

    # Get all patients
    patients = db.get_all_patients()
    print(f"\n1. Found {len(patients)} patients in database")

    if patients:
        # Test patient summary PDF export
        patient = patients[0]
        print(f"\n2. Testing PDF export for patient: {patient.name}")

        try:
            pdf_path = export.export_patient_summary_pdf(patient.id)
            print(f"   Success! PDF saved to: {pdf_path}")
        except Exception as e:
            print(f"   Error: {e}")

        # Test patient JSON export
        print(f"\n3. Testing JSON export for patient: {patient.name}")
        try:
            json_path = export.export_patient_json(patient.id)
            print(f"   Success! JSON saved to: {json_path}")
        except Exception as e:
            print(f"   Error: {e}")

    # Test CSV exports
    print(f"\n4. Testing CSV exports...")

    try:
        patients_csv = export.export_all_patients_csv()
        print(f"   Patients CSV: {patients_csv}")
    except Exception as e:
        print(f"   Patients CSV Error: {e}")

    try:
        visits_csv = export.export_all_visits_csv()
        print(f"   Visits CSV: {visits_csv}")
    except Exception as e:
        print(f"   Visits CSV Error: {e}")

    try:
        investigations_csv = export.export_all_investigations_csv()
        print(f"   Investigations CSV: {investigations_csv}")
    except Exception as e:
        print(f"   Investigations CSV Error: {e}")

    try:
        procedures_csv = export.export_all_procedures_csv()
        print(f"   Procedures CSV: {procedures_csv}")
    except Exception as e:
        print(f"   Procedures CSV Error: {e}")

    # Test full database JSON export
    print(f"\n5. Testing full database JSON export...")
    try:
        full_json = export.export_full_database_json()
        print(f"   Success! Full database JSON: {full_json}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 50)
    print("Export test completed!")
    print(f"Check the data/exports/ directory for exported files.")

if __name__ == "__main__":
    test_export()
