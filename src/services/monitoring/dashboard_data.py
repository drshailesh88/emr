"""
Monitoring dashboard data aggregation.

Provides unified interface to all monitoring data for dashboards and external tools.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from .error_tracker import ErrorTracker, ErrorSummary
from .health_checker import HealthChecker, HealthReport
from .metrics_collector import MetricsCollector
from .alerting import AlertingService, Alert
from .crash_reporter import CrashReporter, CrashReport
from .performance_monitor import PerformanceMonitor, PerformanceReport


@dataclass
class DashboardData:
    """Complete monitoring dashboard data"""
    timestamp: datetime
    health: Dict[str, Any]
    errors: Dict[str, Any]
    performance: Dict[str, Any]
    metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    crashes: Dict[str, Any]
    system: Dict[str, Any]


class MonitoringDashboard:
    """Aggregate all monitoring data"""

    def __init__(
        self,
        error_tracker: ErrorTracker,
        health_checker: HealthChecker,
        metrics_collector: MetricsCollector,
        alerting_service: AlertingService,
        crash_reporter: CrashReporter,
        performance_monitor: PerformanceMonitor
    ):
        """
        Initialize monitoring dashboard

        Args:
            error_tracker: ErrorTracker instance
            health_checker: HealthChecker instance
            metrics_collector: MetricsCollector instance
            alerting_service: AlertingService instance
            crash_reporter: CrashReporter instance
            performance_monitor: PerformanceMonitor instance
        """
        self.error_tracker = error_tracker
        self.health_checker = health_checker
        self.metrics_collector = metrics_collector
        self.alerting_service = alerting_service
        self.crash_reporter = crash_reporter
        self.performance_monitor = performance_monitor

    def get_dashboard_data(self, period: str = "24h") -> DashboardData:
        """
        Get complete dashboard data

        Args:
            period: Time period for statistics

        Returns:
            DashboardData with all monitoring information
        """
        # Health check
        health_report = self.health_checker.check_all()

        # Error summary
        error_summary = self.error_tracker.get_error_summary(period)

        # Performance report
        perf_report = self.performance_monitor.get_performance_report(period)

        # Recent alerts
        recent_alerts = self.alerting_service.get_recent_alerts(limit=10)

        # Crash reports
        crash_reports = self.crash_reporter.get_crash_reports()

        # Key metrics
        key_metrics = self._get_key_metrics(period)

        # System info
        system_info = self.health_checker.get_system_info()

        return DashboardData(
            timestamp=datetime.now(),
            health=health_report.to_dict(),
            errors={
                'period': error_summary.period,
                'total_errors': error_summary.total_errors,
                'unique_errors': error_summary.unique_errors,
                'error_rate': error_summary.error_rate,
                'top_errors': error_summary.top_errors[:5]
            },
            performance={
                'period': perf_report.period,
                'total_operations': perf_report.total_operations,
                'slow_operations': perf_report.slow_operations,
                'avg_duration_ms': round(perf_report.avg_duration_ms, 2),
                'p50_ms': round(perf_report.p50_ms, 2),
                'p90_ms': round(perf_report.p90_ms, 2),
                'p95_ms': round(perf_report.p95_ms, 2),
                'p99_ms': round(perf_report.p99_ms, 2),
                'cpu_usage_avg': round(perf_report.cpu_usage_avg, 2),
                'memory_usage_avg_mb': round(perf_report.memory_usage_avg_mb, 2),
                'slowest_operations': [
                    {
                        'operation': op.operation,
                        'duration_ms': round(op.duration_ms, 2),
                        'timestamp': op.timestamp.isoformat()
                    }
                    for op in perf_report.slowest_operations[:5]
                ]
            },
            metrics=key_metrics,
            alerts=[
                {
                    'severity': alert.severity.value,
                    'title': alert.title,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat()
                }
                for alert in recent_alerts
            ],
            crashes={
                'total': len(crash_reports),
                'recent': [
                    {
                        'id': crash.id,
                        'exception_type': crash.exception_type,
                        'exception_message': crash.exception_message[:100],
                        'timestamp': crash.timestamp.isoformat(),
                        'submitted': crash.submitted
                    }
                    for crash in crash_reports[:5]
                ]
            },
            system=asdict(system_info)
        )

    def _get_key_metrics(self, period: str) -> Dict[str, Any]:
        """Get key application metrics"""
        metrics = {}

        # Important metrics to track
        metric_names = [
            'consultation_duration_ms',
            'prescription_generation_ms',
            'search_latency_ms',
            'llm_response_ms',
            'patients_created',
            'visits_saved',
            'active_consultations',
            'memory_usage_mb'
        ]

        for name in metric_names:
            summary = self.metrics_collector.get_summary(name, period)
            if summary:
                metrics[name] = {
                    'count': summary.count,
                    'mean': round(summary.mean, 2),
                    'min': round(summary.min, 2),
                    'max': round(summary.max, 2)
                }

                # Add percentiles for timing metrics
                if 'ms' in name or 'latency' in name:
                    percentiles = self.metrics_collector.get_percentiles(name, period)
                    if percentiles:
                        metrics[name]['p50'] = round(percentiles.p50, 2)
                        metrics[name]['p90'] = round(percentiles.p90, 2)
                        metrics[name]['p99'] = round(percentiles.p99, 2)

        return metrics

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get quick health status

        Returns:
            Dictionary with overall health status
        """
        health_report = self.health_checker.check_all()

        return {
            'status': health_report.overall_status.value,
            'timestamp': health_report.timestamp.isoformat(),
            'services': {
                service.service_name: service.status.value
                for service in health_report.services
            }
        }

    def get_error_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get error trends over time

        Args:
            days: Number of days to analyze

        Returns:
            List of daily error counts
        """
        trends = []

        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)

            # This would need to be implemented in error_tracker
            # For now, return empty
            trends.append({
                'date': start.date().isoformat(),
                'total_errors': 0,
                'unique_errors': 0
            })

        return trends

    def get_performance_trends(self, metric: str, period: str = "24h") -> List[Dict[str, Any]]:
        """
        Get performance trends for a metric

        Args:
            metric: Metric name
            period: Time period

        Returns:
            List of time-series data points
        """
        return self.metrics_collector.get_timeseries(metric, period, bucket_size="1h")

    def export_json(self, filepath: str, period: str = "24h"):
        """
        Export dashboard data to JSON file

        Args:
            filepath: Path to save JSON file
            period: Time period for statistics
        """
        data = self.get_dashboard_data(period)

        # Convert to dict
        data_dict = {
            'timestamp': data.timestamp.isoformat(),
            'health': data.health,
            'errors': data.errors,
            'performance': data.performance,
            'metrics': data.metrics,
            'alerts': data.alerts,
            'crashes': data.crashes,
            'system': data.system
        }

        with open(filepath, 'w') as f:
            json.dump(data_dict, f, indent=2)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get quick summary of monitoring status

        Returns:
            Dictionary with key indicators
        """
        health = self.health_checker.check_all()
        errors = self.error_tracker.get_error_summary("24h")
        perf = self.performance_monitor.get_performance_report("1h")
        current_metrics = self.performance_monitor.get_current_metrics()

        # Determine overall health score (0-100)
        health_score = 100

        # Deduct points for issues
        if health.overall_status.value == "degraded":
            health_score -= 20
        elif health.overall_status.value == "unhealthy":
            health_score -= 50

        if errors.error_rate > 1:  # More than 1 error per hour
            health_score -= 10

        if perf.slow_operations > 10:
            health_score -= 10

        if current_metrics.get('memory_percent', 0) > 90:
            health_score -= 10

        health_score = max(0, health_score)

        return {
            'health_score': health_score,
            'status': health.overall_status.value,
            'errors_last_24h': errors.total_errors,
            'error_rate': round(errors.error_rate, 2),
            'avg_response_time_ms': round(perf.avg_duration_ms, 2),
            'slow_operations_last_hour': perf.slow_operations,
            'current_cpu_percent': round(current_metrics.get('cpu_percent', 0), 1),
            'current_memory_mb': round(current_metrics.get('memory_mb', 0), 1),
            'timestamp': datetime.now().isoformat()
        }

    def check_alerts(self):
        """Check for conditions that require alerts"""
        # Get current status
        health = self.health_checker.check_all()
        perf = self.performance_monitor.get_performance_report("1h")
        current_metrics = self.performance_monitor.get_current_metrics()

        # Alert on unhealthy services
        for service in health.services:
            if service.status.value == "unhealthy":
                self.alerting_service.alert(
                    severity=AlertingService.Severity.ERROR,
                    title=f"Service unhealthy: {service.service_name}",
                    message=service.message,
                    dedupe_key=f"service:{service.service_name}"
                )
            elif service.status.value == "degraded":
                self.alerting_service.alert(
                    severity=AlertingService.Severity.WARNING,
                    title=f"Service degraded: {service.service_name}",
                    message=service.message,
                    dedupe_key=f"service:{service.service_name}"
                )

        # Alert on high memory
        if current_metrics.get('memory_percent', 0) > 90:
            self.alerting_service.alert(
                severity=AlertingService.Severity.WARNING,
                title="High memory usage",
                message=f"Memory usage is {current_metrics['memory_percent']:.1f}%",
                dedupe_key="memory:high"
            )

        # Alert on many slow operations
        if perf.slow_operations > 20:
            self.alerting_service.alert(
                severity=AlertingService.Severity.WARNING,
                title="Many slow operations",
                message=f"{perf.slow_operations} slow operations in the last hour",
                dedupe_key="performance:slow_ops"
            )

    def generate_report(self, period: str = "24h") -> str:
        """
        Generate text report

        Args:
            period: Time period for report

        Returns:
            Formatted text report
        """
        data = self.get_dashboard_data(period)

        report = f"""
DocAssist EMR Monitoring Report
================================
Generated: {data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Period: {period}

HEALTH STATUS
-------------
Overall: {data.health['overall_status'].upper()}

Services:
"""

        for service in data.health['services']:
            status = service['status']
            name = service['service_name']
            message = service['message']
            report += f"  - {name}: {status.upper()} - {message}\n"

        report += f"""
ERRORS
------
Total errors: {data.errors['total_errors']}
Unique errors: {data.errors['unique_errors']}
Error rate: {data.errors['error_rate']:.2f} per hour

Top errors:
"""

        for error in data.errors['top_errors']:
            report += f"  - {error['type']}: {error['message']} ({error['count']} times)\n"

        report += f"""
PERFORMANCE
-----------
Total operations: {data.performance['total_operations']}
Slow operations: {data.performance['slow_operations']}
Average duration: {data.performance['avg_duration_ms']:.2f}ms
P50: {data.performance['p50_ms']:.2f}ms
P90: {data.performance['p90_ms']:.2f}ms
P99: {data.performance['p99_ms']:.2f}ms
CPU usage: {data.performance['cpu_usage_avg']:.1f}%
Memory usage: {data.performance['memory_usage_avg_mb']:.1f}MB

SYSTEM
------
OS: {data.system['os']}
Python: {data.system['python_version']}
CPUs: {data.system['cpu_count']}
Total RAM: {data.system['total_memory_gb']:.1f}GB
Disk free: {data.system['disk_free_gb']:.1f}GB
Uptime: {data.system['uptime_hours']:.1f} hours

ALERTS
------
Recent alerts: {len(data.alerts)}
"""

        for alert in data.alerts[:5]:
            report += f"  [{alert['severity'].upper()}] {alert['title']} - {alert['timestamp']}\n"

        report += f"""
CRASHES
-------
Total crashes: {data.crashes['total']}
Recent crashes: {len(data.crashes['recent'])}
"""

        return report
