"""
User Preferences Service - Persistent storage for app preferences.

Stores user preferences like onboarding completion, theme settings,
and other app configuration using SQLite.
"""

import sqlite3
import os
import json
from typing import Any, Optional
from pathlib import Path


class PreferencesService:
    """
    Service for storing and retrieving user preferences.

    Uses a separate SQLite database for preferences to keep them
    independent of synced patient data.

    Usage:
        prefs = PreferencesService()
        prefs.set_onboarding_complete()
        if not prefs.has_seen_onboarding():
            show_onboarding()
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "preferences.db")
        self._connection: Optional[sqlite3.Connection] = None
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection (lazy initialization)."""
        if self._connection is None:
            # Ensure data directory exists
            Path(self.data_dir).mkdir(parents=True, exist_ok=True)

            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
            )

        return self._connection

    def _initialize_database(self):
        """Create preferences table if it doesn't exist."""
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    # -------------------------------------------------------------------------
    # Generic Preference Operations
    # -------------------------------------------------------------------------

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a preference value.

        Args:
            key: Preference key
            default: Default value if key doesn't exist

        Returns:
            Preference value (JSON-decoded) or default
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT value FROM preferences WHERE key = ?",
            (key,)
        )

        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return row[0]

        return default

    def set_preference(self, key: str, value: Any):
        """
        Set a preference value.

        Args:
            key: Preference key
            value: Preference value (will be JSON-encoded)
        """
        conn = self._get_connection()

        # Encode value as JSON
        json_value = json.dumps(value)

        # Insert or replace
        conn.execute("""
            INSERT OR REPLACE INTO preferences (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, json_value))

        conn.commit()

    def delete_preference(self, key: str):
        """Delete a preference."""
        conn = self._get_connection()
        conn.execute("DELETE FROM preferences WHERE key = ?", (key,))
        conn.commit()

    def clear_all(self):
        """Clear all preferences (use with caution)."""
        conn = self._get_connection()
        conn.execute("DELETE FROM preferences")
        conn.commit()

    # -------------------------------------------------------------------------
    # Onboarding Preferences
    # -------------------------------------------------------------------------

    def has_seen_onboarding(self) -> bool:
        """Check if user has completed onboarding."""
        return self.get_preference("onboarding_complete", False)

    def set_onboarding_complete(self):
        """Mark onboarding as complete."""
        self.set_preference("onboarding_complete", True)
        self.set_preference("onboarding_completed_at", str(self._now()))

    def reset_onboarding(self):
        """Reset onboarding (for testing/debugging)."""
        self.set_preference("onboarding_complete", False)

    # -------------------------------------------------------------------------
    # App Preferences
    # -------------------------------------------------------------------------

    def get_dark_mode(self) -> bool:
        """Get dark mode preference."""
        return self.get_preference("dark_mode", False)

    def set_dark_mode(self, enabled: bool):
        """Set dark mode preference."""
        self.set_preference("dark_mode", enabled)

    def get_haptics_enabled(self) -> bool:
        """Get haptics preference."""
        return self.get_preference("haptics_enabled", True)

    def set_haptics_enabled(self, enabled: bool):
        """Set haptics preference."""
        self.set_preference("haptics_enabled", enabled)

    def get_biometrics_enabled(self) -> bool:
        """Get biometrics preference."""
        return self.get_preference("biometrics_enabled", False)

    def set_biometrics_enabled(self, enabled: bool):
        """Set biometrics preference."""
        self.set_preference("biometrics_enabled", enabled)

    def get_auto_sync(self) -> bool:
        """Get auto-sync preference."""
        return self.get_preference("auto_sync", True)

    def set_auto_sync(self, enabled: bool):
        """Set auto-sync preference."""
        self.set_preference("auto_sync", enabled)

    def get_notification_enabled(self) -> bool:
        """Get notification preference."""
        return self.get_preference("notifications_enabled", True)

    def set_notification_enabled(self, enabled: bool):
        """Set notification preference."""
        self.set_preference("notifications_enabled", enabled)

    # -------------------------------------------------------------------------
    # User Session
    # -------------------------------------------------------------------------

    def set_last_login(self, timestamp: str):
        """Record last login time."""
        self.set_preference("last_login", timestamp)

    def get_last_login(self) -> Optional[str]:
        """Get last login time."""
        return self.get_preference("last_login")

    def set_user_name(self, name: str):
        """Store user name for welcome screen."""
        self.set_preference("user_name", name)

    def get_user_name(self) -> Optional[str]:
        """Get stored user name."""
        return self.get_preference("user_name")

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _now(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime
        return datetime.now().isoformat()

    def export_preferences(self) -> dict:
        """Export all preferences as a dictionary."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT key, value FROM preferences")

        prefs = {}
        for row in cursor.fetchall():
            key, value = row
            try:
                prefs[key] = json.loads(value)
            except json.JSONDecodeError:
                prefs[key] = value

        return prefs

    def import_preferences(self, prefs: dict):
        """Import preferences from a dictionary."""
        for key, value in prefs.items():
            self.set_preference(key, value)


# Singleton instance
_preferences_instance: Optional[PreferencesService] = None


def get_preferences(data_dir: str = "data") -> PreferencesService:
    """
    Get the global preferences service instance.

    Args:
        data_dir: Data directory for preferences database

    Returns:
        PreferencesService instance
    """
    global _preferences_instance

    if _preferences_instance is None:
        _preferences_instance = PreferencesService(data_dir)

    return _preferences_instance
