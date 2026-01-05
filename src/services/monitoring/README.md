# DocAssist EMR Monitoring System

Production-grade monitoring and alerting system for DocAssist EMR.

## Features

- **Error Tracking**: Capture and track all errors with full context
- **Health Checks**: Monitor health of all services (database, LLM, disk, memory, backup)
- **Performance Monitoring**: Track operation timing and identify slow operations
- **Metrics Collection**: Collect and analyze application metrics
- **Alerting**: Send alerts via notifications, email, Slack, webhooks
- **Crash Reporting**: Handle crashes gracefully with detailed reports
- **Dashboard**: Unified view of all monitoring data

## Quick Start

```python
from src.services.monitoring import init_monitoring, monitor_all

# Initialize monitoring system
monitoring = init_monitoring(app_version="1.0.0")

# Use decorators for automatic monitoring
@monitor_all("save_prescription")
def save_prescription(data):
    # Your code here
    pass

# Get health status
if not monitoring.is_healthy():
    print("System is unhealthy!")

# Get summary
summary = monitoring.get_summary()
print(f"Health score: {summary['health_score']}")
```

## Components

### 1. Error Tracker

Captures exceptions and stores them locally, with optional Sentry integration.

```python
from src.services.monitoring import ErrorTracker

tracker = ErrorTracker(app_version="1.0.0")

# Set user context
tracker.set_user("doctor_123", {"name": "Dr. Smith"})

# Capture exception
try:
    risky_operation()
except Exception as e:
    tracker.capture_exception(e, context={"patient_id": "123"})

# Get error summary
summary = tracker.get_error_summary("24h")
print(f"Errors in last 24h: {summary.total_errors}")
```

### 2. Health Checker

Monitors health of all critical services.

```python
from src.services.monitoring import HealthChecker

checker = HealthChecker()

# Check all services
report = checker.check_all()
print(f"Overall status: {report.overall_status.value}")

# Check individual services
db_health = checker.check_database()
llm_health = checker.check_llm()
```

### 3. Metrics Collector

Collects timing, count, and gauge metrics.

```python
from src.services.monitoring import MetricsCollector

metrics = MetricsCollector()

# Record timing
metrics.record_timing("prescription_generation_ms", 1250.5)

# Record count
metrics.record_count("patients_created", 1)

# Record gauge (current value)
metrics.record_gauge("memory_usage_mb", 512.3)

# Get percentiles
percentiles = metrics.get_percentiles("prescription_generation_ms", "24h")
print(f"P90: {percentiles.p90}ms, P99: {percentiles.p99}ms")
```

### 4. Alerting Service

Send alerts through multiple channels.

```python
from src.services.monitoring import AlertingService, AlertConfig, Severity

config = AlertConfig(
    enable_email=True,
    smtp_host="smtp.gmail.com",
    smtp_username="your-email@gmail.com",
    smtp_password="your-password",
    email_from="alerts@docassist.com",
    email_to=["admin@docassist.com"]
)

alerting = AlertingService(config=config)

# Send alert
alerting.alert(
    severity=Severity.ERROR,
    title="Database connection lost",
    message="Cannot connect to database after 3 retries",
    context={"error": "Connection timeout"}
)

# Alert on threshold
alerting.alert_if_threshold("error_rate", value=5.2, threshold=5.0)
```

### 5. Crash Reporter

Handle crashes gracefully and create detailed reports.

```python
from src.services.monitoring import CrashReporter

reporter = CrashReporter(app_version="1.0.0")

# Install global exception handler
reporter.install()

# Get crash reports
crashes = reporter.get_crash_reports()

# Submit crash report (with user consent)
reporter.submit_crash_report(crash_id)
```

### 6. Performance Monitor

Track operation performance in real-time.

```python
from src.services.monitoring import PerformanceMonitor

monitor = PerformanceMonitor(slow_threshold_ms=1000)
monitor.start()

# Measure operation
with monitor.measure("complex_calculation"):
    result = complex_calculation()

# Get slow operations
slow_ops = monitor.get_slow_operations(threshold_ms=2000)

# Get performance report
report = monitor.get_performance_report("1h")
print(f"Avg duration: {report.avg_duration_ms}ms")
print(f"P90: {report.p90_ms}ms")
```

### 7. Monitoring Dashboard

Unified view of all monitoring data.

```python
from src.services.monitoring import MonitoringDashboard

dashboard = MonitoringDashboard(
    error_tracker=tracker,
    health_checker=checker,
    metrics_collector=metrics,
    alerting_service=alerting,
    crash_reporter=reporter,
    performance_monitor=monitor
)

# Get complete dashboard data
data = dashboard.get_dashboard_data("24h")

# Get summary
summary = dashboard.get_summary()

# Export to JSON
dashboard.export_json("monitoring_report.json", "24h")

# Generate text report
report = dashboard.generate_report("24h")
print(report)
```

## Decorators

Use decorators for automatic monitoring:

### @monitor_performance

```python
from src.services.monitoring.decorators import monitor_performance

@monitor_performance("save_prescription")
def save_prescription(data):
    # Automatically tracks timing and records metrics
    pass
```

### @capture_errors

```python
from src.services.monitoring.decorators import capture_errors

@capture_errors
def risky_operation():
    # Automatically captures and reports exceptions
    pass
```

### @alert_on_failure

```python
from src.services.monitoring.decorators import alert_on_failure
from src.services.monitoring import Severity

@alert_on_failure(severity=Severity.CRITICAL)
def critical_operation():
    # Sends alert if function fails
    pass
```

### @monitor_all (Recommended)

```python
from src.services.monitoring.decorators import monitor_all

@monitor_all("save_prescription", slow_threshold_ms=500)
def save_prescription(data):
    # Complete monitoring: performance + errors + alerts
    pass
```

### @retry_with_monitoring

```python
from src.services.monitoring.decorators import retry_with_monitoring

@retry_with_monitoring(max_attempts=3, delay_seconds=1.0)
def flaky_api_call():
    # Automatically retries with monitoring
    pass
```

## Configuration

### Environment Variables

```bash
# Sentry integration (optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project

# Crash reporting endpoint (optional)
CRASH_REPORT_URL=https://api.docassist.com/crash-reports

# Environment
ENVIRONMENT=production
```

### Alert Configuration

```python
from src.services.monitoring import AlertConfig

config = AlertConfig(
    enable_notifications=True,
    enable_email=True,
    enable_slack=True,

    # Email settings
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_username="alerts@docassist.com",
    smtp_password="your-password",
    email_from="alerts@docassist.com",
    email_to=["admin@docassist.com"],

    # Slack settings
    slack_webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",

    # Rate limiting
    max_alerts_per_hour=10,
    deduplicate_window_minutes=60
)
```

## Integration with DocAssist

Add to your main application:

```python
# main.py
from src.services.monitoring import init_monitoring, AlertConfig

def main():
    # Initialize monitoring
    alert_config = AlertConfig(
        enable_notifications=True,
        enable_email=True,
        smtp_host=os.getenv("SMTP_HOST"),
        smtp_username=os.getenv("SMTP_USERNAME"),
        smtp_password=os.getenv("SMTP_PASSWORD"),
        email_from=os.getenv("ALERT_EMAIL_FROM"),
        email_to=os.getenv("ALERT_EMAIL_TO", "").split(",")
    )

    monitoring = init_monitoring(
        app_version="1.0.0",
        alert_config=alert_config,
        auto_start=True
    )

    # Run periodic maintenance
    import schedule
    schedule.every().hour.do(monitoring.aggregate_metrics)
    schedule.every().day.do(lambda: monitoring.cleanup(days=90))

    # Your app code here
    app = DocAssistApp()
    app.run()

if __name__ == "__main__":
    main()
```

## Monitoring Best Practices

1. **Use Decorators**: Apply `@monitor_all` to all important functions
2. **Set Context**: Always set user context before operations
3. **Monitor Critical Paths**: Focus on user-facing operations
4. **Set Thresholds**: Define slow operation thresholds per operation
5. **Review Regularly**: Check dashboard daily for issues
6. **Clean Up**: Run cleanup regularly to manage disk space
7. **Alert Wisely**: Don't over-alert, use appropriate severity levels
8. **Aggregate Metrics**: Run hourly aggregation for better performance

## Database Schema

All monitoring data is stored in SQLite (`data/monitoring.db`):

- `errors` - Error tracking
- `messages` - Log messages
- `transactions` - Performance transactions
- `metrics` - Raw metrics data
- `metrics_hourly` - Aggregated hourly metrics
- `alerts` - Alert history
- `crash_reports` - Crash report metadata

## Maintenance

### Cleanup Old Data

```python
# Keep last 90 days of data
monitoring.cleanup(days=90)
```

### Aggregate Metrics

```python
# Run hourly for better performance
monitoring.aggregate_metrics()
```

### Health Check

```python
# Check if system is healthy
if not monitoring.is_healthy():
    # Take action
    pass
```

## Performance Impact

The monitoring system is designed to have minimal performance impact:

- Metrics are buffered and written in batches
- Performance monitoring uses efficient data structures
- Database operations are optimized with indexes
- Background threads handle system metrics collection
- Optional Sentry integration only sends data asynchronously

Typical overhead: < 1% CPU, < 50MB RAM

## Troubleshooting

### No alerts received

1. Check alert configuration
2. Verify SMTP/Slack credentials
3. Check rate limiting settings
4. Review logs for errors

### High disk usage

1. Run cleanup: `monitoring.cleanup(days=30)`
2. Reduce metric retention
3. Aggregate metrics hourly

### Performance overhead

1. Disable Sentry if not needed
2. Increase metric buffer size
3. Reduce monitoring frequency
4. Use decorators selectively

## License

Part of DocAssist EMR - Local-First AI-Powered EMR for Indian Doctors
