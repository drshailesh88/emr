#!/usr/bin/env python3
"""
DocAssist EMR - Local-First AI-Powered Electronic Medical Records

A privacy-first EMR system that runs entirely on your local machine.
Powered by local LLMs via Ollama.

Usage:
    python main.py

Requirements:
    - Python 3.11+
    - Ollama running locally (https://ollama.com)
    - Run: pip install -r requirements.txt
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.app import run_app


def check_ollama():
    """Check if Ollama is accessible."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("✓ Ollama is running")
            models = response.json().get("models", [])
            if models:
                print(f"  Available models: {', '.join(m['name'] for m in models)}")
            return True
    except Exception:
        pass

    print("⚠ Ollama is not running")
    print("  Please start Ollama first: https://ollama.com")
    print("  The app will start, but AI features will be disabled.")
    return False


def check_dependencies():
    """Check if required packages are installed."""
    required = ['flet', 'requests', 'pydantic', 'chromadb', 'fpdf', 'psutil']
    missing = []

    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"✗ Missing packages: {', '.join(missing)}")
        print(f"  Run: pip install -r requirements.txt")
        return False

    print("✓ All dependencies installed")
    return True


def main():
    """Main entry point."""
    print("\n" + "=" * 50)
    print("  DocAssist EMR - Local AI-Powered EMR")
    print("=" * 50 + "\n")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check Ollama (non-blocking)
    check_ollama()

    print("\nStarting application...\n")

    # Run the app
    run_app()


if __name__ == "__main__":
    main()
