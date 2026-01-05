"""
Error tracking and reporting for production monitoring.

Captures exceptions, stores them locally, and optionally forwards to Sentry.
"""

import os
import sys
import json
import sqlite3
import traceback
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from pathlib import Path
import platform
import threading

try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


@dataclass
class ErrorSummary:
    """Summary of errors for a time period"""
    period: str
    total_errors: int
    unique_errors: int
    top_errors: List[Dict[str, Any]]
    error_rate: float  # errors per hour


@dataclass
class Transaction:
    """Performance transaction tracking"""
    name: str
    op: str
    start_time: datetime
    _tracker: 'ErrorTracker'
    _sentry_transaction: Optional[Any] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000
        self._tracker._record_transaction(self.name, self.op, duration_ms, exc_type is not None)

        if self._sentry_transaction:
            if exc_type:
                self._sentry_transaction.set_status("internal_error")
            else:
                self._sentry_transaction.set_status("ok")
            self._sentry_transaction.__exit__(exc_type, exc_val, exc_tb)

        return False  # Don't suppress exceptions

    def set_tag(self, key: str, value: str):
        """Add tag to transaction"""
        if self._sentry_transaction:
            self._sentry_transaction.set_tag(key, value)

    def set_data(self, key: str, value: Any):
        """Add data to transaction"""
        if self._sentry_transaction:
            self._sentry_transaction.set_data(key, value)


class ErrorTracker:
    """Track and report errors for production monitoring"""

    def __init__(self, db_path: str = "data/monitoring.db", app_version: str = "unknown"):
        """
        Initialize error tracker

        Args:
            db_path: Path to SQLite database for storing errors
            app_version: Application version string
        """
        self.db_path = db_path
        self.app_version = app_version
        self._ensure_db()

        # Thread-local storage for user context
        self._local = threading.local()

        # Sentry initialization (if configured)
        self._sentry_enabled = False
        sentry_dsn = os.getenv("SENTRY_DSN")
        if SENTRY_AVAILABLE and sentry_dsn:
            try:
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    traces_sample_rate=0.1,  # 10% of transactions
                    environment=os.getenv("ENVIRONMENT", "production"),
                    release=app_version,
                )
                self._sentry_enabled = True
            except Exception as e:
                print(f"Failed to initialize Sentry: {e}")

    def _ensure_db(self):
        """Create database tables if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    error_hash TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    context TEXT,
                    user_id TEXT,
                    user_data TEXT,
                    tags TEXT,
                    environment_info TEXT,
                    app_version TEXT,
                    resolved BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_errors_hash
                ON errors(error_hash)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_errors_timestamp
                ON errors(timestamp DESC)
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    context TEXT,
                    user_id TEXT,
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    name TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_name
                ON transactions(name, timestamp DESC)
            """)

    def capture_exception(self, exception: Exception, context: Dict[str, Any] = None):
        """
        Capture exception with full context

        Args:
            exception: The exception to capture
            context: Additional context dictionary
        """
        # Get full traceback
        exc_type, exc_value, exc_tb = sys.exc_info()
        if exc_tb is None:
            # If called outside exception handler, create minimal traceback
            stack_trace = traceback.format_stack()
            stack_trace_str = ''.join(stack_trace[:-1])  # Exclude this function
        else:
            stack_trace_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))

        # Create error hash for deduplication
        error_hash = self._compute_error_hash(exception, stack_trace_str)

        # Get environment info
        env_info = self._get_environment_info()

        # Get user context
        user_id = getattr(self._local, 'user_id', None)
        user_data = getattr(self._local, 'user_data', None)
        tags = getattr(self._local, 'tags', {})

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO errors (
                    timestamp, error_hash, error_type, error_message,
                    stack_trace, context, user_id, user_data, tags,
                    environment_info, app_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                error_hash,
                type(exception).__name__,
                str(exception),
                stack_trace_str,
                json.dumps(context) if context else None,
                user_id,
                json.dumps(user_data) if user_data else None,
                json.dumps(tags) if tags else None,
                json.dumps(env_info),
                self.app_version
            ))

        # Send to Sentry if enabled
        if self._sentry_enabled:
            try:
                with sentry_sdk.push_scope() as scope:
                    if context:
                        for key, value in context.items():
                            scope.set_context(key, value)

                    if user_id:
                        scope.set_user({"id": user_id, **(user_data or {})})

                    for key, value in tags.items():
                        scope.set_tag(key, value)

                    sentry_sdk.capture_exception(exception)
            except Exception as e:
                print(f"Failed to send exception to Sentry: {e}")

    def capture_message(self, message: str, level: str = "info", context: Dict[str, Any] = None):
        """
        Capture warning/info message

        Args:
            message: The message to capture
            level: Message level (debug/info/warning/error)
            context: Additional context dictionary
        """
        user_id = getattr(self._local, 'user_id', None)
        tags = getattr(self._local, 'tags', {})

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO messages (timestamp, level, message, context, user_id, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                level,
                message,
                json.dumps(context) if context else None,
                user_id,
                json.dumps(tags) if tags else None
            ))

        # Send to Sentry if enabled and level is warning or higher
        if self._sentry_enabled and level in ["warning", "error"]:
            try:
                with sentry_sdk.push_scope() as scope:
                    if context:
                        for key, value in context.items():
                            scope.set_context(key, value)

                    sentry_level = {
                        "debug": "debug",
                        "info": "info",
                        "warning": "warning",
                        "error": "error"
                    }.get(level, "info")

                    sentry_sdk.capture_message(message, level=sentry_level)
            except Exception as e:
                print(f"Failed to send message to Sentry: {e}")

    def set_user(self, user_id: str, user_data: Dict[str, Any] = None):
        """
        Set current user for error context

        Args:
            user_id: User identifier (e.g., doctor ID)
            user_data: Additional user data (anonymized)
        """
        self._local.user_id = user_id
        self._local.user_data = user_data or {}

        if self._sentry_enabled:
            sentry_sdk.set_user({"id": user_id, **self._local.user_data})

    def set_tag(self, key: str, value: str):
        """
        Add tag to current scope

        Args:
            key: Tag key
            value: Tag value
        """
        if not hasattr(self._local, 'tags'):
            self._local.tags = {}

        self._local.tags[key] = value

        if self._sentry_enabled:
            sentry_sdk.set_tag(key, value)

    def clear_context(self):
        """Clear all user context"""
        self._local.user_id = None
        self._local.user_data = None
        self._local.tags = {}

        if self._sentry_enabled:
            sentry_sdk.set_user(None)

    def start_transaction(self, name: str, op: str) -> Transaction:
        """
        Start performance transaction

        Args:
            name: Transaction name (e.g., "save_prescription")
            op: Operation type (e.g., "db.query", "llm.generate")

        Returns:
            Transaction context manager
        """
        sentry_transaction = None
        if self._sentry_enabled:
            sentry_transaction = sentry_sdk.start_transaction(name=name, op=op)
            sentry_transaction.__enter__()

        return Transaction(
            name=name,
            op=op,
            start_time=datetime.now(),
            _tracker=self,
            _sentry_transaction=sentry_transaction
        )

    def _record_transaction(self, name: str, op: str, duration_ms: float, failed: bool):
        """Record transaction to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO transactions (timestamp, name, operation, duration_ms, success)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                name,
                op,
                duration_ms,
                not failed
            ))

    def get_error_summary(self, period: str = "24h") -> ErrorSummary:
        """
        Get summary of errors for period

        Args:
            period: Time period (1h, 24h, 7d, 30d)

        Returns:
            ErrorSummary with statistics
        """
        # Parse period
        period_hours = {
            "1h": 1,
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30
        }.get(period, 24)

        cutoff = datetime.now() - timedelta(hours=period_hours)

        with sqlite3.connect(self.db_path) as conn:
            # Total errors
            cursor = conn.execute("""
                SELECT COUNT(*) FROM errors
                WHERE timestamp >= ?
            """, (cutoff.isoformat(),))
            total_errors = cursor.fetchone()[0]

            # Unique errors
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT error_hash) FROM errors
                WHERE timestamp >= ?
            """, (cutoff.isoformat(),))
            unique_errors = cursor.fetchone()[0]

            # Top errors
            cursor = conn.execute("""
                SELECT
                    error_type,
                    error_message,
                    COUNT(*) as count,
                    MAX(timestamp) as last_seen
                FROM errors
                WHERE timestamp >= ?
                GROUP BY error_hash
                ORDER BY count DESC
                LIMIT 10
            """, (cutoff.isoformat(),))

            top_errors = [
                {
                    "type": row[0],
                    "message": row[1],
                    "count": row[2],
                    "last_seen": row[3]
                }
                for row in cursor.fetchall()
            ]

            # Error rate (errors per hour)
            error_rate = total_errors / period_hours if period_hours > 0 else 0

        return ErrorSummary(
            period=period,
            total_errors=total_errors,
            unique_errors=unique_errors,
            top_errors=top_errors,
            error_rate=error_rate
        )

    def get_error_details(self, error_hash: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific error"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM errors
                WHERE error_hash = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (error_hash,))

            row = cursor.fetchone()
            if not row:
                return None

            return dict(row)

    def mark_resolved(self, error_hash: str):
        """Mark error as resolved"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE errors
                SET resolved = 1
                WHERE error_hash = ?
            """, (error_hash,))

    def _compute_error_hash(self, exception: Exception, stack_trace: str) -> str:
        """Compute hash for error deduplication"""
        # Use exception type and first few lines of stack trace
        lines = stack_trace.split('\n')
        # Find the first line that's not from this file
        relevant_lines = [
            line for line in lines
            if 'error_tracker.py' not in line
        ][:5]

        hash_input = f"{type(exception).__name__}:{':'.join(relevant_lines)}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information"""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

    def cleanup_old_data(self, days: int = 90):
        """
        Clean up old error data

        Args:
            days: Keep data from last N days
        """
        cutoff = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM errors WHERE timestamp < ?", (cutoff.isoformat(),))
            conn.execute("DELETE FROM messages WHERE timestamp < ?", (cutoff.isoformat(),))
            conn.execute("DELETE FROM transactions WHERE timestamp < ?", (cutoff.isoformat(),))
            conn.execute("VACUUM")
