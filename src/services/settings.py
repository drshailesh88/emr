"""Settings management for DocAssist EMR.

Handles:
- Backup settings (auto-backup, frequency, cloud sync)
- Application settings (doctor info, clinic info)
- Settings persistence to JSON file
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class BackupSettings:
    """Backup-related settings."""
    auto_backup_enabled: bool = True
    backup_frequency_hours: int = 4  # 1, 4, 12, or 24
    backup_on_close: bool = True
    cloud_sync_enabled: bool = False
    cloud_backend_type: str = "docassist"  # "docassist", "s3", or "local"
    cloud_config: Dict[str, Any] = field(default_factory=dict)
    max_local_backups: int = 10

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupSettings':
        """Create from dictionary."""
        # Handle cloud_config specially (might be None)
        if 'cloud_config' in data and data['cloud_config'] is None:
            data['cloud_config'] = {}
        return cls(**data)


@dataclass
class DoctorSettings:
    """Doctor/clinic information."""
    doctor_name: str = ""
    qualifications: str = ""  # e.g., "MBBS, MD (Medicine)"
    registration_number: str = ""
    specialization: str = ""
    clinic_name: str = ""
    clinic_address: str = ""
    phone: str = ""
    email: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DoctorSettings':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class AppSettings:
    """Complete application settings."""
    version: str = "1.0"
    backup: BackupSettings = field(default_factory=BackupSettings)
    doctor: DoctorSettings = field(default_factory=DoctorSettings)
    theme: str = "light"  # "light" or "dark"
    language: str = "en"  # Currently only "en" supported
    tutorial_completed: bool = False  # First-run tutorial completion status

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'version': self.version,
            'backup': self.backup.to_dict(),
            'doctor': self.doctor.to_dict(),
            'theme': self.theme,
            'language': self.language,
            'tutorial_completed': self.tutorial_completed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """Create from dictionary."""
        # Extract nested settings
        backup_data = data.get('backup', {})
        doctor_data = data.get('doctor', {})

        return cls(
            version=data.get('version', '1.0'),
            backup=BackupSettings.from_dict(backup_data),
            doctor=DoctorSettings.from_dict(doctor_data),
            theme=data.get('theme', 'light'),
            language=data.get('language', 'en'),
            tutorial_completed=data.get('tutorial_completed', False),
        )


class SettingsService:
    """Manages application settings with persistence."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize settings service.

        Args:
            data_dir: Directory to store settings file (default: data/)
        """
        if data_dir is None:
            data_dir = Path(os.getenv("DOCASSIST_DATA_DIR", "data"))

        self.data_dir = Path(data_dir)
        self.settings_path = self.data_dir / "settings.json"

        # Ensure directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load or create settings
        self._settings: Optional[AppSettings] = None
        self._load()

    def _load(self):
        """Load settings from file."""
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r') as f:
                    data = json.load(f)
                    self._settings = AppSettings.from_dict(data)
                    logger.info("Settings loaded successfully")
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                logger.info("Creating default settings")
                self._settings = AppSettings()
        else:
            logger.info("No settings file found, creating default settings")
            self._settings = AppSettings()
            self.save()

    def save(self, settings: Optional[AppSettings] = None):
        """Save settings to file.

        Args:
            settings: Settings to save (if None, saves current settings)
        """
        if settings is not None:
            self._settings = settings

        try:
            with open(self.settings_path, 'w') as f:
                json.dump(self._settings.to_dict(), f, indent=2)
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            raise

    def load(self) -> AppSettings:
        """Get current settings.

        Returns:
            Current AppSettings instance
        """
        if self._settings is None:
            self._load()
        return self._settings

    def get_backup_settings(self) -> BackupSettings:
        """Get backup settings.

        Returns:
            BackupSettings instance
        """
        return self.load().backup

    def update_backup_settings(self, backup_settings: BackupSettings):
        """Update backup settings.

        Args:
            backup_settings: New backup settings
        """
        settings = self.load()
        settings.backup = backup_settings
        self.save(settings)
        logger.info("Backup settings updated")

    def get_doctor_settings(self) -> DoctorSettings:
        """Get doctor/clinic settings.

        Returns:
            DoctorSettings instance
        """
        return self.load().doctor

    def update_doctor_settings(self, doctor_settings: DoctorSettings):
        """Update doctor/clinic settings.

        Args:
            doctor_settings: New doctor settings
        """
        settings = self.load()
        settings.doctor = doctor_settings
        self.save(settings)
        logger.info("Doctor settings updated")

    def set_backup_frequency(self, hours: int):
        """Set backup frequency.

        Args:
            hours: Frequency in hours (1, 4, 12, or 24)
        """
        if hours not in [1, 4, 12, 24]:
            raise ValueError("Frequency must be 1, 4, 12, or 24 hours")

        backup_settings = self.get_backup_settings()
        backup_settings.backup_frequency_hours = hours
        self.update_backup_settings(backup_settings)

    def enable_auto_backup(self, enabled: bool):
        """Enable or disable automatic backups.

        Args:
            enabled: Whether to enable auto-backup
        """
        backup_settings = self.get_backup_settings()
        backup_settings.auto_backup_enabled = enabled
        self.update_backup_settings(backup_settings)

    def enable_cloud_sync(self, enabled: bool, backend_type: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Enable or disable cloud sync.

        Args:
            enabled: Whether to enable cloud sync
            backend_type: Backend type ("docassist", "s3", "local")
            config: Backend configuration
        """
        backup_settings = self.get_backup_settings()
        backup_settings.cloud_sync_enabled = enabled

        if backend_type:
            backup_settings.cloud_backend_type = backend_type

        if config:
            backup_settings.cloud_config = config

        self.update_backup_settings(backup_settings)

    def enable_backup_on_close(self, enabled: bool):
        """Enable or disable backup on app close.

        Args:
            enabled: Whether to enable backup on close
        """
        backup_settings = self.get_backup_settings()
        backup_settings.backup_on_close = enabled
        self.update_backup_settings(backup_settings)

    def get_all_as_dict(self) -> Dict[str, Any]:
        """Get all settings as dictionary.

        Returns:
            Dictionary with all settings
        """
        return self.load().to_dict()

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        logger.warning("Resetting settings to defaults")
        self._settings = AppSettings()
        self.save()

    def is_first_run(self) -> bool:
        """Check if this is the first run (no doctor profile configured).

        Returns:
            True if no doctor profile is set up, False otherwise
        """
        doctor_settings = self.get_doctor_settings()
        # First run if doctor name is empty or not set
        return not doctor_settings.doctor_name.strip()

    def save_doctor_profile(
        self,
        doctor_name: str,
        qualifications: str = "",
        registration_number: str = "",
        specialization: str = ""
    ):
        """Save doctor profile information.

        Args:
            doctor_name: Doctor's full name
            qualifications: Medical qualifications (e.g., "MBBS, MD")
            registration_number: Medical registration number
            specialization: Medical specialization
        """
        doctor_settings = self.get_doctor_settings()
        doctor_settings.doctor_name = doctor_name
        doctor_settings.qualifications = qualifications
        doctor_settings.registration_number = registration_number
        doctor_settings.specialization = specialization

        self.update_doctor_settings(doctor_settings)
        logger.info(f"Doctor profile saved: {doctor_name}")

    def save_clinic_info(
        self,
        clinic_name: str,
        clinic_address: str,
        phone: str,
        email: str = ""
    ):
        """Save clinic information.

        Args:
            clinic_name: Clinic/hospital name
            clinic_address: Full clinic address
            phone: Contact phone number
            email: Contact email (optional)
        """
        doctor_settings = self.get_doctor_settings()
        doctor_settings.clinic_name = clinic_name
        doctor_settings.clinic_address = clinic_address
        doctor_settings.phone = phone
        doctor_settings.email = email

        self.update_doctor_settings(doctor_settings)
        logger.info(f"Clinic info saved: {clinic_name}")

    def is_tutorial_completed(self) -> bool:
        """Check if the tutorial has been completed.

        Returns:
            True if tutorial has been completed, False otherwise
        """
        return self.load().tutorial_completed

    def mark_tutorial_completed(self):
        """Mark the tutorial as completed."""
        settings = self.load()
        settings.tutorial_completed = True
        self.save(settings)
        logger.info("Tutorial marked as completed")

    def reset_tutorial(self):
        """Reset tutorial completion status (for re-triggering)."""
        settings = self.load()
        settings.tutorial_completed = False
        self.save(settings)
        logger.info("Tutorial status reset")
