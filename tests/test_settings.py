"""Tests for the settings service."""

import pytest
import json
import tempfile
from pathlib import Path

from src.services.settings import (
    BackupSettings,
    DoctorSettings,
    AppSettings,
    SettingsService
)


class TestBackupSettings:
    """Tests for BackupSettings dataclass."""

    def test_default_values(self):
        """Test default backup settings."""
        settings = BackupSettings()

        assert settings.auto_backup_enabled is True
        assert settings.backup_frequency_hours == 4
        assert settings.backup_on_close is True
        assert settings.cloud_sync_enabled is False
        assert settings.cloud_backend_type == "docassist"
        assert settings.cloud_config == {}
        assert settings.max_local_backups == 10

    def test_custom_values(self):
        """Test custom backup settings."""
        settings = BackupSettings(
            auto_backup_enabled=False,
            backup_frequency_hours=12,
            cloud_sync_enabled=True,
            cloud_backend_type="s3",
            cloud_config={'bucket': 'my-bucket'}
        )

        assert settings.auto_backup_enabled is False
        assert settings.backup_frequency_hours == 12
        assert settings.cloud_sync_enabled is True
        assert settings.cloud_backend_type == "s3"
        assert settings.cloud_config == {'bucket': 'my-bucket'}

    def test_to_dict(self):
        """Test conversion to dictionary."""
        settings = BackupSettings()
        data = settings.to_dict()

        assert isinstance(data, dict)
        assert 'auto_backup_enabled' in data
        assert 'backup_frequency_hours' in data
        assert data['auto_backup_enabled'] is True

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'auto_backup_enabled': False,
            'backup_frequency_hours': 24,
            'backup_on_close': False,
            'cloud_sync_enabled': True,
            'cloud_backend_type': 's3',
            'cloud_config': {'region': 'us-east-1'},
            'max_local_backups': 5
        }

        settings = BackupSettings.from_dict(data)

        assert settings.auto_backup_enabled is False
        assert settings.backup_frequency_hours == 24
        assert settings.cloud_config == {'region': 'us-east-1'}

    def test_from_dict_handles_none_config(self):
        """Test from_dict handles None cloud_config."""
        data = {
            'auto_backup_enabled': True,
            'backup_frequency_hours': 4,
            'backup_on_close': True,
            'cloud_sync_enabled': False,
            'cloud_backend_type': 'docassist',
            'cloud_config': None,
            'max_local_backups': 10
        }

        settings = BackupSettings.from_dict(data)
        assert settings.cloud_config == {}


class TestDoctorSettings:
    """Tests for DoctorSettings dataclass."""

    def test_default_values(self):
        """Test default doctor settings."""
        settings = DoctorSettings()

        assert settings.doctor_name == ""
        assert settings.clinic_name == ""
        assert settings.registration_number == ""

    def test_custom_values(self):
        """Test custom doctor settings."""
        settings = DoctorSettings(
            doctor_name="Dr. Sharma",
            clinic_name="Heart Care Clinic",
            specialization="Cardiology",
            registration_number="MCI-12345"
        )

        assert settings.doctor_name == "Dr. Sharma"
        assert settings.clinic_name == "Heart Care Clinic"
        assert settings.specialization == "Cardiology"

    def test_roundtrip(self):
        """Test to_dict and from_dict roundtrip."""
        original = DoctorSettings(
            doctor_name="Dr. Patel",
            clinic_address="123 Medical Road"
        )

        data = original.to_dict()
        restored = DoctorSettings.from_dict(data)

        assert restored.doctor_name == original.doctor_name
        assert restored.clinic_address == original.clinic_address


class TestAppSettings:
    """Tests for AppSettings dataclass."""

    def test_default_values(self):
        """Test default app settings."""
        settings = AppSettings()

        assert settings.version == "1.0"
        assert settings.theme == "light"
        assert settings.language == "en"
        assert isinstance(settings.backup, BackupSettings)
        assert isinstance(settings.doctor, DoctorSettings)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        settings = AppSettings()
        data = settings.to_dict()

        assert 'version' in data
        assert 'backup' in data
        assert 'doctor' in data
        assert 'theme' in data
        assert isinstance(data['backup'], dict)

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'version': '2.0',
            'theme': 'dark',
            'language': 'hi',
            'backup': {
                'auto_backup_enabled': False,
                'backup_frequency_hours': 12,
                'backup_on_close': True,
                'cloud_sync_enabled': False,
                'cloud_backend_type': 'docassist',
                'cloud_config': {},
                'max_local_backups': 10
            },
            'doctor': {
                'doctor_name': 'Dr. Test',
                'clinic_name': '',
                'clinic_address': '',
                'phone': '',
                'email': '',
                'registration_number': '',
                'specialization': ''
            }
        }

        settings = AppSettings.from_dict(data)

        assert settings.version == '2.0'
        assert settings.theme == 'dark'
        assert settings.backup.backup_frequency_hours == 12
        assert settings.doctor.doctor_name == 'Dr. Test'


class TestSettingsService:
    """Tests for SettingsService."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def service(self, temp_dir):
        """Create settings service with temp directory."""
        return SettingsService(data_dir=temp_dir)

    def test_creates_default_settings(self, service, temp_dir):
        """Test that default settings file is created."""
        settings_path = temp_dir / "settings.json"
        assert settings_path.exists()

    def test_load_settings(self, service):
        """Test loading settings."""
        settings = service.load()

        assert isinstance(settings, AppSettings)
        assert settings.version == "1.0"

    def test_save_settings(self, service, temp_dir):
        """Test saving settings."""
        settings = service.load()
        settings.theme = "dark"
        service.save(settings)

        # Read file directly
        with open(temp_dir / "settings.json") as f:
            data = json.load(f)

        assert data['theme'] == 'dark'

    def test_get_backup_settings(self, service):
        """Test getting backup settings."""
        backup = service.get_backup_settings()

        assert isinstance(backup, BackupSettings)
        assert backup.auto_backup_enabled is True

    def test_update_backup_settings(self, service):
        """Test updating backup settings."""
        new_backup = BackupSettings(
            auto_backup_enabled=False,
            backup_frequency_hours=12
        )

        service.update_backup_settings(new_backup)

        # Reload and verify
        backup = service.get_backup_settings()
        assert backup.auto_backup_enabled is False
        assert backup.backup_frequency_hours == 12

    def test_get_doctor_settings(self, service):
        """Test getting doctor settings."""
        doctor = service.get_doctor_settings()

        assert isinstance(doctor, DoctorSettings)

    def test_update_doctor_settings(self, service):
        """Test updating doctor settings."""
        new_doctor = DoctorSettings(
            doctor_name="Dr. Test",
            specialization="General Medicine"
        )

        service.update_doctor_settings(new_doctor)

        # Reload and verify
        doctor = service.get_doctor_settings()
        assert doctor.doctor_name == "Dr. Test"
        assert doctor.specialization == "General Medicine"

    def test_set_backup_frequency(self, service):
        """Test setting backup frequency."""
        service.set_backup_frequency(12)

        backup = service.get_backup_settings()
        assert backup.backup_frequency_hours == 12

    def test_set_backup_frequency_invalid(self, service):
        """Test invalid backup frequency raises error."""
        with pytest.raises(ValueError):
            service.set_backup_frequency(5)

        with pytest.raises(ValueError):
            service.set_backup_frequency(0)

    def test_enable_auto_backup(self, service):
        """Test enabling/disabling auto backup."""
        service.enable_auto_backup(False)
        assert service.get_backup_settings().auto_backup_enabled is False

        service.enable_auto_backup(True)
        assert service.get_backup_settings().auto_backup_enabled is True

    def test_enable_cloud_sync(self, service):
        """Test enabling cloud sync."""
        service.enable_cloud_sync(
            enabled=True,
            backend_type="s3",
            config={'bucket': 'test-bucket'}
        )

        backup = service.get_backup_settings()
        assert backup.cloud_sync_enabled is True
        assert backup.cloud_backend_type == "s3"
        assert backup.cloud_config == {'bucket': 'test-bucket'}

    def test_enable_backup_on_close(self, service):
        """Test enabling/disabling backup on close."""
        service.enable_backup_on_close(False)
        assert service.get_backup_settings().backup_on_close is False

        service.enable_backup_on_close(True)
        assert service.get_backup_settings().backup_on_close is True

    def test_get_all_as_dict(self, service):
        """Test getting all settings as dictionary."""
        data = service.get_all_as_dict()

        assert isinstance(data, dict)
        assert 'version' in data
        assert 'backup' in data
        assert 'doctor' in data

    def test_reset_to_defaults(self, service):
        """Test resetting to default settings."""
        # Modify settings
        service.set_backup_frequency(24)
        service.enable_auto_backup(False)

        # Reset
        service.reset_to_defaults()

        # Verify defaults restored
        backup = service.get_backup_settings()
        assert backup.backup_frequency_hours == 4
        assert backup.auto_backup_enabled is True

    def test_persistence(self, temp_dir):
        """Test settings persist across service instances."""
        # First instance - modify settings
        service1 = SettingsService(data_dir=temp_dir)
        service1.set_backup_frequency(24)
        service1.update_doctor_settings(DoctorSettings(doctor_name="Dr. Persist"))

        # Second instance - should load saved settings
        service2 = SettingsService(data_dir=temp_dir)
        backup = service2.get_backup_settings()
        doctor = service2.get_doctor_settings()

        assert backup.backup_frequency_hours == 24
        assert doctor.doctor_name == "Dr. Persist"

    def test_handles_corrupted_file(self, temp_dir):
        """Test handling of corrupted settings file."""
        # Write corrupted JSON
        settings_path = temp_dir / "settings.json"
        settings_path.write_text("not valid json {{{")

        # Should create default settings
        service = SettingsService(data_dir=temp_dir)
        settings = service.load()

        assert isinstance(settings, AppSettings)
        assert settings.version == "1.0"
