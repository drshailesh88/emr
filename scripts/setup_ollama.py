#!/usr/bin/env python3
"""Ollama Auto-Setup Script for DocAssist EMR.

This script:
1. Detects if Ollama is installed
2. Provides installation instructions if not installed
3. Checks if Ollama service is running
4. Starts Ollama service if not running (where possible)
5. Detects available RAM and selects appropriate model
6. Pulls the selected model if not present
7. Verifies model works with a test prompt

Model Selection:
- RAM < 6GB  → qwen2.5:1.5b (~1.2GB)
- RAM 6-10GB → qwen2.5:3b (~2.5GB)
- RAM > 10GB → qwen2.5:7b (~5GB)
"""

import os
import sys
import platform
import subprocess
import shutil
import time
import json
from pathlib import Path
from typing import Tuple, Optional

try:
    import requests
except ImportError:
    print("❌ Error: 'requests' library not found.")
    print("Please install it: pip install requests")
    sys.exit(1)

try:
    import psutil
except ImportError:
    print("❌ Error: 'psutil' library not found.")
    print("Please install it: pip install psutil")
    sys.exit(1)


class OllamaSetup:
    """Handles Ollama installation, configuration, and model setup."""

    OLLAMA_BASE_URL = "http://localhost:11434"

    # RAM thresholds (GB) and corresponding models
    MODEL_SELECTION = [
        (6, "qwen2.5:1.5b", "~1.2GB", "Low RAM systems"),
        (10, "qwen2.5:3b", "~2.5GB", "Standard systems"),
        (float('inf'), "qwen2.5:7b", "~5GB", "High RAM systems")
    ]

    def __init__(self):
        self.system = platform.system()
        self.total_ram_gb = self._get_total_ram()
        self.selected_model = None
        self.model_size = None
        self.model_description = None

    def _get_total_ram(self) -> float:
        """Get total system RAM in GB."""
        try:
            mem = psutil.virtual_memory()
            return mem.total / (1024 ** 3)
        except Exception as e:
            print(f"⚠️ Warning: Could not detect RAM: {e}")
            return 8.0  # Default assumption

    def _run_command(self, command: list, capture_output: bool = True,
                     timeout: int = 30) -> Tuple[bool, str]:
        """Run a shell command and return success status and output."""
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                return result.returncode == 0, result.stdout + result.stderr
            else:
                result = subprocess.run(command, timeout=timeout)
                return result.returncode == 0, ""
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def check_ollama_installed(self) -> bool:
        """Check if Ollama is installed."""
        print("\n🔍 Checking if Ollama is installed...")

        # Try to find ollama in PATH
        ollama_path = shutil.which("ollama")

        if ollama_path:
            print(f"✅ Ollama found at: {ollama_path}")
            # Try to get version
            success, output = self._run_command(["ollama", "--version"])
            if success:
                print(f"   Version: {output.strip()}")
            return True
        else:
            print("❌ Ollama not found in system PATH")
            return False

    def provide_installation_instructions(self):
        """Provide OS-specific installation instructions."""
        print("\n📥 OLLAMA INSTALLATION REQUIRED")
        print("=" * 60)

        if self.system == "Windows":
            print("\n🪟 Windows Installation:")
            print("1. Download Ollama for Windows:")
            print("   https://ollama.ai/download/windows")
            print("\n2. Run the installer (OllamaSetup.exe)")
            print("3. Follow the installation wizard")
            print("4. Ollama will start automatically after installation")
            print("\nAlternative (PowerShell):")
            print("   winget install Ollama.Ollama")

        elif self.system == "Darwin":  # macOS
            print("\n🍎 macOS Installation:")
            print("1. Download Ollama for macOS:")
            print("   https://ollama.ai/download/mac")
            print("\n2. Open the downloaded .dmg file")
            print("3. Drag Ollama to Applications folder")
            print("4. Launch Ollama from Applications")
            print("\nAlternative (Homebrew):")
            print("   brew install ollama")

        elif self.system == "Linux":
            print("\n🐧 Linux Installation:")
            print("Run this command:")
            print("   curl -fsSL https://ollama.ai/install.sh | sh")
            print("\nThis will:")
            print("• Install Ollama binary to /usr/local/bin")
            print("• Create systemd service (if available)")
            print("• Start Ollama automatically")

        print("\n" + "=" * 60)
        print("After installation, run this script again.")
        print("=" * 60)

    def check_ollama_running(self) -> bool:
        """Check if Ollama service is running."""
        print("\n🔍 Checking if Ollama service is running...")

        try:
            response = requests.get(
                f"{self.OLLAMA_BASE_URL}/api/tags",
                timeout=3
            )
            if response.status_code == 200:
                print("✅ Ollama service is running")
                return True
        except requests.RequestException:
            pass

        print("❌ Ollama service is not responding")
        return False

    def start_ollama_service(self) -> bool:
        """Attempt to start Ollama service."""
        print("\n🚀 Attempting to start Ollama service...")

        if self.system == "Windows":
            print("   Starting Ollama on Windows...")
            # On Windows, Ollama runs as a service or background app
            # Try to start it
            success, _ = self._run_command(
                ["powershell", "-Command", "Start-Process", "ollama", "serve"],
                capture_output=False,
                timeout=5
            )
            time.sleep(3)  # Give it time to start

        elif self.system == "Darwin":  # macOS
            print("   Starting Ollama on macOS...")
            # On macOS, try to start the app
            success, _ = self._run_command(
                ["open", "-a", "Ollama"],
                capture_output=False,
                timeout=5
            )
            time.sleep(3)

        elif self.system == "Linux":
            print("   Starting Ollama on Linux...")
            # Try systemctl first
            success, output = self._run_command(
                ["systemctl", "start", "ollama"],
                capture_output=True,
                timeout=10
            )
            if not success:
                # Try as background process
                try:
                    subprocess.Popen(
                        ["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    success = True
                except Exception:
                    success = False
            time.sleep(3)

        # Verify it's running
        if self.check_ollama_running():
            print("✅ Ollama service started successfully")
            return True
        else:
            print("⚠️ Could not automatically start Ollama")
            print("\nPlease start Ollama manually:")
            if self.system == "Windows":
                print("   • Open Ollama from Start Menu, or")
                print("   • Run: ollama serve")
            elif self.system == "Darwin":
                print("   • Open Ollama from Applications, or")
                print("   • Run in Terminal: ollama serve")
            elif self.system == "Linux":
                print("   • Run: sudo systemctl start ollama, or")
                print("   • Run: ollama serve")
            return False

    def select_model(self) -> Tuple[str, str, str]:
        """Select appropriate model based on system RAM."""
        print("\n🧠 Analyzing system RAM for model selection...")
        print(f"   Total RAM: {self.total_ram_gb:.1f} GB")

        for threshold, model, size, description in self.MODEL_SELECTION:
            if self.total_ram_gb < threshold:
                self.selected_model = model
                self.model_size = size
                self.model_description = description
                print(f"\n✅ Selected: {model}")
                print(f"   Size: {size}")
                print(f"   Reason: {description} ({self.total_ram_gb:.1f}GB RAM)")
                return model, size, description

        # Fallback (shouldn't reach here)
        return "qwen2.5:1.5b", "~1.2GB", "Fallback"

    def check_model_exists(self, model: str) -> bool:
        """Check if a model is already pulled."""
        try:
            response = requests.get(
                f"{self.OLLAMA_BASE_URL}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                for m in models:
                    model_name = m.get("name", "")
                    # Check for exact match or partial match
                    if model in model_name or model_name.startswith(model.split(':')[0]):
                        return True
            return False
        except Exception as e:
            print(f"⚠️ Error checking models: {e}")
            return False

    def pull_model(self, model: str) -> bool:
        """Pull the specified model from Ollama registry."""
        print(f"\n📦 Pulling model: {model}")
        print(f"   This may take several minutes depending on your internet speed...")
        print(f"   Model size: {self.model_size}")

        try:
            # Use ollama CLI for better progress feedback
            print("\n" + "=" * 60)
            success, output = self._run_command(
                ["ollama", "pull", model],
                capture_output=True,
                timeout=600  # 10 minutes timeout
            )
            print("=" * 60)

            if success:
                print(f"\n✅ Model {model} pulled successfully!")
                return True
            else:
                print(f"\n❌ Failed to pull model: {output}")
                return False

        except Exception as e:
            print(f"\n❌ Error pulling model: {e}")
            return False

    def verify_model(self, model: str) -> bool:
        """Verify model works with a test prompt."""
        print(f"\n🧪 Testing model: {model}")
        print("   Running test prompt...")

        try:
            test_prompt = "Respond with just 'OK' if you can read this."

            response = requests.post(
                f"{self.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": test_prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 10
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                result = data.get("response", "").strip()
                print(f"   Model response: {result[:50]}")
                print("✅ Model is working correctly!")
                return True
            else:
                print(f"❌ Model test failed: HTTP {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing model: {e}")
            return False

    def run_setup(self) -> bool:
        """Run the complete setup process."""
        print("\n" + "=" * 60)
        print("🏥 DocAssist EMR - Ollama Auto-Setup")
        print("=" * 60)

        # Step 1: Check if Ollama is installed
        if not self.check_ollama_installed():
            self.provide_installation_instructions()
            return False

        # Step 2: Check if Ollama is running
        if not self.check_ollama_running():
            if not self.start_ollama_service():
                print("\n⚠️ Please start Ollama manually and run this script again.")
                return False

        # Step 3: Select appropriate model
        model, size, description = self.select_model()

        # Step 4: Check if model exists
        print(f"\n🔍 Checking if {model} is already available...")
        if self.check_model_exists(model):
            print(f"✅ Model {model} is already installed")
        else:
            # Step 5: Pull the model
            if not self.pull_model(model):
                print("\n❌ Setup failed: Could not pull model")
                return False

        # Step 6: Verify model works
        if not self.verify_model(model):
            print("\n⚠️ Model verification failed, but it may still work")
            print("   Try running the DocAssist EMR app to confirm")

        # Success!
        print("\n" + "=" * 60)
        print("✅ OLLAMA SETUP COMPLETE!")
        print("=" * 60)
        print(f"\nConfiguration:")
        print(f"  • Model: {model}")
        print(f"  • Size: {size}")
        print(f"  • RAM: {self.total_ram_gb:.1f} GB")
        print(f"\nYou can now run DocAssist EMR:")
        print(f"  python main.py")
        print("\n" + "=" * 60)

        return True


def main():
    """Main entry point."""
    try:
        setup = OllamaSetup()
        success = setup.run_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
