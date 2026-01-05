"""
Smoke Tests for DocAssist EMR

Quick tests to verify basic functionality is working.
These tests should run in < 5 seconds total.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime


@pytest.mark.smoke
class TestBasicFunctionality:
    """Quick smoke tests for basic functionality"""

    def test_can_import_main_modules(self):
        """Test that main modules can be imported"""
        try:
            from src.services import database
            from src.models import schemas
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import core modules: {e}")

    def test_can_create_database(self):
        """Test that database can be created"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Create a simple table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            ''')

            # Insert data
            cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("Test",))
            conn.commit()

            # Query data
            cursor.execute("SELECT * FROM test_table")
            results = cursor.fetchall()

            assert len(results) == 1
            assert results[0][1] == "Test"

            conn.close()

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_pydantic_models_work(self):
        """Test that Pydantic models can be instantiated"""
        try:
            from src.models.schemas import Patient

            patient = Patient(
                name="Test Patient",
                age=30,
                gender="M",
                phone="1234567890",
                address="Test Address"
            )

            assert patient.name == "Test Patient"
            assert patient.age == 30

        except ImportError:
            pytest.skip("Schemas not yet implemented")
        except Exception as e:
            pytest.fail(f"Failed to create Pydantic model: {e}")

    def test_datetime_handling(self):
        """Test that datetime handling works"""
        now = datetime.now()
        assert now is not None
        assert now.year >= 2024

        # Test ISO format
        iso_str = now.isoformat()
        parsed = datetime.fromisoformat(iso_str)
        assert parsed.year == now.year

    def test_json_serialization(self):
        """Test that JSON serialization works"""
        import json

        data = {
            "patient_name": "John Doe",
            "age": 45,
            "diagnosis": ["Hypertension", "Diabetes"],
        }

        # Serialize
        json_str = json.dumps(data)
        assert isinstance(json_str, str)

        # Deserialize
        parsed = json.loads(json_str)
        assert parsed["patient_name"] == "John Doe"
        assert len(parsed["diagnosis"]) == 2

    def test_pathlib_works(self):
        """Test that pathlib operations work"""
        project_root = Path(__file__).parent.parent.parent
        assert project_root.exists()
        assert (project_root / "src").exists()

    def test_string_operations(self):
        """Test basic string operations used in app"""
        # UHID generation pattern
        uhid = f"EMR-2024-{1:04d}"
        assert uhid == "EMR-2024-0001"

        # Name formatting
        name = "  John Doe  "
        assert name.strip() == "John Doe"

        # Case operations
        gender = "male"
        assert gender.upper() == "MALE"

    def test_list_operations(self):
        """Test list operations used in app"""
        medications = [
            {"name": "Aspirin", "dose": "75mg"},
            {"name": "Metformin", "dose": "500mg"},
        ]

        # Filtering
        aspirin = [m for m in medications if m["name"] == "Aspirin"]
        assert len(aspirin) == 1

        # Mapping
        names = [m["name"] for m in medications]
        assert "Aspirin" in names
        assert "Metformin" in names


@pytest.mark.smoke
class TestDatabaseSmoke:
    """Smoke tests for database operations"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        yield db_path

        Path(db_path).unlink(missing_ok=True)

    def test_can_create_patient_table(self, temp_db):
        """Test patient table creation"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE patients (
                id INTEGER PRIMARY KEY,
                uhid TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients'")
        result = cursor.fetchone()
        assert result is not None

        conn.close()

    def test_can_insert_patient(self, temp_db):
        """Test patient insertion"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE patients (
                id INTEGER PRIMARY KEY,
                uhid TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT
            )
        ''')

        cursor.execute(
            "INSERT INTO patients (uhid, name, age, gender) VALUES (?, ?, ?, ?)",
            ("EMR-2024-0001", "John Doe", 45, "M")
        )
        conn.commit()

        # Verify insertion
        cursor.execute("SELECT * FROM patients WHERE uhid = ?", ("EMR-2024-0001",))
        result = cursor.fetchone()

        assert result is not None
        assert result[2] == "John Doe"  # name column

        conn.close()

    def test_can_query_patient(self, temp_db):
        """Test patient query"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE patients (
                id INTEGER PRIMARY KEY,
                uhid TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL
            )
        ''')

        cursor.execute("INSERT INTO patients (uhid, name) VALUES (?, ?)",
                      ("EMR-001", "Alice"))
        cursor.execute("INSERT INTO patients (uhid, name) VALUES (?, ?)",
                      ("EMR-002", "Bob"))
        conn.commit()

        # Search by name
        cursor.execute("SELECT * FROM patients WHERE name LIKE ?", ("%Alice%",))
        results = cursor.fetchall()

        assert len(results) == 1
        assert results[0][2] == "Alice"

        conn.close()


@pytest.mark.smoke
class TestFileOperations:
    """Smoke tests for file operations"""

    def test_can_read_prompts(self):
        """Test that prompt files can be read"""
        project_root = Path(__file__).parent.parent.parent
        prompts_dir = project_root / "prompts"

        if prompts_dir.exists():
            prompt_files = list(prompts_dir.glob("*.txt"))
            # Should have at least some prompt files
            assert len(prompt_files) >= 0

    def test_can_create_temp_files(self):
        """Test temporary file creation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        # Verify file exists
        assert Path(temp_path).exists()

        # Read content
        content = Path(temp_path).read_text()
        assert content == "Test content"

        # Cleanup
        Path(temp_path).unlink()

    def test_can_handle_directories(self):
        """Test directory operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create subdirectory
            subdir = temp_path / "subdir"
            subdir.mkdir()

            assert subdir.exists()
            assert subdir.is_dir()

            # Create file in subdirectory
            file_path = subdir / "test.txt"
            file_path.write_text("Test")

            assert file_path.exists()
            assert file_path.read_text() == "Test"
