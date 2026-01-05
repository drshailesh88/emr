"""
Example usage of the DocAssist EMR monitoring system.

This file demonstrates how to use all monitoring components.
"""

import time
import random
from datetime import datetime

from src.services.monitoring import (
    init_monitoring,
    MonitoringSystem,
    AlertConfig,
    Severity
)
from src.services.monitoring.decorators import (
    monitor_all,
    monitor_performance,
    capture_errors,
    alert_on_failure,
    retry_with_monitoring,
    count_calls
)


# Example 1: Initialize monitoring system
def setup_monitoring():
    """Initialize monitoring with custom configuration"""

    # Configure alerts
    alert_config = AlertConfig(
        enable_notifications=True,
        enable_email=False,  # Set to True and configure SMTP in production
        enable_slack=False,   # Set to True and add webhook URL in production

        # Email config (for production)
        # smtp_host="smtp.gmail.com",
        # smtp_port=587,
        # smtp_username="alerts@docassist.com",
        # smtp_password="your-password",
        # email_from="alerts@docassist.com",
        # email_to=["admin@docassist.com"],

        # Slack config (for production)
        # slack_webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",

        # Rate limiting
        max_alerts_per_hour=10,
        deduplicate_window_minutes=60
    )

    # Initialize monitoring
    monitoring = init_monitoring(
        db_path="data/monitoring.db",
        clinic_db_path="data/clinic.db",
        app_version="1.0.0",
        alert_config=alert_config,
        auto_start=True
    )

    print("✓ Monitoring system initialized")
    return monitoring


# Example 2: Using decorators for automatic monitoring
@monitor_all("save_prescription", slow_threshold_ms=500)
def save_prescription(patient_id: int, prescription_data: dict):
    """Example function with complete monitoring"""
    print(f"Saving prescription for patient {patient_id}...")

    # Simulate work
    time.sleep(random.uniform(0.1, 0.8))

    # Simulate occasional errors
    if random.random() < 0.1:  # 10% error rate
        raise ValueError("Invalid prescription data")

    return {"id": 123, "status": "saved"}


@monitor_performance("generate_prescription")
def generate_prescription_with_llm(symptoms: str):
    """Example function with performance monitoring only"""
    print(f"Generating prescription for symptoms: {symptoms}...")

    # Simulate LLM call
    time.sleep(random.uniform(0.5, 2.0))

    return {"medications": ["Paracetamol 500mg"]}


@capture_errors
def risky_database_operation():
    """Example function with error capture only"""
    # Simulate database work
    if random.random() < 0.2:  # 20% error rate
        raise ConnectionError("Database connection lost")

    return "success"


@alert_on_failure(severity=Severity.CRITICAL)
def critical_backup_operation():
    """Example function that sends alert on failure"""
    # Simulate backup
    if random.random() < 0.05:  # 5% error rate
        raise Exception("Backup failed - disk full")

    return "backup_complete"


@retry_with_monitoring(max_attempts=3, delay_seconds=0.5)
def flaky_external_api():
    """Example function with automatic retry and monitoring"""
    # Simulate flaky API
    if random.random() < 0.6:  # 60% failure rate
        raise ConnectionError("API temporarily unavailable")

    return {"status": "success"}


@count_calls("prescription_pdf_generated")
def generate_prescription_pdf(prescription_id: int):
    """Example function that counts calls"""
    print(f"Generating PDF for prescription {prescription_id}...")
    time.sleep(0.2)
    return f"prescription_{prescription_id}.pdf"


# Example 3: Manual monitoring
def manual_monitoring_example(monitoring: MonitoringSystem):
    """Example of manual monitoring without decorators"""

    # Set user context
    monitoring.error_tracker.set_user(
        "doctor_123",
        {"name": "Dr. Sharma", "specialty": "Cardiology"}
    )
    monitoring.error_tracker.set_tag("clinic_id", "clinic_001")

    # Measure performance manually
    with monitoring.performance.measure("load_patient_records"):
        print("Loading patient records...")
        time.sleep(0.3)

    # Record metrics manually
    monitoring.metrics.record_timing("search_latency_ms", 125.5)
    monitoring.metrics.record_count("patients_created", 1)
    monitoring.metrics.record_gauge("memory_usage_mb", 512.3)

    # Start a transaction
    with monitoring.error_tracker.start_transaction("save_visit", "db.operation") as transaction:
        transaction.set_tag("patient_id", "12345")
        print("Saving visit...")
        time.sleep(0.2)

    # Capture an error manually
    try:
        raise ValueError("Example error")
    except Exception as e:
        monitoring.error_tracker.capture_exception(e, context={
            "operation": "test",
            "patient_id": "12345"
        })

    # Send an alert manually
    monitoring.alerting.alert(
        severity=Severity.WARNING,
        title="High memory usage detected",
        message="Memory usage is above 80%",
        context={"memory_percent": 85.2},
        dedupe_key="memory:high"
    )

    print("✓ Manual monitoring examples completed")


# Example 4: Health checks
def health_check_example(monitoring: MonitoringSystem):
    """Example of health checks"""

    print("\n=== Health Check ===")

    # Quick health check
    is_healthy = monitoring.is_healthy()
    print(f"System healthy: {is_healthy}")

    # Detailed health report
    report = monitoring.health_checker.check_all()
    print(f"Overall status: {report.overall_status.value}")

    for service in report.services:
        status_emoji = "✓" if service.status.value == "healthy" else "✗"
        print(f"  {status_emoji} {service.service_name}: {service.status.value} - {service.message}")

    # Check individual services
    db_health = monitoring.health_checker.check_database()
    if db_health.details:
        print(f"\nDatabase details:")
        print(f"  Patient count: {db_health.details.get('patient_count', 0)}")
        print(f"  Size: {db_health.details.get('size_mb', 0):.2f} MB")


# Example 5: Error summary
def error_summary_example(monitoring: MonitoringSystem):
    """Example of error tracking and summary"""

    print("\n=== Error Summary ===")

    # Get error summary for different periods
    for period in ["1h", "24h"]:
        summary = monitoring.error_tracker.get_error_summary(period)
        print(f"\n{period}:")
        print(f"  Total errors: {summary.total_errors}")
        print(f"  Unique errors: {summary.unique_errors}")
        print(f"  Error rate: {summary.error_rate:.2f} per hour")

        if summary.top_errors:
            print(f"  Top errors:")
            for error in summary.top_errors[:3]:
                print(f"    - {error['type']}: {error['message'][:50]}... ({error['count']} times)")


# Example 6: Performance report
def performance_report_example(monitoring: MonitoringSystem):
    """Example of performance reporting"""

    print("\n=== Performance Report ===")

    report = monitoring.performance.get_performance_report("1h")

    print(f"Total operations: {report.total_operations}")
    print(f"Slow operations: {report.slow_operations}")
    print(f"Average duration: {report.avg_duration_ms:.2f}ms")
    print(f"Percentiles:")
    print(f"  P50: {report.p50_ms:.2f}ms")
    print(f"  P90: {report.p90_ms:.2f}ms")
    print(f"  P95: {report.p95_ms:.2f}ms")
    print(f"  P99: {report.p99_ms:.2f}ms")

    if report.slowest_operations:
        print(f"\nSlowest operations:")
        for op in report.slowest_operations[:5]:
            print(f"  - {op.operation}: {op.duration_ms:.0f}ms at {op.timestamp.strftime('%H:%M:%S')}")


# Example 7: Metrics and percentiles
def metrics_example(monitoring: MonitoringSystem):
    """Example of metrics collection and analysis"""

    print("\n=== Metrics ===")

    # Get metric summary
    summary = monitoring.metrics.get_summary("save_prescription", "1h")
    if summary:
        print(f"save_prescription (last hour):")
        print(f"  Count: {summary.count}")
        print(f"  Mean: {summary.mean:.2f}ms")
        print(f"  Min: {summary.min:.2f}ms")
        print(f"  Max: {summary.max:.2f}ms")

    # Get percentiles
    percentiles = monitoring.metrics.get_percentiles("save_prescription", "1h")
    if percentiles:
        print(f"  P50: {percentiles.p50:.2f}ms")
        print(f"  P90: {percentiles.p90:.2f}ms")
        print(f"  P99: {percentiles.p99:.2f}ms")

    # Get all metric names
    all_metrics = monitoring.metrics.get_all_metric_names()
    print(f"\nTracked metrics: {', '.join(all_metrics[:10])}")


# Example 8: Dashboard and summary
def dashboard_example(monitoring: MonitoringSystem):
    """Example of dashboard data"""

    print("\n=== Dashboard Summary ===")

    summary = monitoring.get_summary()
    print(f"Health score: {summary['health_score']}/100")
    print(f"Status: {summary['status']}")
    print(f"Errors (24h): {summary['errors_last_24h']}")
    print(f"Error rate: {summary['error_rate']:.2f}/hour")
    print(f"Avg response time: {summary['avg_response_time_ms']:.2f}ms")
    print(f"CPU: {summary['current_cpu_percent']:.1f}%")
    print(f"Memory: {summary['current_memory_mb']:.1f} MB")

    # Get full dashboard data
    dashboard_data = monitoring.dashboard.get_dashboard_data("24h")

    # Export to JSON (optional)
    # monitoring.dashboard.export_json("monitoring_report.json", "24h")

    # Generate text report
    report = monitoring.dashboard.generate_report("24h")
    print("\n=== Full Report ===")
    print(report)


# Main example
def main():
    """Run all examples"""

    print("DocAssist EMR Monitoring System - Examples\n")

    # Initialize monitoring
    monitoring = setup_monitoring()

    # Simulate some activity
    print("\n=== Simulating Activity ===")

    # Run monitored functions
    for i in range(10):
        try:
            save_prescription(i, {"medication": "Test"})
        except Exception as e:
            print(f"  Error in save_prescription: {e}")

        try:
            generate_prescription_with_llm("headache")
        except Exception:
            pass

        try:
            generate_prescription_pdf(i)
        except Exception:
            pass

        if i % 3 == 0:
            try:
                risky_database_operation()
            except Exception as e:
                print(f"  Error in database operation: {e}")

        if i % 5 == 0:
            try:
                flaky_external_api()
            except Exception as e:
                print(f"  Error in API call: {e}")

    print("✓ Activity simulation completed")

    # Manual monitoring examples
    manual_monitoring_example(monitoring)

    # Wait a bit for metrics to be recorded
    time.sleep(1)

    # Run examples
    health_check_example(monitoring)
    error_summary_example(monitoring)
    performance_report_example(monitoring)
    metrics_example(monitoring)
    dashboard_example(monitoring)

    # Cleanup
    print("\n=== Cleanup ===")
    monitoring.stop()
    print("✓ Monitoring stopped")


if __name__ == "__main__":
    main()
