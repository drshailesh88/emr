"""
Monitoring decorators for easy integration.

Provides decorators to automatically monitor functions for performance, errors, and alerts.
"""

import functools
import time
from typing import Optional, Callable, Any
from datetime import datetime

from .error_tracker import ErrorTracker
from .performance_monitor import PerformanceMonitor
from .metrics_collector import MetricsCollector
from .alerting import AlertingService, Severity


# Global monitoring instances (set by application)
_error_tracker: Optional[ErrorTracker] = None
_performance_monitor: Optional[PerformanceMonitor] = None
_metrics_collector: Optional[MetricsCollector] = None
_alerting_service: Optional[AlertingService] = None


def set_monitoring_instances(
    error_tracker: ErrorTracker = None,
    performance_monitor: PerformanceMonitor = None,
    metrics_collector: MetricsCollector = None,
    alerting_service: AlertingService = None
):
    """
    Set global monitoring instances

    Args:
        error_tracker: ErrorTracker instance
        performance_monitor: PerformanceMonitor instance
        metrics_collector: MetricsCollector instance
        alerting_service: AlertingService instance
    """
    global _error_tracker, _performance_monitor, _metrics_collector, _alerting_service

    if error_tracker:
        _error_tracker = error_tracker
    if performance_monitor:
        _performance_monitor = performance_monitor
    if metrics_collector:
        _metrics_collector = metrics_collector
    if alerting_service:
        _alerting_service = alerting_service


def monitor_performance(operation_name: Optional[str] = None):
    """
    Decorator to monitor function performance

    Args:
        operation_name: Custom operation name (uses function name if not provided)

    Usage:
        @monitor_performance("save_prescription")
        def save_prescription(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Record to performance monitor
                if _performance_monitor:
                    _performance_monitor._record_operation(
                        operation=op_name,
                        duration_ms=duration_ms,
                        failed=False
                    )

                # Record to metrics collector
                if _metrics_collector:
                    _metrics_collector.record_timing(op_name, duration_ms)

                return result

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Record failed operation
                if _performance_monitor:
                    _performance_monitor._record_operation(
                        operation=op_name,
                        duration_ms=duration_ms,
                        failed=True
                    )

                raise

        return wrapper
    return decorator


def capture_errors(context_func: Optional[Callable] = None):
    """
    Decorator to capture and report errors

    Args:
        context_func: Optional function to generate context dict

    Usage:
        @capture_errors
        def risky_function():
            ...

        # With context
        @capture_errors(context_func=lambda: {"patient_id": current_patient_id})
        def process_patient():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Generate context
                context = {}
                if context_func:
                    try:
                        context = context_func()
                    except Exception:
                        pass

                # Add function info to context
                context['function'] = func.__name__
                context['module'] = func.__module__

                # Capture exception
                if _error_tracker:
                    _error_tracker.capture_exception(e, context)

                # Re-raise
                raise

        return wrapper
    return decorator


def alert_on_failure(
    severity: Severity = Severity.ERROR,
    title_template: Optional[str] = None,
    message_template: Optional[str] = None
):
    """
    Decorator to send alert if function fails

    Args:
        severity: Alert severity level
        title_template: Alert title template (can use {function_name})
        message_template: Alert message template (can use {function_name}, {error})

    Usage:
        @alert_on_failure(severity=Severity.CRITICAL)
        def critical_function():
            ...

        @alert_on_failure(
            severity=Severity.ERROR,
            title_template="Failed to {function_name}",
            message_template="Error in {function_name}: {error}"
        )
        def important_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Generate title and message
                title = title_template or f"Function failed: {func.__name__}"
                message = message_template or f"Error in {func.__name__}: {str(e)}"

                # Format templates
                title = title.format(function_name=func.__name__)
                message = message.format(function_name=func.__name__, error=str(e))

                # Send alert
                if _alerting_service:
                    _alerting_service.alert(
                        severity=severity,
                        title=title,
                        message=message,
                        context={
                            'function': func.__name__,
                            'module': func.__module__,
                            'error_type': type(e).__name__
                        },
                        dedupe_key=f"failure:{func.__module__}.{func.__name__}"
                    )

                # Re-raise
                raise

        return wrapper
    return decorator


def count_calls(metric_name: Optional[str] = None, tags: dict = None):
    """
    Decorator to count function calls

    Args:
        metric_name: Metric name (uses function name if not provided)
        tags: Optional tags for the metric

    Usage:
        @count_calls("prescriptions_generated")
        def generate_prescription():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            metric = metric_name or f"{func.__name__}_calls"

            # Count the call
            if _metrics_collector:
                _metrics_collector.record_count(metric, 1, tags)

            return func(*args, **kwargs)

        return wrapper
    return decorator


def measure_and_alert(
    operation_name: Optional[str] = None,
    slow_threshold_ms: float = 1000.0,
    alert_severity: Severity = Severity.WARNING
):
    """
    Combined decorator: measure performance and alert if slow

    Args:
        operation_name: Custom operation name
        slow_threshold_ms: Threshold for slow operation alert
        alert_severity: Severity for slow operation alert

    Usage:
        @measure_and_alert("load_patient_data", slow_threshold_ms=500)
        def load_patient_data(patient_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Record performance
                if _performance_monitor:
                    _performance_monitor._record_operation(
                        operation=op_name,
                        duration_ms=duration_ms,
                        failed=False
                    )

                if _metrics_collector:
                    _metrics_collector.record_timing(op_name, duration_ms)

                # Alert if slow
                if duration_ms > slow_threshold_ms and _alerting_service:
                    _alerting_service.alert(
                        severity=alert_severity,
                        title=f"Slow operation: {op_name}",
                        message=f"{op_name} took {duration_ms:.0f}ms (threshold: {slow_threshold_ms}ms)",
                        context={
                            'operation': op_name,
                            'duration_ms': duration_ms,
                            'threshold_ms': slow_threshold_ms
                        },
                        dedupe_key=f"slow:{op_name}"
                    )

                return result

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Record failed operation
                if _performance_monitor:
                    _performance_monitor._record_operation(
                        operation=op_name,
                        duration_ms=duration_ms,
                        failed=True
                    )

                raise

        return wrapper
    return decorator


def retry_with_monitoring(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff: float = 2.0,
    alert_on_all_failures: bool = True
):
    """
    Decorator to retry failed operations with monitoring

    Args:
        max_attempts: Maximum number of attempts
        delay_seconds: Initial delay between retries
        backoff: Backoff multiplier for delay
        alert_on_all_failures: Alert if all retries fail

    Usage:
        @retry_with_monitoring(max_attempts=3, delay_seconds=1.0)
        def flaky_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay_seconds

            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)

                    # Log successful retry
                    if attempt > 1 and _metrics_collector:
                        _metrics_collector.record_count(
                            f"{func.__name__}_retry_success",
                            tags={'attempt': str(attempt)}
                        )

                    return result

                except Exception as e:
                    last_exception = e

                    # Log retry attempt
                    if _metrics_collector:
                        _metrics_collector.record_count(
                            f"{func.__name__}_retry_attempt",
                            tags={'attempt': str(attempt)}
                        )

                    # If this was the last attempt, break
                    if attempt == max_attempts:
                        break

                    # Wait before retrying
                    time.sleep(current_delay)
                    current_delay *= backoff

            # All attempts failed
            if _metrics_collector:
                _metrics_collector.record_count(f"{func.__name__}_retry_failed")

            # Send alert
            if alert_on_all_failures and _alerting_service:
                _alerting_service.alert(
                    severity=Severity.ERROR,
                    title=f"All retries failed: {func.__name__}",
                    message=f"{func.__name__} failed after {max_attempts} attempts: {str(last_exception)}",
                    context={
                        'function': func.__name__,
                        'attempts': max_attempts,
                        'error': str(last_exception)
                    },
                    dedupe_key=f"retry_failed:{func.__name__}"
                )

            # Raise the last exception
            raise last_exception

        return wrapper
    return decorator


def monitor_all(
    operation_name: Optional[str] = None,
    slow_threshold_ms: float = 1000.0,
    alert_on_failure: bool = True,
    alert_on_slow: bool = True
):
    """
    Complete monitoring decorator (performance + errors + alerts)

    Args:
        operation_name: Custom operation name
        slow_threshold_ms: Threshold for slow operation
        alert_on_failure: Send alert on failure
        alert_on_slow: Send alert on slow operation

    Usage:
        @monitor_all("save_prescription", slow_threshold_ms=500)
        def save_prescription(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Record performance
                if _performance_monitor:
                    _performance_monitor._record_operation(
                        operation=op_name,
                        duration_ms=duration_ms,
                        failed=False
                    )

                if _metrics_collector:
                    _metrics_collector.record_timing(op_name, duration_ms)
                    _metrics_collector.record_count(f"{op_name}_success")

                # Alert if slow
                if alert_on_slow and duration_ms > slow_threshold_ms and _alerting_service:
                    _alerting_service.alert(
                        severity=Severity.WARNING,
                        title=f"Slow operation: {op_name}",
                        message=f"{op_name} took {duration_ms:.0f}ms",
                        dedupe_key=f"slow:{op_name}"
                    )

                return result

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Record error
                if _performance_monitor:
                    _performance_monitor._record_operation(
                        operation=op_name,
                        duration_ms=duration_ms,
                        failed=True
                    )

                if _metrics_collector:
                    _metrics_collector.record_count(f"{op_name}_error")

                # Capture exception
                if _error_tracker:
                    _error_tracker.capture_exception(e, {
                        'operation': op_name,
                        'duration_ms': duration_ms
                    })

                # Send alert
                if alert_on_failure and _alerting_service:
                    _alerting_service.alert(
                        severity=Severity.ERROR,
                        title=f"Operation failed: {op_name}",
                        message=f"{op_name} failed: {str(e)}",
                        context={'error_type': type(e).__name__},
                        dedupe_key=f"failure:{op_name}"
                    )

                raise

        return wrapper
    return decorator
