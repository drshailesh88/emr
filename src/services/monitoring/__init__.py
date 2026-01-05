"""
Production monitoring and alerting system for DocAssist EMR.

This module provides comprehensive monitoring capabilities including:
- Error tracking and reporting
- Health checks for all services
- Performance monitoring
- Metrics collection
- Alerting on critical issues
- Crash reporting and recovery

Usage:
    from src.services.monitoring import MonitoringSystem

    # Initialize monitoring
    monitoring = MonitoringSystem()
    monitoring.start()

    # Use decorators
    from src.services.monitoring.decorators import monitor_all

    @monitor_all("save_prescription")
    def save_prescription(data):
        ...

    # Manual monitoring
    with monitoring.performance.measure("complex_operation"):
        do_complex_work()

    # Get dashboard data
    dashboard_data = monitoring.dashboard.get_dashboard_data("24h")
"""

from typing import Optional

# Core monitoring components
from .error_tracker import ErrorTracker, ErrorSummary, Transaction
from .health_checker import HealthChecker, HealthStatus, HealthReport, ServiceHealth, SystemInfo
from .metrics_collector import MetricsCollector, Metric, Percentiles, MetricSummary
from .alerting import AlertingService, AlertConfig, Alert, Severity
from .crash_reporter import CrashReporter, CrashReport
from .performance_monitor import PerformanceMonitor, SlowOperation, PerformanceReport
from .dashboard_data import MonitoringDashboard, DashboardData

# Decorators
from .decorators import (
    set_monitoring_instances,
    monitor_performance,
    capture_errors,
    alert_on_failure,
    count_calls,
    measure_and_alert,
    retry_with_monitoring,
    monitor_all
)


# Global monitoring instance
_monitoring_system: Optional['MonitoringSystem'] = None


class MonitoringSystem:
    """
    Unified monitoring system for DocAssist EMR

    Provides access to all monitoring components through a single interface.
    """

    def __init__(
        self,
        db_path: str = "data/monitoring.db",
        clinic_db_path: str = "data/clinic.db",
        backup_db_path: str = "data/backup_metadata.db",
        audit_log_path: str = "data/audit.db",
        crash_dir: str = "data/crash_reports",
        ollama_url: str = "http://localhost:11434",
        app_version: str = "1.0.0",
        alert_config: AlertConfig = None
    ):
        """
        Initialize monitoring system

        Args:
            db_path: Path to monitoring database
            clinic_db_path: Path to main clinic database
            backup_db_path: Path to backup metadata database
            audit_log_path: Path to audit log database
            crash_dir: Directory for crash reports
            ollama_url: URL for Ollama API
            app_version: Application version
            alert_config: Alert configuration
        """
        # Initialize all components
        self.error_tracker = ErrorTracker(
            db_path=db_path,
            app_version=app_version
        )

        self.health_checker = HealthChecker(
            db_path=clinic_db_path,
            backup_db_path=backup_db_path,
            ollama_url=ollama_url
        )

        self.metrics = MetricsCollector(db_path=db_path)

        self.alerting = AlertingService(
            db_path=db_path,
            config=alert_config or AlertConfig()
        )

        self.crash_reporter = CrashReporter(
            db_path=db_path,
            crash_dir=crash_dir,
            app_version=app_version,
            audit_log_path=audit_log_path
        )

        self.performance = PerformanceMonitor()

        # Set global performance monitor
        from .performance_monitor import set_global_performance_monitor
        set_global_performance_monitor(self.performance)

        self.dashboard = MonitoringDashboard(
            error_tracker=self.error_tracker,
            health_checker=self.health_checker,
            metrics_collector=self.metrics,
            alerting_service=self.alerting,
            crash_reporter=self.crash_reporter,
            performance_monitor=self.performance
        )

        # Set global instances for decorators
        set_monitoring_instances(
            error_tracker=self.error_tracker,
            performance_monitor=self.performance,
            metrics_collector=self.metrics,
            alerting_service=self.alerting
        )

        # Track if system is started
        self._started = False

    def start(self):
        """Start all monitoring services"""
        if self._started:
            return

        # Install crash reporter
        self.crash_reporter.install()

        # Start performance monitor
        self.performance.start()

        self._started = True

    def stop(self):
        """Stop all monitoring services"""
        if not self._started:
            return

        # Uninstall crash reporter
        self.crash_reporter.uninstall()

        # Stop performance monitor
        self.performance.stop()

        # Flush metrics
        self.metrics.flush()

        self._started = False

    def is_healthy(self) -> bool:
        """Quick health check"""
        return self.health_checker.is_healthy()

    def get_summary(self) -> dict:
        """Get quick monitoring summary"""
        return self.dashboard.get_summary()

    def cleanup(self, days: int = 90):
        """
        Clean up old monitoring data

        Args:
            days: Keep data from last N days
        """
        self.error_tracker.cleanup_old_data(days)
        self.metrics.cleanup_old_data(days)
        self.alerting.cleanup_old_alerts(days // 3)  # Keep alerts for 1/3 the time
        self.crash_reporter.cleanup_old_reports(days)

    def aggregate_metrics(self):
        """Aggregate metrics for faster queries (run periodically)"""
        self.metrics.aggregate_hourly()

    def __enter__(self):
        """Context manager support"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.stop()
        return False


def get_monitoring_system() -> Optional[MonitoringSystem]:
    """Get global monitoring system instance"""
    return _monitoring_system


def init_monitoring(
    db_path: str = "data/monitoring.db",
    clinic_db_path: str = "data/clinic.db",
    app_version: str = "1.0.0",
    alert_config: AlertConfig = None,
    auto_start: bool = True
) -> MonitoringSystem:
    """
    Initialize global monitoring system

    Args:
        db_path: Path to monitoring database
        clinic_db_path: Path to clinic database
        app_version: Application version
        alert_config: Alert configuration
        auto_start: Automatically start monitoring

    Returns:
        MonitoringSystem instance
    """
    global _monitoring_system

    _monitoring_system = MonitoringSystem(
        db_path=db_path,
        clinic_db_path=clinic_db_path,
        app_version=app_version,
        alert_config=alert_config
    )

    if auto_start:
        _monitoring_system.start()

    return _monitoring_system


# Export all public classes
__all__ = [
    # Main system
    'MonitoringSystem',
    'init_monitoring',
    'get_monitoring_system',

    # Core components
    'ErrorTracker',
    'HealthChecker',
    'MetricsCollector',
    'AlertingService',
    'CrashReporter',
    'PerformanceMonitor',
    'MonitoringDashboard',

    # Data classes
    'ErrorSummary',
    'Transaction',
    'HealthStatus',
    'HealthReport',
    'ServiceHealth',
    'SystemInfo',
    'Metric',
    'Percentiles',
    'MetricSummary',
    'AlertConfig',
    'Alert',
    'Severity',
    'CrashReport',
    'SlowOperation',
    'PerformanceReport',
    'DashboardData',

    # Decorators
    'set_monitoring_instances',
    'monitor_performance',
    'capture_errors',
    'alert_on_failure',
    'count_calls',
    'measure_and_alert',
    'retry_with_monitoring',
    'monitor_all',
]
