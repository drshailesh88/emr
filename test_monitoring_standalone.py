#!/usr/bin/env python3
"""
Standalone test for monitoring system (bypasses other dependencies).
"""

import sys
import os

# Test direct imports of monitoring modules
def test_direct_imports():
    """Test importing monitoring modules directly"""
    print("Testing direct imports of monitoring modules...\n")

    modules_to_test = [
        ('error_tracker', 'src.services.monitoring.error_tracker'),
        ('health_checker', 'src.services.monitoring.health_checker'),
        ('metrics_collector', 'src.services.monitoring.metrics_collector'),
        ('alerting', 'src.services.monitoring.alerting'),
        ('crash_reporter', 'src.services.monitoring.crash_reporter'),
        ('performance_monitor', 'src.services.monitoring.performance_monitor'),
        ('dashboard_data', 'src.services.monitoring.dashboard_data'),
        ('decorators', 'src.services.monitoring.decorators'),
    ]

    failed = []
    for name, module_path in modules_to_test:
        try:
            __import__(module_path)
            print(f"✓ {name:25} imported successfully")
        except Exception as e:
            print(f"✗ {name:25} FAILED: {e}")
            failed.append((name, e))

    if not failed:
        print("\n✓ All modules imported successfully!")
        return True
    else:
        print(f"\n✗ {len(failed)} module(s) failed to import")
        return False


def test_basic_classes():
    """Test basic class instantiation"""
    print("\nTesting basic class instantiation...\n")

    import tempfile

    # Create temp db
    fd, temp_db = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    try:
        # Test ErrorTracker
        from src.services.monitoring.error_tracker import ErrorTracker
        tracker = ErrorTracker(db_path=temp_db, app_version="test")
        print("✓ ErrorTracker instantiated")

        # Test HealthChecker
        from src.services.monitoring.health_checker import HealthChecker
        checker = HealthChecker(db_path=temp_db)
        print("✓ HealthChecker instantiated")

        # Test MetricsCollector
        from src.services.monitoring.metrics_collector import MetricsCollector
        metrics = MetricsCollector(db_path=temp_db)
        print("✓ MetricsCollector instantiated")

        # Test AlertingService
        from src.services.monitoring.alerting import AlertingService, AlertConfig
        alerting = AlertingService(db_path=temp_db, config=AlertConfig())
        print("✓ AlertingService instantiated")

        # Test CrashReporter
        from src.services.monitoring.crash_reporter import CrashReporter
        temp_dir = tempfile.mkdtemp()
        reporter = CrashReporter(db_path=temp_db, crash_dir=temp_dir, app_version="test")
        print("✓ CrashReporter instantiated")

        # Test PerformanceMonitor
        from src.services.monitoring.performance_monitor import PerformanceMonitor
        perf = PerformanceMonitor()
        print("✓ PerformanceMonitor instantiated")

        print("\n✓ All classes instantiated successfully!")
        return True

    except Exception as e:
        print(f"\n✗ Instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_basic_operations():
    """Test basic operations"""
    print("\nTesting basic operations...\n")

    import tempfile

    fd, temp_db = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    try:
        from src.services.monitoring.error_tracker import ErrorTracker
        from src.services.monitoring.metrics_collector import MetricsCollector
        from src.services.monitoring.performance_monitor import PerformanceMonitor

        # Test error tracking
        tracker = ErrorTracker(db_path=temp_db, app_version="test")
        try:
            raise ValueError("Test error")
        except Exception as e:
            tracker.capture_exception(e, context={"test": True})
        summary = tracker.get_error_summary("1h")
        assert summary.total_errors == 1, "Error count mismatch"
        print("✓ Error tracking works")

        # Test metrics
        metrics = MetricsCollector(db_path=temp_db)
        metrics.record_timing("test_op", 123.45)
        metrics.flush()
        summary = metrics.get_summary("test_op", "1h")
        assert summary is not None, "Metric summary not found"
        assert summary.count == 1, "Metric count mismatch"
        print("✓ Metrics collection works")

        # Test performance monitoring
        perf = PerformanceMonitor()
        perf.start()
        import time
        with perf.measure("test"):
            time.sleep(0.01)
        report = perf.get_performance_report("1h")
        assert report.total_operations >= 1, "No operations tracked"
        perf.stop()
        print("✓ Performance monitoring works")

        print("\n✓ All basic operations work!")
        return True

    except Exception as e:
        print(f"\n✗ Operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def main():
    """Run all tests"""
    print("="*60)
    print("DocAssist EMR Monitoring System - Standalone Tests")
    print("="*60)
    print()

    results = []

    # Test imports
    results.append(("Module Imports", test_direct_imports()))

    # Test instantiation
    results.append(("Class Instantiation", test_basic_classes()))

    # Test operations
    results.append(("Basic Operations", test_basic_operations()))

    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:30} {status}")

    all_passed = all(result[1] for result in results)

    print("="*60)
    if all_passed:
        print("\n✓✓✓ ALL TESTS PASSED! ✓✓✓")
        print("\nThe monitoring system is ready to use!")
        return 0
    else:
        print("\n✗✗✗ SOME TESTS FAILED ✗✗✗")
        return 1


if __name__ == "__main__":
    sys.exit(main())
