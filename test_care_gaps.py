#!/usr/bin/env python3
"""Test script for care gap detection."""

import sys
import os
from datetime import date, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.database import DatabaseService
from src.services.analytics.care_gap_detector import CareGapDetector, CareGapPriority
from src.models.schemas import Patient, Visit, Investigation, Procedure
import json


def print_care_gap(gap):
    """Pretty print a care gap."""
    priority_emoji = {
        CareGapPriority.URGENT: "🔴",
        CareGapPriority.SOON: "🟡",
        CareGapPriority.ROUTINE: "🔵",
    }

    emoji = priority_emoji.get(gap.priority, "ℹ️")
    print(f"\n{emoji} {gap.description}")
    print(f"   Category: {gap.category}")
    print(f"   Priority: {gap.priority.value}")
    print(f"   Recommendation: {gap.recommendation}")
    if gap.days_overdue:
        print(f"   Days overdue: {gap.days_overdue}")
    if gap.last_done_date:
        print(f"   Last done: {gap.last_done_date}")
    if gap.details:
        print(f"   Details: {gap.details}")
    print(f"   Action type: {gap.action_type}")


def main():
    """Test care gap detection."""
    print("=" * 70)
    print("CARE GAP DETECTOR TEST")
    print("=" * 70)

    # Initialize database (use test database)
    db_path = "data/clinic_test_gaps.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    db = DatabaseService(db_path)
    detector = CareGapDetector(db)

    print("\n📝 Creating test patient with diabetes and hypertension...")

    # Create a diabetic, hypertensive patient
    patient = Patient(
        name="Ram Kumar",
        age=58,
        gender="M",
        phone="9876543210"
    )
    patient = db.add_patient(patient)
    print(f"✓ Created patient: {patient.name} (ID: {patient.id})")

    # Add a visit with diabetes and hypertension diagnosis
    visit = Visit(
        patient_id=patient.id,
        visit_date=date.today() - timedelta(days=120),  # 4 months ago
        chief_complaint="Follow-up for diabetes and hypertension",
        diagnosis="Type 2 Diabetes Mellitus, Hypertension",
        prescription_json=json.dumps({
            "diagnosis": ["Type 2 Diabetes", "Hypertension"],
            "medications": [
                {
                    "drug_name": "Metformin",
                    "strength": "500mg",
                    "dose": "1",
                    "frequency": "BD"
                },
                {
                    "drug_name": "Atorvastatin",
                    "strength": "10mg",
                    "dose": "1",
                    "frequency": "OD"
                }
            ],
            "follow_up": "2 weeks"
        })
    )
    db.add_visit(visit)
    print(f"✓ Added visit from {visit.visit_date}")

    # Add an old HbA1c test (5 months ago)
    hba1c = Investigation(
        patient_id=patient.id,
        test_name="HbA1c",
        result="7.2",
        unit="%",
        reference_range="4.0-5.6",
        test_date=date.today() - timedelta(days=150),
        is_abnormal=True
    )
    db.add_investigation(hba1c)
    print(f"✓ Added HbA1c test from {hba1c.test_date}")

    # Detect care gaps
    print("\n" + "=" * 70)
    print("DETECTING CARE GAPS...")
    print("=" * 70)

    gaps = detector.detect_care_gaps(patient.id)

    if gaps:
        print(f"\n✓ Found {len(gaps)} care gap(s):\n")
        for i, gap in enumerate(gaps, 1):
            print(f"\n--- Care Gap {i}/{len(gaps)} ---")
            print_care_gap(gap)
    else:
        print("\n✓ No care gaps detected!")

    # Test case 2: Patient on Warfarin
    print("\n" + "=" * 70)
    print("TEST CASE 2: Patient on Warfarin")
    print("=" * 70)

    patient2 = Patient(
        name="Sita Devi",
        age=72,
        gender="F",
    )
    patient2 = db.add_patient(patient2)
    print(f"✓ Created patient: {patient2.name} (ID: {patient2.id})")

    visit2 = Visit(
        patient_id=patient2.id,
        visit_date=date.today() - timedelta(days=45),
        diagnosis="Atrial fibrillation on warfarin",
        prescription_json=json.dumps({
            "medications": [
                {
                    "drug_name": "Warfarin",
                    "strength": "5mg",
                    "dose": "1",
                    "frequency": "OD"
                }
            ]
        })
    )
    db.add_visit(visit2)

    gaps2 = detector.detect_care_gaps(patient2.id)
    if gaps2:
        print(f"\n✓ Found {len(gaps2)} care gap(s):\n")
        for i, gap in enumerate(gaps2, 1):
            print(f"\n--- Care Gap {i}/{len(gaps2)} ---")
            print_care_gap(gap)

    # Test case 3: Elderly patient needing preventive care
    print("\n" + "=" * 70)
    print("TEST CASE 3: Elderly patient needing preventive care")
    print("=" * 70)

    patient3 = Patient(
        name="Rajesh Sharma",
        age=55,
        gender="M",
    )
    patient3 = db.add_patient(patient3)
    print(f"✓ Created patient: {patient3.name} (ID: {patient3.id})")

    visit3 = Visit(
        patient_id=patient3.id,
        visit_date=date.today() - timedelta(days=30),
        diagnosis="Routine checkup",
    )
    db.add_visit(visit3)

    gaps3 = detector.detect_care_gaps(patient3.id)
    if gaps3:
        print(f"\n✓ Found {len(gaps3)} care gap(s):\n")
        for i, gap in enumerate(gaps3, 1):
            print(f"\n--- Care Gap {i}/{len(gaps3)} ---")
            print_care_gap(gap)

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\nNote: Care gaps are automatically displayed when a patient is selected.")
    print("The UI shows color-coded alerts (red=urgent, yellow=soon, blue=routine)")
    print("with action buttons to create orders or set reminders.")

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"\n✓ Cleaned up test database: {db_path}")


if __name__ == "__main__":
    main()
