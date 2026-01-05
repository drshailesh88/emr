"""Simple local backup service for DocAssist EMR.

This service provides local-only backups WITHOUT encryption.
Perfect for users who want simple, fast backups without the complexity
of encryption and passwords.

Features:
- Copies SQLite database + ChromaDB folder to backup location
- Creates timestamped backup folders (backup_2026-01-05_14-30-00/)
- Keeps last N backups (configurable, default 5)
- Can restore from any backup
- Cross-platform (Windows/Mac/Linux)
- No external dependencies beyond standard library
"""

import sqlite3
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, asdict
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class SimpleBackupInfo:
    """Information about a simple backup."""
    path: Path
    folder_name: str
    created_at: datetime
    size_bytes: int
    patient_count: int
    visit_count: int

    def to_dict(self) -> dict:
        result = asdict(self)
        result['path'] = str(self.path)
        result['created_at'] = self.created_at.isoformat()
        return result


class SimpleBackupService:
    """Handles simple local backups without encryption."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        backup_dir: Optional[Path] = None,
        max_backups: int = 5
    ):
        """Initialize simple backup service.

        Args:
            data_dir: Directory containing clinic.db and chroma/
            backup_dir: Directory to store backups (default: ~/DocAssist/backups/)
            max_backups: Maximum number of backups to keep
        """
        if data_dir is None:
            data_dir = Path(os.getenv("DOCASSIST_DATA_DIR", "data"))

        if backup_dir is None:
            # Default to workspace-local backups to avoid permission issues
            backup_dir = Path(os.getenv("DOCASSIST_BACKUP_DIR", "data/backups"))

        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Paths to backup
        self.db_path = self.data_dir / "clinic.db"
        self.chroma_dir = self.data_dir / "chroma"
        self.prescriptions_dir = self.data_dir / "prescriptions"
        self.settings_file = self.data_dir / "settings.json"

        logger.info(f"SimpleBackupService initialized - backup location: {self.backup_dir}")

    def create_backup(
        self,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Optional[Path]:
        """Create a backup of all EMR data.

        Args:
            progress_callback: Called with (message, percent) updates

        Returns:
            Path to the created backup folder, or None if failed.
        """
        def update_progress(message: str, percent: int):
            if progress_callback:
                progress_callback(message, percent)
            logger.info(f"Backup progress: {percent}% - {message}")

        try:
            # Generate timestamp-based folder name
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_name = f"backup_{timestamp}"
            backup_path = self.backup_dir / backup_name

            # Create backup directory
            backup_path.mkdir(exist_ok=True)
            logger.info(f"Creating backup at: {backup_path}")

            update_progress("Starting backup...", 0)

            # 1. Backup SQLite database using backup API (safe for active DB)
            if self.db_path.exists():
                update_progress("Backing up database...", 20)
                dest_db = backup_path / "clinic.db"
                self._backup_sqlite(self.db_path, dest_db)
                logger.info(f"Database backed up: {dest_db}")
            else:
                logger.warning("clinic.db not found, skipping database backup")

            # 2. Copy ChromaDB folder
            if self.chroma_dir.exists():
                update_progress("Backing up vector store...", 40)
                dest_chroma = backup_path / "chroma"
                shutil.copytree(self.chroma_dir, dest_chroma)
                logger.info(f"Vector store backed up: {dest_chroma}")
            else:
                logger.warning("chroma/ not found, skipping vector store backup")

            # 3. Copy prescriptions folder if exists
            if self.prescriptions_dir.exists():
                update_progress("Backing up prescriptions...", 60)
                dest_prescriptions = backup_path / "prescriptions"
                shutil.copytree(self.prescriptions_dir, dest_prescriptions)
                logger.info(f"Prescriptions backed up: {dest_prescriptions}")

            # 4. Copy settings file if exists
            if self.settings_file.exists():
                update_progress("Backing up settings...", 70)
                dest_settings = backup_path / "settings.json"
                shutil.copy2(self.settings_file, dest_settings)
                logger.info(f"Settings backed up: {dest_settings}")

            # 5. Create backup manifest
            update_progress("Creating manifest...", 80)
            manifest = self._create_manifest()
            manifest_path = backup_path / "backup_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"Manifest created: {manifest_path}")

            # 6. Calculate total size
            total_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
            logger.info(f"Total backup size: {total_size / (1024*1024):.2f} MB")

            update_progress("Backup complete!", 100)
            logger.info(f"Backup created successfully: {backup_path}")

            # Cleanup old backups
            self.cleanup_old_backups()

            return backup_path

        except Exception as e:
            logger.error(f"Backup failed: {e}", exc_info=True)
            # Clean up failed backup
            if backup_path.exists():
                try:
                    shutil.rmtree(backup_path)
                except Exception:
                    pass
            return None

    def _backup_sqlite(self, source_db: Path, dest_db: Path):
        """Backup SQLite database using the backup API.

        This is safe to use while the database is in use.
        """
        source_conn = sqlite3.connect(source_db)
        dest_conn = sqlite3.connect(dest_db)

        try:
            with source_conn:
                source_conn.backup(dest_conn)
        finally:
            source_conn.close()
            dest_conn.close()

    def _create_manifest(self) -> dict:
        """Create backup manifest with metadata."""
        manifest = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "type": "simple_backup",
            "patient_count": 0,
            "visit_count": 0,
            "app_version": "0.1.0",
            "encrypted": False
        }

        if self.db_path.exists():
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM patients")
                manifest["patient_count"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM visits")
                manifest["visit_count"] = cursor.fetchone()[0]

                conn.close()
            except Exception as e:
                logger.error(f"Error getting counts for manifest: {e}")

        return manifest

    def restore_backup(
        self,
        backup_path: Path,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> bool:
        """Restore from a backup folder.

        Args:
            backup_path: Path to the backup folder
            progress_callback: Called with (message, percent) updates

        Returns:
            True if successful, False otherwise
        """
        def update_progress(message: str, percent: int):
            if progress_callback:
                progress_callback(message, percent)
            logger.info(f"Restore progress: {percent}% - {message}")

        try:
            if not backup_path.exists() or not backup_path.is_dir():
                logger.error(f"Backup folder not found: {backup_path}")
                return False

            logger.info(f"Restoring from backup: {backup_path}")
            update_progress("Starting restore...", 0)

            # Create safety backup of current state first
            update_progress("Creating safety backup of current state...", 5)
            safety_backup = self._create_safety_backup()
            if safety_backup:
                logger.info(f"Safety backup created at: {safety_backup}")

            # Verify manifest
            manifest_path = backup_path / "backup_manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    logger.info(f"Restoring backup from {manifest.get('created_at')}")
                    logger.info(f"  Patients: {manifest.get('patient_count', 'unknown')}")
                    logger.info(f"  Visits: {manifest.get('visit_count', 'unknown')}")

            # Restore database
            backup_db = backup_path / "clinic.db"
            if backup_db.exists():
                update_progress("Restoring database...", 20)
                shutil.copy2(backup_db, self.db_path)
                logger.info(f"Database restored to {self.db_path}")

            # Restore ChromaDB
            backup_chroma = backup_path / "chroma"
            if backup_chroma.exists():
                update_progress("Restoring vector store...", 50)
                if self.chroma_dir.exists():
                    shutil.rmtree(self.chroma_dir)
                shutil.copytree(backup_chroma, self.chroma_dir)
                logger.info(f"Vector store restored to {self.chroma_dir}")

            # Restore prescriptions
            backup_prescriptions = backup_path / "prescriptions"
            if backup_prescriptions.exists():
                update_progress("Restoring prescriptions...", 70)
                if self.prescriptions_dir.exists():
                    shutil.rmtree(self.prescriptions_dir)
                shutil.copytree(backup_prescriptions, self.prescriptions_dir)
                logger.info(f"Prescriptions restored to {self.prescriptions_dir}")

            # Restore settings
            backup_settings = backup_path / "settings.json"
            if backup_settings.exists():
                update_progress("Restoring settings...", 85)
                shutil.copy2(backup_settings, self.settings_file)
                logger.info(f"Settings restored to {self.settings_file}")

            update_progress("Restore complete!", 100)
            logger.info(f"Restore completed successfully from {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}", exc_info=True)
            return False

    def _create_safety_backup(self) -> Optional[Path]:
        """Create a safety backup before restore.

        Returns:
            Path to safety backup or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            safety_path = self.backup_dir / f"safety_backup_{timestamp}"
            safety_path.mkdir(exist_ok=True)

            # Just backup the essentials
            if self.db_path.exists():
                shutil.copy2(self.db_path, safety_path / "clinic.db")

            if self.settings_file.exists():
                shutil.copy2(self.settings_file, safety_path / "settings.json")

            # Create marker file
            marker = safety_path / "SAFETY_BACKUP.txt"
            marker.write_text(
                f"This is a safety backup created before restore at {timestamp}\n"
                f"Original backup can be safely deleted after confirming restore success.\n"
            )

            return safety_path
        except Exception as e:
            logger.error(f"Failed to create safety backup: {e}")
            return None

    def list_backups(self) -> List[SimpleBackupInfo]:
        """List all available backups.

        Returns:
            List of SimpleBackupInfo objects, sorted by date (newest first)
        """
        backups = []

        if not self.backup_dir.exists():
            return backups

        # Find all backup folders
        for backup_folder in sorted(self.backup_dir.glob("backup_*"), reverse=True):
            if not backup_folder.is_dir():
                continue

            # Skip safety backups
            if "safety_backup" in backup_folder.name:
                continue

            try:
                # Read manifest if available
                manifest_path = backup_folder / "backup_manifest.json"
                patient_count = 0
                visit_count = 0
                created_at = None

                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                        patient_count = manifest.get("patient_count", 0)
                        visit_count = manifest.get("visit_count", 0)
                        created_at_str = manifest.get("created_at", "")
                        if created_at_str:
                            created_at = datetime.fromisoformat(created_at_str)

                # Fallback: extract timestamp from folder name
                if not created_at:
                    try:
                        # backup_2026-01-05_14-30-00 -> 2026-01-05 14:30:00
                        timestamp_str = backup_folder.name.replace("backup_", "").replace("_", " ", 1).replace("-", ":")
                        created_at = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        # Fallback to folder modification time
                        created_at = datetime.fromtimestamp(backup_folder.stat().st_mtime)

                # Calculate total size
                total_size = sum(f.stat().st_size for f in backup_folder.rglob('*') if f.is_file())

                backup_info = SimpleBackupInfo(
                    path=backup_folder,
                    folder_name=backup_folder.name,
                    created_at=created_at,
                    size_bytes=total_size,
                    patient_count=patient_count,
                    visit_count=visit_count
                )
                backups.append(backup_info)

            except Exception as e:
                logger.error(f"Error reading backup {backup_folder}: {e}")
                continue

        # Sort by created_at (newest first)
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups

    def cleanup_old_backups(self):
        """Delete backups beyond max_backups limit."""
        backups = self.list_backups()

        if len(backups) > self.max_backups:
            logger.info(f"Cleaning up old backups (keeping {self.max_backups} most recent)")
            for backup in backups[self.max_backups:]:
                try:
                    shutil.rmtree(backup.path)
                    logger.info(f"Deleted old backup: {backup.folder_name}")
                except Exception as e:
                    logger.error(f"Error deleting backup {backup.folder_name}: {e}")

    def get_last_backup_time(self) -> Optional[datetime]:
        """Get timestamp of most recent backup.

        Returns:
            datetime of last backup, or None if no backups exist
        """
        backups = self.list_backups()
        if not backups:
            return None
        return backups[0].created_at

    def set_backup_location(self, new_location: Path):
        """Change the backup location.

        Args:
            new_location: New backup directory path
        """
        new_location = Path(new_location)
        new_location.mkdir(parents=True, exist_ok=True)
        self.backup_dir = new_location
        logger.info(f"Backup location changed to: {self.backup_dir}")

    def get_backup_location(self) -> Path:
        """Get current backup location.

        Returns:
            Path to backup directory
        """
        return self.backup_dir

    def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup statistics.

        Returns:
            Dictionary with backup stats
        """
        backups = self.list_backups()
        total_size = sum(b.size_bytes for b in backups)

        last_backup = backups[0] if backups else None

        return {
            "total_backups": len(backups),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "backup_location": str(self.backup_dir),
            "last_backup_time": last_backup.created_at if last_backup else None,
            "oldest_backup_time": backups[-1].created_at if backups else None,
        }
