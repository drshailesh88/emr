#!/usr/bin/env python3
"""Script to view sample patient data in DocAssist EMR."""

import sys
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.database import DatabaseService


def format_patient_summary(db: DatabaseService, patient_id: int):
    """Format and print patient summary."""
    patient = db.get_patient(patient_id)
    if not patient:
        print(f"Patient with ID {patient_id} not found.")
        return

    print(f"\n{'=' * 80}")
    print(f"PATIENT: {patient.name}")
    print(f"{'=' * 80}")
    print(f"UHID:    {patient.uhid}")
    print(f"Age:     {patient.age} years")
    print(f"Gender:  {patient.gender}")
    print(f"Phone:   {patient.phone}")
    print(f"Address: {patient.address}")

    # Visits
    visits = db.get_patient_visits(patient_id)
    print(f"\n--- VISITS ({len(visits)}) ---")
    for i, visit in enumerate(visits, 1):
        print(f"\n{i}. Visit Date: {visit.visit_date}")
        print(f"   Chief Complaint: {visit.chief_complaint}")
        print(f"   Diagnosis: {visit.diagnosis}")

        if visit.prescription_json:
            try:
                rx = json.loads(visit.prescription_json)
                meds = rx.get('medications', [])
                if meds:
                    print(f"   Medications ({len(meds)}):")
                    for med in meds:
                        print(f"     • {med['drug_name']} {med['strength']} - "
                              f"{med['dose']} {med['frequency']} x {med['duration']}")
            except json.JSONDecodeError:
                pass

    # Investigations
    investigations = db.get_patient_investigations(patient_id)
    if investigations:
        print(f"\n--- INVESTIGATIONS ({len(investigations)}) ---")
        for inv in investigations:
            abnormal = " ⚠️  ABNORMAL" if inv.is_abnormal else ""
            print(f"  • {inv.test_name}: {inv.result} {inv.unit} "
                  f"(Ref: {inv.reference_range}) - {inv.test_date}{abnormal}")

    # Procedures
    procedures = db.get_patient_procedures(patient_id)
    if procedures:
        print(f"\n--- PROCEDURES ({len(procedures)}) ---")
        for proc in procedures:
            print(f"\n  • {proc.procedure_name} ({proc.procedure_date})")
            print(f"    Details: {proc.details}")
            if proc.notes:
                notes_preview = proc.notes[:100] + "..." if len(proc.notes) > 100 else proc.notes
                print(f"    Notes: {notes_preview}")

    print(f"\n{'=' * 80}\n")


def list_all_patients(db: DatabaseService):
    """List all patients with basic info."""
    patients = db.get_all_patients()

    print(f"\n{'=' * 80}")
    print(f"ALL PATIENTS ({len(patients)})")
    print(f"{'=' * 80}\n")

    for i, patient in enumerate(patients, 1):
        visits = db.get_patient_visits(patient.id)
        investigations = db.get_patient_investigations(patient.id)
        procedures = db.get_patient_procedures(patient.id)

        # Get primary diagnosis from latest visit
        diagnosis = "No visits"
        if visits:
            diagnosis = visits[0].diagnosis or "No diagnosis recorded"

        print(f"{i:2}. {patient.name:<25} ({patient.uhid})")
        print(f"    {patient.age}{patient.gender} | {diagnosis[:50]}")
        print(f"    Visits: {len(visits)} | Labs: {len(investigations)} | Procedures: {len(procedures)}")
        print()


def main():
    """Main entry point."""
    db = DatabaseService()

    if len(sys.argv) > 1:
        try:
            patient_id = int(sys.argv[1])
            format_patient_summary(db, patient_id)
        except ValueError:
            print("Error: Patient ID must be a number")
            print("Usage: python3 view_sample_data.py [patient_id]")
            sys.exit(1)
    else:
        list_all_patients(db)
        print("\nTo view detailed info for a patient, run:")
        print("  python3 view_sample_data.py <patient_id>")
        print("\nExample: python3 view_sample_data.py 1")


if __name__ == "__main__":
    main()
