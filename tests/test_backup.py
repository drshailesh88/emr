"""Tests for the backup service."""

import pytest
import sqlite3
import tempfile
import json
from pathlib import Path
from datetime import datetime

from src.services.backup import BackupService, BackupInfo

# Check if crypto is available for encrypted backup tests
try:
    from src.services.crypto import is_crypto_available
    CRYPTO_AVAILABLE = is_crypto_available()
except ImportError:
    CRYPTO_AVAILABLE = False


class TestBackupService:
    """Tests for BackupService."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory with test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            data_dir = tmpdir / "data"
            data_dir.mkdir()

            # Create test database
            db_path = data_dir / "clinic.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Create tables
            cursor.execute("""
                CREATE TABLE patients (
                    id INTEGER PRIMARY KEY,
                    uhid TEXT UNIQUE,
                    name TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE visits (
                    id INTEGER PRIMARY KEY,
                    patient_id INTEGER,
                    visit_date DATE,
                    chief_complaint TEXT
                )
            """)

            # Insert test data
            cursor.execute(
                "INSERT INTO patients (uhid, name, age, gender) VALUES (?, ?, ?, ?)",
                ("EMR-2024-0001", "Test Patient", 45, "M")
            )
            cursor.execute(
                "INSERT INTO patients (uhid, name, age, gender) VALUES (?, ?, ?, ?)",
                ("EMR-2024-0002", "Another Patient", 32, "F")
            )
            cursor.execute(
                "INSERT INTO visits (patient_id, visit_date, chief_complaint) VALUES (?, ?, ?)",
                (1, "2024-01-15", "Chest pain")
            )

            conn.commit()
            conn.close()

            # Create fake chroma directory
            chroma_dir = data_dir / "chroma"
            chroma_dir.mkdir()
            (chroma_dir / "test_collection.txt").write_text("test vector data")

            yield data_dir

    @pytest.fixture
    def backup_service(self, temp_data_dir):
        """Create a BackupService instance."""
        return BackupService(
            data_dir=temp_data_dir,
            backup_dir=temp_data_dir / "backups",
            max_backups=5
        )

    def test_create_backup(self, backup_service):
        """Test creating an unencrypted backup."""
        backup_path = backup_service.create_backup()

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.suffix == ".zip"
        assert "backup_" in backup_path.name

    def test_backup_contains_database(self, backup_service):
        """Test that backup contains the database."""
        import zipfile

        backup_path = backup_service.create_backup()

        with zipfile.ZipFile(backup_path, 'r') as zipf:
            names = zipf.namelist()
            assert "clinic.db" in names

    def test_backup_contains_manifest(self, backup_service):
        """Test that backup contains manifest with correct counts."""
        import zipfile

        backup_path = backup_service.create_backup()

        with zipfile.ZipFile(backup_path, 'r') as zipf:
            manifest_data = zipf.read("backup_manifest.json")
            manifest = json.loads(manifest_data)

            assert manifest["patient_count"] == 2
            assert manifest["visit_count"] == 1
            assert "created_at" in manifest

    def test_backup_contains_chroma(self, backup_service):
        """Test that backup contains ChromaDB data."""
        import zipfile

        backup_path = backup_service.create_backup()

        with zipfile.ZipFile(backup_path, 'r') as zipf:
            names = zipf.namelist()
            chroma_files = [n for n in names if n.startswith("chroma/")]
            assert len(chroma_files) > 0

    def test_list_backups(self, backup_service):
        """Test listing backups."""
        import time
        # Create multiple backups with delay to ensure different timestamps
        backup_service.create_backup()
        time.sleep(1.1)  # Ensure different second in filename
        backup_service.create_backup()

        backups = backup_service.list_backups()

        assert len(backups) == 2
        assert all(isinstance(b, BackupInfo) for b in backups)
        # Should be sorted newest first
        assert backups[0].created_at >= backups[1].created_at

    def test_restore_backup(self, backup_service, temp_data_dir):
        """Test restoring from a backup."""
        # Create backup
        backup_path = backup_service.create_backup()

        # Modify database
        db_path = temp_data_dir / "clinic.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patients")
        conn.commit()
        conn.close()

        # Verify deletion
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        assert cursor.fetchone()[0] == 0
        conn.close()

        # Restore
        success = backup_service.restore_backup(backup_path)
        assert success

        # Verify restoration
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        assert cursor.fetchone()[0] == 2
        conn.close()

    def test_cleanup_old_backups(self, backup_service):
        """Test cleanup of old backups."""
        # Create more than max_backups
        for _ in range(7):
            backup_service.create_backup()

        backup_service.cleanup_old_backups()

        backups = backup_service.list_backups()
        assert len(backups) <= backup_service.max_backups

    def test_get_last_backup_time(self, backup_service):
        """Test getting last backup time."""
        # No backups yet
        assert backup_service.get_last_backup_time() is None

        # Create backup
        backup_service.create_backup()

        last_time = backup_service.get_last_backup_time()
        assert last_time is not None
        assert isinstance(last_time, datetime)

    def test_auto_backup(self, backup_service):
        """Test automatic backup with cleanup."""
        success = backup_service.auto_backup()
        assert success

        backups = backup_service.list_backups()
        assert len(backups) == 1

    def test_progress_callback(self, backup_service):
        """Test progress callback during backup."""
        progress_updates = []

        def callback(message, percent):
            progress_updates.append((message, percent))

        backup_service.create_backup(progress_callback=callback)

        assert len(progress_updates) > 0
        # Should end with 100%
        assert progress_updates[-1][1] == 100


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="Crypto not available")
class TestEncryptedBackup:
    """Tests for encrypted backups."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory with test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            data_dir = tmpdir / "data"
            data_dir.mkdir()

            # Create test database
            db_path = data_dir / "clinic.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE patients (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            """)
            cursor.execute("INSERT INTO patients (name) VALUES (?)", ("Test",))
            conn.commit()
            conn.close()

            yield data_dir

    @pytest.fixture
    def backup_service(self, temp_data_dir):
        """Create a BackupService instance."""
        return BackupService(
            data_dir=temp_data_dir,
            backup_dir=temp_data_dir / "backups"
        )

    def test_create_encrypted_backup(self, backup_service):
        """Test creating an encrypted backup."""
        backup_path = backup_service.create_backup(
            encrypt=True,
            password="test_password"
        )

        assert backup_path is not None
        assert backup_path.exists()
        assert ".encrypted.zip" in backup_path.name

    def test_encrypted_backup_not_readable_as_zip(self, backup_service):
        """Encrypted backup should not be a valid zip file."""
        import zipfile

        backup_path = backup_service.create_backup(
            encrypt=True,
            password="test_password"
        )

        with pytest.raises(zipfile.BadZipFile):
            zipfile.ZipFile(backup_path, 'r')

    def test_restore_encrypted_backup(self, backup_service, temp_data_dir):
        """Test restoring from an encrypted backup."""
        password = "secure_password_123"

        # Create encrypted backup
        backup_path = backup_service.create_backup(
            encrypt=True,
            password=password
        )

        # Delete database
        db_path = temp_data_dir / "clinic.db"
        db_path.unlink()

        # Restore
        success = backup_service.restore_backup(backup_path, password=password)
        assert success

        # Verify
        assert db_path.exists()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        assert cursor.fetchone()[0] == 1
        conn.close()

    def test_restore_encrypted_wrong_password(self, backup_service):
        """Test restore with wrong password fails."""
        backup_path = backup_service.create_backup(
            encrypt=True,
            password="correct_password"
        )

        success = backup_service.restore_backup(
            backup_path,
            password="wrong_password"
        )
        assert not success

    def test_encrypted_backup_requires_password(self, backup_service):
        """Creating encrypted backup without password should fail."""
        with pytest.raises(ValueError, match="Password required"):
            backup_service.create_backup(encrypt=True)

    def test_list_encrypted_backups(self, backup_service):
        """Test listing includes encrypted backups."""
        backup_service.create_backup()  # Unencrypted
        backup_service.create_backup(encrypt=True, password="pass")  # Encrypted

        backups = backup_service.list_backups()

        assert len(backups) == 2
        encrypted = [b for b in backups if b.is_encrypted]
        unencrypted = [b for b in backups if not b.is_encrypted]

        assert len(encrypted) == 1
        assert len(unencrypted) == 1
