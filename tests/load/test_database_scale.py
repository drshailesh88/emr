"""Database scale load tests.

Comprehensive tests at different scale levels: 1K, 10K, and 50K patients.
Tests query performance, search times, and data integrity at scale.
"""

import pytest
import time
import os
import tempfile
from datetime import date, timedelta

from src.services.database import DatabaseService
from src.models.schemas import Patient, Visit
from tests.load.benchmarks import BENCHMARKS, format_benchmark_result
from tests.load.generators.patient_generator import generate_patients
from tests.load.generators.visit_generator import generate_patient_visits
from tests.load.generators.prescription_generator import generate_prescription_json


class TestDatabaseScale:
    """Test suite for database performance at different scales."""

    @pytest.fixture(scope='class')
    def db_1k_patients(self):
        """Create database with 1,000 patients."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db = DatabaseService(db_path)

        print("\n" + "="*60)
        print("Creating 1K patient database...")
        print("="*60)

        start_time = time.time()

        patients_data = generate_patients(1000)
        for idx, patient_data in enumerate(patients_data):
            if idx % 200 == 0:
                print(f"  Progress: {idx}/1000...")

            patient = Patient(**patient_data)
            patient = db.add_patient(patient)

            # 5-15 visits per patient
            visit_count = 5 if patient.age < 40 else 15
            visits = generate_patient_visits(patient.id, visit_count)

            for visit_data in visits:
                visit_data['prescription_json'] = generate_prescription_json(
                    visit_data['diagnosis']
                )
                visit = Visit(**visit_data)
                db.add_visit(visit)

        elapsed = time.time() - start_time
        print(f"Database created in {elapsed:.2f}s\n")

        yield db

        try:
            os.unlink(db_path)
        except:
            pass

    @pytest.fixture(scope='class')
    def db_50k_patients(self):
        """Create database with 50,000 patients.

        WARNING: This fixture creates a very large database (~2-5 GB)
        and may take 10-15 minutes to generate.
        """
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db = DatabaseService(db_path)

        print("\n" + "="*60)
        print("Creating 50K patient database (this may take 10-15 minutes)...")
        print("="*60)

        start_time = time.time()

        # Generate in batches
        batch_size = 5000
        total = 50000

        for batch_num in range(total // batch_size):
            batch_start = batch_num * batch_size
            print(f"\nBatch {batch_num + 1}/10: Patients {batch_start + 1}-{batch_start + batch_size}")

            patients_data = generate_patients(batch_size, start_id=batch_start + 1)

            for idx, patient_data in enumerate(patients_data):
                if idx % 500 == 0 and idx > 0:
                    print(f"  Batch progress: {idx}/5000...")

                patient = Patient(**patient_data)
                patient = db.add_patient(patient)

                # Varied visit counts
                if patient.age > 65:
                    visit_count = 20
                elif patient.age > 50:
                    visit_count = 15
                elif patient.age > 35:
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

        elapsed = time.time() - start_time
        print(f"\n50K database created in {elapsed:.2f}s ({elapsed/60:.2f} minutes)\n")

        yield db

        try:
            os.unlink(db_path)
        except:
            pass

    # ============== 1K PATIENT TESTS ==============

    def test_1k_patient_search(self, db_1k_patients, timer):
        """Patient search at 1K scale should be <200ms."""
        db = db_1k_patients

        search_terms = ['Kumar', 'Sharma', 'Priya', 'Singh', 'Patel']
        total_time = 0

        print("\n1K Patient Search Tests:")
        for term in search_terms:
            with timer(f"Search '{term}'") as t:
                results = db.search_patients_basic(term)

            print(f"  {term}: {t.elapsed_ms:.2f}ms - {len(results)} results")
            total_time += t.elapsed_ms

        avg_time = total_time / len(search_terms)
        print(f"\n  Average: {avg_time:.2f}ms")

        assert avg_time <= 200, \
            f"1K search too slow: {avg_time:.2f}ms > 200ms"

    def test_1k_visit_retrieval(self, db_1k_patients, timer):
        """Visit retrieval at 1K scale should be <100ms."""
        db = db_1k_patients

        # Get patients with most visits
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.name, COUNT(v.id) as visit_count
                FROM patients p
                LEFT JOIN visits v ON p.id = v.patient_id
                GROUP BY p.id
                ORDER BY visit_count DESC
                LIMIT 10
            """)
            patients = cursor.fetchall()

        total_time = 0
        print("\n1K Visit Retrieval Tests:")

        for row in patients[:5]:
            patient_id, name, visit_count = row[0], row[1], row[2]

            with timer(f"Load visits for {name}") as t:
                visits = db.get_patient_visits(patient_id)

            print(f"  {name}: {t.elapsed_ms:.2f}ms - {len(visits)} visits")
            total_time += t.elapsed_ms

        avg_time = total_time / 5
        print(f"\n  Average: {avg_time:.2f}ms")

        assert avg_time <= 100, \
            f"1K visit retrieval too slow: {avg_time:.2f}ms > 100ms"

    def test_1k_patient_list(self, db_1k_patients, timer):
        """List all patients at 1K scale should be <500ms."""
        db = db_1k_patients

        with timer("Get all patients (1K)") as t:
            patients = db.get_all_patients()

        print(f"\n  {t} - {len(patients)} patients")

        assert t.elapsed_ms <= 500, \
            f"1K patient list too slow: {t.elapsed_ms:.2f}ms > 500ms"

    # ============== 10K PATIENT TESTS ==============

    def test_10k_patient_search(self, large_db, timer):
        """Patient search at 10K scale should be <500ms."""
        db = large_db
        benchmark = BENCHMARKS['patient_search']

        search_terms = ['Kumar', 'Sharma', 'Priya', 'Singh', 'Patel', 'Gupta']
        total_time = 0

        print("\n10K Patient Search Tests:")
        for term in search_terms:
            with timer(f"Search '{term}'") as t:
                results = db.search_patients_basic(term)

            print(f"  {term}: {t.elapsed_ms:.2f}ms - {len(results)} results")
            total_time += t.elapsed_ms

        avg_time = total_time / len(search_terms)
        print(f"\n  Average: {avg_time:.2f}ms")
        print(f"\n{format_benchmark_result('patient_search', avg_time, benchmark)}")

        assert avg_time <= benchmark['max_ms'], \
            f"10K search too slow: {avg_time:.2f}ms > {benchmark['max_ms']}ms"

    def test_10k_visit_retrieval(self, large_db, timer):
        """Visit retrieval at 10K scale should be <200ms."""
        db = large_db

        # Get patients with most visits
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.name, COUNT(v.id) as visit_count
                FROM patients p
                LEFT JOIN visits v ON p.id = v.patient_id
                GROUP BY p.id
                ORDER BY visit_count DESC
                LIMIT 10
            """)
            patients = cursor.fetchall()

        total_time = 0
        print("\n10K Visit Retrieval Tests:")

        for row in patients[:5]:
            patient_id, name, visit_count = row[0], row[1], row[2]

            with timer(f"Load visits for {name}") as t:
                visits = db.get_patient_visits(patient_id)

            print(f"  {name}: {t.elapsed_ms:.2f}ms - {len(visits)} visits")
            total_time += t.elapsed_ms

        avg_time = total_time / 5
        print(f"\n  Average: {avg_time:.2f}ms")

        assert avg_time <= 200, \
            f"10K visit retrieval too slow: {avg_time:.2f}ms > 200ms"

    def test_10k_complex_queries(self, large_db, timer):
        """Complex analytical queries at 10K scale should be reasonable."""
        db = large_db

        queries = {
            'Patients with >10 visits': """
                SELECT p.id, p.name, COUNT(v.id) as visit_count
                FROM patients p
                LEFT JOIN visits v ON p.id = v.patient_id
                GROUP BY p.id
                HAVING visit_count > 10
                ORDER BY visit_count DESC
            """,
            'Recent visits (30 days)': """
                SELECT COUNT(*)
                FROM visits
                WHERE visit_date >= date('now', '-30 days')
            """,
            'Patient age distribution': """
                SELECT
                    CASE
                        WHEN age < 18 THEN 'Pediatric'
                        WHEN age < 40 THEN 'Young Adult'
                        WHEN age < 60 THEN 'Adult'
                        ELSE 'Senior'
                    END as age_group,
                    COUNT(*) as count
                FROM patients
                GROUP BY age_group
            """,
        }

        print("\n10K Complex Query Tests:")
        for query_name, query_sql in queries.items():
            with timer(query_name) as t:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query_sql)
                    results = cursor.fetchall()

            print(f"  {query_name}: {t.elapsed_ms:.2f}ms - {len(results)} results")

            # Complex queries should complete within 1 second
            assert t.elapsed_ms <= 1000, \
                f"Complex query too slow: {query_name} - {t.elapsed_ms:.2f}ms > 1000ms"

    # ============== 50K PATIENT TESTS ==============

    @pytest.mark.slow
    def test_50k_patient_search(self, db_50k_patients, timer):
        """Patient search at 50K scale should still be usable (<1s)."""
        db = db_50k_patients

        search_terms = ['Kumar', 'Sharma', 'Priya', 'Singh', 'Patel']
        total_time = 0

        print("\n50K Patient Search Tests:")
        for term in search_terms:
            with timer(f"Search '{term}'") as t:
                results = db.search_patients_basic(term)

            print(f"  {term}: {t.elapsed_ms:.2f}ms - {len(results)} results")
            total_time += t.elapsed_ms

        avg_time = total_time / len(search_terms)
        print(f"\n  Average: {avg_time:.2f}ms")

        # At 50K scale, we allow up to 1 second
        assert avg_time <= 1000, \
            f"50K search too slow: {avg_time:.2f}ms > 1000ms"

    @pytest.mark.slow
    def test_50k_visit_retrieval(self, db_50k_patients, timer):
        """Visit retrieval at 50K scale should be <500ms."""
        db = db_50k_patients

        # Get random patients
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name
                FROM patients
                ORDER BY RANDOM()
                LIMIT 10
            """)
            patients = cursor.fetchall()

        total_time = 0
        print("\n50K Visit Retrieval Tests:")

        for row in patients[:5]:
            patient_id, name = row[0], row[1]

            with timer(f"Load visits for {name}") as t:
                visits = db.get_patient_visits(patient_id)

            print(f"  {name}: {t.elapsed_ms:.2f}ms - {len(visits)} visits")
            total_time += t.elapsed_ms

        avg_time = total_time / 5
        print(f"\n  Average: {avg_time:.2f}ms")

        assert avg_time <= 500, \
            f"50K visit retrieval too slow: {avg_time:.2f}ms > 500ms"

    @pytest.mark.slow
    def test_50k_patient_list_pagination(self, db_50k_patients, timer):
        """Paginated patient list at 50K scale should be fast."""
        db = db_50k_patients

        page_size = 100
        total_time = 0

        print("\n50K Pagination Tests:")
        for page in range(5):  # Test first 5 pages
            offset = page * page_size

            with timer(f"Page {page + 1}") as t:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT * FROM patients
                        ORDER BY name
                        LIMIT ? OFFSET ?
                    """, (page_size, offset))
                    results = cursor.fetchall()

            print(f"  Page {page + 1}: {t.elapsed_ms:.2f}ms - {len(results)} results")
            total_time += t.elapsed_ms

        avg_time = total_time / 5
        print(f"\n  Average: {avg_time:.2f}ms")

        # Pagination should be fast even at 50K
        assert avg_time <= 300, \
            f"50K pagination too slow: {avg_time:.2f}ms > 300ms"

    @pytest.mark.slow
    def test_50k_database_statistics(self, db_50k_patients, timer):
        """Generate statistics at 50K scale."""
        db = db_50k_patients

        print("\n50K Database Statistics:")

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Patient count
            with timer("Count patients") as t:
                cursor.execute("SELECT COUNT(*) FROM patients")
                patient_count = cursor.fetchone()[0]
            print(f"  Patients: {patient_count:,} ({t.elapsed_ms:.2f}ms)")

            # Visit count
            with timer("Count visits") as t:
                cursor.execute("SELECT COUNT(*) FROM visits")
                visit_count = cursor.fetchone()[0]
            print(f"  Visits: {visit_count:,} ({t.elapsed_ms:.2f}ms)")

            # Average visits per patient
            with timer("Calculate averages") as t:
                cursor.execute("""
                    SELECT AVG(visit_count) as avg_visits
                    FROM (
                        SELECT COUNT(v.id) as visit_count
                        FROM patients p
                        LEFT JOIN visits v ON p.id = v.patient_id
                        GROUP BY p.id
                    )
                """)
                avg_visits = cursor.fetchone()[0]
            print(f"  Avg visits/patient: {avg_visits:.1f} ({t.elapsed_ms:.2f}ms)")

            # Database size
            db_size_mb = os.path.getsize(db.db_path) / 1024 / 1024
            print(f"  Database size: {db_size_mb:.2f} MB")

    # ============== SCALE COMPARISON ==============

    def test_scale_comparison(self, db_1k_patients, large_db, timer):
        """Compare performance across different scales."""
        print("\n" + "="*60)
        print("Scale Comparison Tests")
        print("="*60)

        test_cases = [
            ('1K patients', db_1k_patients),
            ('10K patients', large_db),
        ]

        results = {}

        for scale_name, db in test_cases:
            print(f"\n{scale_name}:")
            results[scale_name] = {}

            # Search test
            with timer("Search 'Kumar'") as t:
                db.search_patients_basic('Kumar')
            results[scale_name]['search'] = t.elapsed_ms
            print(f"  Search: {t.elapsed_ms:.2f}ms")

            # Get patient test
            with timer("Get patient") as t:
                db.get_patient(1)
            results[scale_name]['get_patient'] = t.elapsed_ms
            print(f"  Get patient: {t.elapsed_ms:.2f}ms")

            # Get visits test
            with timer("Get visits") as t:
                db.get_patient_visits(1)
            results[scale_name]['get_visits'] = t.elapsed_ms
            print(f"  Get visits: {t.elapsed_ms:.2f}ms")

        print("\n" + "="*60)
        print("Performance Degradation:")
        print("="*60)

        for operation in ['search', 'get_patient', 'get_visits']:
            time_1k = results['1K patients'][operation]
            time_10k = results['10K patients'][operation]
            degradation = (time_10k / time_1k - 1) * 100

            print(f"\n{operation.replace('_', ' ').title()}:")
            print(f"  1K: {time_1k:.2f}ms")
            print(f"  10K: {time_10k:.2f}ms")
            print(f"  Degradation: {degradation:+.1f}%")

            # Degradation should not be excessive
            # Allow up to 100% degradation (2x slower)
            assert degradation <= 100, \
                f"{operation} degraded too much at 10K: {degradation:.1f}% > 100%"

    def test_write_performance_at_scale(self, large_db, timer):
        """Test write performance on large database."""
        db = large_db

        # Add new patient
        from tests.load.generators.patient_generator import generate_patient

        patient_data = generate_patient()
        patient = Patient(**patient_data)

        with timer("Add patient to 10K DB") as t:
            saved_patient = db.add_patient(patient)

        print(f"\n  {t}")

        # Write should still be fast even on large DB
        assert t.elapsed_ms <= 200, \
            f"Write too slow on large DB: {t.elapsed_ms:.2f}ms > 200ms"

        # Add visit
        visits = generate_patient_visits(saved_patient.id, 1)
        visit_data = visits[0]
        visit_data['prescription_json'] = generate_prescription_json(
            visit_data['diagnosis']
        )
        visit = Visit(**visit_data)

        with timer("Add visit to 10K DB") as t:
            db.add_visit(visit)

        print(f"  {t}")

        assert t.elapsed_ms <= 200, \
            f"Visit write too slow on large DB: {t.elapsed_ms:.2f}ms > 200ms"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
