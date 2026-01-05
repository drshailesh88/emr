#!/usr/bin/env python3
"""Test script for WhatsApp integration components."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_imports():
    """Test that all modules can be imported."""
    print("\n" + "=" * 60)
    print("Testing Module Imports")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0

    # Test service imports
    try:
        from src.services.whatsapp_settings import WhatsAppSettingsService, WhatsAppCredentials
        print("✓ WhatsApp settings service")
        tests_passed += 1
    except Exception as e:
        print(f"✗ WhatsApp settings service: {e}")
        tests_failed += 1

    try:
        from src.services.whatsapp.client import WhatsAppClient, MessageStatus
        print("✓ WhatsApp client")
        tests_passed += 1
    except Exception as e:
        print(f"✗ WhatsApp client: {e}")
        tests_failed += 1

    try:
        from src.services.whatsapp.templates import MessageTemplates
        print("✓ WhatsApp templates")
        tests_passed += 1
    except Exception as e:
        print(f"✗ WhatsApp templates: {e}")
        tests_failed += 1

    try:
        from src.services.whatsapp.message_queue import WhatsAppMessageQueue
        print("✓ WhatsApp message queue")
        tests_passed += 1
    except Exception as e:
        print(f"✗ WhatsApp message queue: {e}")
        tests_failed += 1

    try:
        from src.services.whatsapp.database_migration import WhatsAppDatabaseMigration
        print("✓ WhatsApp database migration")
        tests_passed += 1
    except Exception as e:
        print(f"✗ WhatsApp database migration: {e}")
        tests_failed += 1

    # Test UI imports
    try:
        from src.ui.whatsapp.whatsapp_setup import WhatsAppSetupPanel
        print("✓ WhatsApp setup panel")
        tests_passed += 1
    except Exception as e:
        print(f"✗ WhatsApp setup panel: {e}")
        tests_failed += 1

    try:
        from src.ui.whatsapp.send_message_dialog import SendMessageDialog
        print("✓ Send message dialog")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Send message dialog: {e}")
        tests_failed += 1

    try:
        from src.ui.whatsapp.template_selector import TemplateSelector
        print("✓ Template selector")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Template selector: {e}")
        tests_failed += 1

    try:
        from src.ui.whatsapp.reminder_scheduler import ReminderScheduler
        print("✓ Reminder scheduler")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Reminder scheduler: {e}")
        tests_failed += 1

    print(f"\nImport Tests: {tests_passed} passed, {tests_failed} failed")
    return tests_failed == 0


def test_settings_service():
    """Test WhatsApp settings service."""
    print("\n" + "=" * 60)
    print("Testing WhatsApp Settings Service")
    print("=" * 60)

    try:
        from src.services.whatsapp_settings import WhatsAppSettingsService, WhatsAppCredentials

        # Initialize service
        service = WhatsAppSettingsService(settings_path="data/test_whatsapp_settings.json")
        print("✓ Service initialized")

        # Test credentials
        creds = service.get_credentials()
        print(f"✓ Got credentials (configured: {creds.is_configured()})")

        # Test update
        service.update_credentials(
            phone_number_id="test123",
            access_token="test_token",
            enabled=True,
            mock_mode=True
        )
        print("✓ Updated credentials")

        # Verify update
        creds = service.get_credentials()
        assert creds.phone_number_id == "test123", "Phone number ID not updated"
        assert creds.access_token == "test_token", "Access token not updated"
        assert creds.enabled == True, "Enabled flag not updated"
        assert creds.mock_mode == True, "Mock mode not updated"
        print("✓ Verified credentials persisted")

        # Test clear
        service.clear_credentials()
        creds = service.get_credentials()
        assert not creds.is_configured(), "Credentials not cleared"
        print("✓ Credentials cleared")

        print("\nSettings Service Tests: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Settings Service Tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_migration():
    """Test database migration."""
    print("\n" + "=" * 60)
    print("Testing Database Migration")
    print("=" * 60)

    try:
        from src.services.whatsapp.database_migration import WhatsAppDatabaseMigration
        import sqlite3
        from pathlib import Path

        # Use test database
        test_db = Path("data/test_whatsapp.db")
        test_db.parent.mkdir(parents=True, exist_ok=True)

        # Remove if exists
        if test_db.exists():
            test_db.unlink()

        # Run migration
        migration = WhatsAppDatabaseMigration(db_path=str(test_db))
        success = migration.run_migrations()

        assert success, "Migration failed"
        print("✓ Migration completed")

        # Verify tables exist
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert "whatsapp_conversations" in tables, "conversations table not created"
        print("✓ whatsapp_conversations table created")

        assert "whatsapp_messages" in tables, "messages table not created"
        print("✓ whatsapp_messages table created")

        assert "whatsapp_escalations" in tables, "escalations table not created"
        print("✓ whatsapp_escalations table created")

        conn.close()

        # Clean up
        test_db.unlink()

        print("\nDatabase Migration Tests: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Database Migration Tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_message_queue():
    """Test message queue service."""
    print("\n" + "=" * 60)
    print("Testing Message Queue Service")
    print("=" * 60)

    try:
        from src.services.whatsapp.message_queue import WhatsAppMessageQueue
        from src.services.communications.notification_queue import NotificationPriority
        from pathlib import Path

        # Use test database
        test_db = Path("data/test_queue.db")
        test_db.parent.mkdir(parents=True, exist_ok=True)

        # Initialize queue
        queue = WhatsAppMessageQueue(db_path=str(test_db))
        print("✓ Queue initialized")

        # Queue a text message
        notif_id = queue.send_text_message(
            patient_id=1,
            phone="9876543210",
            message="Test message",
            priority=NotificationPriority.NORMAL
        )
        print(f"✓ Text message queued: {notif_id}")

        # Queue a prescription
        notif_id2 = queue.send_prescription(
            patient_id=1,
            phone="9876543210",
            prescription_pdf_path="/path/to/rx.pdf",
            visit_date="15 Jan 2024"
        )
        print(f"✓ Prescription queued: {notif_id2}")

        # Get status
        status = queue.get_status()
        print(f"✓ Queue status: {status.pending} pending, {status.sent_today} sent today")

        # Clean up
        test_db.unlink()

        print("\nMessage Queue Tests: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Message Queue Tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("WhatsApp Integration Test Suite")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("Settings Service", test_settings_service()))
    results.append(("Database Migration", test_database_migration()))
    results.append(("Message Queue", test_message_queue()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:.<40} {status}")

    print()
    print(f"Total: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n✓ All tests passed! WhatsApp integration is ready.")
        print("\nNext steps:")
        print("1. Run setup_whatsapp.py to initialize")
        print("2. Add WhatsApp tab to settings dialog")
        print("3. Configure credentials or enable mock mode")
        print("4. Test in the UI")
        return True
    else:
        print("\n✗ Some tests failed. Please fix errors and try again.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
