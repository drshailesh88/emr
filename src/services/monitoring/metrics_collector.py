"""
Metrics collection and storage for application monitoring.

Tracks timing, counts, and gauges for performance analysis.
"""

import os
import sqlite3
import statistics
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from collections import defaultdict
import threading


@dataclass
class Metric:
    """A single metric data point"""
    timestamp: datetime
    name: str
    value: float
    tags: Dict[str, str]


@dataclass
class Percentiles:
    """Percentile statistics for a metric"""
    name: str
    period: str
    count: int
    min: float
    max: float
    mean: float
    median: float
    p50: float
    p90: float
    p95: float
    p99: float


@dataclass
class MetricSummary:
    """Summary statistics for a metric"""
    name: str
    period: str
    count: int
    sum: float
    min: float
    max: float
    mean: float


class MetricsCollector:
    """Collect and store application metrics"""

    def __init__(self, db_path: str = "data/monitoring.db"):
        """
        Initialize metrics collector

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._ensure_db()

        # Thread-safe metric buffer
        self._lock = threading.Lock()
        self._buffer = []
        self._buffer_size = 100  # Flush after 100 metrics

    def _ensure_db(self):
        """Create database tables if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    name TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp
                ON metrics(name, timestamp DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_type_timestamp
                ON metrics(metric_type, timestamp DESC)
            """)

            # Create aggregated metrics table for faster queries
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics_hourly (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hour TEXT NOT NULL,
                    name TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    sum REAL NOT NULL,
                    min REAL NOT NULL,
                    max REAL NOT NULL,
                    mean REAL NOT NULL,
                    UNIQUE(hour, name, metric_type)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_hourly_name
                ON metrics_hourly(name, hour DESC)
            """)

    def record_timing(self, name: str, duration_ms: float, tags: Dict[str, str] = None):
        """
        Record timing metric

        Args:
            name: Metric name (e.g., "consultation_duration_ms")
            duration_ms: Duration in milliseconds
            tags: Optional tags for filtering
        """
        self._record_metric(name, "timing", duration_ms, tags)

    def record_count(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """
        Record count metric

        Args:
            name: Metric name (e.g., "patients_created")
            value: Count value
            tags: Optional tags for filtering
        """
        self._record_metric(name, "count", float(value), tags)

    def record_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """
        Record gauge metric (current value)

        Args:
            name: Metric name (e.g., "memory_usage_mb")
            value: Current value
            tags: Optional tags for filtering
        """
        self._record_metric(name, "gauge", value, tags)

    def _record_metric(self, name: str, metric_type: str, value: float, tags: Dict[str, str] = None):
        """Internal method to record a metric"""
        import json

        metric = {
            "timestamp": datetime.now().isoformat(),
            "name": name,
            "metric_type": metric_type,
            "value": value,
            "tags": json.dumps(tags) if tags else None
        }

        with self._lock:
            self._buffer.append(metric)

            # Flush if buffer is full
            if len(self._buffer) >= self._buffer_size:
                self._flush_buffer()

    def _flush_buffer(self):
        """Flush metrics buffer to database"""
        if not self._buffer:
            return

        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("""
                INSERT INTO metrics (timestamp, name, metric_type, value, tags)
                VALUES (:timestamp, :name, :metric_type, :value, :tags)
            """, self._buffer)

        self._buffer.clear()

    def flush(self):
        """Manually flush metrics buffer"""
        with self._lock:
            self._flush_buffer()

    def get_metrics(self, name: str, period: str = "24h") -> List[Metric]:
        """
        Get metric history

        Args:
            name: Metric name
            period: Time period (1h, 24h, 7d, 30d)

        Returns:
            List of Metric objects
        """
        import json

        # Flush buffer first
        self.flush()

        # Parse period
        period_hours = {
            "1h": 1,
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30
        }.get(period, 24)

        cutoff = datetime.now() - timedelta(hours=period_hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT timestamp, name, value, tags
                FROM metrics
                WHERE name = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (name, cutoff.isoformat()))

            metrics = []
            for row in cursor.fetchall():
                metrics.append(Metric(
                    timestamp=datetime.fromisoformat(row[0]),
                    name=row[1],
                    value=row[2],
                    tags=json.loads(row[3]) if row[3] else {}
                ))

            return metrics

    def get_percentiles(self, name: str, period: str = "24h") -> Optional[Percentiles]:
        """
        Get p50, p90, p99 for timing metric

        Args:
            name: Metric name
            period: Time period (1h, 24h, 7d, 30d)

        Returns:
            Percentiles object or None if no data
        """
        # Flush buffer first
        self.flush()

        # Parse period
        period_hours = {
            "1h": 1,
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30
        }.get(period, 24)

        cutoff = datetime.now() - timedelta(hours=period_hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT value
                FROM metrics
                WHERE name = ? AND timestamp >= ? AND metric_type = 'timing'
                ORDER BY value
            """, (name, cutoff.isoformat()))

            values = [row[0] for row in cursor.fetchall()]

            if not values:
                return None

            def percentile(data, p):
                """Calculate percentile"""
                if not data:
                    return 0
                k = (len(data) - 1) * p
                f = int(k)
                c = f + 1
                if c >= len(data):
                    return data[-1]
                return data[f] + (k - f) * (data[c] - data[f])

            return Percentiles(
                name=name,
                period=period,
                count=len(values),
                min=min(values),
                max=max(values),
                mean=statistics.mean(values),
                median=statistics.median(values),
                p50=percentile(values, 0.50),
                p90=percentile(values, 0.90),
                p95=percentile(values, 0.95),
                p99=percentile(values, 0.99)
            )

    def get_summary(self, name: str, period: str = "24h") -> Optional[MetricSummary]:
        """
        Get summary statistics for a metric

        Args:
            name: Metric name
            period: Time period (1h, 24h, 7d, 30d)

        Returns:
            MetricSummary or None if no data
        """
        # Flush buffer first
        self.flush()

        # Parse period
        period_hours = {
            "1h": 1,
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30
        }.get(period, 24)

        cutoff = datetime.now() - timedelta(hours=period_hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*), SUM(value), MIN(value), MAX(value), AVG(value)
                FROM metrics
                WHERE name = ? AND timestamp >= ?
            """, (name, cutoff.isoformat()))

            row = cursor.fetchone()

            if row[0] == 0:
                return None

            return MetricSummary(
                name=name,
                period=period,
                count=row[0],
                sum=row[1],
                min=row[2],
                max=row[3],
                mean=row[4]
            )

    def get_rate(self, name: str, period: str = "1h") -> float:
        """
        Get rate of count metric (events per hour)

        Args:
            name: Metric name
            period: Time period to calculate rate over

        Returns:
            Events per hour
        """
        summary = self.get_summary(name, period)
        if not summary:
            return 0.0

        period_hours = {
            "1h": 1,
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30
        }.get(period, 1)

        return summary.sum / period_hours if period_hours > 0 else 0.0

    def get_timeseries(
        self,
        name: str,
        period: str = "24h",
        bucket_size: str = "1h"
    ) -> List[Dict[str, Any]]:
        """
        Get time series data bucketed by time

        Args:
            name: Metric name
            period: Time period to query
            bucket_size: Size of each time bucket (1h, 5m, etc.)

        Returns:
            List of time buckets with aggregated values
        """
        # Flush buffer first
        self.flush()

        # Parse period
        period_hours = {
            "1h": 1,
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30
        }.get(period, 24)

        # Parse bucket size (in minutes)
        bucket_minutes = {
            "5m": 5,
            "15m": 15,
            "1h": 60,
            "6h": 360,
            "1d": 1440
        }.get(bucket_size, 60)

        cutoff = datetime.now() - timedelta(hours=period_hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT timestamp, value
                FROM metrics
                WHERE name = ? AND timestamp >= ?
                ORDER BY timestamp
            """, (name, cutoff.isoformat()))

            # Group by time buckets
            buckets = defaultdict(list)
            for row in cursor.fetchall():
                timestamp = datetime.fromisoformat(row[0])
                value = row[1]

                # Round timestamp to bucket
                bucket_time = timestamp.replace(
                    minute=(timestamp.minute // bucket_minutes) * bucket_minutes,
                    second=0,
                    microsecond=0
                )

                buckets[bucket_time].append(value)

            # Aggregate each bucket
            result = []
            for bucket_time in sorted(buckets.keys()):
                values = buckets[bucket_time]
                result.append({
                    "timestamp": bucket_time.isoformat(),
                    "count": len(values),
                    "sum": sum(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": statistics.mean(values)
                })

            return result

    def aggregate_hourly(self):
        """
        Aggregate metrics by hour for faster queries

        Should be run periodically (e.g., every hour)
        """
        # Flush buffer first
        self.flush()

        with sqlite3.connect(self.db_path) as conn:
            # Get the last aggregated hour
            cursor = conn.execute("""
                SELECT MAX(hour) FROM metrics_hourly
            """)
            last_hour = cursor.fetchone()[0]

            if last_hour:
                cutoff = datetime.fromisoformat(last_hour)
            else:
                # Start from beginning
                cursor = conn.execute("SELECT MIN(timestamp) FROM metrics")
                min_timestamp = cursor.fetchone()[0]
                if not min_timestamp:
                    return
                cutoff = datetime.fromisoformat(min_timestamp).replace(minute=0, second=0, microsecond=0)

            # Aggregate up to current hour
            current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)

            while cutoff < current_hour:
                next_hour = cutoff + timedelta(hours=1)

                # Aggregate this hour
                cursor = conn.execute("""
                    SELECT
                        name,
                        metric_type,
                        COUNT(*) as count,
                        SUM(value) as sum,
                        MIN(value) as min,
                        MAX(value) as max,
                        AVG(value) as mean
                    FROM metrics
                    WHERE timestamp >= ? AND timestamp < ?
                    GROUP BY name, metric_type
                """, (cutoff.isoformat(), next_hour.isoformat()))

                for row in cursor.fetchall():
                    conn.execute("""
                        INSERT OR REPLACE INTO metrics_hourly
                        (hour, name, metric_type, count, sum, min, max, mean)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (cutoff.isoformat(), row[0], row[1], row[2], row[3], row[4], row[5], row[6]))

                cutoff = next_hour

            conn.commit()

    def cleanup_old_data(self, days: int = 90):
        """
        Clean up old metric data

        Args:
            days: Keep data from last N days
        """
        cutoff = datetime.now() - timedelta(days=days)

        # Flush buffer first
        self.flush()

        with sqlite3.connect(self.db_path) as conn:
            # Keep hourly aggregates, delete raw metrics
            conn.execute("""
                DELETE FROM metrics
                WHERE timestamp < ?
            """, (cutoff.isoformat(),))

            # Also clean up old hourly data
            hourly_cutoff = datetime.now() - timedelta(days=days * 2)
            conn.execute("""
                DELETE FROM metrics_hourly
                WHERE hour < ?
            """, (hourly_cutoff.isoformat(),))

            conn.execute("VACUUM")

    def get_all_metric_names(self) -> List[str]:
        """Get list of all metric names"""
        self.flush()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT name FROM metrics
                UNION
                SELECT DISTINCT name FROM metrics_hourly
                ORDER BY name
            """)

            return [row[0] for row in cursor.fetchall()]
