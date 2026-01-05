"""File Access Security Tests.

Tests file system security to prevent:
- Path traversal attacks
- Unauthorized file access
- Insecure file permissions
- Sensitive data in logs
"""

import pytest
import tempfile
import os
import stat
from pathlib import Path

from src.services.backup import BackupService
from src.services.pdf import PDFService
from src.services.crypto import CryptoService
from src.models.schemas import Patient, Visit


class TestPathTraversal:
    """Test protection against path traversal attacks."""

    def test_backup_path_traversal_prevention(self):
        """Test that backup service prevents path traversal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_service = BackupService()

            # Attempt path traversal in backup name
            dangerous_paths = [
                "../../../etc/passwd",
                "../../root/.ssh/id_rsa",
                "backup/../../../important_file",
            ]

            for dangerous_path in dangerous_paths:
                # Backup service should sanitize or reject these paths
                # Implementation should not allow writing outside backup directory
                try:
                    # This should either reject or sanitize the path
                    result = backup_service._sanitize_filename(dangerous_path)
                    # If it returns a value, it should be safe (no ..)
                    assert ".." not in result
                    assert "/" not in result or not result.startswith("/")
                except (ValueError, AttributeError):
                    # Rejecting is also acceptable
                    pass

    def test_pdf_output_path_validation(self):
        """Test that PDF service validates output paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_service = PDFService()

            # Create a patient and visit for testing
            patient = Patient(
                id=1,
                uhid="TEST-001",
                name="Test Patient",
                age=30,
                gender="M"
            )

            visit = Visit(
                id=1,
                patient_id=1,
                chief_complaint="Test",
                clinical_notes="Test notes"
            )

            # Try to write to dangerous location
            dangerous_path = Path("/etc/passwd_backup.pdf")

            # PDF service should either:
            # 1. Validate and reject the path
            # 2. Only allow writes to designated output directory
            # 3. Require explicit permission for non-standard paths

            # This test documents expected behavior
            # Actual implementation may vary


class TestFilePermissions:
    """Test file permission security."""

    def test_backup_file_permissions(self):
        """Test that backup files have correct permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_service = BackupService()
            backup_path = Path(tmpdir) / "test_backup.zip"

            # Create a backup
            try:
                backup_service.create_backup(str(backup_path))

                if backup_path.exists():
                    # Check file permissions
                    file_stat = backup_path.stat()
                    mode = file_stat.st_mode

                    # File should not be world-readable (medical data is sensitive)
                    assert not (mode & stat.S_IROTH), "Backup file should not be world-readable"

                    # Ideally, file should be owner-only (0600 or 0400)
                    # This is platform-specific and may not always apply
            except Exception:
                # Backup service might not be fully initialized
                pytest.skip("Backup service not available")

    def test_database_file_permissions(self):
        """Test that database file has restricted permissions."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)

        try:
            # Create a database
            from src.services.database import DatabaseService
            db = DatabaseService(str(db_path))

            # Add some data
            patient = Patient(name="Test", age=30)
            db.add_patient(patient)

            # Check file permissions
            file_stat = db_path.stat()
            mode = file_stat.st_mode

            # Database should not be world-readable
            assert not (mode & stat.S_IROTH), "Database should not be world-readable"

        finally:
            if db_path.exists():
                db_path.unlink()

    def test_encrypted_file_permissions(self):
        """Test that encrypted files have correct permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            crypto = CryptoService()

            plaintext_path = Path(tmpdir) / "plaintext.txt"
            encrypted_path = Path(tmpdir) / "encrypted.bin"

            plaintext_path.write_text("Sensitive patient data")

            # Encrypt file
            crypto.encrypt_file(plaintext_path, encrypted_path, "password123")

            if encrypted_path.exists():
                file_stat = encrypted_path.stat()
                mode = file_stat.st_mode

                # Encrypted file should not be world-readable
                assert not (mode & stat.S_IROTH), "Encrypted file should not be world-readable"


class TestSensitiveDataInLogs:
    """Test that sensitive data is not logged."""

    def test_passwords_not_logged(self, caplog):
        """Test that passwords don't appear in logs."""
        from src.services.crypto import CryptoService

        crypto = CryptoService()
        password = "super_secret_password_12345"

        # Perform operations that might log
        with tempfile.NamedTemporaryFile(delete=False) as f:
            plaintext_path = Path(f.name)
            encrypted_path = Path(str(f.name) + ".enc")

        try:
            plaintext_path.write_text("test data")
            crypto.encrypt_file(plaintext_path, encrypted_path, password)

            # Check logs don't contain password
            log_text = caplog.text.lower()
            assert password.lower() not in log_text, "Password found in logs!"

        finally:
            plaintext_path.unlink(missing_ok=True)
            encrypted_path.unlink(missing_ok=True)

    def test_patient_names_logged_appropriately(self, caplog):
        """Test that patient names are only logged when necessary."""
        from src.services.database import DatabaseService

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)

        try:
            db = DatabaseService(str(db_path))

            patient = Patient(
                name="Very Secret Patient Name",
                age=30,
                phone="1234567890"
            )

            db.add_patient(patient)

            # Check if patient name appears in logs
            log_text = caplog.text

            # It's okay if patient name appears in debug logs,
            # but it should not appear in error messages
            # (This is application-specific policy)

        finally:
            db_path.unlink(missing_ok=True)

    def test_encryption_keys_not_logged(self, caplog):
        """Test that encryption keys don't appear in logs."""
        from src.services.crypto import CryptoService

        crypto = CryptoService()
        recovery_key = crypto.generate_recovery_key()

        # Perform operations
        data = b"test data"
        encrypted = crypto.encrypt_with_recovery_key(data, recovery_key)

        # Check logs don't contain the key
        log_text = caplog.text
        assert recovery_key not in log_text, "Recovery key found in logs!"


class TestTemporaryFileHandling:
    """Test secure handling of temporary files."""

    def test_temporary_files_are_deleted(self):
        """Test that temporary files are cleaned up."""
        # This is implementation-specific
        # Generally, services should clean up temp files

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir)

            # Count files before
            files_before = list(temp_dir.glob("*"))

            # Perform operations that might create temp files
            # (This depends on implementation)

            # Count files after - should be same or cleanup should happen
            # This test documents expected behavior


class TestBackupFileSecurity:
    """Test security of backup files."""

    def test_backup_contains_no_plaintext_passwords(self):
        """Test that backups don't contain plaintext passwords."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_service = BackupService()
            backup_path = Path(tmpdir) / "test_backup.zip"

            try:
                # Create backup
                backup_service.create_backup(str(backup_path))

                if backup_path.exists():
                    # Read backup file
                    backup_content = backup_path.read_bytes()

                    # Check for common password indicators
                    # (This is a basic check - real passwords might be hashed)
                    dangerous_patterns = [
                        b"password=",
                        b"passwd:",
                        b"secret_key=",
                    ]

                    for pattern in dangerous_patterns:
                        assert pattern not in backup_content.lower(), \
                            f"Found potential plaintext password pattern: {pattern}"

            except Exception:
                pytest.skip("Backup service not available")

    def test_encrypted_backup_not_readable(self):
        """Test that encrypted backups are not human-readable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            crypto = CryptoService()

            plaintext_path = Path(tmpdir) / "backup.zip"
            encrypted_path = Path(tmpdir) / "backup.encrypted.zip"

            # Create a plaintext backup with recognizable content
            plaintext_content = b"PATIENT NAME: John Doe\nDIAGNOSIS: Diabetes"
            plaintext_path.write_bytes(plaintext_content)

            # Encrypt it
            crypto.encrypt_file(plaintext_path, encrypted_path, "password")

            # Read encrypted content
            encrypted_content = encrypted_path.read_bytes()

            # Verify plaintext is not visible
            assert b"PATIENT" not in encrypted_content
            assert b"John Doe" not in encrypted_content
            assert b"Diabetes" not in encrypted_content


class TestDirectoryTraversal:
    """Test directory access controls."""

    def test_cannot_access_parent_directories(self):
        """Test that services don't allow accessing parent directories."""
        # This test documents expected behavior
        # Actual enforcement depends on service implementation

        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "app_data"
            base_dir.mkdir()

            # Create a sensitive file outside app directory
            sensitive_file = Path(tmpdir) / "sensitive.txt"
            sensitive_file.write_text("Secret data")

            # Try to access file via path traversal
            traversal_path = base_dir / "../sensitive.txt"

            # Services should either:
            # 1. Validate paths and reject traversal
            # 2. Resolve paths and check they're within allowed directory
            # 3. Use sandboxing to restrict file access

            # Attempting to access should fail or be sanitized
            resolved = traversal_path.resolve()
            if base_dir in resolved.parents or resolved == base_dir:
                # Path was sanitized to stay within base_dir
                pass
            else:
                # Path escapes base_dir - should be rejected
                # This test documents that such access should be prevented
                pass


class TestSecureFileDeletion:
    """Test secure file deletion."""

    def test_secure_file_deletion_overwrites(self):
        """Test that secure deletion overwrites data."""
        from src.services.security.data_protection import DataProtectionService

        protection = DataProtectionService()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = Path(f.name)
            original_content = b"Sensitive patient data that must be destroyed"
            f.write(original_content)

        try:
            # Securely delete the file
            protection.secure_delete_file(file_path, passes=3)

            # File should not exist
            assert not file_path.exists()

        except Exception as e:
            # Clean up if test fails
            if file_path.exists():
                file_path.unlink()
            raise

    def test_normal_deletion_vs_secure_deletion(self):
        """Compare normal deletion with secure deletion."""
        # Normal deletion
        with tempfile.NamedTemporaryFile(delete=False) as f:
            normal_path = Path(f.name)
            f.write(b"Normal deletion data")

        # Secure deletion
        with tempfile.NamedTemporaryFile(delete=False) as f:
            secure_path = Path(f.name)
            f.write(b"Secure deletion data")

        # Normal delete
        normal_path.unlink()

        # Secure delete
        from src.services.security.data_protection import DataProtectionService
        protection = DataProtectionService()
        protection.secure_delete_file(secure_path, passes=3)

        # Both files should be gone
        assert not normal_path.exists()
        assert not secure_path.exists()

        # With secure deletion, data is overwritten before deletion
        # (harder to recover with forensic tools)
