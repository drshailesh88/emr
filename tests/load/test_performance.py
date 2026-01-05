"""
Performance and Load Tests

Tests system performance under load.
"""

import pytest
import sqlite3
import tempfile
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


@pytest.mark.load
class TestDatabasePerformance:
    """Test database performance"""

    @pytest.fixture
    def perf_db(self):
        """Create database for performance testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE patients (
                id INTEGER PRIMARY KEY,
                uhid TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                phone TEXT
            )
        ''')

        cursor.execute('''
            CREATE INDEX idx_patients_name ON patients(name)
        ''')

        cursor.execute('''
            CREATE INDEX idx_patients_uhid ON patients(uhid)
        ''')

        conn.commit()
        conn.close()

        yield db_path

        Path(db_path).unlink(missing_ok=True)

    def test_bulk_insert_performance(self, perf_db):
        """Test bulk insert performance"""
        conn = sqlite3.connect(perf_db)
        cursor = conn.cursor()

        # Insert 1000 patients
        start_time = time.time()

        patients = [
            (f"EMR-2024-{i:04d}", f"Patient {i}", 30 + (i % 50), "M" if i % 2 == 0 else "F", f"123456{i:04d}")
            for i in range(1000)
        ]

        cursor.executemany(
            "INSERT INTO patients (uhid, name, age, gender, phone) VALUES (?, ?, ?, ?, ?)",
            patients
        )
        conn.commit()

        duration = time.time() - start_time

        # Should insert 1000 records in < 1 second
        assert duration < 1.0, f"Bulk insert took {duration:.2f}s, expected < 1s"

        # Verify count
        cursor.execute("SELECT COUNT(*) FROM patients")
        count = cursor.fetchone()[0]
        assert count == 1000

        conn.close()

    def test_search_performance(self, perf_db):
        """Test search performance with large dataset"""
        conn = sqlite3.connect(perf_db)
        cursor = conn.cursor()

        # Insert 10,000 patients
        patients = [
            (f"EMR-2024-{i:05d}", f"Patient {i}", 30, "M", f"1234567890")
            for i in range(10000)
        ]

        cursor.executemany(
            "INSERT INTO patients (uhid, name, age, gender, phone) VALUES (?, ?, ?, ?, ?)",
            patients
        )
        conn.commit()

        # Test indexed search
        start_time = time.time()

        cursor.execute("SELECT * FROM patients WHERE uhid = ?", ("EMR-2024-05000",))
        result = cursor.fetchone()

        duration = time.time() - start_time

        # Indexed search should be very fast (< 0.05s)
        assert duration < 0.05, f"Indexed search took {duration:.3f}s, expected < 0.05s"
        assert result is not None

        # Test LIKE search (slower, but should still be reasonable)
        start_time = time.time()

        cursor.execute("SELECT * FROM patients WHERE name LIKE ?", ("%Patient 500%",))
        results = cursor.fetchall()

        duration = time.time() - start_time

        # LIKE search should complete in < 0.5s
        assert duration < 0.5, f"LIKE search took {duration:.3f}s, expected < 0.5s"
        assert len(results) > 0

        conn.close()

    def test_concurrent_access(self, perf_db):
        """Test concurrent database access"""
        def insert_patient(patient_id):
            conn = sqlite3.connect(perf_db)
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "INSERT INTO patients (uhid, name, age, gender) VALUES (?, ?, ?, ?)",
                    (f"EMR-{patient_id:05d}", f"Patient {patient_id}", 30, "M")
                )
                conn.commit()
                return True
            except Exception as e:
                return False
            finally:
                conn.close()

        # Test with 10 concurrent insertions
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(insert_patient, range(100)))

        duration = time.time() - start_time

        # Should complete in reasonable time
        assert duration < 5.0, f"Concurrent inserts took {duration:.2f}s, expected < 5s"

        # Verify all succeeded
        success_count = sum(results)
        assert success_count == 100, f"Only {success_count}/100 inserts succeeded"


@pytest.mark.load
class TestMemoryUsage:
    """Test memory usage under load"""

    def test_large_result_set_memory(self):
        """Test memory usage with large result sets"""
        # Create large dataset in memory
        large_data = [
            {
                "uhid": f"EMR-{i:06d}",
                "name": f"Patient {i}",
                "visits": [
                    {"date": f"2024-01-{j:02d}", "diagnosis": f"Diagnosis {j}"}
                    for j in range(1, 11)  # 10 visits per patient
                ]
            }
            for i in range(1000)  # 1000 patients
        ]

        # Should be able to handle this in memory
        assert len(large_data) == 1000
        assert all(len(p["visits"]) == 10 for p in large_data)

        # Filtering should work efficiently
        filtered = [p for p in large_data if "500" in p["uhid"]]
        assert len(filtered) > 0

    def test_string_operations_efficiency(self):
        """Test string operation efficiency"""
        # Generate large text (clinical notes)
        large_text = "Patient presents with " + " ".join([f"symptom{i}" for i in range(1000)])

        start_time = time.time()

        # Common operations
        lower = large_text.lower()
        words = large_text.split()
        search_result = "symptom500" in large_text

        duration = time.time() - start_time

        # Should be very fast
        assert duration < 0.1, f"String operations took {duration:.3f}s"
        assert search_result is True


@pytest.mark.load
@pytest.mark.slow
class TestStressTest:
    """Stress tests for system limits"""

    def test_maximum_patients(self):
        """Test system with maximum expected patient count"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE patients (
                    id INTEGER PRIMARY KEY,
                    uhid TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL
                )
            ''')

            cursor.execute('CREATE INDEX idx_uhid ON patients(uhid)')

            # Insert 100,000 patients (typical large clinic)
            batch_size = 1000
            for batch in range(100):
                patients = [
                    (f"EMR-{batch:03d}-{i:04d}", f"Patient {batch * 1000 + i}")
                    for i in range(batch_size)
                ]

                cursor.executemany(
                    "INSERT INTO patients (uhid, name) VALUES (?, ?)",
                    patients
                )

                if batch % 10 == 0:
                    conn.commit()

            conn.commit()

            # Verify count
            cursor.execute("SELECT COUNT(*) FROM patients")
            count = cursor.fetchone()[0]
            assert count == 100000

            # Test search performance still good
            start_time = time.time()
            cursor.execute("SELECT * FROM patients WHERE uhid = ?", ("EMR-050-5000",))
            result = cursor.fetchone()
            duration = time.time() - start_time

            assert duration < 0.1, f"Search in 100K records took {duration:.3f}s"
            assert result is not None

            conn.close()

        finally:
            Path(db_path).unlink(missing_ok=True)
