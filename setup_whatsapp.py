#!/usr/bin/env python3
"""Setup script for WhatsApp integration in DocAssist EMR."""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.whatsapp.database_migration import run_whatsapp_migrations
from src.services.whatsapp_settings import WhatsAppSettingsService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run WhatsApp setup."""
    print("=" * 60)
    print("DocAssist EMR - WhatsApp Integration Setup")
    print("=" * 60)
    print()

    # Step 1: Run database migrations
    print("Step 1: Creating WhatsApp database tables...")
    success = run_whatsapp_migrations()

    if success:
        print("✓ WhatsApp database tables created successfully!")
    else:
        print("✗ Failed to create WhatsApp database tables")
        print("  Check logs for errors")
        return False

    print()

    # Step 2: Initialize settings
    print("Step 2: Initializing WhatsApp settings...")
    try:
        settings_service = WhatsAppSettingsService()
        credentials = settings_service.get_credentials()

        if credentials.is_configured():
            print("✓ WhatsApp credentials already configured")
            print(f"  - Mock mode: {'Enabled' if credentials.mock_mode else 'Disabled'}")
            print(f"  - Features: {'Enabled' if credentials.enabled else 'Disabled'}")
        else:
            print("✓ WhatsApp settings initialized (not configured)")
            print("  - Default: Mock mode enabled")
            print("  - Configure via Settings > WhatsApp in the app")

    except Exception as e:
        logger.error(f"Error initializing settings: {e}")
        print("✗ Failed to initialize WhatsApp settings")
        return False

    print()

    # Step 3: Summary
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print()
    print("1. Add WhatsApp tab to Settings dialog:")
    print("   - Open src/ui/settings_dialog.py")
    print("   - Add WhatsAppSetupPanel as a new tab")
    print("   - See WHATSAPP_INTEGRATION_SUMMARY.md for details")
    print()
    print("2. Configure WhatsApp (choose one):")
    print()
    print("   Option A - Mock Mode (No credentials needed):")
    print("   - Open DocAssist EMR")
    print("   - Go to Settings > WhatsApp")
    print("   - Enable 'Mock Mode'")
    print("   - Enable 'WhatsApp Features'")
    print("   - Save settings")
    print()
    print("   Option B - Production Mode (Requires credentials):")
    print("   - Get credentials from Meta Business Suite")
    print("   - Go to https://business.facebook.com")
    print("   - Navigate to WhatsApp > API Setup")
    print("   - Copy Phone Number ID and Access Token")
    print("   - Enter in Settings > WhatsApp")
    print("   - Disable 'Mock Mode'")
    print("   - Enable 'WhatsApp Features'")
    print("   - Click 'Test Connection'")
    print("   - Save settings")
    print()
    print("3. Test WhatsApp integration:")
    print("   - Open a patient")
    print("   - Generate a prescription")
    print("   - Click 'Share WhatsApp'")
    print("   - In mock mode: Check console for logged message")
    print("   - In production: Patient receives WhatsApp message")
    print()
    print("Documentation:")
    print("  - Integration Guide: src/ui/whatsapp/INTEGRATION_GUIDE.md")
    print("  - Summary: WHATSAPP_INTEGRATION_SUMMARY.md")
    print("  - Conversation UI: src/ui/whatsapp/README.md")
    print()
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
