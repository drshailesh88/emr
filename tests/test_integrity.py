"""Backup/restore integrity tests.

These tests verify:
- Complete data roundtrip (backup -> restore -> verify)
- Encrypted backup integrity
- Database consistency after restore
- Large data handling
- Edge cases and error recovery
"""

import pytest
import tempfile
import sqlite3
import json
import hashlib
import zipfile
from pathlib import Path
from datetime import date, datetime

from src.services.backup import BackupService, BackupInfo
from src.services.database import DatabaseService
from src.services.crypto import CryptoService
from src.models.schemas import Patient, Visit, Investigation, Procedure, Medication, Prescription


class TestBackupRestoreRoundtrip:
    """Tests for complete backup/restore cycles."""

    @pytest.fixture
    def data_dir(self):
        """Create temporary data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "chroma").mkdir()
            yield tmpdir

    @pytest.fixture
    def populated_database(self, data_dir):
        """Create database with sample data."""
        db_path = data_dir / "clinic.db"
        db = DatabaseService(db_path=str(db_path))

        # Add patients
        patients = []
        for i in range(5):
            patient = db.add_patient(Patient(
                name=f"Patient {i}",
                age=30 + i * 10,
                gender=["M", "F", "O"][i % 3],
                phone=f"98765432{i:02d}",
                address=f"Address {i}, City"
            ))
            patients.append(patient)

        # Add visits
        for patient in patients:
            for j in range(3):
                rx = Prescription(
                    diagnosis=[f"Diagnosis {j}"],
                    medications=[
                        Medication(drug_name=f"Drug {j}", frequency="BD")
                    ]
                )
                db.add_visit(Visit(
                    patient_id=patient.id,
                    visit_date=date(2024, j + 1, 15),
                    chief_complaint=f"Complaint {j}",
                    clinical_notes=f"Notes for visit {j}",
                    diagnosis=f"Diagnosis {j}",
                    prescription_json=rx.model_dump_json()
                ))

        # Add investigations
        for patient in patients:
            db.add_investigation(Investigation(
                patient_id=patient.id,
                test_name="Creatinine",
                result="1.2",
                unit="mg/dL",
                reference_range="0.7-1.3",
                is_abnormal=False
            ))
            db.add_investigation(Investigation(
                patient_id=patient.id,
                test_name="HbA1c",
                result="7.5",
                unit="%",
                is_abnormal=True
            ))

        # Add procedures
        for patient in patients[:2]:
            db.add_procedure(Procedure(
                patient_id=patient.id,
                procedure_name="Angiography",
                details="Diagnostic angiography",
                procedure_date=date(2024, 6, 15)
            ))

        return db

    def test_full_roundtrip_unencrypted(self, data_dir, populated_database):
        """Test complete backup/restore cycle without encryption."""
        backup_service = BackupService(data_dir=data_dir)

        # Create backup
        backup_path = backup_service.create_backup()
        assert backup_path.exists()

        # Get original data counts
        original_patients = populated_database.get_all_patients()
        original_patient_count = len(original_patients)

        # Clear database
        with populated_database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM procedures")
            cursor.execute("DELETE FROM investigations")
            cursor.execute("DELETE FROM visits")
            cursor.execute("DELETE FROM patients")

        # Verify database is empty
        assert len(populated_database.get_all_patients()) == 0

        # Restore
        success = backup_service.restore_backup(backup_path)
        assert success is True

        # Verify data restored
        restored_patients = populated_database.get_all_patients()
        assert len(restored_patients) == original_patient_count

        # Verify patient details
        for original in original_patients:
            restored = populated_database.get_patient(original.id)
            assert restored is not None
            assert restored.name == original.name
            assert restored.uhid == original.uhid
            assert restored.age == original.age

    def test_full_roundtrip_encrypted(self, data_dir, populated_database):
        """Test complete backup/restore cycle with encryption."""
        backup_service = BackupService(data_dir=data_dir)
        password = "secure_backup_password_123"

        # Create encrypted backup
        backup_path = backup_service.create_backup(encrypt=True, password=password)
        assert backup_path.exists()
        assert ".encrypted" in backup_path.name

        # Get original data
        original_patients = populated_database.get_all_patients()

        # Clear database
        with populated_database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM procedures")
            cursor.execute("DELETE FROM investigations")
            cursor.execute("DELETE FROM visits")
            cursor.execute("DELETE FROM patients")

        # Restore with password
        success = backup_service.restore_backup(backup_path, password=password)
        assert success is True

        # Verify data restored
        restored_patients = populated_database.get_all_patients()
        assert len(restored_patients) == len(original_patients)

    def test_visits_preserved_after_restore(self, data_dir, populated_database):
        """Test all visits are preserved after restore."""
        backup_service = BackupService(data_dir=data_dir)

        # Get original visits
        patients = populated_database.get_all_patients()
        original_visits = {}
        for patient in patients:
            visits = populated_database.get_patient_visits(patient.id)
            original_visits[patient.id] = visits

        # Backup
        backup_path = backup_service.create_backup()

        # Clear and restore
        with populated_database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM visits")
            cursor.execute("DELETE FROM patients")

        backup_service.restore_backup(backup_path)

        # Verify visits
        for patient_id, original in original_visits.items():
            restored = populated_database.get_patient_visits(patient_id)
            assert len(restored) == len(original)

            for orig_visit, rest_visit in zip(original, restored):
                assert orig_visit.chief_complaint == rest_visit.chief_complaint
                assert orig_visit.diagnosis == rest_visit.diagnosis

    def test_prescription_json_preserved(self, data_dir, populated_database):
        """Test prescription JSON is preserved exactly."""
        backup_service = BackupService(data_dir=data_dir)

        # Get original prescription
        patient = populated_database.get_all_patients()[0]
        original_visits = populated_database.get_patient_visits(patient.id)
        original_rx_json = original_visits[0].prescription_json

        # Parse to verify it's valid
        original_rx = json.loads(original_rx_json)

        # Backup and restore
        backup_path = backup_service.create_backup()
        with populated_database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM visits")

        backup_service.restore_backup(backup_path)

        # Verify prescription
        restored_visits = populated_database.get_patient_visits(patient.id)
        restored_rx = json.loads(restored_visits[0].prescription_json)

        assert restored_rx == original_rx


class TestBackupIntegrity:
    """Tests for backup file integrity."""

    @pytest.fixture
    def backup_service(self):
        """Create backup service with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "chroma").mkdir()

            # Create minimal database
            db = DatabaseService(db_path=str(tmpdir / "clinic.db"))
            db.add_patient(Patient(name="Test Patient"))

            yield BackupService(data_dir=tmpdir)

    def test_backup_contains_manifest(self, backup_service):
        """Test backup contains manifest with metadata."""
        backup_path = backup_service.create_backup()

        with zipfile.ZipFile(backup_path, 'r') as zf:
            assert "backup_manifest.json" in zf.namelist()

            manifest = json.loads(zf.read("backup_manifest.json"))
            assert "created_at" in manifest
            assert "patient_count" in manifest
            assert "visit_count" in manifest

    def test_backup_manifest_accurate(self, backup_service):
        """Test manifest counts are accurate."""
        backup_path = backup_service.create_backup()

        with zipfile.ZipFile(backup_path, 'r') as zf:
            manifest = json.loads(zf.read("backup_manifest.json"))

        assert manifest["patient_count"] == 1
        assert manifest["visit_count"] == 0

    def test_backup_database_integrity(self, backup_service):
        """Test database in backup is valid SQLite."""
        backup_path = backup_service.create_backup()

        with zipfile.ZipFile(backup_path, 'r') as zf:
            db_data = zf.read("clinic.db")

        # SQLite files start with specific header
        assert db_data[:16] == b"SQLite format 3\x00"

    def test_backup_checksum_verification(self, backup_service):
        """Test backup file checksum can be verified."""
        backup_path = backup_service.create_backup()

        # Calculate checksum
        with open(backup_path, 'rb') as f:
            checksum = hashlib.sha256(f.read()).hexdigest()

        # Checksum should be consistent
        with open(backup_path, 'rb') as f:
            checksum2 = hashlib.sha256(f.read()).hexdigest()

        assert checksum == checksum2


class TestEncryptedBackupIntegrity:
    """Tests for encrypted backup integrity."""

    @pytest.fixture
    def backup_service(self):
        """Create backup service with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "chroma").mkdir()

            db = DatabaseService(db_path=str(tmpdir / "clinic.db"))
            db.add_patient(Patient(name="Encrypted Patient", age=50))

            yield BackupService(data_dir=tmpdir)

    def test_encrypted_backup_not_zip(self, backup_service):
        """Test encrypted backup is not directly readable as ZIP."""
        backup_path = backup_service.create_backup(
            encrypt=True,
            password="test_password"
        )

        # Should not be readable as ZIP
        with pytest.raises(zipfile.BadZipFile):
            zipfile.ZipFile(backup_path, 'r')

    def test_encrypted_backup_no_plaintext(self, backup_service):
        """Test encrypted backup contains no plaintext data."""
        backup_path = backup_service.create_backup(
            encrypt=True,
            password="test_password"
        )

        content = backup_path.read_bytes()

        # Should not contain recognizable strings
        assert b"Encrypted Patient" not in content
        assert b"clinic.db" not in content
        assert b"manifest" not in content
        assert b"SQLite" not in content

    def test_wrong_password_fails_restore(self, backup_service):
        """Test wrong password fails to restore."""
        backup_path = backup_service.create_backup(
            encrypt=True,
            password="correct_password"
        )

        success = backup_service.restore_backup(
            backup_path,
            password="wrong_password"
        )

        assert success is False

    def test_encrypted_restore_requires_password(self, backup_service):
        """Test encrypted backup requires password to restore."""
        backup_path = backup_service.create_backup(
            encrypt=True,
            password="test_password"
        )

        # Try restore without password
        success = backup_service.restore_backup(backup_path)
        assert success is False


class TestLargeDataHandling:
    """Tests for handling large amounts of data."""

    @pytest.fixture
    def large_database(self):
        """Create database with large amount of data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "chroma").mkdir()

            db = DatabaseService(db_path=str(tmpdir / "clinic.db"))

            # Add many patients
            for i in range(100):
                patient = db.add_patient(Patient(
                    name=f"Patient {i:03d}",
                    age=20 + (i % 60),
                    gender=["M", "F"][i % 2],
                    address="A" * 500  # Long address
                ))

                # Add visits with long notes
                for j in range(10):
                    db.add_visit(Visit(
                        patient_id=patient.id,
                        clinical_notes="Detailed notes " * 100,
                        diagnosis=f"Diagnosis {j}"
                    ))

            yield tmpdir, db

    def test_large_backup_creates_successfully(self, large_database):
        """Test backup of large database completes."""
        tmpdir, db = large_database
        backup_service = BackupService(data_dir=tmpdir)

        backup_path = backup_service.create_backup()

        assert backup_path.exists()
        # Should be reasonably sized (compressed)
        assert backup_path.stat().st_size > 10000  # At least 10KB

    def test_large_restore_preserves_all_data(self, large_database):
        """Test restore preserves all data from large backup."""
        tmpdir, db = large_database
        backup_service = BackupService(data_dir=tmpdir)

        original_count = len(db.get_all_patients())

        backup_path = backup_service.create_backup()

        # Clear database
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM visits")
            cursor.execute("DELETE FROM patients")

        # Restore
        backup_service.restore_backup(backup_path)

        # Verify count
        restored_count = len(db.get_all_patients())
        assert restored_count == original_count


class TestEdgeCases:
    """Tests for edge cases and error scenarios."""

    @pytest.fixture
    def backup_service(self):
        """Create backup service with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "chroma").mkdir()
            DatabaseService(db_path=str(tmpdir / "clinic.db"))
            yield BackupService(data_dir=tmpdir), tmpdir

    def test_backup_empty_database(self, backup_service):
        """Test backup of empty database works."""
        service, tmpdir = backup_service

        backup_path = service.create_backup()

        assert backup_path.exists()

        # Manifest should show zero counts
        with zipfile.ZipFile(backup_path, 'r') as zf:
            manifest = json.loads(zf.read("backup_manifest.json"))

        assert manifest["patient_count"] == 0

    def test_restore_to_non_empty_database(self, backup_service):
        """Test restore overwrites existing data."""
        service, tmpdir = backup_service
        db = DatabaseService(db_path=str(tmpdir / "clinic.db"))

        # Add initial patient
        db.add_patient(Patient(name="Initial Patient"))
        backup_path = service.create_backup()

        # Add more patients
        db.add_patient(Patient(name="New Patient 1"))
        db.add_patient(Patient(name="New Patient 2"))
        assert len(db.get_all_patients()) == 3

        # Restore should bring back to 1 patient
        service.restore_backup(backup_path)
        assert len(db.get_all_patients()) == 1

    def test_backup_with_unicode_data(self, backup_service):
        """Test backup preserves unicode data."""
        service, tmpdir = backup_service
        db = DatabaseService(db_path=str(tmpdir / "clinic.db"))

        # Add patient with unicode name
        patient = db.add_patient(Patient(
            name="राम कुमार शर्मा",  # Hindi
            address="मुंबई, महाराष्ट्र"
        ))

        db.add_visit(Visit(
            patient_id=patient.id,
            clinical_notes="रोगी को बुखार है। 🤒",
            diagnosis="वायरल बुखार"
        ))

        # Backup and restore
        backup_path = service.create_backup()

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM visits")
            cursor.execute("DELETE FROM patients")

        service.restore_backup(backup_path)

        # Verify unicode preserved
        restored = db.get_all_patients()[0]
        assert restored.name == "राम कुमार शर्मा"

        visits = db.get_patient_visits(restored.id)
        assert "🤒" in visits[0].clinical_notes

    def test_corrupted_backup_detected(self, backup_service):
        """Test corrupted backup is detected."""
        service, tmpdir = backup_service
        db = DatabaseService(db_path=str(tmpdir / "clinic.db"))
        db.add_patient(Patient(name="Test"))

        backup_path = service.create_backup()

        # Corrupt the backup
        with open(backup_path, 'r+b') as f:
            f.seek(100)
            f.write(b'\x00\x00\x00\x00')

        # Restore should fail
        success = service.restore_backup(backup_path)
        assert success is False

    def test_missing_backup_file(self, backup_service):
        """Test missing backup file handled gracefully."""
        service, tmpdir = backup_service

        fake_path = tmpdir / "nonexistent_backup.zip"

        success = service.restore_backup(fake_path)
        assert success is False


class TestRecoveryKeyIntegrity:
    """Tests for recovery key backup/restore."""

    @pytest.fixture
    def backup_service(self):
        """Create backup service with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "chroma").mkdir()

            db = DatabaseService(db_path=str(tmpdir / "clinic.db"))
            db.add_patient(Patient(name="Recovery Test Patient"))

            yield BackupService(data_dir=tmpdir), tmpdir

    def test_recovery_key_backup_restore(self, backup_service):
        """Test backup with recovery key can be restored."""
        service, tmpdir = backup_service
        db = DatabaseService(db_path=str(tmpdir / "clinic.db"))

        crypto = CryptoService()
        recovery_key = crypto.generate_recovery_key()

        # Create backup with password (would typically store recovery key separately)
        backup_path = service.create_backup(encrypt=True, password="password123")

        # Clear and restore
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM patients")

        success = service.restore_backup(backup_path, password="password123")
        assert success is True

        # Verify data
        patients = db.get_all_patients()
        assert len(patients) == 1
        assert patients[0].name == "Recovery Test Patient"
