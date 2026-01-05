#!/usr/bin/env python3
"""
DocAssist Mobile - Entry Point

A privacy-first mobile companion app for DocAssist EMR.
Syncs patient records from desktop and provides view-only access.

Mobile lifecycle events:
- On resume: Check for sync updates
- On pause: Save app state
- On orientation change: Adjust layout
"""

import flet as ft
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.mobile_app import DocAssistMobile


def main(page: ft.Page):
    """
    Main entry point for the mobile app.

    This function is called by Flet when the app starts.
    For mobile builds (APK/IPA), Flet automatically:
    - Creates splash screen
    - Handles permissions
    - Manages app lifecycle
    """

    # Create and initialize app
    app = DocAssistMobile(page)

    # Handle app lifecycle events
    def on_route_change(e):
        """Handle navigation changes."""
        pass  # DocAssistMobile handles navigation internally

    def on_view_pop(e):
        """Handle back button on Android."""
        page.views.pop()
        top_view = page.views[-1] if page.views else None
        page.go(top_view.route if top_view else "/")

    # Register lifecycle handlers
    page.on_route_change = on_route_change
    page.on_view_pop = on_view_pop

    # Build the app UI
    app.build()


if __name__ == "__main__":
    # Development mode: run as desktop app
    # This allows testing without building for mobile
    ft.app(target=main)

    # Production mobile build commands:
    # Android: flet build apk --org app.docassist --project DocAssist
    # iOS:     flet build ipa --org app.docassist --project DocAssist
    #
    # Or use the build scripts:
    # ./build_android.sh
    # ./build_ios.sh
