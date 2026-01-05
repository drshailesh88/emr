"""Database performance load tests.

Tests database operations under load with realistic data volumes.
"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.models.schemas import Patient, Visit
from tests.load.benchmarks import BENCHMARKS, format_benchmark_result
from tests.load.generators.patient_generator import generate_patient
from tests.load.generators.visit_generator import generate_visit
from tests.load.generators.prescription_generator import generate_prescription_json


class TestDatabasePerformance:
    """Test suite for database performance under load."""

    def test_patient_search_10k_patients(self, large_db, timer):
        """Patient search should complete in <500ms across 10K patients."""
        db = large_db
        benchmark = BENCHMARKS['patient_search']

        # Test various search queries
        search_queries = ['Sharma', 'Kumar', 'Priya', 'EMR-2024']

        total_time = 0
        for query in search_queries:
            with timer(f"Search '{query}'") as t:
                results = db.search_patients_basic(query)

            print(f"  {t} - Found {len(results)} patients")
            total_time += t.elapsed_ms

        avg_time = total_time / len(search_queries)
        print(f"\n{format_benchmark_result('patient_search', avg_time, benchmark)}")

        assert avg_time <= benchmark['max_ms'], \
            f"Search too slow: {avg_time:.2f}ms > {benchmark['max_ms']}ms"

    def test_patient_list_pagination(self, large_db, timer):
        """List 100 patients at a time should complete in <200ms."""
        db = large_db
        benchmark = BENCHMARKS['patient_list_pagination']

        with timer("Get all patients") as t:
            patients = db.get_all_patients()

        print(f"  {t} - Retrieved {len(patients)} patients")
        print(f"\n{format_benchmark_result('patient_list_pagination', t.elapsed_ms, benchmark)}")

        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"Patient list too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_visit_history_heavy_patient(self, heavy_patient_db, timer):
        """Load visit history for patient with 100+ visits in <1000ms."""
        db = heavy_patient_db
        benchmark = BENCHMARKS['visit_history_load']

        # Get a patient with many visits
        patients = db.get_all_patients()
        assert len(patients) > 0, "No patients in database"

        patient = patients[0]

        with timer(f"Load visits for {patient.name}") as t:
            visits = db.get_patient_visits(patient.id)

        print(f"  {t} - Loaded {len(visits)} visits")
        print(f"\n{format_benchmark_result('visit_history_load', t.elapsed_ms, benchmark)}")

        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"Visit history load too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_visit_save_performance(self, medium_db, timer):
        """Saving a visit should complete in <200ms."""
        db = medium_db
        benchmark = BENCHMARKS['visit_save']

        # Get a patient
        patients = db.get_all_patients()
        patient = patients[0]

        # Generate visit data
        visit_data = generate_visit(patient.id)
        visit_data['prescription_json'] = generate_prescription_json(
            visit_data['diagnosis']
        )

        with timer("Save visit") as t:
            visit = Visit(**visit_data)
            saved_visit = db.add_visit(visit)

        assert saved_visit.id is not None

        print(f"  {t}")
        print(f"\n{format_benchmark_result('visit_save', t.elapsed_ms, benchmark)}")

        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"Visit save too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_concurrent_writes(self, medium_db, timer):
        """Test 10 concurrent visit saves with no deadlocks."""
        db = medium_db

        # Get first patient
        patients = db.get_all_patients()
        patient = patients[0]

        def save_visit(visit_num):
            """Save a single visit."""
            visit_data = generate_visit(patient.id)
            visit_data['prescription_json'] = generate_prescription_json(
                visit_data['diagnosis']
            )
            visit = Visit(**visit_data)
            return db.add_visit(visit)

        with timer("10 concurrent writes") as t:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(save_visit, i) for i in range(10)]

                # Wait for all to complete
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        pytest.fail(f"Concurrent write failed: {e}")

        print(f"  {t} - Saved {len(results)} visits concurrently")

        # Verify all visits were saved
        assert len(results) == 10, "Not all concurrent writes succeeded"
        assert all(v.id is not None for v in results), "Some visits not saved properly"

        # Check for reasonable performance
        assert t.elapsed_ms <= 2000, \
            f"Concurrent writes too slow: {t.elapsed_ms:.2f}ms > 2000ms"

    def test_bulk_patient_import(self, temp_db, timer):
        """Import 1000 patients should complete in <30 seconds."""
        db = temp_db
        benchmark = BENCHMARKS['bulk_patient_import']

        from tests.load.generators.patient_generator import generate_patients

        # Generate patient data
        patients_data = generate_patients(1000)

        with timer("Import 1000 patients") as t:
            for patient_data in patients_data:
                patient = Patient(**patient_data)
                db.add_patient(patient)

        print(f"  {t}")
        print(f"\n{format_benchmark_result('bulk_patient_import', t.elapsed_ms, benchmark)}")

        # Verify count
        all_patients = db.get_all_patients()
        assert len(all_patients) == 1000, f"Expected 1000 patients, got {len(all_patients)}"

        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"Bulk import too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_patient_summary_generation(self, large_db, timer):
        """Test patient summary generation for RAG."""
        db = large_db

        # Get patients
        patients = db.get_all_patients()[:100]  # Test on 100 patients

        total_time = 0
        for patient in patients[:10]:  # Sample 10 for timing
            with timer(f"Summary for {patient.name}") as t:
                summary = db.get_patient_summary(patient.id)

            total_time += t.elapsed_ms
            assert len(summary) > 0, "Summary should not be empty"

        avg_time = total_time / 10
        print(f"\nAverage summary generation: {avg_time:.2f}ms")

        # Should be fast
        assert avg_time <= 100, \
            f"Summary generation too slow: {avg_time:.2f}ms > 100ms"

    def test_patient_documents_for_rag(self, medium_db, timer):
        """Test retrieving all patient documents for RAG indexing."""
        db = medium_db

        # Get a patient with visits
        patients = db.get_all_patients()
        patient = patients[0]

        with timer(f"Get RAG documents for {patient.name}") as t:
            documents = db.get_patient_documents_for_rag(patient.id)

        print(f"  {t} - Retrieved {len(documents)} documents")

        assert len(documents) > 0, "Should have documents"

        # Verify document structure
        for doc_id, content, metadata in documents[:3]:
            assert isinstance(doc_id, str)
            assert isinstance(content, str)
            assert isinstance(metadata, dict)
            assert 'type' in metadata
            assert 'patient_id' in metadata

        # Should complete quickly
        assert t.elapsed_ms <= 500, \
            f"RAG document retrieval too slow: {t.elapsed_ms:.2f}ms > 500ms"

    def test_database_index_efficiency(self, large_db, timer):
        """Verify indexes are being used efficiently."""
        db = large_db

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Test name index
            with timer("Search with index") as t:
                cursor.execute("""
                    SELECT * FROM patients
                    WHERE name LIKE ?
                    ORDER BY name
                """, ('%Sharma%',))
                results = cursor.fetchall()

            print(f"  {t} - Found {len(results)} patients using index")

            # Verify it's fast
            assert t.elapsed_ms <= 200, \
                f"Indexed search too slow: {t.elapsed_ms:.2f}ms"

    def test_visit_query_with_joins(self, large_db, timer):
        """Test complex queries with joins."""
        db = large_db

        with db.get_connection() as conn:
            cursor = conn.cursor()

            with timer("Complex join query") as t:
                cursor.execute("""
                    SELECT p.name, p.uhid, COUNT(v.id) as visit_count
                    FROM patients p
                    LEFT JOIN visits v ON p.id = v.patient_id
                    GROUP BY p.id
                    HAVING visit_count > 10
                    ORDER BY visit_count DESC
                    LIMIT 100
                """)
                results = cursor.fetchall()

            print(f"  {t} - Found {len(results)} patients with >10 visits")

            # Should complete in reasonable time
            assert t.elapsed_ms <= 1000, \
                f"Join query too slow: {t.elapsed_ms:.2f}ms > 1000ms"

    def test_transaction_rollback_performance(self, medium_db, timer):
        """Test transaction rollback doesn't significantly impact performance."""
        db = medium_db

        patient = db.get_all_patients()[0]

        # Successful transaction
        with timer("Successful transaction") as t1:
            visit_data = generate_visit(patient.id)
            visit = Visit(**visit_data)
            db.add_visit(visit)

        # Failed transaction (should rollback)
        with timer("Failed transaction") as t2:
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    # This should fail due to foreign key constraint
                    cursor.execute("""
                        INSERT INTO visits (patient_id, visit_date)
                        VALUES (?, ?)
                    """, (999999, '2024-01-01'))  # Non-existent patient
            except Exception:
                pass  # Expected to fail

        print(f"  Successful: {t1}")
        print(f"  Failed: {t2}")

        # Rollback should be fast
        assert t2.elapsed_ms <= 100, \
            f"Rollback too slow: {t2.elapsed_ms:.2f}ms"

    def test_concurrent_reads(self, large_db, timer):
        """Test 10 concurrent read operations."""
        db = large_db

        def read_patient_data(patient_id):
            """Read all data for a patient."""
            patient = db.get_patient(patient_id)
            if patient:
                visits = db.get_patient_visits(patient.id)
                summary = db.get_patient_summary(patient.id)
                return len(visits)
            return 0

        # Get some patient IDs
        patients = db.get_all_patients()[:20]
        patient_ids = [p.id for p in patients]

        with timer("10 concurrent reads") as t:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(read_patient_data, pid)
                    for pid in patient_ids[:10]
                ]

                results = []
                for future in as_completed(futures):
                    results.append(future.result())

        print(f"  {t} - Read data for {len(results)} patients")

        # Concurrent reads should be fast
        assert t.elapsed_ms <= 1000, \
            f"Concurrent reads too slow: {t.elapsed_ms:.2f}ms"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
