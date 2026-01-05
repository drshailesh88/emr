"""Startup time load tests.

Tests application startup performance at different database scales.
"""

import pytest
import time
import os
import tempfile
from pathlib import Path

from src.services.database import DatabaseService
from tests.load.benchmarks import BENCHMARKS, format_benchmark_result
from tests.load.generators.patient_generator import generate_patients
from tests.load.generators.visit_generator import generate_patient_visits
from src.models.schemas import Patient, Visit


class TestStartupTime:
    """Test suite for application startup performance."""

    def test_cold_start_empty_db(self, timer):
        """Cold start with empty database should be <2s."""
        benchmark = BENCHMARKS['database_init']

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            with timer("Cold start - empty DB") as t:
                db = DatabaseService(db_path)
                # Simulate basic app initialization
                db.get_all_patients()

            print(f"\n  {t}")
            print(f"\n{format_benchmark_result('database_init', t.elapsed_ms, benchmark)}")

            assert t.elapsed_ms <= benchmark['max_ms'], \
                f"Cold start too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

        finally:
            try:
                os.unlink(db_path)
            except:
                pass

    def test_startup_with_100_patients(self, temp_db, timer):
        """Startup with 100 patients should be <2s."""
        db = temp_db

        # Add 100 patients with visits
        print("\n  Populating database with 100 patients...")
        patients_data = generate_patients(100)

        for patient_data in patients_data:
            patient = Patient(**patient_data)
            patient = db.add_patient(patient)

            # Add 5 visits per patient
            visits = generate_patient_visits(patient.id, 5)
            for visit_data in visits:
                visit = Visit(**visit_data)
                db.add_visit(visit)

        # Simulate app restart by reconnecting
        db_path = db.db_path

        with timer("Startup with 100 patients") as t:
            # Reconnect to database
            new_db = DatabaseService(db_path)

            # Simulate initial data load
            patients = new_db.get_all_patients()

        print(f"\n  {t}")
        print(f"  Loaded {len(patients)} patients")

        # Should be very fast with 100 patients
        assert t.elapsed_ms <= 1000, \
            f"Startup with 100 patients too slow: {t.elapsed_ms:.2f}ms > 1000ms"

    def test_startup_with_1k_patients(self, temp_db, timer):
        """Startup with 1,000 patients should be <3s."""
        db = temp_db

        print("\n  Populating database with 1,000 patients...")
        patients_data = generate_patients(1000)

        for idx, patient_data in enumerate(patients_data):
            if idx % 200 == 0:
                print(f"    Progress: {idx}/1000...")

            patient = Patient(**patient_data)
            patient = db.add_patient(patient)

            # Add 5-10 visits
            visit_count = 5 if patient.age < 50 else 10
            visits = generate_patient_visits(patient.id, visit_count)
            for visit_data in visits:
                visit = Visit(**visit_data)
                db.add_visit(visit)

        db_path = db.db_path

        with timer("Startup with 1,000 patients") as t:
            # Reconnect to database
            new_db = DatabaseService(db_path)

            # Simulate initial data load
            patients = new_db.get_all_patients()

        print(f"\n  {t}")
        print(f"  Loaded {len(patients)} patients")

        assert t.elapsed_ms <= 3000, \
            f"Startup with 1K patients too slow: {t.elapsed_ms:.2f}ms > 3000ms"

    def test_startup_with_10k_patients(self, large_db, timer):
        """Startup with 10,000 patients should be <5s."""
        db = large_db
        benchmark = BENCHMARKS['app_startup']

        db_path = db.db_path

        with timer("Startup with 10,000 patients") as t:
            # Reconnect to database
            new_db = DatabaseService(db_path)

            # Simulate initial data load
            patients = new_db.get_all_patients()

        print(f"\n  {t}")
        print(f"  Loaded {len(patients)} patients")
        print(f"\n{format_benchmark_result('app_startup', t.elapsed_ms, benchmark)}")

        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"Startup with 10K patients too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_index_creation_time(self, timer):
        """Index creation should be fast even on large tables."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            # Create database and populate
            db = DatabaseService(db_path)

            print("\n  Adding 5,000 patients...")
            patients_data = generate_patients(5000)

            for idx, patient_data in enumerate(patients_data):
                if idx % 500 == 0:
                    print(f"    Progress: {idx}/5000...")

                patient = Patient(**patient_data)
                db.add_patient(patient)

            # Measure index query performance
            with timer("Query with indexes") as t:
                # Test name index
                db.search_patients_basic('Kumar')

                # Test patient_id index on visits
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM visits
                        WHERE patient_id = 1
                    """)
                    cursor.fetchone()

            print(f"\n  {t}")

            # Indexes should make queries very fast
            assert t.elapsed_ms <= 100, \
                f"Indexed queries too slow: {t.elapsed_ms:.2f}ms"

        finally:
            try:
                os.unlink(db_path)
            except:
                pass

    def test_incremental_load_performance(self, medium_db, timer):
        """Test loading patients incrementally vs all at once."""
        db = medium_db

        # Load all at once
        with timer("Load all patients at once") as t_all:
            all_patients = db.get_all_patients()

        print(f"\n  All at once: {t_all} - {len(all_patients)} patients")

        # Load in batches
        with timer("Load patients in batches") as t_batch:
            batch_size = 100
            batch_count = 0

            with db.get_connection() as conn:
                cursor = conn.cursor()
                offset = 0

                while True:
                    cursor.execute("""
                        SELECT * FROM patients
                        ORDER BY id
                        LIMIT ? OFFSET ?
                    """, (batch_size, offset))

                    batch = cursor.fetchall()
                    if not batch:
                        break

                    batch_count += len(batch)
                    offset += batch_size

        print(f"  In batches: {t_batch} - {batch_count} patients")

        # Batch loading might be slightly slower due to overhead
        # but should still be reasonable
        assert t_batch.elapsed_ms <= 2000, \
            f"Batch loading too slow: {t_batch.elapsed_ms:.2f}ms"

    def test_connection_pool_overhead(self, medium_db, timer):
        """Test connection creation overhead."""
        db = medium_db

        # Multiple connections
        with timer("Open 10 connections") as t:
            for _ in range(10):
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()

        print(f"\n  {t}")

        # Connection overhead should be minimal
        avg_ms = t.elapsed_ms / 10
        print(f"  Average per connection: {avg_ms:.2f}ms")

        assert avg_ms <= 10, \
            f"Connection overhead too high: {avg_ms:.2f}ms > 10ms"

    def test_vacuum_performance(self, medium_db, timer):
        """Test VACUUM operation on moderate database."""
        db = medium_db

        with timer("VACUUM operation") as t:
            with db.get_connection() as conn:
                conn.execute("VACUUM")

        print(f"\n  {t}")

        # VACUUM should complete reasonably fast on medium DB
        assert t.elapsed_ms <= 10000, \
            f"VACUUM too slow: {t.elapsed_ms:.2f}ms > 10s"

    def test_database_size_impact(self, large_db, timer):
        """Measure impact of database size on operations."""
        db = large_db

        # Get database file size
        db_size_mb = os.path.getsize(db.db_path) / 1024 / 1024
        print(f"\n  Database size: {db_size_mb:.2f}MB")

        # Test basic operations
        operations = {
            'Search': lambda: db.search_patients_basic('Kumar'),
            'Get patient': lambda: db.get_patient(1),
            'Get visits': lambda: db.get_patient_visits(1),
            'Count patients': lambda: len(db.get_all_patients())
        }

        results = {}
        for op_name, op_func in operations.items():
            with timer(op_name) as t:
                op_func()

            results[op_name] = t.elapsed_ms
            print(f"  {op_name}: {t.elapsed_ms:.2f}ms")

        # All operations should still be fast despite large DB
        for op_name, elapsed in results.items():
            assert elapsed <= 5000, \
                f"{op_name} too slow on large DB: {elapsed:.2f}ms"

    def test_concurrent_startup_simulation(self, medium_db, timer):
        """Simulate multiple users starting app simultaneously."""
        from concurrent.futures import ThreadPoolExecutor
        import threading

        db_path = medium_db.db_path
        results = []
        lock = threading.Lock()

        def simulate_user_startup():
            """Simulate single user starting app."""
            start = time.perf_counter()

            # Each user connects and loads data
            user_db = DatabaseService(db_path)
            patients = user_db.get_all_patients()[:10]  # Load first 10

            for patient in patients:
                user_db.get_patient_visits(patient.id)

            elapsed = (time.perf_counter() - start) * 1000

            with lock:
                results.append(elapsed)

        with timer("5 concurrent user startups") as t:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(simulate_user_startup) for _ in range(5)]

                for future in futures:
                    future.result()

        print(f"\n  {t}")
        print(f"  Individual startup times:")
        for idx, elapsed in enumerate(results):
            print(f"    User {idx + 1}: {elapsed:.2f}ms")

        avg_startup = sum(results) / len(results)
        print(f"  Average startup: {avg_startup:.2f}ms")

        # Concurrent startups should not significantly degrade performance
        assert avg_startup <= 2000, \
            f"Concurrent startup too slow: {avg_startup:.2f}ms"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
