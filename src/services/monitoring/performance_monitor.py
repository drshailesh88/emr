"""
Performance monitoring for DocAssist EMR.

Tracks operation timing, identifies slow operations, and provides performance reports.
"""

import time
import threading
import psutil
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from contextlib import contextmanager
from collections import defaultdict, deque


@dataclass
class SlowOperation:
    """A slow operation record"""
    timestamp: datetime
    operation: str
    duration_ms: float
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceReport:
    """Performance summary report"""
    period: str
    total_operations: int
    slow_operations: int
    avg_duration_ms: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    slowest_operations: List[SlowOperation]
    cpu_usage_avg: float
    memory_usage_avg_mb: float


class PerformanceMonitor:
    """Monitor app performance in real-time"""

    def __init__(
        self,
        slow_threshold_ms: float = 1000.0,
        monitor_interval_seconds: float = 60.0
    ):
        """
        Initialize performance monitor

        Args:
            slow_threshold_ms: Threshold for slow operations (ms)
            monitor_interval_seconds: How often to collect system metrics
        """
        self.slow_threshold_ms = slow_threshold_ms
        self.monitor_interval_seconds = monitor_interval_seconds

        # Operation tracking
        self._operations = deque(maxlen=10000)  # Keep last 10k operations
        self._slow_operations = deque(maxlen=1000)  # Keep last 1k slow ops

        # System metrics
        self._cpu_samples = deque(maxlen=1000)
        self._memory_samples = deque(maxlen=1000)

        # Threading
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Custom performance handlers
        self._slow_operation_handlers: List[Callable] = []

    def start(self):
        """Start background monitoring"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="PerformanceMonitor"
        )
        self._monitor_thread.start()

    def stop(self):
        """Stop monitoring"""
        if not self._monitor_thread:
            return

        self._stop_event.set()
        self._monitor_thread.join(timeout=5.0)
        self._monitor_thread = None

    def _monitor_loop(self):
        """Background monitoring loop"""
        process = psutil.Process()

        while not self._stop_event.is_set():
            try:
                # Collect CPU usage
                cpu_percent = process.cpu_percent(interval=1.0)

                # Collect memory usage
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)

                with self._lock:
                    self._cpu_samples.append({
                        'timestamp': datetime.now(),
                        'value': cpu_percent
                    })
                    self._memory_samples.append({
                        'timestamp': datetime.now(),
                        'value': memory_mb
                    })

            except Exception as e:
                print(f"Performance monitor error: {e}")

            # Wait for next interval
            self._stop_event.wait(self.monitor_interval_seconds)

    @contextmanager
    def measure(self, operation: str, context: Dict[str, Any] = None):
        """
        Context manager to measure operation time

        Args:
            operation: Operation name
            context: Additional context

        Usage:
            with perf_monitor.measure("save_prescription"):
                save_prescription(...)
        """
        start_time = time.perf_counter()
        exception_occurred = False

        try:
            yield
        except Exception:
            exception_occurred = True
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Record operation
            self._record_operation(
                operation=operation,
                duration_ms=duration_ms,
                failed=exception_occurred,
                context=context
            )

    def _record_operation(
        self,
        operation: str,
        duration_ms: float,
        failed: bool = False,
        context: Dict[str, Any] = None
    ):
        """Record an operation"""
        timestamp = datetime.now()

        with self._lock:
            # Add to operations log
            self._operations.append({
                'timestamp': timestamp,
                'operation': operation,
                'duration_ms': duration_ms,
                'failed': failed,
                'context': context
            })

            # Check if slow
            if duration_ms > self.slow_threshold_ms:
                slow_op = SlowOperation(
                    timestamp=timestamp,
                    operation=operation,
                    duration_ms=duration_ms,
                    stack_trace=self._get_stack_trace() if duration_ms > 5000 else None,
                    context=context
                )

                self._slow_operations.append(slow_op)

                # Call handlers
                for handler in self._slow_operation_handlers:
                    try:
                        handler(slow_op)
                    except Exception as e:
                        print(f"Slow operation handler failed: {e}")

    def get_slow_operations(self, threshold_ms: Optional[float] = None) -> List[SlowOperation]:
        """
        Get operations exceeding threshold

        Args:
            threshold_ms: Custom threshold (uses default if not provided)

        Returns:
            List of SlowOperation objects
        """
        threshold = threshold_ms or self.slow_threshold_ms

        with self._lock:
            return [
                op for op in self._slow_operations
                if op.duration_ms >= threshold
            ]

    def get_performance_report(self, period: str = "1h") -> PerformanceReport:
        """
        Get performance summary

        Args:
            period: Time period (1h, 24h, 7d)

        Returns:
            PerformanceReport with statistics
        """
        # Parse period
        period_hours = {
            "1h": 1,
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30
        }.get(period, 1)

        cutoff = datetime.now() - timedelta(hours=period_hours)

        with self._lock:
            # Filter operations in period
            period_ops = [
                op for op in self._operations
                if op['timestamp'] >= cutoff
            ]

            if not period_ops:
                return PerformanceReport(
                    period=period,
                    total_operations=0,
                    slow_operations=0,
                    avg_duration_ms=0,
                    p50_ms=0,
                    p90_ms=0,
                    p95_ms=0,
                    p99_ms=0,
                    slowest_operations=[],
                    cpu_usage_avg=0,
                    memory_usage_avg_mb=0
                )

            # Calculate statistics
            durations = sorted([op['duration_ms'] for op in period_ops])
            total_operations = len(durations)
            slow_operations = len([d for d in durations if d > self.slow_threshold_ms])

            avg_duration = sum(durations) / len(durations)

            def percentile(data, p):
                k = (len(data) - 1) * p
                f = int(k)
                c = f + 1
                if c >= len(data):
                    return data[-1]
                return data[f] + (k - f) * (data[c] - data[f])

            p50 = percentile(durations, 0.50)
            p90 = percentile(durations, 0.90)
            p95 = percentile(durations, 0.95)
            p99 = percentile(durations, 0.99)

            # Get slowest operations
            slowest = sorted(
                [op for op in self._slow_operations if op.timestamp >= cutoff],
                key=lambda x: x.duration_ms,
                reverse=True
            )[:10]

            # System metrics
            cpu_samples = [s['value'] for s in self._cpu_samples if s['timestamp'] >= cutoff]
            memory_samples = [s['value'] for s in self._memory_samples if s['timestamp'] >= cutoff]

            cpu_avg = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
            memory_avg = sum(memory_samples) / len(memory_samples) if memory_samples else 0

            return PerformanceReport(
                period=period,
                total_operations=total_operations,
                slow_operations=slow_operations,
                avg_duration_ms=avg_duration,
                p50_ms=p50,
                p90_ms=p90,
                p95_ms=p95,
                p99_ms=p99,
                slowest_operations=slowest,
                cpu_usage_avg=cpu_avg,
                memory_usage_avg_mb=memory_avg
            )

    def get_operation_stats(self, operation: str, period: str = "1h") -> Dict[str, Any]:
        """
        Get statistics for a specific operation

        Args:
            operation: Operation name
            period: Time period

        Returns:
            Dictionary with statistics
        """
        period_hours = {
            "1h": 1,
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30
        }.get(period, 1)

        cutoff = datetime.now() - timedelta(hours=period_hours)

        with self._lock:
            # Filter operations
            ops = [
                op for op in self._operations
                if op['operation'] == operation and op['timestamp'] >= cutoff
            ]

            if not ops:
                return {
                    'operation': operation,
                    'count': 0,
                    'avg_duration_ms': 0,
                    'min_duration_ms': 0,
                    'max_duration_ms': 0,
                    'failure_rate': 0
                }

            durations = [op['duration_ms'] for op in ops]
            failures = [op for op in ops if op.get('failed', False)]

            return {
                'operation': operation,
                'count': len(ops),
                'avg_duration_ms': sum(durations) / len(durations),
                'min_duration_ms': min(durations),
                'max_duration_ms': max(durations),
                'failure_rate': len(failures) / len(ops) if ops else 0,
                'failures': len(failures)
            }

    def get_top_operations(self, period: str = "1h", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top operations by count

        Args:
            period: Time period
            limit: Number of top operations to return

        Returns:
            List of operation statistics
        """
        period_hours = {
            "1h": 1,
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30
        }.get(period, 1)

        cutoff = datetime.now() - timedelta(hours=period_hours)

        with self._lock:
            # Group by operation
            op_counts = defaultdict(int)
            op_durations = defaultdict(list)

            for op in self._operations:
                if op['timestamp'] >= cutoff:
                    op_name = op['operation']
                    op_counts[op_name] += 1
                    op_durations[op_name].append(op['duration_ms'])

            # Calculate stats for each
            results = []
            for op_name in op_counts:
                durations = op_durations[op_name]
                results.append({
                    'operation': op_name,
                    'count': op_counts[op_name],
                    'avg_duration_ms': sum(durations) / len(durations),
                    'max_duration_ms': max(durations)
                })

            # Sort by count
            results.sort(key=lambda x: x['count'], reverse=True)
            return results[:limit]

    def add_slow_operation_handler(self, handler: Callable[[SlowOperation], None]):
        """
        Add handler for slow operations

        Args:
            handler: Function that takes a SlowOperation
        """
        self._slow_operation_handlers.append(handler)

    def _get_stack_trace(self) -> str:
        """Get current stack trace (excluding this function)"""
        import traceback
        stack = traceback.format_stack()[:-1]  # Exclude this function
        return ''.join(stack)

    def reset_stats(self):
        """Reset all statistics"""
        with self._lock:
            self._operations.clear()
            self._slow_operations.clear()
            self._cpu_samples.clear()
            self._memory_samples.clear()

    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current system metrics

        Returns:
            Dictionary with current CPU and memory usage
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                'cpu_percent': process.cpu_percent(),
                'memory_mb': memory_info.rss / (1024 * 1024),
                'memory_percent': process.memory_percent(),
                'num_threads': process.num_threads(),
                'num_fds': process.num_fds() if hasattr(process, 'num_fds') else None
            }
        except Exception as e:
            return {'error': str(e)}


# Global performance monitor instance (optional)
_global_performance_monitor: Optional['PerformanceMonitor'] = None


def set_global_performance_monitor(monitor: 'PerformanceMonitor'):
    """Set global performance monitor instance"""
    global _global_performance_monitor
    _global_performance_monitor = monitor


def get_global_performance_monitor() -> Optional['PerformanceMonitor']:
    """Get global performance monitor instance"""
    return _global_performance_monitor


# Decorator for measuring performance
def measure_performance(operation_name: Optional[str] = None):
    """
    Decorator to measure function performance

    Args:
        operation_name: Custom operation name (uses function name if not provided)

    Usage:
        @measure_performance("save_prescription")
        def save_prescription(...):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__

            # Get global performance monitor if available
            monitor = get_global_performance_monitor()

            if monitor:
                with monitor.measure(op_name):
                    return func(*args, **kwargs)
            else:
                # No monitor available, just call function
                return func(*args, **kwargs)

        return wrapper
    return decorator
