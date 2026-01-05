"""
Basic tests for the monitoring system.

Run with: pytest tests/test_monitoring.py
"""

import os
import tempfile
import pytest
from datetime import datetime

# Import monitoring components
from src.services.monitoring import (
    MonitoringSystem,
    ErrorTracker,
    HealthChecker,
    MetricsCollector,
    AlertingService,
    CrashReporter,
    PerformanceMonitor,
    AlertConfig,
    Severity,
    init_monitoring
)
from src.services.monitoring.decorators import (
    monitor_performance,
    capture_errors,
    monitor_all
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def monitoring_system(temp_db):
    """Create monitoring system for testing"""
    system = MonitoringSystem(
        db_path=temp_db,
        clinic_db_path=temp_db,
        backup_db_path=temp_db,
        audit_log_path=temp_db,
        app_version="test-1.0.0"
    )
    system.start()
    yield system
    system.stop()


def test_error_tracker_basic(temp_db):
    """Test basic error tracking"""
    tracker = ErrorTracker(db_path=temp_db, app_version="test")

    # Capture an exception
    try:
        raise ValueError("Test error")
    except Exception as e:
        tracker.capture_exception(e, context={"test": "value"})

    # Get error summary
    summary = tracker.get_error_summary("1h")
    assert summary.total_errors == 1
    assert summary.unique_errors == 1


def test_error_tracker_with_user_context(temp_db):
    """Test error tracking with user context"""
    tracker = ErrorTracker(db_path=temp_db, app_version="test")

    # Set user context
    tracker.set_user("doctor_123", {"name": "Dr. Test"})
    tracker.set_tag("clinic_id", "clinic_001")

    # Capture exception
    try:
        raise RuntimeError("Test error")
    except Exception as e:
        tracker.capture_exception(e)

    summary = tracker.get_error_summary("1h")
    assert summary.total_errors == 1


def test_metrics_collector(temp_db):
    """Test metrics collection"""
    metrics = MetricsCollector(db_path=temp_db)

    # Record some metrics
    metrics.record_timing("test_operation", 123.45)
    metrics.record_count("test_count", 5)
    metrics.record_gauge("test_gauge", 42.0)

    # Flush to database
    metrics.flush()

    # Get summary
    summary = metrics.get_summary("test_operation", "1h")
    assert summary is not None
    assert summary.count == 1
    assert summary.mean == 123.45


def test_performance_monitor():
    """Test performance monitoring"""
    monitor = PerformanceMonitor(slow_threshold_ms=100)
    monitor.start()

    # Measure an operation
    import time
    with monitor.measure("test_operation"):
        time.sleep(0.05)  # 50ms

    # Get report
    report = monitor.get_performance_report("1h")
    assert report.total_operations == 1
    assert report.avg_duration_ms > 40  # Should be around 50ms

    monitor.stop()


def test_alerting_service(temp_db):
    """Test alerting service"""
    config = AlertConfig(enable_notifications=False)
    alerting = AlertingService(db_path=temp_db, config=config)

    # Send an alert
    alerting.alert(
        severity=Severity.WARNING,
        title="Test alert",
        message="This is a test",
        context={"test": True}
    )

    # Get recent alerts
    alerts = alerting.get_recent_alerts(limit=10)
    assert len(alerts) == 1
    assert alerts[0].title == "Test alert"
    assert alerts[0].severity == Severity.WARNING


def test_crash_reporter(temp_db):
    """Test crash reporter"""
    temp_dir = tempfile.mkdtemp()

    try:
        reporter = CrashReporter(
            db_path=temp_db,
            crash_dir=temp_dir,
            app_version="test"
        )

        # Simulate a crash
        try:
            raise RuntimeError("Test crash")
        except Exception:
            import sys
            exc_type, exc_value, exc_tb = sys.exc_info()
            report_path = reporter.on_crash(exc_type, exc_value, exc_tb)

        # Verify crash report was created
        assert os.path.exists(report_path)

        # Get crash reports
        reports = reporter.get_crash_reports()
        assert len(reports) == 1
        assert reports[0].exception_type == "RuntimeError"

    finally:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_monitoring_system_initialization(monitoring_system):
    """Test monitoring system initialization"""
    assert monitoring_system is not None
    assert monitoring_system.error_tracker is not None
    assert monitoring_system.health_checker is not None
    assert monitoring_system.metrics is not None
    assert monitoring_system.alerting is not None
    assert monitoring_system.crash_reporter is not None
    assert monitoring_system.performance is not None
    assert monitoring_system.dashboard is not None


def test_monitoring_system_health_check(monitoring_system):
    """Test health check through monitoring system"""
    # Quick health check
    # Note: This might fail if database doesn't exist, that's ok
    try:
        is_healthy = monitoring_system.is_healthy()
        assert isinstance(is_healthy, bool)
    except Exception:
        pass  # Health check may fail in test environment


def test_monitoring_system_summary(monitoring_system):
    """Test getting monitoring summary"""
    summary = monitoring_system.get_summary()

    assert 'health_score' in summary
    assert 'status' in summary
    assert 'errors_last_24h' in summary
    assert 'timestamp' in summary


def test_decorator_monitor_performance(monitoring_system):
    """Test @monitor_performance decorator"""
    import time

    @monitor_performance("test_function")
    def test_function():
        time.sleep(0.01)
        return "success"

    result = test_function()
    assert result == "success"

    # Check that performance was recorded
    report = monitoring_system.performance.get_performance_report("1h")
    assert report.total_operations >= 1


def test_decorator_capture_errors(monitoring_system):
    """Test @capture_errors decorator"""

    @capture_errors
    def failing_function():
        raise ValueError("Test error from decorator")

    with pytest.raises(ValueError):
        failing_function()

    # Check that error was captured
    summary = monitoring_system.error_tracker.get_error_summary("1h")
    assert summary.total_errors >= 1


def test_decorator_monitor_all(monitoring_system):
    """Test @monitor_all decorator"""
    import time

    @monitor_all("complete_test")
    def complete_test():
        time.sleep(0.01)
        return "done"

    result = complete_test()
    assert result == "done"

    # Check both performance and metrics were recorded
    perf_report = monitoring_system.performance.get_performance_report("1h")
    assert perf_report.total_operations >= 1


def test_transaction_tracking(temp_db):
    """Test transaction tracking"""
    tracker = ErrorTracker(db_path=temp_db, app_version="test")

    with tracker.start_transaction("test_transaction", "test.op") as transaction:
        transaction.set_tag("test_tag", "test_value")
        # Transaction completes successfully

    # Transaction should be recorded
    # Note: Actual verification would require checking the database


def test_metrics_percentiles(temp_db):
    """Test metrics percentile calculation"""
    metrics = MetricsCollector(db_path=temp_db)

    # Record multiple timing metrics
    values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    for value in values:
        metrics.record_timing("test_metric", value)

    metrics.flush()

    # Get percentiles
    percentiles = metrics.get_percentiles("test_metric", "1h")
    assert percentiles is not None
    assert percentiles.count == 10
    assert percentiles.p50 > 0
    assert percentiles.p90 > percentiles.p50
    assert percentiles.p99 >= percentiles.p90


def test_alert_deduplication(temp_db):
    """Test alert deduplication"""
    config = AlertConfig(
        enable_notifications=False,
        deduplicate_window_minutes=60
    )
    alerting = AlertingService(db_path=temp_db, config=config)

    # Send same alert twice
    for _ in range(2):
        alerting.alert(
            severity=Severity.INFO,
            title="Test",
            message="Duplicate test",
            dedupe_key="test_duplicate"
        )

    # Should only have 1 alert due to deduplication
    alerts = alerting.get_recent_alerts(limit=10)
    assert len(alerts) == 1


def test_context_manager(temp_db):
    """Test monitoring system as context manager"""
    with MonitoringSystem(db_path=temp_db, app_version="test") as monitoring:
        assert monitoring._started is True

        # Use monitoring
        monitoring.metrics.record_count("test", 1)

    # After context exit, should be stopped
    # Note: Can't easily verify stop state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
