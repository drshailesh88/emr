#!/usr/bin/env python3
"""
DocAssist Mobile - Entry Point

A privacy-first mobile companion app for DocAssist EMR.
Syncs patient records from desktop and provides view-only access.
"""

import flet as ft
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.mobile_app import DocAssistMobile


def main(page: ft.Page):
    """Main entry point for the mobile app."""
    app = DocAssistMobile(page)
    app.build()


if __name__ == "__main__":
    # For development: run as desktop app
    ft.app(target=main)

    # For mobile build, Flet handles this automatically:
    # flet build apk  (Android)
    # flet build ipa  (iOS)
