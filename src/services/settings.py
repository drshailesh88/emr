"""Settings persistence service."""

from pathlib import Path
from pydantic import BaseModel
import json
from typing import Optional


class DoctorSettings(BaseModel):
    """Doctor profile settings."""
    name: str = "Dr. "
    qualifications: str = ""
    registration_number: str = ""


class ClinicSettings(BaseModel):
    """Clinic information settings."""
    name: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""


class PreferenceSettings(BaseModel):
    """Application preferences."""
    backup_frequency_hours: int = 4
    backup_retention_count: int = 10
    model_override: Optional[str] = None
    theme: str = "light"


class AppSettings(BaseModel):
    """Complete application settings."""
    version: int = 1
    doctor: DoctorSettings = DoctorSettings()
    clinic: ClinicSettings = ClinicSettings()
    preferences: PreferenceSettings = PreferenceSettings()


class SettingsService:
    """Service for loading and saving application settings."""

    def __init__(self, settings_path: Path):
        """Initialize settings service.

        Args:
            settings_path: Path to settings.json file
        """
        self.settings_path = Path(settings_path)
        self._settings: Optional[AppSettings] = None

    def load(self) -> AppSettings:
        """Load settings from disk, or create defaults.

        Returns:
            AppSettings object
        """
        if self._settings is not None:
            return self._settings

        # Ensure parent directory exists
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        # Try to load from file
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle version migrations if needed
                if data.get('version', 1) == 1:
                    self._settings = AppSettings(**data)
                else:
                    # Future: handle version migrations
                    self._settings = AppSettings(**data)

                return self._settings

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # Corrupted file - log and use defaults
                print(f"Warning: Settings file corrupted ({e}). Using defaults.")
                self._settings = AppSettings()
                # Backup corrupted file
                backup_path = self.settings_path.with_suffix('.json.corrupted')
                if self.settings_path.exists():
                    self.settings_path.rename(backup_path)
                # Save defaults
                self.save(self._settings)
                return self._settings

        # No file exists - create with defaults
        self._settings = AppSettings()
        self.save(self._settings)
        return self._settings

    def save(self, settings: AppSettings):
        """Save settings to disk.

        Args:
            settings: AppSettings object to save
        """
        # Ensure parent directory exists
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file with pretty formatting
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings.model_dump(), f, indent=2, ensure_ascii=False)

        # Update cache
        self._settings = settings

    @property
    def settings(self) -> AppSettings:
        """Get current settings (cached).

        Returns:
            AppSettings object
        """
        if self._settings is None:
            return self.load()
        return self._settings

    def update_doctor(self, **kwargs):
        """Update doctor settings.

        Args:
            **kwargs: Fields to update in DoctorSettings
        """
        current = self.settings
        doctor_data = current.doctor.model_dump()
        doctor_data.update(kwargs)
        current.doctor = DoctorSettings(**doctor_data)
        self.save(current)

    def update_clinic(self, **kwargs):
        """Update clinic settings.

        Args:
            **kwargs: Fields to update in ClinicSettings
        """
        current = self.settings
        clinic_data = current.clinic.model_dump()
        clinic_data.update(kwargs)
        current.clinic = ClinicSettings(**clinic_data)
        self.save(current)

    def update_preferences(self, **kwargs):
        """Update preference settings.

        Args:
            **kwargs: Fields to update in PreferenceSettings
        """
        current = self.settings
        prefs_data = current.preferences.model_dump()
        prefs_data.update(kwargs)
        current.preferences = PreferenceSettings(**prefs_data)
        self.save(current)
