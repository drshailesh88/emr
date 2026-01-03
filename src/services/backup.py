"""Backup service for SQLite database and ChromaDB vector store.

Supports:
- Local backup (unencrypted for fast access)
- Encrypted backup (for cloud upload)
- Cloud sync via multiple backends

Security: All cloud backups are encrypted client-side with AES-256-GCM.
The cloud service never sees plaintext data (zero-knowledge).
"""

import sqlite3
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, asdict
import os


@dataclass
class BackupInfo:
    """Information about a backup."""
    path: Path
    filename: str
    created_at: str
    size_bytes: int
    patient_count: int
    visit_count: int
    is_encrypted: bool = False
    cloud_synced: bool = False

    def to_dict(self) -> dict:
        result = asdict(self)
        result['path'] = str(self.path)
        return result


class BackupService:
    """Handles backup and restore of EMR data with optional encryption."""

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

    def create_backup(
        self,
        encrypt: bool = False,
        password: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Optional[Path]:
        """Create a backup of SQLite DB and ChromaDB folder.

        Args:
            encrypt: Whether to encrypt the backup
            password: Encryption password (required if encrypt=True)
            progress_callback: Called with (message, percent) updates

        Returns:
            Path to the created backup file, or None if failed.
        """
        if encrypt and not password:
            raise ValueError("Password required for encrypted backup")

        def update_progress(message: str, percent: int):
            if progress_callback:
                progress_callback(message, percent)

        try:
            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            suffix = ".encrypted.zip" if encrypt else ".zip"
            backup_name = f"backup_{timestamp}{suffix}"
            backup_path = self.backup_dir / backup_name

            # Create temporary directory for backup contents
            temp_dir = self.backup_dir / f"temp_{timestamp}"
            temp_dir.mkdir(exist_ok=True)

            try:
                update_progress("Backing up database...", 10)

                # 1. Backup SQLite database using backup API (safe for active DB)
                if self.db_path.exists():
                    temp_db_path = temp_dir / "clinic.db"
                    self._backup_sqlite(self.db_path, temp_db_path)
                else:
                    print("Warning: clinic.db not found, skipping database backup")

                update_progress("Backing up vector store...", 30)

                # 2. Copy ChromaDB folder
                if self.chroma_dir.exists():
                    temp_chroma_dir = temp_dir / "chroma"
                    shutil.copytree(self.chroma_dir, temp_chroma_dir)
                else:
                    print("Warning: chroma/ not found, skipping vector store backup")

                update_progress("Creating manifest...", 50)

                # 3. Create backup manifest
                manifest = self._create_manifest()
                manifest["encrypted"] = encrypt
                manifest_path = temp_dir / "backup_manifest.json"
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)

                update_progress("Creating archive...", 60)

                # 4. Create zip file (unencrypted first)
                temp_zip = temp_dir / "backup.zip"
                with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in temp_dir.rglob('*'):
                        if file_path.is_file() and file_path != temp_zip:
                            arcname = file_path.relative_to(temp_dir)
                            zipf.write(file_path, arcname)

                # 5. Encrypt if requested
                if encrypt:
                    update_progress("Encrypting backup...", 80)
                    from .crypto import CryptoService
                    crypto = CryptoService()

                    if not crypto.encrypt_file(temp_zip, backup_path, password):
                        raise Exception("Encryption failed")
                else:
                    shutil.move(str(temp_zip), str(backup_path))

                update_progress("Backup complete!", 100)
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
        source_conn = sqlite3.connect(source_db)
        dest_conn = sqlite3.connect(dest_db)

        try:
            source_conn.backup(dest_conn)
        finally:
            source_conn.close()
            dest_conn.close()

    def _create_manifest(self) -> dict:
        """Create backup manifest with metadata."""
        manifest = {
            "created_at": datetime.now().isoformat(),
            "version": "2.0",  # v2 supports encryption
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
                print(f"Error getting counts for manifest: {e}")

        return manifest

    def restore_backup(
        self,
        backup_path: Path,
        password: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> bool:
        """Restore from a backup file.

        Args:
            backup_path: Path to the backup file
            password: Decryption password (required for encrypted backups)
            progress_callback: Called with (message, percent) updates

        Returns:
            True if successful, False otherwise
        """
        def update_progress(message: str, percent: int):
            if progress_callback:
                progress_callback(message, percent)

        try:
            if not backup_path.exists():
                print(f"Backup file not found: {backup_path}")
                return False

            is_encrypted = ".encrypted" in backup_path.name

            if is_encrypted and not password:
                raise ValueError("Password required for encrypted backup")

            temp_dir = self.backup_dir / f"restore_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_dir.mkdir(exist_ok=True)

            try:
                # Decrypt if needed
                if is_encrypted:
                    update_progress("Decrypting backup...", 10)
                    from .crypto import CryptoService, DecryptionError
                    crypto = CryptoService()

                    decrypted_path = temp_dir / "decrypted.zip"
                    if not crypto.decrypt_file(backup_path, decrypted_path, password):
                        raise DecryptionError("Decryption failed - wrong password?")
                    zip_path = decrypted_path
                else:
                    zip_path = backup_path

                update_progress("Extracting backup...", 30)

                # Extract backup
                extract_dir = temp_dir / "extracted"
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extractall(extract_dir)

                # Verify manifest
                manifest_path = extract_dir / "backup_manifest.json"
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                        print(f"Restoring backup from {manifest.get('created_at')}")
                        print(f"  Patients: {manifest.get('patient_count', 'unknown')}")
                        print(f"  Visits: {manifest.get('visit_count', 'unknown')}")

                update_progress("Restoring database...", 50)

                # Restore database
                temp_db = extract_dir / "clinic.db"
                if temp_db.exists():
                    if self.db_path.exists():
                        backup_current = self.db_path.with_suffix('.db.pre-restore')
                        shutil.copy2(self.db_path, backup_current)
                    shutil.copy2(temp_db, self.db_path)
                    print(f"Database restored to {self.db_path}")

                update_progress("Restoring vector store...", 70)

                # Restore ChromaDB
                temp_chroma = extract_dir / "chroma"
                if temp_chroma.exists():
                    if self.chroma_dir.exists():
                        backup_current = self.chroma_dir.with_name('chroma.pre-restore')
                        if backup_current.exists():
                            shutil.rmtree(backup_current)
                        shutil.move(str(self.chroma_dir), str(backup_current))
                    shutil.copytree(temp_chroma, self.chroma_dir)
                    print(f"Vector store restored to {self.chroma_dir}")

                update_progress("Restore complete!", 100)
                print(f"Restore completed successfully from {backup_path}")
                return True

            finally:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)

        except Exception as e:
            print(f"Restore failed: {e}")
            return False

    def list_backups(self) -> List[BackupInfo]:
        """List all available backups with metadata.

        Returns:
            List of BackupInfo objects
        """
        backups = []
        seen_files = set()

        if not self.backup_dir.exists():
            return backups

        # Find all backup zip files (use set to avoid duplicates)
        for backup_file in sorted(self.backup_dir.glob("backup_*.zip"), reverse=True):
            if backup_file in seen_files:
                continue
            seen_files.add(backup_file)

            is_encrypted = ".encrypted" in backup_file.name

            backup_info = BackupInfo(
                path=backup_file,
                filename=backup_file.name,
                created_at="",
                size_bytes=backup_file.stat().st_size,
                patient_count=0,
                visit_count=0,
                is_encrypted=is_encrypted
            )

            # Try to read manifest from zip (only for unencrypted)
            if not is_encrypted:
                try:
                    with zipfile.ZipFile(backup_file, 'r') as zipf:
                        if 'backup_manifest.json' in zipf.namelist():
                            manifest_data = zipf.read('backup_manifest.json')
                            manifest = json.loads(manifest_data)
                            backup_info.created_at = manifest.get("created_at", "")
                            backup_info.patient_count = manifest.get("patient_count", 0)
                            backup_info.visit_count = manifest.get("visit_count", 0)
                except Exception as e:
                    print(f"Error reading manifest from {backup_file}: {e}")

            # Fallback: extract timestamp from filename
            if not backup_info.created_at:
                try:
                    # backup_2026-01-02_10-30-00.zip -> 2026-01-02 10:30:00
                    name = backup_file.stem.replace(".encrypted", "")
                    timestamp_str = name.replace("backup_", "").replace("_", " ", 1).replace("-", ":")
                    backup_info.created_at = datetime.strptime(
                        timestamp_str, "%Y-%m-%d %H:%M:%S"
                    ).isoformat()
                except Exception:
                    backup_info.created_at = datetime.fromtimestamp(
                        backup_file.stat().st_mtime
                    ).isoformat()

            backups.append(backup_info)

        # Sort by created_at (newest first)
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups

    def cleanup_old_backups(self, keep_encrypted: bool = True):
        """Delete backups beyond max_backups limit.

        Args:
            keep_encrypted: If True, encrypted backups don't count toward limit
        """
        backups = self.list_backups()

        if keep_encrypted:
            # Separate encrypted and unencrypted
            unencrypted = [b for b in backups if not b.is_encrypted]
            if len(unencrypted) > self.max_backups:
                for backup in unencrypted[self.max_backups:]:
                    try:
                        backup.path.unlink()
                        print(f"Deleted old backup: {backup.filename}")
                    except Exception as e:
                        print(f"Error deleting backup {backup.filename}: {e}")
        else:
            if len(backups) > self.max_backups:
                for backup in backups[self.max_backups:]:
                    try:
                        backup.path.unlink()
                        print(f"Deleted old backup: {backup.filename}")
                    except Exception as e:
                        print(f"Error deleting backup {backup.filename}: {e}")

    def get_last_backup_time(self) -> Optional[datetime]:
        """Get timestamp of most recent backup.

        Returns:
            datetime of last backup, or None if no backups exist
        """
        backups = self.list_backups()
        if not backups:
            return None

        try:
            return datetime.fromisoformat(backups[0].created_at)
        except Exception:
            return None

    def auto_backup(self, encrypt: bool = False, password: Optional[str] = None) -> bool:
        """Perform automatic backup with cleanup.

        Args:
            encrypt: Whether to encrypt the backup
            password: Encryption password

        Returns:
            True if backup was created successfully
        """
        backup_path = self.create_backup(encrypt=encrypt, password=password)
        if backup_path:
            self.cleanup_old_backups()
            return True
        return False

    def sync_to_cloud(
        self,
        password: str,
        backend_config: Dict[str, Any],
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> bool:
        """Create encrypted backup and upload to cloud.

        Args:
            password: Encryption password
            backend_config: Cloud backend configuration
            progress_callback: Called with (message, percent) updates

        Returns:
            True if successful
        """
        from .sync import (
            SyncService, LocalStorageBackend, S3StorageBackend,
            DocAssistCloudBackend, get_or_create_device_id
        )

        def update_progress(message: str, percent: int):
            if progress_callback:
                progress_callback(message, percent)

        try:
            # Create encrypted backup
            update_progress("Creating encrypted backup...", 10)
            backup_path = self.create_backup(encrypt=True, password=password)
            if not backup_path:
                return False

            # Initialize backend
            update_progress("Connecting to cloud...", 30)
            backend_type = backend_config.get("type", "local")

            if backend_type == "local":
                backend = LocalStorageBackend(Path(backend_config["path"]))
            elif backend_type == "s3":
                backend = S3StorageBackend(
                    bucket=backend_config["bucket"],
                    access_key=backend_config["access_key"],
                    secret_key=backend_config["secret_key"],
                    endpoint_url=backend_config.get("endpoint_url"),
                    region=backend_config.get("region", "us-east-1")
                )
            elif backend_type == "docassist":
                device_id = get_or_create_device_id(self.data_dir)
                backend = DocAssistCloudBackend(
                    api_key=backend_config["api_key"],
                    device_id=device_id
                )
            else:
                raise ValueError(f"Unknown backend type: {backend_type}")

            # Upload
            update_progress("Uploading backup...", 50)
            sync = SyncService(backend, self.backup_dir)
            success = sync.upload_backup(backup_path)

            if success:
                update_progress("Sync complete!", 100)
            else:
                update_progress("Sync failed", 0)

            return success

        except Exception as e:
            print(f"Cloud sync failed: {e}")
            return False

    def restore_from_cloud(
        self,
        remote_key: str,
        password: str,
        backend_config: Dict[str, Any],
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> bool:
        """Download and restore backup from cloud.

        Args:
            remote_key: Remote backup key
            password: Decryption password
            backend_config: Cloud backend configuration
            progress_callback: Called with (message, percent) updates

        Returns:
            True if successful
        """
        from .sync import (
            SyncService, LocalStorageBackend, S3StorageBackend,
            DocAssistCloudBackend, get_or_create_device_id
        )

        def update_progress(message: str, percent: int):
            if progress_callback:
                progress_callback(message, percent)

        try:
            # Initialize backend
            update_progress("Connecting to cloud...", 10)
            backend_type = backend_config.get("type", "local")

            if backend_type == "local":
                backend = LocalStorageBackend(Path(backend_config["path"]))
            elif backend_type == "s3":
                backend = S3StorageBackend(
                    bucket=backend_config["bucket"],
                    access_key=backend_config["access_key"],
                    secret_key=backend_config["secret_key"],
                    endpoint_url=backend_config.get("endpoint_url"),
                    region=backend_config.get("region", "us-east-1")
                )
            elif backend_type == "docassist":
                device_id = get_or_create_device_id(self.data_dir)
                backend = DocAssistCloudBackend(
                    api_key=backend_config["api_key"],
                    device_id=device_id
                )
            else:
                raise ValueError(f"Unknown backend type: {backend_type}")

            # Download
            update_progress("Downloading backup...", 30)
            sync = SyncService(backend, self.backup_dir)
            local_path = sync.download_backup(remote_key)

            if not local_path:
                return False

            # Restore
            update_progress("Restoring backup...", 60)
            return self.restore_backup(local_path, password=password)

        except Exception as e:
            print(f"Cloud restore failed: {e}")
            return False

    def list_cloud_backups(self, backend_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List backups available in cloud storage.

        Args:
            backend_config: Cloud backend configuration

        Returns:
            List of backup info dicts
        """
        from .sync import (
            SyncService, LocalStorageBackend, S3StorageBackend,
            DocAssistCloudBackend, get_or_create_device_id
        )

        try:
            backend_type = backend_config.get("type", "local")

            if backend_type == "local":
                backend = LocalStorageBackend(Path(backend_config["path"]))
            elif backend_type == "s3":
                backend = S3StorageBackend(
                    bucket=backend_config["bucket"],
                    access_key=backend_config["access_key"],
                    secret_key=backend_config["secret_key"],
                    endpoint_url=backend_config.get("endpoint_url"),
                    region=backend_config.get("region", "us-east-1")
                )
            elif backend_type == "docassist":
                device_id = get_or_create_device_id(self.data_dir)
                backend = DocAssistCloudBackend(
                    api_key=backend_config["api_key"],
                    device_id=device_id
                )
            else:
                return []

            sync = SyncService(backend, self.backup_dir)
            return sync.list_cloud_backups()

        except Exception as e:
            print(f"Failed to list cloud backups: {e}")
            return []
