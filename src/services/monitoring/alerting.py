"""
Alerting service for critical issues.

Sends alerts via multiple channels: notifications, email, Slack, etc.
"""

import os
import json
import sqlite3
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import platform
import threading


class Severity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"  # Immediate attention needed
    ERROR = "error"       # Investigation needed
    WARNING = "warning"   # Monitor situation
    INFO = "info"         # FYI


@dataclass
class AlertConfig:
    """Configuration for alert channels"""
    enable_notifications: bool = True
    enable_email: bool = False
    enable_slack: bool = False
    enable_webhook: bool = False

    # Email config
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: Optional[List[str]] = None

    # Slack config
    slack_webhook_url: Optional[str] = None

    # Custom webhook config
    webhook_url: Optional[str] = None

    # Rate limiting
    max_alerts_per_hour: int = 10
    deduplicate_window_minutes: int = 60


@dataclass
class Alert:
    """An alert instance"""
    id: Optional[int] = None
    timestamp: datetime = None
    severity: Severity = Severity.INFO
    title: str = ""
    message: str = ""
    context: Optional[Dict[str, Any]] = None
    channels_sent: Optional[List[str]] = None
    dedupe_key: Optional[str] = None


class AlertingService:
    """Send alerts on critical issues"""

    def __init__(self, db_path: str = "data/monitoring.db", config: AlertConfig = None):
        """
        Initialize alerting service

        Args:
            db_path: Path to SQLite database
            config: Alert configuration
        """
        self.db_path = db_path
        self.config = config or AlertConfig()
        self._ensure_db()

        # Custom alert handlers
        self._custom_handlers: List[Callable] = []

        # Lock for thread safety
        self._lock = threading.Lock()

    def _ensure_db(self):
        """Create database tables if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    context TEXT,
                    channels_sent TEXT,
                    dedupe_key TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp
                ON alerts(timestamp DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_dedupe
                ON alerts(dedupe_key, timestamp DESC)
            """)

    def configure(self, config: AlertConfig):
        """
        Configure alert channels

        Args:
            config: Alert configuration
        """
        self.config = config

    def alert(
        self,
        severity: Severity,
        title: str,
        message: str,
        context: Dict[str, Any] = None,
        dedupe_key: Optional[str] = None
    ):
        """
        Send alert

        Args:
            severity: Alert severity level
            title: Alert title
            message: Alert message
            context: Additional context
            dedupe_key: Optional key for deduplication
        """
        with self._lock:
            # Check rate limiting
            if not self._check_rate_limit():
                print(f"Alert rate limit exceeded, dropping alert: {title}")
                return

            # Check deduplication
            if dedupe_key and self._is_duplicate(dedupe_key):
                print(f"Duplicate alert suppressed: {title}")
                return

            # Create alert
            alert = Alert(
                timestamp=datetime.now(),
                severity=severity,
                title=title,
                message=message,
                context=context,
                dedupe_key=dedupe_key
            )

            # Send through channels
            channels_sent = []

            try:
                if self.config.enable_notifications:
                    self._send_notification(alert)
                    channels_sent.append("notification")
            except Exception as e:
                print(f"Failed to send notification: {e}")

            try:
                if self.config.enable_email and self.config.email_to:
                    self._send_email(alert)
                    channels_sent.append("email")
            except Exception as e:
                print(f"Failed to send email alert: {e}")

            try:
                if self.config.enable_slack and self.config.slack_webhook_url:
                    self._send_slack(alert)
                    channels_sent.append("slack")
            except Exception as e:
                print(f"Failed to send Slack alert: {e}")

            try:
                if self.config.enable_webhook and self.config.webhook_url:
                    self._send_webhook(alert)
                    channels_sent.append("webhook")
            except Exception as e:
                print(f"Failed to send webhook alert: {e}")

            # Call custom handlers
            for handler in self._custom_handlers:
                try:
                    handler(alert)
                    channels_sent.append("custom")
                except Exception as e:
                    print(f"Custom alert handler failed: {e}")

            # Store alert
            alert.channels_sent = channels_sent
            self._store_alert(alert)

    def alert_if_threshold(self, metric: str, value: float, threshold: float):
        """
        Alert if value exceeds threshold

        Args:
            metric: Metric name
            value: Current value
            threshold: Threshold value
        """
        if value > threshold:
            self.alert(
                severity=Severity.WARNING,
                title=f"{metric} exceeds threshold",
                message=f"{metric} is {value:.2f}, threshold is {threshold:.2f}",
                context={"metric": metric, "value": value, "threshold": threshold},
                dedupe_key=f"threshold:{metric}"
            )

    def add_handler(self, handler: Callable[[Alert], None]):
        """
        Add custom alert handler

        Args:
            handler: Function that takes an Alert and returns None
        """
        self._custom_handlers.append(handler)

    def _send_notification(self, alert: Alert):
        """Send system notification"""
        if platform.system() == "Darwin":
            # macOS
            os.system(f"""
                osascript -e 'display notification "{alert.message}" with title "{alert.title}"'
            """)
        elif platform.system() == "Linux":
            # Linux with notify-send
            os.system(f'notify-send "{alert.title}" "{alert.message}"')
        elif platform.system() == "Windows":
            # Windows with PowerShell
            try:
                import win10toast
                toaster = win10toast.ToastNotifier()
                toaster.show_toast(
                    alert.title,
                    alert.message,
                    duration=10,
                    threaded=True
                )
            except ImportError:
                # Fallback to basic notification
                print(f"[ALERT] {alert.title}: {alert.message}")

    def _send_email(self, alert: Alert):
        """Send email alert"""
        if not all([
            self.config.smtp_host,
            self.config.smtp_username,
            self.config.smtp_password,
            self.config.email_from,
            self.config.email_to
        ]):
            return

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
        msg['From'] = self.config.email_from
        msg['To'] = ', '.join(self.config.email_to)

        # Create email body
        text_body = f"""
DocAssist EMR Alert

Severity: {alert.severity.value.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{alert.title}

{alert.message}
"""

        if alert.context:
            text_body += f"\n\nContext:\n{json.dumps(alert.context, indent=2)}"

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: {self._get_severity_color(alert.severity)};">
        [{alert.severity.value.upper()}] {alert.title}
    </h2>
    <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>{alert.message}</p>
"""

        if alert.context:
            html_body += f"""
    <h3>Context</h3>
    <pre>{json.dumps(alert.context, indent=2)}</pre>
"""

        html_body += """
</body>
</html>
"""

        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Send email
        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
            server.starttls()
            server.login(self.config.smtp_username, self.config.smtp_password)
            server.send_message(msg)

    def _send_slack(self, alert: Alert):
        """Send Slack alert"""
        if not self.config.slack_webhook_url:
            return

        # Create Slack message
        color = {
            Severity.CRITICAL: "danger",
            Severity.ERROR: "danger",
            Severity.WARNING: "warning",
            Severity.INFO: "good"
        }.get(alert.severity, "warning")

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"[{alert.severity.value.upper()}] {alert.title}",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Time",
                            "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            "short": True
                        },
                        {
                            "title": "Severity",
                            "value": alert.severity.value.upper(),
                            "short": True
                        }
                    ],
                    "footer": "DocAssist EMR Monitoring",
                    "ts": int(alert.timestamp.timestamp())
                }
            ]
        }

        if alert.context:
            payload["attachments"][0]["fields"].append({
                "title": "Context",
                "value": f"```{json.dumps(alert.context, indent=2)}```",
                "short": False
            })

        # Send to Slack
        response = requests.post(
            self.config.slack_webhook_url,
            json=payload,
            timeout=10
        )
        response.raise_for_status()

    def _send_webhook(self, alert: Alert):
        """Send webhook alert"""
        if not self.config.webhook_url:
            return

        payload = {
            "timestamp": alert.timestamp.isoformat(),
            "severity": alert.severity.value,
            "title": alert.title,
            "message": alert.message,
            "context": alert.context or {}
        }

        response = requests.post(
            self.config.webhook_url,
            json=payload,
            timeout=10
        )
        response.raise_for_status()

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limit"""
        cutoff = datetime.now() - timedelta(hours=1)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM alerts
                WHERE timestamp >= ?
            """, (cutoff.isoformat(),))

            count = cursor.fetchone()[0]

        return count < self.config.max_alerts_per_hour

    def _is_duplicate(self, dedupe_key: str) -> bool:
        """Check if this is a duplicate alert"""
        cutoff = datetime.now() - timedelta(minutes=self.config.deduplicate_window_minutes)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM alerts
                WHERE dedupe_key = ? AND timestamp >= ?
            """, (dedupe_key, cutoff.isoformat()))

            count = cursor.fetchone()[0]

        return count > 0

    def _store_alert(self, alert: Alert):
        """Store alert in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO alerts (timestamp, severity, title, message, context, channels_sent, dedupe_key)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.timestamp.isoformat(),
                alert.severity.value,
                alert.title,
                alert.message,
                json.dumps(alert.context) if alert.context else None,
                json.dumps(alert.channels_sent) if alert.channels_sent else None,
                alert.dedupe_key
            ))

    def _get_severity_color(self, severity: Severity) -> str:
        """Get color for severity level"""
        return {
            Severity.CRITICAL: "#FF0000",
            Severity.ERROR: "#FF6600",
            Severity.WARNING: "#FFA500",
            Severity.INFO: "#0066FF"
        }.get(severity, "#999999")

    def get_recent_alerts(self, limit: int = 50) -> List[Alert]:
        """
        Get recent alerts

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of Alert objects
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM alerts
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            alerts = []
            for row in cursor.fetchall():
                alerts.append(Alert(
                    id=row['id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    severity=Severity(row['severity']),
                    title=row['title'],
                    message=row['message'],
                    context=json.loads(row['context']) if row['context'] else None,
                    channels_sent=json.loads(row['channels_sent']) if row['channels_sent'] else None,
                    dedupe_key=row['dedupe_key']
                ))

            return alerts

    def cleanup_old_alerts(self, days: int = 30):
        """
        Clean up old alerts

        Args:
            days: Keep alerts from last N days
        """
        cutoff = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM alerts WHERE timestamp < ?", (cutoff.isoformat(),))
            conn.execute("VACUUM")
