#!/usr/bin/env python3
"""
DocAssist EMR - Cross-Platform Installation Script
Handles Python dependencies, virtual environment, and system checks
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Tuple, Optional

# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

    @staticmethod
    def disable():
        """Disable colors for Windows without ANSI support"""
        Colors.RED = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.CYAN = ''
        Colors.BOLD = ''
        Colors.NC = ''


# Check if running on Windows without ANSI support
if platform.system() == 'Windows' and not os.environ.get('ANSICON'):
    try:
        import colorama
        colorama.init()
    except ImportError:
        Colors.disable()


def print_success(message: str):
    """Print success message in green"""
    print(f"{Colors.GREEN}✓ {message}{Colors.NC}")


def print_info(message: str):
    """Print info message in cyan"""
    print(f"{Colors.CYAN}→ {message}{Colors.NC}")


def print_warning(message: str):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.NC}")


def print_error(message: str):
    """Print error message in red"""
    print(f"{Colors.RED}✗ {message}{Colors.NC}")


def print_banner():
    """Print installation banner"""
    print()
    print(f"{Colors.CYAN}{'═' * 60}{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}  DocAssist EMR - Cross-Platform Installer{Colors.NC}")
    print(f"{Colors.CYAN}  Version 1.0.0{Colors.NC}")
    print(f"{Colors.CYAN}{'═' * 60}{Colors.NC}")
    print()


def get_python_version() -> Tuple[int, int, int]:
    """Get current Python version as tuple"""
    return sys.version_info[:3]


def check_python_version() -> bool:
    """Check if Python version meets requirements (3.11+)"""
    print_info("Checking Python version...")

    version = get_python_version()
    version_str = f"{version[0]}.{version[1]}.{version[2]}"

    print_success(f"Python version: {version_str}")

    if version[0] < 3 or (version[0] == 3 and version[1] < 11):
        print_error(f"Python 3.11+ required, but you have {version_str}")
        print_info("Please upgrade Python from https://www.python.org/downloads/")
        return False

    return True


def check_pip() -> bool:
    """Check if pip is available"""
    print_info("Checking for pip...")

    try:
        import pip
        print_success("pip is installed")
        return True
    except ImportError:
        print_error("pip is not installed")
        print_info("Install pip from https://pip.pypa.io/en/stable/installation/")
        return False


def check_venv_module() -> bool:
    """Check if venv module is available"""
    print_info("Checking for venv module...")

    try:
        import venv
        print_success("venv module is available")
        return True
    except ImportError:
        print_warning("venv module is not available")

        system = platform.system()
        if system == 'Linux':
            print_info("Install with: sudo apt install python3-venv")
        elif system == 'Darwin':
            print_info("venv should be included with Python on macOS")
        elif system == 'Windows':
            print_info("venv should be included with Python on Windows")

        return False


def get_project_root() -> Path:
    """Get the project root directory"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    return project_root


def create_virtual_environment(venv_path: Path, force: bool = False) -> bool:
    """Create a virtual environment"""
    if venv_path.exists():
        if not force:
            print_success(f"Virtual environment already exists at: {venv_path}")
            return True
        else:
            print_info(f"Removing existing virtual environment...")
            shutil.rmtree(venv_path)

    print_info(f"Creating virtual environment at: {venv_path}")

    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True
        )
        print_success("Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False


def get_venv_python(venv_path: Path) -> Path:
    """Get path to Python executable in virtual environment"""
    system = platform.system()

    if system == 'Windows':
        return venv_path / 'Scripts' / 'python.exe'
    else:
        return venv_path / 'bin' / 'python'


def get_venv_pip(venv_path: Path) -> Path:
    """Get path to pip executable in virtual environment"""
    system = platform.system()

    if system == 'Windows':
        return venv_path / 'Scripts' / 'pip.exe'
    else:
        return venv_path / 'bin' / 'pip'


def upgrade_pip(venv_path: Path) -> bool:
    """Upgrade pip in virtual environment"""
    print_info("Upgrading pip...")

    python_exe = get_venv_python(venv_path)

    try:
        subprocess.run(
            [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True
        )
        print_success("pip upgraded")
        return True
    except subprocess.CalledProcessError as e:
        print_warning(f"Failed to upgrade pip: {e}")
        return False


def install_requirements(venv_path: Path, requirements_file: Path) -> bool:
    """Install requirements from requirements.txt"""
    print_info(f"Installing requirements from: {requirements_file}")

    if not requirements_file.exists():
        print_error(f"requirements.txt not found at: {requirements_file}")
        return False

    python_exe = get_venv_python(venv_path)

    try:
        # Install with progress output
        process = subprocess.Popen(
            [str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Stream output
        if process.stdout:
            for line in process.stdout:
                line = line.strip()
                if line and not line.startswith('Requirement already satisfied'):
                    print(f"  {line}")

        return_code = process.wait()

        if return_code == 0:
            print_success("Requirements installed successfully")
            return True
        else:
            print_error(f"Failed to install requirements (exit code: {return_code})")
            return False

    except Exception as e:
        print_error(f"Error installing requirements: {e}")
        return False


def install_platform_dependencies() -> bool:
    """Install platform-specific dependencies"""
    system = platform.system()
    print_info(f"Detected platform: {system}")

    if system == 'Windows':
        print_info("Windows-specific dependencies:")
        print_info("  - Consider installing Visual C++ Redistributable if you encounter errors")
        print_info("  - Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe")

    elif system == 'Darwin':
        print_info("macOS-specific dependencies:")

        # Check for Homebrew
        if shutil.which('brew'):
            print_success("Homebrew is installed")
        else:
            print_warning("Homebrew not found (optional but recommended)")
            print_info("Install from: https://brew.sh")

    elif system == 'Linux':
        print_info("Linux-specific dependencies:")

        # Detect distribution
        try:
            with open('/etc/os-release', 'r') as f:
                os_release = f.read()
                if 'ubuntu' in os_release.lower() or 'debian' in os_release.lower():
                    print_info("Ubuntu/Debian detected")
                    print_info("Install system deps: sudo apt install python3-dev build-essential")
                elif 'fedora' in os_release.lower():
                    print_info("Fedora detected")
                    print_info("Install system deps: sudo dnf install python3-devel gcc gcc-c++")
                elif 'arch' in os_release.lower():
                    print_info("Arch Linux detected")
                    print_info("Install system deps: sudo pacman -S python base-devel")
        except FileNotFoundError:
            print_info("Unknown Linux distribution")

    return True


def download_whisper_model(venv_path: Path) -> bool:
    """Download Whisper model for voice input (optional)"""
    print_info("Checking Whisper model...")

    python_exe = get_venv_python(venv_path)

    # Check if faster-whisper is installed
    try:
        result = subprocess.run(
            [str(python_exe), "-c", "import faster_whisper"],
            capture_output=True,
            timeout=10
        )

        if result.returncode != 0:
            print_info("Whisper not installed (optional feature)")
            print_info("Install with: pip install faster-whisper sounddevice numpy")
            return True

        print_success("Whisper is available")

        # Try to download base model
        print_info("Downloading Whisper base model (this may take a while)...")

        test_code = """
from faster_whisper import WhisperModel
try:
    model = WhisperModel("base", device="cpu", compute_type="int8")
    print("Model downloaded successfully")
except Exception as e:
    print(f"Error: {e}")
"""

        result = subprocess.run(
            [str(python_exe), "-c", test_code],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if "Model downloaded successfully" in result.stdout:
            print_success("Whisper model downloaded")
            return True
        else:
            print_warning("Could not download Whisper model automatically")
            print_info("Model will be downloaded on first use")
            return True

    except subprocess.TimeoutExpired:
        print_warning("Whisper model download timed out")
        print_info("Model will be downloaded on first use")
        return True
    except Exception as e:
        print_warning(f"Could not check Whisper: {e}")
        return True


def verify_imports(venv_path: Path) -> bool:
    """Verify critical imports work"""
    print_info("Verifying critical imports...")

    python_exe = get_venv_python(venv_path)

    critical_imports = [
        'flet',
        'requests',
        'pydantic',
        'chromadb',
        'sentence_transformers',
        'fpdf2',
        'psutil',
        'dotenv',
        'nacl'
    ]

    failed_imports = []

    for module in critical_imports:
        module_import = module if module != 'dotenv' else 'dotenv'
        module_import = module_import if module != 'nacl' else 'nacl'

        try:
            result = subprocess.run(
                [str(python_exe), "-c", f"import {module_import}"],
                capture_output=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"  ✓ {module}")
            else:
                print(f"  ✗ {module}")
                failed_imports.append(module)

        except Exception as e:
            print(f"  ✗ {module} (error: {e})")
            failed_imports.append(module)

    if failed_imports:
        print_error(f"Failed to import: {', '.join(failed_imports)}")
        return False

    print_success("All critical imports verified")
    return True


def check_system_resources():
    """Check system RAM and disk space"""
    print_info("Checking system resources...")

    try:
        import psutil

        # Check RAM
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        print_success(f"RAM: {ram_gb:.1f} GB")

        if ram_gb < 4:
            print_warning(f"Low RAM: {ram_gb:.1f} GB. At least 4 GB recommended for LLM features.")

        # Check disk space
        project_root = get_project_root()
        disk = psutil.disk_usage(str(project_root))
        free_gb = disk.free / (1024 ** 3)

        print_success(f"Free disk space: {free_gb:.1f} GB")

        if free_gb < 5:
            print_warning(f"Low disk space: {free_gb:.1f} GB. At least 5 GB recommended.")

    except Exception as e:
        print_warning(f"Could not check system resources: {e}")


def create_env_file(project_root: Path) -> bool:
    """Create .env file from .env.example if it doesn't exist"""
    print_info("Checking .env file...")

    env_file = project_root / '.env'
    env_example = project_root / '.env.example'

    if env_file.exists():
        print_success(".env file already exists")
        return True

    if env_example.exists():
        try:
            shutil.copy(env_example, env_file)
            print_success("Created .env file from .env.example")
            return True
        except Exception as e:
            print_error(f"Failed to create .env file: {e}")
            return False
    else:
        print_warning(".env.example not found, skipping .env creation")
        return True


def show_post_install_instructions(venv_path: Path, project_root: Path):
    """Display post-installation instructions"""
    system = platform.system()

    print()
    print(f"{Colors.GREEN}{'═' * 60}{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}  Installation Complete!{Colors.NC}")
    print(f"{Colors.GREEN}{'═' * 60}{Colors.NC}")
    print()
    print(f"{Colors.CYAN}Next Steps:{Colors.NC}")
    print()

    # Activation instructions
    print(f"{Colors.BOLD}1. Activate the virtual environment:{Colors.NC}")

    if system == 'Windows':
        print(f"   {venv_path}\\Scripts\\activate")
    else:
        print(f"   source {venv_path}/bin/activate")

    print()

    # Run instructions
    print(f"{Colors.BOLD}2. Start DocAssist EMR:{Colors.NC}")
    print(f"   python main.py")
    print()

    # Ollama instructions
    print(f"{Colors.BOLD}3. Install and configure Ollama (for LLM features):{Colors.NC}")

    if system == 'Windows':
        print(f"   Download from: https://ollama.ai/download/windows")
    elif system == 'Darwin':
        print(f"   brew install ollama")
        print(f"   OR download from: https://ollama.ai/download/mac")
    else:
        print(f"   curl -fsSL https://ollama.ai/install.sh | sh")

    print()
    print(f"   Then pull a model:")
    print(f"   ollama pull qwen2.5:3b")
    print()

    # Optional features
    print(f"{Colors.BOLD}4. Optional features:{Colors.NC}")
    print(f"   Voice input: pip install faster-whisper sounddevice numpy")
    print(f"   S3 backup: pip install boto3")
    print()

    print(f"{Colors.CYAN}For more information:{Colors.NC}")
    print(f"   README: {project_root / 'README.md'}")
    print(f"   Documentation: {project_root / 'CLAUDE.md'}")
    print()


def main():
    """Main installation flow"""
    print_banner()

    # Parse arguments
    use_venv = '--no-venv' not in sys.argv
    force_venv = '--force-venv' in sys.argv
    skip_whisper = '--skip-whisper' in sys.argv

    if '--help' in sys.argv or '-h' in sys.argv:
        print("Usage: python install.py [OPTIONS]")
        print()
        print("Options:")
        print("  --no-venv         Skip virtual environment creation")
        print("  --force-venv      Recreate virtual environment if exists")
        print("  --skip-whisper    Skip Whisper model download")
        print("  -h, --help        Show this help message")
        print()
        return 0

    # Check Python version
    if not check_python_version():
        return 1

    # Check pip
    if not check_pip():
        return 1

    # Get project root
    project_root = get_project_root()
    print_info(f"Project root: {project_root}")
    print()

    # Check platform dependencies
    install_platform_dependencies()
    print()

    # Virtual environment setup
    venv_path = project_root / 'venv'

    if use_venv:
        # Check venv module
        if not check_venv_module():
            print_warning("Continuing without virtual environment")
            use_venv = False
        else:
            # Create virtual environment
            if not create_virtual_environment(venv_path, force=force_venv):
                return 1
            print()

            # Upgrade pip
            upgrade_pip(venv_path)
            print()
    else:
        print_info("Skipping virtual environment (--no-venv)")
        venv_path = Path(sys.prefix)  # Use current Python environment
        print()

    # Install requirements
    requirements_file = project_root / 'requirements.txt'
    if not install_requirements(venv_path, requirements_file):
        return 1
    print()

    # Check system resources
    check_system_resources()
    print()

    # Verify imports
    if not verify_imports(venv_path):
        print_error("Some imports failed. Please check the error messages above.")
        return 1
    print()

    # Download Whisper model (optional)
    if not skip_whisper:
        download_whisper_model(venv_path)
        print()

    # Create .env file
    create_env_file(project_root)
    print()

    # Show post-install instructions
    show_post_install_instructions(venv_path, project_root)

    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        print_warning("Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
