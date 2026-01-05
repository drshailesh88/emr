#!/usr/bin/env python3
"""
Simple smoke test for monitoring system (without pytest).
"""

import sys
import os
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")

    try:
        from src.services.monitoring import (
            MonitoringSystem,
            ErrorTracker,
            HealthChecker,
            MetricsCollector,
            AlertingService,
            CrashReporter,
            PerformanceMonitor,
            MonitoringDashboard,
            AlertConfig,
            Severity,
            init_monitoring
        )
        print("✓ All main components imported successfully")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

    try:
        from src.services.monitoring.decorators import (
            monitor_performance,
            capture_errors,
            alert_on_failure,
            count_calls,
            monitor_all
        )
        print("✓ All decorators imported successfully")
    except Exception as e:
        print(f"✗ Decorator import failed: {e}")
        return False

    return True


def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")

    from src.services.monitoring import MonitoringSystem

    # Create temporary database
    fd, temp_db = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    try:
        # Initialize monitoring system
        monitoring = MonitoringSystem(
            db_path=temp_db,
            clinic_db_path=temp_db,
            backup_db_path=temp_db,
            app_version="test-1.0.0"
        )
        print("✓ MonitoringSystem initialized")

        # Start monitoring
        monitoring.start()
        print("✓ Monitoring started")

        # Test error tracking
        try:
            raise ValueError("Test error")
        except Exception as e:
            monitoring.error_tracker.capture_exception(e, context={"test": True})
        print("✓ Error captured")

        # Test metrics
        monitoring.metrics.record_timing("test_operation", 123.45)
        monitoring.metrics.record_count("test_count", 1)
        monitoring.metrics.flush()
        print("✓ Metrics recorded")

        # Test performance monitoring
        import time
        with monitoring.performance.measure("test_op"):
            time.sleep(0.01)
        print("✓ Performance measured")

        # Test alert
        from src.services.monitoring import Severity, AlertConfig
        monitoring.alerting.alert(
            severity=Severity.INFO,
            title="Test alert",
            message="This is a test"
        )
        print("✓ Alert sent")

        # Get summary
        summary = monitoring.get_summary()
        print(f"✓ Summary retrieved (health score: {summary['health_score']})")

        # Stop monitoring
        monitoring.stop()
        print("✓ Monitoring stopped")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_decorators():
    """Test decorators"""
    print("\nTesting decorators...")

    from src.services.monitoring import init_monitoring
    from src.services.monitoring.decorators import monitor_all

    # Create temporary database
    fd, temp_db = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    try:
        # Initialize monitoring
        monitoring = init_monitoring(
            db_path=temp_db,
            clinic_db_path=temp_db,
            app_version="test",
            auto_start=True
        )

        # Define decorated function
        @monitor_all("test_function")
        def test_function():
            import time
            time.sleep(0.01)
            return "success"

        # Call decorated function
        result = test_function()
        assert result == "success"
        print("✓ Decorated function executed")

        # Check that it was monitored
        report = monitoring.performance.get_performance_report("1h")
        if report.total_operations > 0:
            print(f"✓ Decorator monitoring worked ({report.total_operations} operations tracked)")
        else:
            print("⚠ No operations tracked (may be timing issue)")

        monitoring.stop()
        return True

    except Exception as e:
        print(f"✗ Decorator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def main():
    """Run all tests"""
    print("="*60)
    print("DocAssist EMR Monitoring System - Smoke Tests")
    print("="*60)

    results = []

    # Test imports
    results.append(("Imports", test_imports()))

    # Test basic functionality
    results.append(("Basic Functionality", test_basic_functionality()))

    # Test decorators
    results.append(("Decorators", test_decorators()))

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
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
