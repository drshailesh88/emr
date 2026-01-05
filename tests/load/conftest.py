"""Fixtures for load testing.

This module provides fixtures to create large test databases with
realistic data for performance testing.
"""

import os
import sys
import time
import sqlite3
import tempfile
import functools
import tracemalloc
from pathlib import Path
from datetime import datetime, date
from typing import List, Generator

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.database import DatabaseService
from src.models.schemas import Patient, Visit
from tests.load.generators.patient_generator import generate_patients, generate_heavy_patients
from tests.load.generators.visit_generator import (
    generate_patient_visits,
    generate_heavy_patient_visits
)
from tests.load.generators.prescription_generator import (
    generate_prescription_json,
    generate_chronic_prescription
)


# ============== PERFORMANCE MEASUREMENT DECORATORS ==============

class PerformanceTimer:
    """Context manager and decorator for timing operations."""

    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.elapsed_ms = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end_time = time.perf_counter()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000

    def __call__(self, func):
        """Use as decorator."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                result = func(*args, **kwargs)
            return result
        return wrapper

    def __str__(self):
        if self.elapsed_ms is not None:
            return f"{self.name}: {self.elapsed_ms:.2f}ms"
        return f"{self.name}: not measured"


class MemoryProfiler:
    """Context manager for profiling memory usage."""

    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_memory = None
        self.peak_memory = None
        self.end_memory = None
        self.memory_delta_mb = None

    def __enter__(self):
        tracemalloc.start()
        self.start_memory = tracemalloc.get_traced_memory()[0]
        return self

    def __exit__(self, *args):
        current, peak = tracemalloc.get_traced_memory()
        self.end_memory = current
        self.peak_memory = peak
        self.memory_delta_mb = (current - self.start_memory) / 1024 / 1024
        tracemalloc.stop()

    def get_peak_mb(self):
        """Get peak memory usage in MB."""
        if self.peak_memory is not None:
            return self.peak_memory / 1024 / 1024
        return 0

    def __str__(self):
        if self.memory_delta_mb is not None:
            peak_mb = self.get_peak_mb()
            return f"{self.name}: Delta={self.memory_delta_mb:.2f}MB, Peak={peak_mb:.2f}MB"
        return f"{self.name}: not measured"


def performance_timer(name: str = None):
    """Decorator factory for performance timing."""
    def decorator(func):
        timer_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timer = PerformanceTimer(timer_name)
            with timer:
                result = func(*args, **kwargs)
            # Store timing in function for test access
            wrapper.elapsed_ms = timer.elapsed_ms
            return result
        return wrapper
    return decorator


# ============== DATABASE FIXTURES ==============

@pytest.fixture(scope='function')
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    db_service = DatabaseService(db_path)
    yield db_service

    # Cleanup
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture(scope='function')
def small_db(temp_db):
    """Database with 100 patients, 5-10 visits each."""
    db = temp_db

    print("\nGenerating small test database (100 patients)...")
    patients_data = generate_patients(100)

    for patient_data in patients_data:
        # Add patient
        patient = Patient(**patient_data)
        patient = db.add_patient(patient)

        # Add visits
        visit_count = 5 if patient.age < 40 else 10
        visits = generate_patient_visits(patient.id, visit_count)

        for visit_data in visits:
            # Add prescription
            visit_data['prescription_json'] = generate_prescription_json(
                visit_data['diagnosis']
            )

            visit = Visit(**visit_data)
            db.add_visit(visit)

    print(f"Created {len(patients_data)} patients")
    return db


@pytest.fixture(scope='function')
def medium_db(temp_db):
    """Database with 1,000 patients, realistic visit distribution."""
    db = temp_db

    print("\nGenerating medium test database (1,000 patients)...")
    patients_data = generate_patients(1000)

    for idx, patient_data in enumerate(patients_data):
        if idx % 100 == 0:
            print(f"  Progress: {idx}/1000 patients...")

        # Add patient
        patient = Patient(**patient_data)
        patient = db.add_patient(patient)

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
            db.add_visit(visit)

    print(f"Created {len(patients_data)} patients")
    return db


@pytest.fixture(scope='session')
def large_db():
    """Database with 10,000 patients - created once per session.

    This is the main fixture for load testing. It creates a realistic
    database with 10K patients and varied visit histories.
    """
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    db = DatabaseService(db_path)

    print("\n" + "="*60)
    print("GENERATING LARGE TEST DATABASE (10,000 patients)")
    print("="*60)
    print("This may take a few minutes...")

    start_time = time.time()

    # Generate patients in batches
    batch_size = 1000
    total_patients = 10000

    for batch_num in range(total_patients // batch_size):
        batch_start = batch_num * batch_size
        print(f"\nBatch {batch_num + 1}/10: Patients {batch_start + 1}-{batch_start + batch_size}")

        patients_data = generate_patients(
            batch_size,
            start_id=batch_start + 1
        )

        for idx, patient_data in enumerate(patients_data):
            if idx % 100 == 0 and idx > 0:
                print(f"  Progress: {idx}/1000 in batch...")

            # Add patient
            patient = Patient(**patient_data)
            patient = db.add_patient(patient)

            # Determine visit count based on age
            if patient.age > 65:
                visit_count = 20  # Elderly patients
            elif patient.age > 50:
                visit_count = 15
            elif patient.age > 35:
                visit_count = 10
            else:
                visit_count = 5  # Young patients

            # Generate visits
            chronic_condition = None
            if patient.age > 50 and (idx % 3 == 0):  # ~33% have chronic conditions
                chronic_condition = 'Type 2 Diabetes Mellitus'

            visits = generate_patient_visits(
                patient.id,
                visit_count,
                chronic_condition=chronic_condition
            )

            for visit_data in visits:
                # Generate prescription
                if chronic_condition:
                    import json
                    prescription = generate_chronic_prescription(chronic_condition)
                    visit_data['prescription_json'] = json.dumps(prescription)
                else:
                    visit_data['prescription_json'] = generate_prescription_json(
                        visit_data['diagnosis'],
                        medication_count=3
                    )

                visit = Visit(**visit_data)
                db.add_visit(visit)

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Database generation complete in {elapsed:.2f} seconds")
    print(f"{'='*60}\n")

    # Print statistics
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM visits")
        visit_count = cursor.fetchone()[0]

    print(f"Statistics:")
    print(f"  Patients: {patient_count:,}")
    print(f"  Visits: {visit_count:,}")
    print(f"  Avg visits/patient: {visit_count/patient_count:.1f}")
    print()

    yield db

    # Cleanup
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture(scope='function')
def heavy_patient_db(temp_db):
    """Database with patients having very heavy visit histories (50-100 visits each).

    Used for testing performance with individual patients who have
    extensive medical histories.
    """
    db = temp_db

    print("\nGenerating heavy patient database...")
    patients_data = generate_heavy_patients(20)

    for patient_data in patients_data:
        # Add patient
        patient = Patient(**patient_data)
        patient = db.add_patient(patient)

        # Generate many visits
        visits = generate_heavy_patient_visits(patient.id)

        for visit_data in visits:
            visit_data['prescription_json'] = generate_prescription_json(
                visit_data['diagnosis']
            )
            visit = Visit(**visit_data)
            db.add_visit(visit)

    print(f"Created {len(patients_data)} heavy patients")
    return db


# ============== UTILITY FIXTURES ==============

@pytest.fixture
def timer():
    """Fixture providing a PerformanceTimer."""
    return PerformanceTimer


@pytest.fixture
def memory_profiler():
    """Fixture providing a MemoryProfiler."""
    return MemoryProfiler


@pytest.fixture
def benchmark_result():
    """Fixture for storing benchmark results."""
    results = {}

    def store(name: str, value: float, unit: str = 'ms'):
        results[name] = {'value': value, 'unit': unit}

    store.results = results
    return store


# ============== HELPER FUNCTIONS ==============

def get_db_stats(db: DatabaseService) -> dict:
    """Get database statistics.

    Args:
        db: DatabaseService instance

    Returns:
        Dict with patient count, visit count, etc.
    """
    with db.get_connection() as conn:
        cursor = conn.cursor()

        stats = {}

        cursor.execute("SELECT COUNT(*) FROM patients")
        stats['patient_count'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM visits")
        stats['visit_count'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM investigations")
        stats['investigation_count'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM procedures")
        stats['procedure_count'] = cursor.fetchone()[0]

        if stats['patient_count'] > 0:
            stats['avg_visits_per_patient'] = stats['visit_count'] / stats['patient_count']
        else:
            stats['avg_visits_per_patient'] = 0

    return stats


def print_db_stats(db: DatabaseService, label: str = "Database"):
    """Print database statistics."""
    stats = get_db_stats(db)
    print(f"\n{label} Statistics:")
    print(f"  Patients: {stats['patient_count']:,}")
    print(f"  Visits: {stats['visit_count']:,}")
    print(f"  Investigations: {stats['investigation_count']:,}")
    print(f"  Procedures: {stats['procedure_count']:,}")
    print(f"  Avg visits/patient: {stats['avg_visits_per_patient']:.1f}")
