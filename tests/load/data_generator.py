"""Unified data generator for load testing.

This module provides a single interface to generate realistic test data
at various scales. It consolidates patient, visit, and prescription generators.
"""

import json
from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta

from src.services.database import DatabaseService
from src.models.schemas import Patient, Visit, Investigation, Procedure
from tests.load.generators.patient_generator import (
    generate_patient,
    generate_patients,
    generate_patients_with_conditions,
    generate_heavy_patients
)
from tests.load.generators.visit_generator import (
    generate_visit,
    generate_patient_visits,
    generate_heavy_patient_visits,
    generate_visit_sequence
)
from tests.load.generators.prescription_generator import (
    generate_prescription,
    generate_prescription_json,
    generate_chronic_prescription
)


class DataGenerator:
    """Unified data generator for load testing.

    Provides convenient methods to generate realistic test data at scale
    and populate databases with various data patterns.
    """

    def __init__(self, db: Optional[DatabaseService] = None):
        """Initialize data generator.

        Args:
            db: Optional database service to populate
        """
        self.db = db

    # ============== PATIENT GENERATION ==============

    def generate_patient(self, **kwargs) -> Dict:
        """Generate a single patient.

        Args:
            **kwargs: Arguments passed to patient_generator.generate_patient

        Returns:
            Patient data dict
        """
        return generate_patient(**kwargs)

    def generate_patients(self, count: int, **kwargs) -> List[Dict]:
        """Generate multiple patients.

        Args:
            count: Number of patients to generate
            **kwargs: Additional arguments

        Returns:
            List of patient data dicts
        """
        return generate_patients(count, **kwargs)

    def generate_and_save_patients(
        self,
        count: int,
        with_visits: bool = True,
        visits_per_patient: Tuple[int, int] = (5, 15),
        **kwargs
    ) -> List[Patient]:
        """Generate patients and save to database.

        Args:
            count: Number of patients to generate
            with_visits: Whether to generate visits for each patient
            visits_per_patient: Tuple of (min, max) visits per patient
            **kwargs: Additional arguments

        Returns:
            List of saved Patient objects
        """
        if not self.db:
            raise ValueError("Database service required for saving patients")

        import random

        patients_data = generate_patients(count, **kwargs)
        saved_patients = []

        for patient_data in patients_data:
            # Save patient
            patient = Patient(**patient_data)
            patient = self.db.add_patient(patient)
            saved_patients.append(patient)

            # Add visits if requested
            if with_visits:
                min_visits, max_visits = visits_per_patient
                visit_count = random.randint(min_visits, max_visits)

                # Adjust based on age
                if patient.age < 30:
                    visit_count = min(visit_count, 5)
                elif patient.age > 60:
                    visit_count = max(visit_count, 10)

                # Generate and save visits
                visits = generate_patient_visits(patient.id, visit_count)
                for visit_data in visits:
                    visit_data['prescription_json'] = generate_prescription_json(
                        visit_data['diagnosis']
                    )
                    visit = Visit(**visit_data)
                    self.db.add_visit(visit)

        return saved_patients

    # ============== VISIT GENERATION ==============

    def generate_visit(self, patient_id: int, **kwargs) -> Dict:
        """Generate a single visit.

        Args:
            patient_id: Patient ID
            **kwargs: Additional arguments

        Returns:
            Visit data dict
        """
        return generate_visit(patient_id, **kwargs)

    def generate_visits(
        self,
        patient_id: int,
        count: int,
        **kwargs
    ) -> List[Dict]:
        """Generate multiple visits for a patient.

        Args:
            patient_id: Patient ID
            count: Number of visits to generate
            **kwargs: Additional arguments

        Returns:
            List of visit data dicts
        """
        return generate_patient_visits(patient_id, count, **kwargs)

    def generate_and_save_visits(
        self,
        patient_id: int,
        count: int,
        with_prescriptions: bool = True,
        **kwargs
    ) -> List[Visit]:
        """Generate visits and save to database.

        Args:
            patient_id: Patient ID
            count: Number of visits to generate
            with_prescriptions: Whether to include prescriptions
            **kwargs: Additional arguments

        Returns:
            List of saved Visit objects
        """
        if not self.db:
            raise ValueError("Database service required for saving visits")

        visits_data = generate_patient_visits(patient_id, count, **kwargs)
        saved_visits = []

        for visit_data in visits_data:
            if with_prescriptions:
                visit_data['prescription_json'] = generate_prescription_json(
                    visit_data['diagnosis']
                )

            visit = Visit(**visit_data)
            visit = self.db.add_visit(visit)
            saved_visits.append(visit)

        return saved_visits

    # ============== PRESCRIPTION GENERATION ==============

    def generate_prescription(
        self,
        diagnosis: str,
        **kwargs
    ) -> Dict:
        """Generate a prescription.

        Args:
            diagnosis: Primary diagnosis
            **kwargs: Additional arguments

        Returns:
            Prescription dict
        """
        return generate_prescription(diagnosis, **kwargs)

    def generate_prescription_json(
        self,
        diagnosis: str,
        **kwargs
    ) -> str:
        """Generate a prescription as JSON string.

        Args:
            diagnosis: Primary diagnosis
            **kwargs: Additional arguments

        Returns:
            JSON string of prescription
        """
        return generate_prescription_json(diagnosis, **kwargs)

    # ============== SCALE TESTING PRESETS ==============

    def populate_small_database(self, patient_count: int = 100) -> Dict:
        """Populate database with small dataset (100 patients).

        Args:
            patient_count: Number of patients (default: 100)

        Returns:
            Dict with statistics
        """
        if not self.db:
            raise ValueError("Database service required")

        print(f"Populating small database ({patient_count} patients)...")

        saved_patients = self.generate_and_save_patients(
            patient_count,
            with_visits=True,
            visits_per_patient=(5, 10)
        )

        stats = self._get_statistics()
        print(f"  Complete: {stats['patient_count']} patients, {stats['visit_count']} visits")

        return stats

    def populate_medium_database(self, patient_count: int = 1000) -> Dict:
        """Populate database with medium dataset (1,000 patients).

        Args:
            patient_count: Number of patients (default: 1,000)

        Returns:
            Dict with statistics
        """
        if not self.db:
            raise ValueError("Database service required")

        print(f"Populating medium database ({patient_count} patients)...")

        import random

        batch_size = 100
        for batch_num in range(patient_count // batch_size):
            batch_start = batch_num * batch_size
            print(f"  Batch {batch_num + 1}: Patients {batch_start + 1}-{batch_start + batch_size}")

            patients_data = generate_patients(batch_size, start_id=batch_start + 1)

            for patient_data in patients_data:
                patient = Patient(**patient_data)
                patient = self.db.add_patient(patient)

                # Varied visit counts
                if patient.age > 60:
                    visit_count = 15
                elif patient.age > 40:
                    visit_count = 10
                else:
                    visit_count = 5

                visits = generate_patient_visits(patient.id, visit_count)
                for visit_data in visits:
                    visit_data['prescription_json'] = generate_prescription_json(
                        visit_data['diagnosis'],
                        medication_count=3
                    )
                    visit = Visit(**visit_data)
                    self.db.add_visit(visit)

        stats = self._get_statistics()
        print(f"  Complete: {stats['patient_count']} patients, {stats['visit_count']} visits")

        return stats

    def populate_large_database(self, patient_count: int = 10000) -> Dict:
        """Populate database with large dataset (10,000 patients).

        Args:
            patient_count: Number of patients (default: 10,000)

        Returns:
            Dict with statistics
        """
        if not self.db:
            raise ValueError("Database service required")

        print(f"Populating large database ({patient_count} patients)...")
        print("This may take several minutes...")

        import random
        import time

        start_time = time.time()
        batch_size = 1000

        for batch_num in range(patient_count // batch_size):
            batch_start = batch_num * batch_size
            print(f"\nBatch {batch_num + 1}/{patient_count // batch_size}: " +
                  f"Patients {batch_start + 1}-{batch_start + batch_size}")

            patients_data = generate_patients(batch_size, start_id=batch_start + 1)

            for idx, patient_data in enumerate(patients_data):
                if idx % 100 == 0 and idx > 0:
                    print(f"    Progress: {idx}/1000...")

                patient = Patient(**patient_data)
                patient = self.db.add_patient(patient)

                # Age-based visit distribution
                if patient.age > 65:
                    visit_count = 20
                elif patient.age > 50:
                    visit_count = 15
                elif patient.age > 35:
                    visit_count = 10
                else:
                    visit_count = 5

                # Chronic conditions for some patients
                chronic_condition = None
                if patient.age > 50 and (idx % 3 == 0):
                    chronic_condition = 'Type 2 Diabetes Mellitus'

                visits = generate_patient_visits(
                    patient.id,
                    visit_count,
                    chronic_condition=chronic_condition
                )

                for visit_data in visits:
                    if chronic_condition:
                        prescription = generate_chronic_prescription(chronic_condition)
                        visit_data['prescription_json'] = json.dumps(prescription)
                    else:
                        visit_data['prescription_json'] = generate_prescription_json(
                            visit_data['diagnosis'],
                            medication_count=3
                        )

                    visit = Visit(**visit_data)
                    self.db.add_visit(visit)

        elapsed = time.time() - start_time
        stats = self._get_statistics()
        print(f"\n  Complete in {elapsed:.2f}s ({elapsed/60:.2f} minutes)")
        print(f"  {stats['patient_count']} patients, {stats['visit_count']} visits")

        return stats

    def populate_heavy_patient_database(
        self,
        patient_count: int = 20,
        visits_per_patient: Tuple[int, int] = (50, 100)
    ) -> Dict:
        """Populate database with patients having heavy visit histories.

        Args:
            patient_count: Number of heavy patients (default: 20)
            visits_per_patient: Tuple of (min, max) visits

        Returns:
            Dict with statistics
        """
        if not self.db:
            raise ValueError("Database service required")

        print(f"Populating heavy patient database ({patient_count} patients)...")

        patients_data = generate_heavy_patients(patient_count)

        for patient_data in patients_data:
            patient = Patient(**patient_data)
            patient = self.db.add_patient(patient)

            # Heavy visit history
            visits = generate_heavy_patient_visits(patient.id)

            for visit_data in visits:
                visit_data['prescription_json'] = generate_prescription_json(
                    visit_data['diagnosis']
                )
                visit = Visit(**visit_data)
                self.db.add_visit(visit)

        stats = self._get_statistics()
        print(f"  Complete: {stats['patient_count']} patients, {stats['visit_count']} visits")
        print(f"  Average: {stats['avg_visits_per_patient']:.1f} visits/patient")

        return stats

    # ============== SPECIALIZED GENERATORS ==============

    def generate_chronic_disease_cohort(
        self,
        condition: str,
        patient_count: int = 50
    ) -> List[Patient]:
        """Generate cohort of patients with specific chronic condition.

        Args:
            condition: Chronic condition (e.g., 'Type 2 Diabetes Mellitus')
            patient_count: Number of patients

        Returns:
            List of Patient objects
        """
        if not self.db:
            raise ValueError("Database service required")

        print(f"Generating {patient_count} patients with {condition}...")

        patients_data = generate_patients(
            patient_count,
            age_distribution={(50, 80): 1.0}  # Older patients
        )

        saved_patients = []

        for patient_data in patients_data:
            patient = Patient(**patient_data)
            patient = self.db.add_patient(patient)
            saved_patients.append(patient)

            # Generate disease progression visits
            visits = generate_visit_sequence(
                patient.id,
                condition.split()[0],  # First word (Diabetes, Hypertension, etc.)
                visit_count=10
            )

            for visit_data in visits:
                prescription = generate_chronic_prescription(condition)
                visit_data['prescription_json'] = json.dumps(prescription)

                visit = Visit(**visit_data)
                self.db.add_visit(visit)

        print(f"  Complete: Generated {len(saved_patients)} patients with {condition}")

        return saved_patients

    def generate_recent_activity(self, days: int = 7) -> Dict:
        """Generate recent patient activity for realistic testing.

        Args:
            days: Number of days of recent activity

        Returns:
            Dict with statistics
        """
        if not self.db:
            raise ValueError("Database service required")

        import random

        print(f"Generating recent activity (last {days} days)...")

        # Get random existing patients
        all_patients = self.db.get_all_patients()
        if not all_patients:
            print("  No patients in database. Add patients first.")
            return {}

        # Select random patients for recent visits
        visit_count = min(20, len(all_patients) // 2)
        recent_patients = random.sample(all_patients, visit_count)

        visits_added = 0

        for patient in recent_patients:
            # Generate 1-3 recent visits
            for _ in range(random.randint(1, 3)):
                days_ago = random.randint(0, days)
                visit_date = date.today() - timedelta(days=days_ago)

                visit_data = generate_visit(patient.id, visit_date=visit_date)
                visit_data['prescription_json'] = generate_prescription_json(
                    visit_data['diagnosis']
                )

                visit = Visit(**visit_data)
                self.db.add_visit(visit)
                visits_added += 1

        print(f"  Complete: Added {visits_added} recent visits")

        return {
            'patients_with_activity': len(recent_patients),
            'visits_added': visits_added,
            'date_range': f"{date.today() - timedelta(days=days)} to {date.today()}"
        }

    # ============== UTILITY METHODS ==============

    def _get_statistics(self) -> Dict:
        """Get database statistics.

        Returns:
            Dict with patient count, visit count, etc.
        """
        if not self.db:
            return {}

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM patients")
            patient_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM visits")
            visit_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM investigations")
            investigation_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM procedures")
            procedure_count = cursor.fetchone()[0]

            avg_visits = visit_count / patient_count if patient_count > 0 else 0

        return {
            'patient_count': patient_count,
            'visit_count': visit_count,
            'investigation_count': investigation_count,
            'procedure_count': procedure_count,
            'avg_visits_per_patient': avg_visits
        }

    def print_statistics(self):
        """Print database statistics."""
        stats = self._get_statistics()

        print("\nDatabase Statistics:")
        print(f"  Patients: {stats['patient_count']:,}")
        print(f"  Visits: {stats['visit_count']:,}")
        print(f"  Investigations: {stats['investigation_count']:,}")
        print(f"  Procedures: {stats['procedure_count']:,}")
        print(f"  Avg visits/patient: {stats['avg_visits_per_patient']:.1f}")


# ============== CONVENIENCE FUNCTIONS ==============

def quick_populate(db: DatabaseService, scale: str = 'small') -> Dict:
    """Quickly populate database with test data.

    Args:
        db: Database service
        scale: Scale level ('small', 'medium', 'large', 'heavy')

    Returns:
        Dict with statistics
    """
    generator = DataGenerator(db)

    scale_map = {
        'small': generator.populate_small_database,
        'medium': generator.populate_medium_database,
        'large': generator.populate_large_database,
        'heavy': generator.populate_heavy_patient_database,
    }

    if scale not in scale_map:
        raise ValueError(f"Unknown scale: {scale}. Choose from: {list(scale_map.keys())}")

    return scale_map[scale]()


if __name__ == '__main__':
    # Demo/test the generator
    import tempfile
    import os

    print("="*60)
    print("Data Generator Demo")
    print("="*60)

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    try:
        db = DatabaseService(db_path)
        generator = DataGenerator(db)

        # Generate small dataset
        print("\nGenerating small dataset...")
        stats = generator.populate_small_database(patient_count=50)
        generator.print_statistics()

        # Generate recent activity
        print("\nGenerating recent activity...")
        activity = generator.generate_recent_activity(days=7)
        print(f"  Recent activity: {activity}")

        print("\n" + "="*60)
        print("Demo complete!")
        print("="*60)

    finally:
        try:
            os.unlink(db_path)
        except:
            pass
