"""Memory usage load tests.

Tests memory consumption and leak detection.
"""

import pytest
import gc
import tracemalloc
from tests.load.benchmarks import MEMORY_BENCHMARKS
from tests.load.generators.visit_generator import generate_visit
from tests.load.generators.prescription_generator import generate_prescription_json
from src.models.schemas import Visit


class TestMemoryUsage:
    """Test suite for memory usage."""

    def test_memory_baseline(self, temp_db, memory_profiler):
        """App startup memory should be <200MB."""
        db = temp_db
        benchmark = MEMORY_BENCHMARKS['baseline']

        with memory_profiler("App baseline memory") as mem:
            # Simulate basic app initialization
            db.get_all_patients()

        peak_mb = mem.get_peak_mb()
        print(f"\n  {mem}")
        print(f"  Peak memory: {peak_mb:.2f}MB")

        # Note: This is Python memory tracking, actual app memory may differ
        assert peak_mb <= benchmark['max_mb'], \
            f"Baseline memory too high: {peak_mb:.2f}MB > {benchmark['max_mb']}MB"

    def test_memory_with_10k_patients(self, large_db, memory_profiler):
        """Memory after loading 10K patients should be <1GB."""
        db = large_db
        benchmark = MEMORY_BENCHMARKS['with_10k_patients']

        # Force garbage collection first
        gc.collect()

        with memory_profiler("Loading 10K patients") as mem:
            # Load all patients into memory
            patients = db.get_all_patients()

            # Access patient data
            for patient in patients[:100]:
                _ = patient.name
                _ = patient.age

        peak_mb = mem.get_peak_mb()
        print(f"\n  {mem}")
        print(f"  Peak memory: {peak_mb:.2f}MB")
        print(f"  Patients loaded: {len(patients)}")

        assert peak_mb <= benchmark['max_mb'], \
            f"Memory with 10K patients too high: {peak_mb:.2f}MB > {benchmark['max_mb']}MB"

    def test_memory_leak_detection(self, medium_db, memory_profiler):
        """1000 operations should not cause memory leak."""
        db = medium_db
        benchmark = MEMORY_BENCHMARKS['memory_leak_threshold']

        # Get a patient
        patients = db.get_all_patients()
        patient = patients[0]

        # Force GC
        gc.collect()

        # Measure initial memory
        tracemalloc.start()
        initial_memory = tracemalloc.get_traced_memory()[0]

        # Perform 1000 operations
        for i in range(1000):
            # Read operations
            db.get_patient(patient.id)
            db.get_patient_visits(patient.id)

            # Write operations every 10 iterations
            if i % 10 == 0:
                visit_data = generate_visit(patient.id)
                visit_data['prescription_json'] = generate_prescription_json(
                    visit_data['diagnosis']
                )
                visit = Visit(**visit_data)
                db.add_visit(visit)

            # Force GC every 100 iterations
            if i % 100 == 0:
                gc.collect()

        # Final GC
        gc.collect()

        # Measure final memory
        final_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()

        memory_growth_mb = (final_memory - initial_memory) / 1024 / 1024

        print(f"\n  Initial memory: {initial_memory / 1024 / 1024:.2f}MB")
        print(f"  Final memory: {final_memory / 1024 / 1024:.2f}MB")
        print(f"  Memory growth: {memory_growth_mb:.2f}MB")

        assert memory_growth_mb <= benchmark['max_mb'], \
            f"Memory leak detected: {memory_growth_mb:.2f}MB > {benchmark['max_mb']}MB"

    def test_large_patient_timeline(self, heavy_patient_db, memory_profiler):
        """Load patient with 500 visits - memory should be <500MB."""
        db = heavy_patient_db
        benchmark = MEMORY_BENCHMARKS['large_patient_timeline']

        # Get heavy patient
        patients = db.get_all_patients()
        patient = patients[0]

        gc.collect()

        with memory_profiler("Large patient timeline") as mem:
            # Load all patient data
            visits = db.get_patient_visits(patient.id)
            investigations = db.get_patient_investigations(patient.id)
            procedures = db.get_patient_procedures(patient.id)
            summary = db.get_patient_summary(patient.id)

            # Process the data
            total_records = len(visits) + len(investigations) + len(procedures)

        peak_mb = mem.get_peak_mb()
        print(f"\n  {mem}")
        print(f"  Peak memory: {peak_mb:.2f}MB")
        print(f"  Total records loaded: {total_records}")

        assert peak_mb <= benchmark['max_mb'], \
            f"Large timeline memory too high: {peak_mb:.2f}MB > {benchmark['max_mb']}MB"

    def test_repeated_query_memory(self, medium_db, memory_profiler):
        """Repeated queries should not accumulate memory."""
        db = medium_db

        gc.collect()
        tracemalloc.start()
        initial_memory = tracemalloc.get_traced_memory()[0]

        # Perform same query 100 times
        for _ in range(100):
            db.search_patients_basic('Sharma')
            gc.collect()

        final_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()

        memory_growth_mb = (final_memory - initial_memory) / 1024 / 1024

        print(f"\n  Memory growth after 100 queries: {memory_growth_mb:.2f}MB")

        # Should have minimal growth
        assert memory_growth_mb <= 10, \
            f"Repeated query memory leak: {memory_growth_mb:.2f}MB > 10MB"

    def test_bulk_operation_memory(self, temp_db, memory_profiler):
        """Bulk operations should manage memory efficiently."""
        db = temp_db

        from tests.load.generators.patient_generator import generate_patients

        gc.collect()

        with memory_profiler("Bulk patient import") as mem:
            # Generate and import 1000 patients
            patients_data = generate_patients(1000)

            for patient_data in patients_data:
                from src.models.schemas import Patient
                patient = Patient(**patient_data)
                db.add_patient(patient)

                # Clear references periodically
                if len(patients_data) % 100 == 0:
                    gc.collect()

        peak_mb = mem.get_peak_mb()
        print(f"\n  {mem}")
        print(f"  Peak memory: {peak_mb:.2f}MB")
        print(f"  Imported: 1000 patients")

        # Bulk import should be memory efficient
        assert peak_mb <= 100, \
            f"Bulk import memory too high: {peak_mb:.2f}MB > 100MB"

    def test_connection_pool_memory(self, medium_db, memory_profiler):
        """Multiple connections should not leak memory."""
        db = medium_db

        gc.collect()
        tracemalloc.start()
        initial_memory = tracemalloc.get_traced_memory()[0]

        # Open and close connections repeatedly
        for _ in range(100):
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM patients")
                cursor.fetchone()

            gc.collect()

        final_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()

        memory_growth_mb = (final_memory - initial_memory) / 1024 / 1024

        print(f"\n  Memory growth after 100 connections: {memory_growth_mb:.2f}MB")

        assert memory_growth_mb <= 5, \
            f"Connection memory leak: {memory_growth_mb:.2f}MB > 5MB"

    def test_patient_list_pagination_memory(self, large_db, memory_profiler):
        """Loading patients in pages should use less memory than loading all."""
        db = large_db

        gc.collect()

        # Load all at once
        with memory_profiler("Load all patients") as mem_all:
            all_patients = db.get_all_patients()

        peak_all = mem_all.get_peak_mb()

        gc.collect()

        # Load in pages (simulated)
        with memory_profiler("Load patients in pages") as mem_paged:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Process in batches of 100
                offset = 0
                batch_size = 100
                total_processed = 0

                while True:
                    cursor.execute("""
                        SELECT * FROM patients
                        ORDER BY id
                        LIMIT ? OFFSET ?
                    """, (batch_size, offset))

                    batch = cursor.fetchall()
                    if not batch:
                        break

                    # Process batch
                    for row in batch:
                        _ = dict(row)

                    total_processed += len(batch)
                    offset += batch_size

        peak_paged = mem_paged.get_peak_mb()

        print(f"\n  All at once: {peak_all:.2f}MB")
        print(f"  Paged: {peak_paged:.2f}MB")
        print(f"  Memory savings: {peak_all - peak_paged:.2f}MB")

        # Paged should use less or similar memory
        # (May not always be less due to overhead, but should not be significantly more)
        assert peak_paged <= peak_all * 1.5, \
            "Paged loading should not use significantly more memory"

    def test_json_parsing_memory(self, medium_db, memory_profiler):
        """JSON parsing should not consume excessive memory."""
        db = medium_db

        import json

        # Get visits with prescriptions
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT prescription_json
                FROM visits
                WHERE prescription_json IS NOT NULL
                LIMIT 1000
            """)
            prescriptions = [row[0] for row in cursor.fetchall()]

        gc.collect()

        with memory_profiler("Parse 1000 prescription JSONs") as mem:
            parsed = []
            for rx_json in prescriptions:
                try:
                    rx = json.loads(rx_json)
                    parsed.append(rx)
                except:
                    pass

        peak_mb = mem.get_peak_mb()
        print(f"\n  {mem}")
        print(f"  Peak memory: {peak_mb:.2f}MB")
        print(f"  Parsed: {len(parsed)} prescriptions")

        # JSON parsing should be efficient
        assert peak_mb <= 50, \
            f"JSON parsing memory too high: {peak_mb:.2f}MB > 50MB"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
