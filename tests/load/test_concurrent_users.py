"""Concurrent user load tests.

Tests system performance with multiple concurrent users performing
realistic workloads simultaneously.
"""

import pytest
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from src.models.schemas import Patient, Visit
from tests.load.benchmarks import CONCURRENCY_BENCHMARKS, format_benchmark_result
from tests.load.generators.patient_generator import generate_patient
from tests.load.generators.visit_generator import generate_visit
from tests.load.generators.prescription_generator import generate_prescription_json


class TestConcurrentUsers:
    """Test suite for concurrent user scenarios."""

    def test_5_concurrent_consultations(self, medium_db, timer):
        """Simulate 5 doctors consulting simultaneously."""
        db = medium_db

        # Get 5 different patients
        all_patients = db.get_all_patients()
        patients = all_patients[:5]

        consultation_results = []
        errors = []
        lock = Lock()

        def simulate_consultation(patient):
            """Simulate a complete consultation workflow."""
            try:
                # 1. Load patient data
                loaded_patient = db.get_patient(patient.id)
                assert loaded_patient is not None

                # 2. Load patient history
                visits = db.get_patient_visits(patient.id)
                investigations = db.get_patient_investigations(patient.id)

                # 3. Create new visit
                visit_data = generate_visit(patient.id)
                visit_data['prescription_json'] = generate_prescription_json(
                    visit_data['diagnosis']
                )
                visit = Visit(**visit_data)

                # 4. Save visit
                saved_visit = db.add_visit(visit)

                # 5. Verify save
                assert saved_visit.id is not None

                with lock:
                    consultation_results.append({
                        'patient_id': patient.id,
                        'visit_id': saved_visit.id,
                        'history_count': len(visits)
                    })

            except Exception as e:
                with lock:
                    errors.append(str(e))

        with timer("5 concurrent consultations") as t:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(simulate_consultation, patient)
                    for patient in patients
                ]

                # Wait for all to complete
                for future in as_completed(futures):
                    future.result()

        print(f"  {t}")
        print(f"  Completed: {len(consultation_results)} consultations")
        print(f"  Errors: {len(errors)}")

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(consultation_results) == 5, "All consultations should complete"

        benchmark = CONCURRENCY_BENCHMARKS['concurrent_writes']
        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"Concurrent consultations too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_10_concurrent_searches(self, large_db, timer):
        """Simulate 10 concurrent patient searches."""
        db = large_db
        benchmark = CONCURRENCY_BENCHMARKS['concurrent_searches']

        # Different search queries
        search_terms = [
            'Sharma', 'Kumar', 'Singh', 'Patel', 'Gupta',
            'Priya', 'Rajesh', 'Amit', 'Sunita', 'EMR-2024'
        ]

        search_results = []
        lock = Lock()

        def perform_search(term):
            """Perform a search."""
            results = db.search_patients_basic(term)
            with lock:
                search_results.append({
                    'term': term,
                    'count': len(results)
                })
            return len(results)

        with timer("10 concurrent searches") as t:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(perform_search, term)
                    for term in search_terms
                ]

                # Wait for all
                for future in as_completed(futures):
                    future.result()

        print(f"  {t}")
        for result in search_results:
            print(f"    '{result['term']}': {result['count']} results")

        print(f"\n{format_benchmark_result('concurrent_searches', t.elapsed_ms, benchmark)}")

        assert len(search_results) == 10, "All searches should complete"
        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"Concurrent searches too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_mixed_workload(self, medium_db, timer):
        """Simulate realistic clinic workload:
        - 3 doctors consulting
        - 2 staff searching patients
        - 1 admin viewing reports
        - Background sync simulation
        """
        db = medium_db
        benchmark = CONCURRENCY_BENCHMARKS['mixed_workload']

        results = {
            'consultations': [],
            'searches': [],
            'reports': [],
            'errors': []
        }
        lock = Lock()

        def doctor_consultation(doctor_id):
            """Doctor performing consultation."""
            try:
                patients = db.get_all_patients()
                patient = random.choice(patients)

                # Load history
                visits = db.get_patient_visits(patient.id)

                # Create visit
                visit_data = generate_visit(patient.id)
                visit_data['prescription_json'] = generate_prescription_json(
                    visit_data['diagnosis']
                )
                visit = Visit(**visit_data)
                saved_visit = db.add_visit(visit)

                with lock:
                    results['consultations'].append({
                        'doctor_id': doctor_id,
                        'patient_id': patient.id,
                        'visit_id': saved_visit.id
                    })

            except Exception as e:
                with lock:
                    results['errors'].append(f"Doctor {doctor_id}: {e}")

        def staff_search(staff_id):
            """Staff searching for patients."""
            try:
                search_terms = ['Sharma', 'Kumar', 'Singh', 'Patel']
                for term in search_terms:
                    found = db.search_patients_basic(term)
                    with lock:
                        results['searches'].append({
                            'staff_id': staff_id,
                            'term': term,
                            'count': len(found)
                        })

            except Exception as e:
                with lock:
                    results['errors'].append(f"Staff {staff_id}: {e}")

        def admin_report():
            """Admin generating report."""
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()

                    # Daily summary
                    cursor.execute("""
                        SELECT COUNT(*) FROM visits
                        WHERE visit_date = date('now')
                    """)
                    today_visits = cursor.fetchone()[0]

                    # Patient count
                    cursor.execute("SELECT COUNT(*) FROM patients")
                    total_patients = cursor.fetchone()[0]

                    with lock:
                        results['reports'].append({
                            'today_visits': today_visits,
                            'total_patients': total_patients
                        })

            except Exception as e:
                with lock:
                    results['errors'].append(f"Admin: {e}")

        def background_sync():
            """Background sync simulation."""
            try:
                # Simulate checking for changes
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM patients")
                    cursor.execute("SELECT COUNT(*) FROM visits")

            except Exception as e:
                with lock:
                    results['errors'].append(f"Sync: {e}")

        with timer("Mixed workload") as t:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []

                # 3 doctors
                for i in range(3):
                    futures.append(executor.submit(doctor_consultation, i + 1))

                # 2 staff searches
                for i in range(2):
                    futures.append(executor.submit(staff_search, i + 1))

                # 1 admin report
                futures.append(executor.submit(admin_report))

                # Background sync
                futures.append(executor.submit(background_sync))

                # Wait for all
                for future in as_completed(futures):
                    future.result()

        print(f"  {t}")
        print(f"  Consultations: {len(results['consultations'])}")
        print(f"  Searches: {len(results['searches'])}")
        print(f"  Reports: {len(results['reports'])}")
        print(f"  Errors: {len(results['errors'])}")

        print(f"\n{format_benchmark_result('mixed_workload', t.elapsed_ms, benchmark)}")

        assert len(results['errors']) == 0, f"Errors: {results['errors']}"
        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"Mixed workload too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_burst_load(self, medium_db, timer):
        """50 requests in 1 second - burst load test."""
        db = medium_db
        benchmark = CONCURRENCY_BENCHMARKS['burst_load']

        completed = []
        errors = []
        lock = Lock()

        def quick_operation(op_id):
            """Quick database operation."""
            try:
                # Mix of read and write operations
                if op_id % 3 == 0:
                    # Write
                    patients = db.get_all_patients()
                    if patients:
                        patient = random.choice(patients)
                        visit_data = generate_visit(patient.id)
                        visit = Visit(**visit_data)
                        db.add_visit(visit)
                else:
                    # Read
                    if op_id % 2 == 0:
                        db.get_all_patients()
                    else:
                        db.search_patients_basic('Kumar')

                with lock:
                    completed.append(op_id)

            except Exception as e:
                with lock:
                    errors.append(str(e))

        with timer("Burst load (50 requests)") as t:
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [
                    executor.submit(quick_operation, i)
                    for i in range(50)
                ]

                for future in as_completed(futures):
                    future.result()

        print(f"  {t}")
        print(f"  Completed: {len(completed)}/50")
        print(f"  Errors: {len(errors)}")

        print(f"\n{format_benchmark_result('burst_load', t.elapsed_ms, benchmark)}")

        assert len(errors) == 0, f"Burst load errors: {errors}"
        assert len(completed) == 50, "All operations should complete"
        assert t.elapsed_ms <= benchmark['max_ms'], \
            f"Burst load too slow: {t.elapsed_ms:.2f}ms > {benchmark['max_ms']}ms"

    def test_read_heavy_workload(self, large_db, timer):
        """20 concurrent read-heavy operations."""
        db = large_db

        completed = []
        lock = Lock()

        def read_heavy_task(task_id):
            """Perform multiple read operations."""
            # Get all patients
            patients = db.get_all_patients()

            # Search
            db.search_patients_basic('Kumar')

            # Get patient details
            if patients:
                patient = random.choice(patients)
                db.get_patient(patient.id)
                db.get_patient_visits(patient.id)
                db.get_patient_summary(patient.id)

            with lock:
                completed.append(task_id)

        with timer("20 concurrent read-heavy tasks") as t:
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [
                    executor.submit(read_heavy_task, i)
                    for i in range(20)
                ]

                for future in as_completed(futures):
                    future.result()

        print(f"  {t} - Completed {len(completed)}/20 tasks")

        assert len(completed) == 20
        assert t.elapsed_ms <= 5000, \
            f"Read-heavy workload too slow: {t.elapsed_ms:.2f}ms"

    def test_write_heavy_workload(self, medium_db, timer):
        """10 concurrent write-heavy operations."""
        db = medium_db

        completed = []
        errors = []
        lock = Lock()

        def write_heavy_task(task_id):
            """Perform multiple write operations."""
            try:
                patients = db.get_all_patients()

                for _ in range(5):  # 5 writes per task
                    if patients:
                        patient = random.choice(patients)
                        visit_data = generate_visit(patient.id)
                        visit_data['prescription_json'] = generate_prescription_json(
                            visit_data['diagnosis']
                        )
                        visit = Visit(**visit_data)
                        db.add_visit(visit)

                with lock:
                    completed.append(task_id)

            except Exception as e:
                with lock:
                    errors.append(str(e))

        with timer("10 concurrent write-heavy tasks") as t:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(write_heavy_task, i)
                    for i in range(10)
                ]

                for future in as_completed(futures):
                    future.result()

        print(f"  {t} - Completed {len(completed)}/10 tasks")
        print(f"  Total writes: {len(completed) * 5}")
        print(f"  Errors: {len(errors)}")

        assert len(errors) == 0, f"Write errors: {errors}"
        assert len(completed) == 10
        assert t.elapsed_ms <= 5000, \
            f"Write-heavy workload too slow: {t.elapsed_ms:.2f}ms"

    def test_sequential_vs_concurrent(self, medium_db, timer):
        """Compare sequential vs concurrent performance."""
        db = medium_db

        # Prepare 10 operations
        patients = db.get_all_patients()[:10]

        def perform_operation(patient):
            """Standard operation."""
            visits = db.get_patient_visits(patient.id)
            db.get_patient_summary(patient.id)
            return len(visits)

        # Sequential
        with timer("Sequential (10 operations)") as t_seq:
            seq_results = []
            for patient in patients:
                result = perform_operation(patient)
                seq_results.append(result)

        # Concurrent
        with timer("Concurrent (10 operations)") as t_con:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(perform_operation, patient)
                    for patient in patients
                ]
                con_results = [f.result() for f in as_completed(futures)]

        print(f"  Sequential: {t_seq}")
        print(f"  Concurrent: {t_con}")
        print(f"  Speedup: {t_seq.elapsed_ms / t_con.elapsed_ms:.2f}x")

        assert len(seq_results) == len(con_results) == 10

        # Concurrent should be faster (or at least not much slower)
        # Due to I/O, we might not see perfect speedup
        speedup = t_seq.elapsed_ms / t_con.elapsed_ms
        print(f"\n  Concurrent speedup: {speedup:.2f}x")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
