"""
Crash reporting and recovery for DocAssist EMR.

Handles unhandled exceptions gracefully and creates detailed crash reports.
"""

import os
import sys
import json
import sqlite3
import traceback
import hashlib
import platform
import psutil
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import threading


@dataclass
class CrashReport:
    """Detailed crash report"""
    id: Optional[str] = None
    timestamp: datetime = None
    exception_type: str = ""
    exception_message: str = ""
    stack_trace: str = ""
    system_info: Dict[str, Any] = None
    memory_snapshot: Dict[str, Any] = None
    recent_actions: List[Dict[str, Any]] = None
    app_version: str = ""
    submitted: bool = False
    crash_hash: str = ""


class CrashReporter:
    """Handle app crashes gracefully"""

    def __init__(
        self,
        db_path: str = "data/monitoring.db",
        crash_dir: str = "data/crash_reports",
        app_version: str = "unknown",
        audit_log_path: str = "data/audit.db"
    ):
        """
        Initialize crash reporter

        Args:
            db_path: Path to monitoring database
            crash_dir: Directory to store crash reports
            app_version: Application version
            audit_log_path: Path to audit log for recent actions
        """
        self.db_path = db_path
        self.crash_dir = crash_dir
        self.app_version = app_version
        self.audit_log_path = audit_log_path

        os.makedirs(crash_dir, exist_ok=True)
        self._ensure_db()

        # Custom crash handlers
        self._crash_handlers: List[Callable] = []

        # Original exception hook (to restore if needed)
        self._original_excepthook = sys.excepthook

        # Installation flag
        self._installed = False

    def _ensure_db(self):
        """Create database tables if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS crash_reports (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    crash_hash TEXT NOT NULL,
                    exception_type TEXT NOT NULL,
                    exception_message TEXT NOT NULL,
                    report_path TEXT NOT NULL,
                    submitted BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_crash_reports_timestamp
                ON crash_reports(timestamp DESC)
            """)

    def install(self):
        """Install global exception handler"""
        if self._installed:
            return

        sys.excepthook = self._exception_handler
        threading.excepthook = self._threading_exception_handler
        self._installed = True

    def uninstall(self):
        """Uninstall global exception handler"""
        if not self._installed:
            return

        sys.excepthook = self._original_excepthook
        self._installed = False

    def _exception_handler(self, exc_type, exc_value, exc_tb):
        """Handle unhandled exception in main thread"""
        # Create crash report
        report = self.on_crash(exc_type, exc_value, exc_tb)

        # Call original handler (to print to stderr)
        self._original_excepthook(exc_type, exc_value, exc_tb)

        # Show crash dialog (if in GUI mode)
        self._show_crash_dialog(report)

    def _threading_exception_handler(self, args):
        """Handle unhandled exception in threads"""
        exc_type = args.exc_type
        exc_value = args.exc_value
        exc_tb = args.exc_traceback

        # Create crash report
        report = self.on_crash(exc_type, exc_value, exc_tb)

        print(f"\n{'='*60}")
        print(f"CRASH IN THREAD: {args.thread.name}")
        print(f"{'='*60}")
        traceback.print_exception(exc_type, exc_value, exc_tb)
        print(f"\nCrash report saved: {report}")
        print(f"{'='*60}\n")

    def on_crash(self, exc_type, exc_value, exc_tb) -> str:
        """
        Handle unhandled exception

        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_tb: Exception traceback

        Returns:
            Path to crash report file
        """
        try:
            # Generate crash report
            report = CrashReport(
                id=self._generate_crash_id(),
                timestamp=datetime.now(),
                exception_type=exc_type.__name__ if exc_type else "Unknown",
                exception_message=str(exc_value),
                stack_trace=''.join(traceback.format_exception(exc_type, exc_value, exc_tb)),
                system_info=self._get_system_info(),
                memory_snapshot=self._get_memory_snapshot(),
                recent_actions=self._get_recent_actions(),
                app_version=self.app_version,
                crash_hash=self._compute_crash_hash(exc_type, exc_value, exc_tb)
            )

            # Save crash report
            report_path = self.save_crash_report(report)

            # Call custom handlers
            for handler in self._crash_handlers:
                try:
                    handler(report)
                except Exception as e:
                    print(f"Crash handler failed: {e}")

            return report_path

        except Exception as e:
            # Last resort error handling
            print(f"CRITICAL: Crash reporter failed: {e}")
            traceback.print_exc()
            return "crash-reporter-failed"

    def save_crash_report(self, crash: CrashReport) -> str:
        """
        Save crash report to file

        Args:
            crash: CrashReport to save

        Returns:
            Path to saved crash report
        """
        # Save to JSON file
        report_filename = f"crash_{crash.id}.json"
        report_path = os.path.join(self.crash_dir, report_filename)

        # Convert to dict and handle datetime
        report_dict = asdict(crash)
        report_dict['timestamp'] = crash.timestamp.isoformat()

        with open(report_path, 'w') as f:
            json.dump(report_dict, f, indent=2)

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO crash_reports (id, timestamp, crash_hash, exception_type, exception_message, report_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                crash.id,
                crash.timestamp.isoformat(),
                crash.crash_hash,
                crash.exception_type,
                crash.exception_message,
                report_path
            ))

        return report_path

    def get_crash_reports(self) -> List[CrashReport]:
        """
        Get list of crash reports

        Returns:
            List of CrashReport objects
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM crash_reports
                ORDER BY timestamp DESC
            """)

            reports = []
            for row in cursor.fetchall():
                # Load full report from file
                try:
                    with open(row['report_path'], 'r') as f:
                        report_dict = json.load(f)

                    report = CrashReport(
                        id=report_dict['id'],
                        timestamp=datetime.fromisoformat(report_dict['timestamp']),
                        exception_type=report_dict['exception_type'],
                        exception_message=report_dict['exception_message'],
                        stack_trace=report_dict['stack_trace'],
                        system_info=report_dict.get('system_info'),
                        memory_snapshot=report_dict.get('memory_snapshot'),
                        recent_actions=report_dict.get('recent_actions'),
                        app_version=report_dict.get('app_version', 'unknown'),
                        submitted=report_dict.get('submitted', False),
                        crash_hash=report_dict.get('crash_hash', '')
                    )
                    reports.append(report)
                except Exception as e:
                    print(f"Failed to load crash report {row['report_path']}: {e}")
                    continue

            return reports

    def submit_crash_report(self, report_id: str) -> bool:
        """
        Submit crash report (with user consent)

        Args:
            report_id: ID of crash report to submit

        Returns:
            True if submitted successfully
        """
        # Find crash report
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT report_path FROM crash_reports
                WHERE id = ?
            """, (report_id,))

            row = cursor.fetchone()
            if not row:
                return False

            report_path = row[0]

        # Load report
        try:
            with open(report_path, 'r') as f:
                report_dict = json.load(f)
        except Exception as e:
            print(f"Failed to load crash report: {e}")
            return False

        # Anonymize report (remove any PII)
        anonymized_report = self._anonymize_report(report_dict)

        # Submit to server (if configured)
        submit_url = os.getenv("CRASH_REPORT_URL")
        if submit_url:
            try:
                import requests
                response = requests.post(
                    submit_url,
                    json=anonymized_report,
                    timeout=30
                )
                response.raise_for_status()

                # Mark as submitted
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE crash_reports
                        SET submitted = 1
                        WHERE id = ?
                    """, (report_id,))

                return True

            except Exception as e:
                print(f"Failed to submit crash report: {e}")
                return False
        else:
            print("No crash report URL configured")
            return False

    def add_crash_handler(self, handler: Callable[[CrashReport], None]):
        """
        Add custom crash handler

        Args:
            handler: Function that takes a CrashReport
        """
        self._crash_handlers.append(handler)

    def _generate_crash_id(self) -> str:
        """Generate unique crash ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{os.getpid()}"

    def _compute_crash_hash(self, exc_type, exc_value, exc_tb) -> str:
        """Compute hash for crash deduplication"""
        stack_trace = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))

        # Use exception type and relevant stack frames
        lines = stack_trace.split('\n')
        relevant_lines = [
            line for line in lines
            if 'File' in line or 'Error' in line or 'Exception' in line
        ][:10]

        hash_input = f"{exc_type.__name__ if exc_type else 'Unknown'}:{':'.join(relevant_lines)}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            return {
                "os": platform.system(),
                "os_version": platform.version(),
                "os_release": platform.release(),
                "python_version": platform.python_version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_memory_snapshot(self) -> Dict[str, Any]:
        """Get memory usage snapshot"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            virtual_memory = psutil.virtual_memory()

            return {
                "process_rss_mb": memory_info.rss / (1024 * 1024),
                "process_vms_mb": memory_info.vms / (1024 * 1024),
                "system_total_mb": virtual_memory.total / (1024 * 1024),
                "system_available_mb": virtual_memory.available / (1024 * 1024),
                "system_percent": virtual_memory.percent,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_recent_actions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent actions from audit log"""
        try:
            if not os.path.exists(self.audit_log_path):
                return []

            with sqlite3.connect(self.audit_log_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT timestamp, action, entity_type, details
                    FROM audit_log
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))

                actions = []
                for row in cursor.fetchall():
                    actions.append({
                        "timestamp": row['timestamp'],
                        "action": row['action'],
                        "entity_type": row['entity_type'],
                        "details": row['details']
                    })

                return actions

        except Exception as e:
            return [{"error": str(e)}]

    def _anonymize_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize crash report (remove PII)

        Args:
            report: Original crash report

        Returns:
            Anonymized crash report
        """
        anonymized = report.copy()

        # Remove system identifiers
        if 'system_info' in anonymized:
            system_info = anonymized['system_info'].copy()
            system_info.pop('hostname', None)
            anonymized['system_info'] = system_info

        # Anonymize recent actions
        if 'recent_actions' in anonymized:
            for action in anonymized['recent_actions']:
                # Remove any details that might contain patient info
                if 'details' in action:
                    action['details'] = '[REDACTED]'

        # Anonymize stack trace (remove file paths)
        if 'stack_trace' in anonymized:
            stack_lines = anonymized['stack_trace'].split('\n')
            anonymized_lines = []
            for line in stack_lines:
                # Replace absolute paths with relative paths
                if 'File "' in line:
                    # Extract just the filename
                    parts = line.split('File "')
                    if len(parts) > 1:
                        path = parts[1].split('"')[0]
                        filename = os.path.basename(path)
                        line = line.replace(path, filename)
                anonymized_lines.append(line)
            anonymized['stack_trace'] = '\n'.join(anonymized_lines)

        return anonymized

    def _show_crash_dialog(self, report_path: str):
        """Show crash dialog to user (GUI mode)"""
        # This would be implemented with Flet UI
        # For now, just print to console
        print("\n" + "="*60)
        print("DocAssist EMR has crashed")
        print("="*60)
        print(f"\nCrash report saved to: {report_path}")
        print("\nPlease report this issue to the developers.")
        print("You can find crash reports in the data/crash_reports directory.")
        print("\n" + "="*60 + "\n")

    def cleanup_old_reports(self, days: int = 90):
        """
        Clean up old crash reports

        Args:
            days: Keep reports from last N days
        """
        cutoff = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            # Get old reports
            cursor = conn.execute("""
                SELECT id, report_path FROM crash_reports
                WHERE timestamp < ?
            """, (cutoff.isoformat(),))

            # Delete files and database entries
            for row in cursor.fetchall():
                report_path = row[1]
                if os.path.exists(report_path):
                    os.remove(report_path)

            conn.execute("""
                DELETE FROM crash_reports
                WHERE timestamp < ?
            """, (cutoff.isoformat(),))


from datetime import timedelta
