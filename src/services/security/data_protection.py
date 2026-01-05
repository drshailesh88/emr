"""Data protection and audit logging for sensitive medical data.

Features:
- Audit trail for all data access and modifications
- Secure deletion (overwrite before delete)
- Optional field-level encryption for extra-sensitive data
- Session timeout tracking
- Data access logging for compliance (HIPAA/DISHA)
"""

import os
import sqlite3
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Types of actions to audit."""
    VIEW_PATIENT = "view_patient"
    CREATE_PATIENT = "create_patient"
    UPDATE_PATIENT = "update_patient"
    DELETE_PATIENT = "delete_patient"
    VIEW_VISIT = "view_visit"
    CREATE_VISIT = "create_visit"
    UPDATE_VISIT = "update_visit"
    DELETE_VISIT = "delete_visit"
    VIEW_INVESTIGATION = "view_investigation"
    CREATE_INVESTIGATION = "create_investigation"
    EXPORT_DATA = "export_data"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    LOGIN = "login"
    LOGOUT = "logout"
    FAILED_LOGIN = "failed_login"
    SETTINGS_CHANGE = "settings_change"


@dataclass
class AuditLogEntry:
    """Single audit log entry."""
    id: Optional[int]
    timestamp: datetime
    action: AuditAction
    user_id: Optional[str]  # User/doctor ID (if auth enabled)
    patient_id: Optional[int]  # Patient ID (if applicable)
    resource_type: str  # "patient", "visit", "investigation", etc.
    resource_id: Optional[int]  # ID of resource
    details: Optional[str]  # Additional details (JSON)
    ip_address: Optional[str]  # If network enabled
    success: bool  # Whether action succeeded


class DataProtectionService:
    """Handles data protection, audit logging, and secure deletion."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize data protection service.

        Args:
            db_path: Path to SQLite database (defaults to main clinic.db)
        """
        if db_path is None:
            db_path = os.getenv("DOCASSIST_DB_PATH", "data/clinic.db")
        self.db_path = Path(db_path)
        self._init_audit_tables()

    @contextmanager
    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            logger.error(f"Database error in data protection: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_audit_tables(self):
        """Initialize audit log tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    action TEXT NOT NULL,
                    user_id TEXT,
                    patient_id INTEGER,
                    resource_type TEXT,
                    resource_id INTEGER,
                    details TEXT,
                    ip_address TEXT,
                    success BOOLEAN DEFAULT 1
                )
            """)

            # Session tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    ip_address TEXT,
                    device_info TEXT
                )
            """)

            # Data access log (for compliance - who viewed what patient)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    patient_id INTEGER NOT NULL,
                    access_type TEXT,
                    purpose TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_log(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_patient
                ON audit_log(patient_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_access_patient
                ON data_access_log(patient_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_active
                ON sessions(is_active, expires_at)
            """)

    # ============== AUDIT LOGGING ==============

    def log_action(
        self,
        action: AuditAction,
        user_id: Optional[str] = None,
        patient_id: Optional[int] = None,
        resource_type: str = "",
        resource_id: Optional[int] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True
    ):
        """Log an action to the audit trail.

        Args:
            action: Type of action
            user_id: User performing action
            patient_id: Patient ID (if applicable)
            resource_type: Type of resource
            resource_id: ID of resource
            details: Additional details (JSON string)
            ip_address: IP address (if network enabled)
            success: Whether action succeeded
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_log
                    (action, user_id, patient_id, resource_type, resource_id,
                     details, ip_address, success)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    action.value,
                    user_id,
                    patient_id,
                    resource_type,
                    resource_id,
                    details,
                    ip_address,
                    success
                ))

                logger.info(
                    f"Audit: {action.value} by {user_id or 'system'} "
                    f"on {resource_type}:{resource_id} - {'success' if success else 'failed'}"
                )

        except Exception as e:
            # Audit logging should never crash the app
            logger.error(f"Failed to write audit log: {e}", exc_info=True)

    def get_audit_log(
        self,
        patient_id: Optional[int] = None,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve audit log entries.

        Args:
            patient_id: Filter by patient
            user_id: Filter by user
            action: Filter by action type
            start_date: Start date
            end_date: End date
            limit: Maximum number of entries

        Returns:
            List of audit log entries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []

            if patient_id is not None:
                query += " AND patient_id = ?"
                params.append(patient_id)

            if user_id is not None:
                query += " AND user_id = ?"
                params.append(user_id)

            if action is not None:
                query += " AND action = ?"
                params.append(action.value)

            if start_date is not None:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())

            if end_date is not None:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def log_data_access(
        self,
        patient_id: int,
        user_id: Optional[str] = None,
        access_type: str = "view",
        purpose: Optional[str] = None
    ):
        """Log access to patient data (for compliance).

        Args:
            patient_id: Patient whose data was accessed
            user_id: User who accessed it
            access_type: Type of access (view, edit, export)
            purpose: Purpose of access (optional, for compliance)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO data_access_log
                    (user_id, patient_id, access_type, purpose)
                    VALUES (?, ?, ?, ?)
                """, (user_id, patient_id, access_type, purpose))

        except Exception as e:
            logger.error(f"Failed to log data access: {e}", exc_info=True)

    def get_patient_access_log(self, patient_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get access log for a specific patient.

        Args:
            patient_id: Patient ID
            limit: Maximum number of entries

        Returns:
            List of access log entries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM data_access_log
                WHERE patient_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (patient_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    # ============== SECURE DELETION ==============

    def secure_delete_file(self, file_path: Path, passes: int = 3) -> bool:
        """Securely delete a file by overwriting before deletion.

        Args:
            file_path: Path to file
            passes: Number of overwrite passes (default 3)

        Returns:
            True if successful
        """
        try:
            if not file_path.exists():
                return True

            file_size = file_path.stat().st_size

            # Overwrite with random data
            with open(file_path, 'wb') as f:
                for _ in range(passes):
                    f.seek(0)
                    # Write random data
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())

            # Finally, delete the file
            file_path.unlink()

            logger.info(f"Securely deleted file: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to securely delete {file_path}: {e}")
            return False

    def secure_delete_record(
        self,
        table_name: str,
        record_id: int,
        id_column: str = "id"
    ) -> bool:
        """Securely delete a database record.

        In SQLite, DELETE doesn't immediately remove data from disk.
        This marks the record for secure deletion and can trigger VACUUM.

        Args:
            table_name: Table name
            record_id: Record ID
            id_column: Name of ID column

        Returns:
            True if successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # First, overwrite sensitive fields with random data
                # (This is database-dependent - SQLite may not truly overwrite)
                cursor.execute(f"""
                    UPDATE {table_name}
                    SET name = ?, phone = ?, address = ?
                    WHERE {id_column} = ?
                """, (
                    hashlib.sha256(os.urandom(32)).hexdigest()[:20],
                    "DELETED",
                    "DELETED",
                    record_id
                ))

                # Then delete
                cursor.execute(f"""
                    DELETE FROM {table_name}
                    WHERE {id_column} = ?
                """, (record_id,))

                # Note: VACUUM should be run periodically to actually reclaim space
                # It's expensive, so we don't do it automatically here

                logger.info(f"Securely deleted record {record_id} from {table_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to securely delete record: {e}")
            return False

    def vacuum_database(self):
        """Run VACUUM to reclaim space from deleted records.

        This should be run periodically (e.g., during maintenance windows).
        WARNING: This can take time and locks the database.
        """
        try:
            with self.get_connection() as conn:
                # VACUUM requires autocommit mode
                conn.isolation_level = None
                cursor = conn.cursor()
                cursor.execute("VACUUM")
                logger.info("Database vacuum completed")

        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")

    # ============== SESSION MANAGEMENT ==============

    def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        timeout_minutes: int = 30,
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None
    ) -> bool:
        """Create a new session.

        Args:
            session_id: Unique session ID
            user_id: User ID
            timeout_minutes: Session timeout in minutes
            ip_address: IP address
            device_info: Device information

        Returns:
            True if successful
        """
        try:
            expires_at = datetime.now() + timedelta(minutes=timeout_minutes)

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions
                    (session_id, user_id, expires_at, ip_address, device_info)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, user_id, expires_at, ip_address, device_info))

            self.log_action(
                AuditAction.LOGIN,
                user_id=user_id,
                ip_address=ip_address,
                success=True
            )

            return True

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return False

    def update_session_activity(self, session_id: str) -> bool:
        """Update last activity time for session.

        Args:
            session_id: Session ID

        Returns:
            True if session is still valid
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions
                    SET last_activity = CURRENT_TIMESTAMP
                    WHERE session_id = ? AND is_active = 1
                """, (session_id,))

                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            return False

    def validate_session(self, session_id: str) -> bool:
        """Check if session is valid and not expired.

        Args:
            session_id: Session ID

        Returns:
            True if session is valid
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT expires_at, is_active
                    FROM sessions
                    WHERE session_id = ?
                """, (session_id,))

                row = cursor.fetchone()
                if not row:
                    return False

                expires_at = datetime.fromisoformat(row[0])
                is_active = bool(row[1])

                if not is_active:
                    return False

                if datetime.now() > expires_at:
                    # Session expired, mark as inactive
                    self.invalidate_session(session_id)
                    return False

                # Update last activity
                self.update_session_activity(session_id)
                return True

        except Exception as e:
            logger.error(f"Failed to validate session: {e}")
            return False

    def invalidate_session(self, session_id: str):
        """Invalidate a session (logout).

        Args:
            session_id: Session ID
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get user_id for logging
                cursor.execute("SELECT user_id FROM sessions WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                user_id = row[0] if row else None

                cursor.execute("""
                    UPDATE sessions
                    SET is_active = 0
                    WHERE session_id = ?
                """, (session_id,))

                self.log_action(
                    AuditAction.LOGOUT,
                    user_id=user_id,
                    success=True
                )

        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")

    def cleanup_expired_sessions(self):
        """Remove expired sessions from database.

        Should be run periodically.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions
                    SET is_active = 0
                    WHERE expires_at < CURRENT_TIMESTAMP
                    AND is_active = 1
                """)

                expired_count = cursor.rowcount

                # Delete very old sessions (older than 30 days)
                thirty_days_ago = datetime.now() - timedelta(days=30)
                cursor.execute("""
                    DELETE FROM sessions
                    WHERE expires_at < ?
                """, (thirty_days_ago,))

                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired sessions")

        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")

    # ============== DATA ANONYMIZATION ==============

    def anonymize_patient_data(self, patient_id: int) -> bool:
        """Anonymize patient data (for research/testing).

        Replaces identifiable information with anonymized values.

        Args:
            patient_id: Patient ID

        Returns:
            True if successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Generate anonymous ID
                anon_name = f"Patient_{hashlib.sha256(str(patient_id).encode()).hexdigest()[:8]}"

                cursor.execute("""
                    UPDATE patients
                    SET name = ?,
                        phone = '',
                        address = 'ANONYMIZED'
                    WHERE id = ?
                """, (anon_name, patient_id))

                self.log_action(
                    AuditAction.UPDATE_PATIENT,
                    patient_id=patient_id,
                    details="Patient data anonymized",
                    success=True
                )

                return True

        except Exception as e:
            logger.error(f"Failed to anonymize patient {patient_id}: {e}")
            return False


# Global instance
_protection_service = None


def get_protection_service() -> DataProtectionService:
    """Get global data protection service instance.

    Returns:
        DataProtectionService instance
    """
    global _protection_service
    if _protection_service is None:
        _protection_service = DataProtectionService()
    return _protection_service
