"""Backup service for SQLite database and ChromaDB vector store."""

import sqlite3
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import os


class BackupService:
    """Handles automatic backup and restore of EMR data."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        backup_dir: Optional[Path] = None,
        max_backups: int = 10
    ):
        """Initialize backup service.

        Args:
            data_dir: Directory containing clinic.db and chroma/
            backup_dir: Directory to store backups
            max_backups: Maximum number of backups to keep
        """
        if data_dir is None:
            data_dir = Path(os.getenv("DOCASSIST_DATA_DIR", "data"))
        if backup_dir is None:
            backup_dir = data_dir / "backups"

        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Paths to backup
        self.db_path = self.data_dir / "clinic.db"
        self.chroma_dir = self.data_dir / "chroma"

    def create_backup(self) -> Optional[Path]:
        """Create a backup of SQLite DB and ChromaDB folder.

        Returns:
            Path to the created backup zip file, or None if failed.
        """
        try:
            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_name = f"backup_{timestamp}.zip"
            backup_path = self.backup_dir / backup_name

            # Create temporary directory for backup contents
            temp_dir = self.backup_dir / f"temp_{timestamp}"
            temp_dir.mkdir(exist_ok=True)

            try:
                # 1. Backup SQLite database using backup API (safe for active DB)
                if self.db_path.exists():
                    temp_db_path = temp_dir / "clinic.db"
                    self._backup_sqlite(self.db_path, temp_db_path)
                else:
                    print("Warning: clinic.db not found, skipping database backup")

                # 2. Copy ChromaDB folder
                if self.chroma_dir.exists():
                    temp_chroma_dir = temp_dir / "chroma"
                    shutil.copytree(self.chroma_dir, temp_chroma_dir)
                else:
                    print("Warning: chroma/ not found, skipping vector store backup")

                # 3. Create backup manifest
                manifest = self._create_manifest()
                manifest_path = temp_dir / "backup_manifest.json"
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)

                # 4. Create zip file
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in temp_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(temp_dir)
                            zipf.write(file_path, arcname)

                print(f"Backup created: {backup_path}")
                return backup_path

            finally:
                # Clean up temp directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)

        except Exception as e:
            print(f"Backup failed: {e}")
            return None

    def _backup_sqlite(self, source_db: Path, dest_db: Path):
        """Backup SQLite database using the backup API.

        This is safe to use while the database is in use.
        """
        # Connect to source and destination databases
        source_conn = sqlite3.connect(source_db)
        dest_conn = sqlite3.connect(dest_db)

        try:
            # Use SQLite backup API (atomic and safe)
            source_conn.backup(dest_conn)
        finally:
            source_conn.close()
            dest_conn.close()

    def _create_manifest(self) -> dict:
        """Create backup manifest with metadata."""
        manifest = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "patient_count": 0,
            "visit_count": 0,
            "app_version": "0.1.0"
        }

        # Get counts from database if available
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
                print(f"Error getting counts for manifest: {e}")

        return manifest

    def restore_backup(self, backup_path: Path) -> bool:
        """Restore from a backup zip file.

        Args:
            backup_path: Path to the backup zip file

        Returns:
            True if successful, False otherwise
        """
        try:
            if not backup_path.exists():
                print(f"Backup file not found: {backup_path}")
                return False

            # Create temporary extraction directory
            temp_dir = self.backup_dir / f"restore_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_dir.mkdir(exist_ok=True)

            try:
                # Extract backup
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)

                # Verify manifest exists
                manifest_path = temp_dir / "backup_manifest.json"
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                        print(f"Restoring backup from {manifest.get('created_at')}")
                        print(f"  Patients: {manifest.get('patient_count', 'unknown')}")
                        print(f"  Visits: {manifest.get('visit_count', 'unknown')}")

                # Restore database
                temp_db = temp_dir / "clinic.db"
                if temp_db.exists():
                    if self.db_path.exists():
                        # Backup current database before overwriting
                        backup_current = self.db_path.with_suffix('.db.pre-restore')
                        shutil.copy2(self.db_path, backup_current)
                    shutil.copy2(temp_db, self.db_path)
                    print(f"Database restored to {self.db_path}")

                # Restore ChromaDB
                temp_chroma = temp_dir / "chroma"
                if temp_chroma.exists():
                    if self.chroma_dir.exists():
                        # Backup current chroma before overwriting
                        backup_current = self.chroma_dir.with_name('chroma.pre-restore')
                        if backup_current.exists():
                            shutil.rmtree(backup_current)
                        shutil.move(str(self.chroma_dir), str(backup_current))
                    shutil.copytree(temp_chroma, self.chroma_dir)
                    print(f"Vector store restored to {self.chroma_dir}")

                print(f"Restore completed successfully from {backup_path}")
                return True

            finally:
                # Clean up temp directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)

        except Exception as e:
            print(f"Restore failed: {e}")
            return False

    def list_backups(self) -> List[dict]:
        """List all available backups with metadata.

        Returns:
            List of dicts with: path, created_at, size_bytes, patient_count, visit_count
        """
        backups = []

        if not self.backup_dir.exists():
            return backups

        # Find all backup zip files
        for backup_file in sorted(self.backup_dir.glob("backup_*.zip"), reverse=True):
            backup_info = {
                "path": backup_file,
                "filename": backup_file.name,
                "size_bytes": backup_file.stat().st_size,
                "created_at": None,
                "patient_count": None,
                "visit_count": None
            }

            # Try to read manifest from zip
            try:
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    if 'backup_manifest.json' in zipf.namelist():
                        manifest_data = zipf.read('backup_manifest.json')
                        manifest = json.loads(manifest_data)
                        backup_info["created_at"] = manifest.get("created_at")
                        backup_info["patient_count"] = manifest.get("patient_count")
                        backup_info["visit_count"] = manifest.get("visit_count")
            except Exception as e:
                print(f"Error reading manifest from {backup_file}: {e}")

            # Fallback: extract timestamp from filename
            if not backup_info["created_at"]:
                try:
                    # backup_2026-01-02_10-30-00.zip -> 2026-01-02 10:30:00
                    timestamp_str = backup_file.stem.replace("backup_", "").replace("_", " ", 1).replace("-", ":")
                    backup_info["created_at"] = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").isoformat()
                except Exception:
                    # Use file modification time as last resort
                    backup_info["created_at"] = datetime.fromtimestamp(
                        backup_file.stat().st_mtime
                    ).isoformat()

            backups.append(backup_info)

        return backups

    def cleanup_old_backups(self):
        """Delete backups beyond max_backups limit (keep newest)."""
        backups = self.list_backups()

        # Sort by created_at (newest first)
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Delete old backups
        if len(backups) > self.max_backups:
            for backup in backups[self.max_backups:]:
                try:
                    backup["path"].unlink()
                    print(f"Deleted old backup: {backup['filename']}")
                except Exception as e:
                    print(f"Error deleting backup {backup['filename']}: {e}")

    def get_last_backup_time(self) -> Optional[datetime]:
        """Get timestamp of most recent backup.

        Returns:
            datetime of last backup, or None if no backups exist
        """
        backups = self.list_backups()
        if not backups:
            return None

        # Backups are already sorted newest first
        last_backup = backups[0]
        created_at = last_backup.get("created_at")

        if created_at:
            try:
                return datetime.fromisoformat(created_at)
            except Exception:
                pass

        return None

    def auto_backup(self) -> bool:
        """Perform automatic backup with cleanup.

        Returns:
            True if backup was created successfully
        """
        backup_path = self.create_backup()
        if backup_path:
            self.cleanup_old_backups()
            return True
        return False
