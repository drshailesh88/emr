#!/usr/bin/env python3
"""Test script for analytics dashboard with sample data."""

import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.database import DatabaseService
from src.services.analytics.practice_analytics import PracticeAnalytics
from src.services.analytics.patient_acquisition import PatientAcquisition
from src.services.analytics.retention_tracker import RetentionTracker
from src.models.schemas import Patient, Visit


def create_sample_data(db: DatabaseService):
    """Create sample patients and visits for testing."""
    print("Creating sample data...")

    # Create sample patients
    patients = [
        Patient(name="Ram Lal", age=65, gender="M", phone="9876543210", address="Delhi"),
        Patient(name="Priya Sharma", age=45, gender="F", phone="9876543211", address="Mumbai"),
        Patient(name="Amit Kumar", age=35, gender="M", phone="9876543212", address="Bangalore"),
        Patient(name="Sunita Devi", age=55, gender="F", phone="9876543213", address="Delhi"),
        Patient(name="Rajesh Singh", age=42, gender="M", phone="9876543214", address="Pune"),
    ]

    created_patients = []
    for p in patients:
        created = db.add_patient(p)
        created_patients.append(created)
        print(f"  Created patient: {created.name} ({created.uhid})")

    # Create sample visits with various diagnoses
    diagnoses = [
        "Diabetes Mellitus Type 2",
        "Hypertension",
        "Common Cold",
        "Diabetes Mellitus Type 2",
        "Hypertension",
        "Acute Gastritis",
        "Diabetes Mellitus Type 2",
        "Common Cold",
        "Migraine",
        "Hypertension",
    ]

    print("\nCreating sample visits...")
    for i, patient in enumerate(created_patients):
        # Create 2 visits per patient
        for j in range(2):
            visit = Visit(
                patient_id=patient.id,
                visit_date=date.today() - timedelta(days=i * 3 + j),
                chief_complaint=f"Complaint {i}{j}",
                clinical_notes=f"Patient presented with symptoms. Treatment initiated.",
                diagnosis=diagnoses[(i * 2 + j) % len(diagnoses)],
            )
            db.add_visit(visit)
            print(f"  Created visit for {patient.name}: {visit.diagnosis}")

    print(f"\nSample data created: {len(created_patients)} patients, {len(created_patients) * 2} visits")


def test_analytics(db: DatabaseService):
    """Test analytics services."""
    print("\n" + "=" * 60)
    print("TESTING ANALYTICS SERVICES")
    print("=" * 60)

    # Initialize analytics services
    practice_analytics = PracticeAnalytics(db)
    patient_acquisition = PatientAcquisition(db)
    retention_tracker = RetentionTracker(db)

    # Test practice analytics
    print("\n--- Practice Analytics ---")
    total = practice_analytics.get_total_patients()
    print(f"Total patients: {total}")

    this_month = practice_analytics.get_patients_this_month()
    print(f"Patients this month: {this_month}")

    today = practice_analytics.get_visits_today()
    print(f"Visits today: {today}")

    week = practice_analytics.get_visits_this_week()
    print(f"Visits this week: {week}")

    # Test top diagnoses
    print("\n--- Top Diagnoses ---")
    top_diagnoses = practice_analytics.get_top_diagnoses(5)
    for diagnosis, count in top_diagnoses:
        print(f"  {diagnosis}: {count} visits")

    # Test patient demographics
    print("\n--- Patient Demographics ---")
    demographics = practice_analytics.get_patient_demographics()
    print(f"Gender distribution: {demographics['gender']}")
    print(f"Age groups: {demographics['age_groups']}")

    # Test patient acquisition
    print("\n--- Patient Acquisition ---")
    growth_rate = patient_acquisition.get_growth_rate()
    print(f"Growth rate: {growth_rate:.1f}%")

    monthly = patient_acquisition.get_new_patients_by_month(3)
    print("New patients by month:")
    for month, count in monthly:
        print(f"  {month}: {count} patients")

    # Test retention tracker
    print("\n--- Retention Tracker ---")
    returning = retention_tracker.get_returning_patients()
    print(f"Returning patients: {returning}")

    churned = retention_tracker.get_patient_churn(30)  # 30 days
    print(f"Churned patients (30 days): {len(churned)}")
    if churned:
        print("Churned patient list:")
        for p in churned[:3]:  # Show first 3
            print(f"  {p['name']}: {p['days_since_visit']} days since last visit")

    print("\n" + "=" * 60)
    print("ANALYTICS TEST COMPLETE")
    print("=" * 60)


def main():
    """Main test function."""
    # Use a temporary database for testing
    test_db_path = "data/test_analytics.db"

    # Remove existing test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"Removed existing test database: {test_db_path}")

    # Initialize database
    db = DatabaseService(test_db_path)

    # Create sample data
    create_sample_data(db)

    # Test analytics
    test_analytics(db)

    print(f"\nTest database saved to: {test_db_path}")
    print("You can now run the app and view the analytics dashboard!")


if __name__ == "__main__":
    main()
