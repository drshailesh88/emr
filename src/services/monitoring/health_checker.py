"""
Health monitoring for all DocAssist services.

Checks database, LLM, disk space, memory, and backup status.
"""

import os
import sqlite3
import psutil
import platform
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ServiceHealth:
    """Health status of a service"""
    service_name: str
    status: HealthStatus
    response_time_ms: Optional[float] = None
    message: str = ""
    last_checked: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "service_name": self.service_name,
            "status": self.status.value,
            "response_time_ms": self.response_time_ms,
            "message": self.message,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "details": self.details or {}
        }


@dataclass
class HealthReport:
    """Overall health report"""
    timestamp: datetime
    overall_status: HealthStatus
    services: List[ServiceHealth]
    system_info: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "overall_status": self.overall_status.value,
            "services": [s.to_dict() for s in self.services],
            "system_info": self.system_info
        }


@dataclass
class SystemInfo:
    """System information"""
    os: str
    os_version: str
    python_version: str
    cpu_count: int
    total_memory_gb: float
    disk_total_gb: float
    disk_used_gb: float
    disk_free_gb: float
    uptime_hours: float


class HealthChecker:
    """Monitor health of all services"""

    def __init__(
        self,
        db_path: str = "data/clinic.db",
        backup_db_path: str = "data/backup_metadata.db",
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize health checker

        Args:
            db_path: Path to main database
            backup_db_path: Path to backup metadata database
            ollama_url: URL for Ollama API
        """
        self.db_path = db_path
        self.backup_db_path = backup_db_path
        self.ollama_url = ollama_url

    def check_all(self) -> HealthReport:
        """
        Check all services

        Returns:
            HealthReport with overall status
        """
        services = []

        # Check each service
        services.append(self.check_database())
        services.append(self.check_llm())
        services.append(self.check_disk_space())
        services.append(self.check_memory())
        services.append(self.check_backup_status())

        # Determine overall status
        status_priority = {
            HealthStatus.UNHEALTHY: 3,
            HealthStatus.DEGRADED: 2,
            HealthStatus.HEALTHY: 1
        }

        overall_status = HealthStatus.HEALTHY
        for service in services:
            if status_priority[service.status] > status_priority[overall_status]:
                overall_status = service.status

        return HealthReport(
            timestamp=datetime.now(),
            overall_status=overall_status,
            services=services,
            system_info=asdict(self.get_system_info())
        )

    def check_database(self) -> ServiceHealth:
        """
        Check database connectivity and performance

        Returns:
            ServiceHealth for database
        """
        start_time = datetime.now()

        try:
            # Check if database file exists
            if not os.path.exists(self.db_path):
                return ServiceHealth(
                    service_name="database",
                    status=HealthStatus.UNHEALTHY,
                    message="Database file not found",
                    last_checked=datetime.now()
                )

            # Try to connect and run a simple query
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM patients")
                patient_count = cursor.fetchone()[0]

                # Check database size
                db_size_mb = os.path.getsize(self.db_path) / (1024 * 1024)

                # Check if database is locked
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    conn.rollback()
                    is_locked = False
                except sqlite3.OperationalError:
                    is_locked = True

            response_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Determine status
            if is_locked:
                status = HealthStatus.DEGRADED
                message = "Database is locked"
            elif response_time_ms > 1000:
                status = HealthStatus.DEGRADED
                message = f"Slow response time: {response_time_ms:.0f}ms"
            else:
                status = HealthStatus.HEALTHY
                message = "Database is healthy"

            return ServiceHealth(
                service_name="database",
                status=status,
                response_time_ms=response_time_ms,
                message=message,
                last_checked=datetime.now(),
                details={
                    "patient_count": patient_count,
                    "size_mb": round(db_size_mb, 2),
                    "is_locked": is_locked
                }
            )

        except sqlite3.Error as e:
            return ServiceHealth(
                service_name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {str(e)}",
                last_checked=datetime.now()
            )

        except Exception as e:
            return ServiceHealth(
                service_name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Unexpected error: {str(e)}",
                last_checked=datetime.now()
            )

    def check_llm(self) -> ServiceHealth:
        """
        Check Ollama availability

        Returns:
            ServiceHealth for LLM service
        """
        start_time = datetime.now()

        try:
            # Check if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            response_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            if response.status_code == 200:
                models = response.json().get("models", [])

                # Check if required models are available
                model_names = [m.get("name", "") for m in models]
                has_qwen = any("qwen" in name.lower() for name in model_names)

                if not models:
                    status = HealthStatus.DEGRADED
                    message = "Ollama running but no models installed"
                elif not has_qwen:
                    status = HealthStatus.DEGRADED
                    message = "Required Qwen model not found"
                else:
                    status = HealthStatus.HEALTHY
                    message = "LLM service is healthy"

                return ServiceHealth(
                    service_name="llm",
                    status=status,
                    response_time_ms=response_time_ms,
                    message=message,
                    last_checked=datetime.now(),
                    details={
                        "model_count": len(models),
                        "models": model_names[:5]  # First 5 models
                    }
                )
            else:
                return ServiceHealth(
                    service_name="llm",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Ollama returned status {response.status_code}",
                    last_checked=datetime.now()
                )

        except requests.ConnectionError:
            return ServiceHealth(
                service_name="llm",
                status=HealthStatus.UNHEALTHY,
                message="Cannot connect to Ollama (not running?)",
                last_checked=datetime.now()
            )

        except requests.Timeout:
            return ServiceHealth(
                service_name="llm",
                status=HealthStatus.DEGRADED,
                message="Ollama is slow to respond",
                last_checked=datetime.now()
            )

        except Exception as e:
            return ServiceHealth(
                service_name="llm",
                status=HealthStatus.UNHEALTHY,
                message=f"Unexpected error: {str(e)}",
                last_checked=datetime.now()
            )

    def check_disk_space(self) -> ServiceHealth:
        """
        Check available disk space

        Returns:
            ServiceHealth for disk space
        """
        try:
            # Get disk usage for data directory
            data_dir = Path(self.db_path).parent
            disk_usage = psutil.disk_usage(str(data_dir))

            free_gb = disk_usage.free / (1024 ** 3)
            percent_used = disk_usage.percent

            # Determine status based on available space
            if free_gb < 1:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: Only {free_gb:.1f}GB free"
            elif free_gb < 5 or percent_used > 90:
                status = HealthStatus.DEGRADED
                message = f"Low disk space: {free_gb:.1f}GB free ({100-percent_used:.0f}% available)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Sufficient disk space: {free_gb:.1f}GB free"

            return ServiceHealth(
                service_name="disk_space",
                status=status,
                message=message,
                last_checked=datetime.now(),
                details={
                    "total_gb": round(disk_usage.total / (1024 ** 3), 2),
                    "used_gb": round(disk_usage.used / (1024 ** 3), 2),
                    "free_gb": round(free_gb, 2),
                    "percent_used": percent_used
                }
            )

        except Exception as e:
            return ServiceHealth(
                service_name="disk_space",
                status=HealthStatus.UNHEALTHY,
                message=f"Error checking disk space: {str(e)}",
                last_checked=datetime.now()
            )

    def check_memory(self) -> ServiceHealth:
        """
        Check available memory

        Returns:
            ServiceHealth for memory
        """
        try:
            memory = psutil.virtual_memory()

            available_gb = memory.available / (1024 ** 3)
            percent_used = memory.percent

            # Determine status based on available memory
            if available_gb < 0.5:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: Only {available_gb:.1f}GB RAM free"
            elif available_gb < 2 or percent_used > 90:
                status = HealthStatus.DEGRADED
                message = f"Low memory: {available_gb:.1f}GB free ({100-percent_used:.0f}% available)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Sufficient memory: {available_gb:.1f}GB free"

            return ServiceHealth(
                service_name="memory",
                status=status,
                message=message,
                last_checked=datetime.now(),
                details={
                    "total_gb": round(memory.total / (1024 ** 3), 2),
                    "used_gb": round(memory.used / (1024 ** 3), 2),
                    "available_gb": round(available_gb, 2),
                    "percent_used": percent_used
                }
            )

        except Exception as e:
            return ServiceHealth(
                service_name="memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Error checking memory: {str(e)}",
                last_checked=datetime.now()
            )

    def check_backup_status(self) -> ServiceHealth:
        """
        Check last backup time and status

        Returns:
            ServiceHealth for backup
        """
        try:
            # Check if backup database exists
            if not os.path.exists(self.backup_db_path):
                return ServiceHealth(
                    service_name="backup",
                    status=HealthStatus.DEGRADED,
                    message="No backups found (backup not configured?)",
                    last_checked=datetime.now()
                )

            # Get last backup info
            with sqlite3.connect(self.backup_db_path) as conn:
                cursor = conn.execute("""
                    SELECT timestamp, status, size_bytes
                    FROM backups
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                row = cursor.fetchone()

                if not row:
                    return ServiceHealth(
                        service_name="backup",
                        status=HealthStatus.DEGRADED,
                        message="No backups found",
                        last_checked=datetime.now()
                    )

                last_backup_time = datetime.fromisoformat(row[0])
                last_backup_status = row[1]
                last_backup_size_mb = row[2] / (1024 * 1024) if row[2] else 0

                # Check how old the last backup is
                hours_since_backup = (datetime.now() - last_backup_time).total_seconds() / 3600

                # Determine status
                if last_backup_status != "completed":
                    status = HealthStatus.UNHEALTHY
                    message = f"Last backup failed: {last_backup_status}"
                elif hours_since_backup > 48:
                    status = HealthStatus.DEGRADED
                    message = f"Last backup was {hours_since_backup:.0f} hours ago"
                elif hours_since_backup > 24:
                    status = HealthStatus.DEGRADED
                    message = f"Backup is {hours_since_backup:.0f} hours old"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Last backup {hours_since_backup:.0f} hours ago"

                return ServiceHealth(
                    service_name="backup",
                    status=status,
                    message=message,
                    last_checked=datetime.now(),
                    details={
                        "last_backup": last_backup_time.isoformat(),
                        "hours_since_backup": round(hours_since_backup, 1),
                        "last_backup_status": last_backup_status,
                        "last_backup_size_mb": round(last_backup_size_mb, 2)
                    }
                )

        except Exception as e:
            return ServiceHealth(
                service_name="backup",
                status=HealthStatus.DEGRADED,
                message=f"Error checking backup: {str(e)}",
                last_checked=datetime.now()
            )

    def get_system_info(self) -> SystemInfo:
        """
        Get system information

        Returns:
            SystemInfo with system details
        """
        try:
            import sys

            # Get disk usage for root
            disk_usage = psutil.disk_usage('/')

            # Get boot time
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime_hours = (datetime.now() - boot_time).total_seconds() / 3600

            return SystemInfo(
                os=platform.system(),
                os_version=platform.version(),
                python_version=platform.python_version(),
                cpu_count=psutil.cpu_count(),
                total_memory_gb=round(psutil.virtual_memory().total / (1024 ** 3), 2),
                disk_total_gb=round(disk_usage.total / (1024 ** 3), 2),
                disk_used_gb=round(disk_usage.used / (1024 ** 3), 2),
                disk_free_gb=round(disk_usage.free / (1024 ** 3), 2),
                uptime_hours=round(uptime_hours, 1)
            )

        except Exception as e:
            # Return minimal info if there's an error
            return SystemInfo(
                os=platform.system(),
                os_version="unknown",
                python_version=platform.python_version(),
                cpu_count=0,
                total_memory_gb=0,
                disk_total_gb=0,
                disk_used_gb=0,
                disk_free_gb=0,
                uptime_hours=0
            )

    def is_healthy(self) -> bool:
        """
        Quick check if system is healthy

        Returns:
            True if all critical services are healthy
        """
        report = self.check_all()
        return report.overall_status == HealthStatus.HEALTHY
