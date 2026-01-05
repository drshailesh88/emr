#!/bin/bash
# DocAssist EMR - Unix One-Click Installer
# Shell script wrapper for install.py (works on Linux and macOS)

set -e  # Exit on error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_SCRIPT="$SCRIPT_DIR/install.py"
INSTALL_LINUX="$SCRIPT_DIR/install_linux.sh"
INSTALL_MACOS="$SCRIPT_DIR/install_macos.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'  # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${CYAN}→ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_banner() {
    echo ""
    echo -e "${CYAN}${BOLD}============================================================${NC}"
    echo -e "${CYAN}${BOLD}  DocAssist EMR - Quick Installer${NC}"
    echo -e "${CYAN}  Version 1.0.0${NC}"
    echo -e "${CYAN}${BOLD}============================================================${NC}"
    echo ""
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        OS="unknown"
    fi
}

# Show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Quick installer for DocAssist EMR (Linux and macOS)"
    echo ""
    echo "Options:"
    echo "  --python          Use Python installer (cross-platform, recommended)"
    echo "  --native          Use native platform installer (Linux/macOS specific)"
    echo "  --no-venv         Skip virtual environment creation (Python installer)"
    echo "  --force-venv      Recreate virtual environment (Python installer)"
    echo "  --skip-whisper    Skip Whisper model download (Python installer)"
    echo "  --install-ollama  Install Ollama (native installer)"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Use Python installer (default)"
    echo "  $0 --native                  # Use native platform installer"
    echo "  $0 --native --install-ollama # Native installer with Ollama"
    echo ""
}

# Main installation flow
main() {
    print_banner

    # Detect OS
    detect_os

    if [[ "$OS" == "unknown" ]]; then
        print_error "Unsupported operating system: $OSTYPE"
        print_info "This script supports Linux and macOS only."
        exit 1
    fi

    print_info "Detected OS: $OS"
    echo ""

    # Check for root
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root. Installation may be system-wide."
        echo ""
    fi

    # Parse arguments
    USE_NATIVE=false
    PYTHON_ARGS=()
    NATIVE_ARGS=()

    while [[ $# -gt 0 ]]; do
        case $1 in
            --python)
                USE_NATIVE=false
                shift
                ;;
            --native)
                USE_NATIVE=true
                shift
                ;;
            --no-venv|--force-venv|--skip-whisper)
                PYTHON_ARGS+=("$1")
                shift
                ;;
            --install-ollama|--create-systemd-service|--create-launch-agent|--install-system-deps)
                NATIVE_ARGS+=("$1")
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Choose installer
    if [ "$USE_NATIVE" = true ]; then
        # Use native platform-specific installer
        print_info "Using native platform installer"
        echo ""

        if [[ "$OS" == "linux" ]]; then
            if [ -f "$INSTALL_LINUX" ]; then
                print_info "Running Linux installer: $INSTALL_LINUX"
                bash "$INSTALL_LINUX" "${NATIVE_ARGS[@]}"
                exit $?
            else
                print_error "Linux installer not found: $INSTALL_LINUX"
                exit 1
            fi
        elif [[ "$OS" == "macos" ]]; then
            if [ -f "$INSTALL_MACOS" ]; then
                print_info "Running macOS installer: $INSTALL_MACOS"
                bash "$INSTALL_MACOS" "${NATIVE_ARGS[@]}"
                exit $?
            else
                print_error "macOS installer not found: $INSTALL_MACOS"
                exit 1
            fi
        fi
    else
        # Use Python installer (default, cross-platform)
        print_info "Using Python installer (cross-platform)"
        echo ""

        # Check for Python
        if command -v python3 &> /dev/null; then
            PYTHON_CMD=python3
        elif command -v python &> /dev/null; then
            PYTHON_CMD=python
        else
            print_error "Python is not installed"
            echo ""

            if [[ "$OS" == "linux" ]]; then
                print_info "Install Python on Linux:"
                print_info "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
                print_info "  Fedora: sudo dnf install python3 python3-pip"
                print_info "  Arch: sudo pacman -S python python-pip"
            elif [[ "$OS" == "macos" ]]; then
                print_info "Install Python on macOS:"
                print_info "  brew install python@3.11"
                print_info "  OR download from: https://www.python.org/downloads/"
            fi

            exit 1
        fi

        # Check Python version
        print_info "Checking Python version..."
        $PYTHON_CMD --version
        echo ""

        # Check if install.py exists
        if [ ! -f "$INSTALL_SCRIPT" ]; then
            print_error "Python installer not found: $INSTALL_SCRIPT"
            exit 1
        fi

        # Make install.py executable
        chmod +x "$INSTALL_SCRIPT"

        # Run Python installer
        cd "$PROJECT_DIR"
        $PYTHON_CMD "$INSTALL_SCRIPT" "${PYTHON_ARGS[@]}"
        EXIT_CODE=$?

        echo ""

        if [ $EXIT_CODE -eq 0 ]; then
            echo -e "${GREEN}${BOLD}============================================================${NC}"
            echo -e "${GREEN}${BOLD}  Installation completed successfully!${NC}"
            echo -e "${GREEN}${BOLD}============================================================${NC}"
            echo ""
            echo "Next steps:"
            echo "  1. Activate virtual environment: source venv/bin/activate"
            echo "  2. Run DocAssist: python main.py"
            echo ""

            if [[ "$OS" == "linux" ]]; then
                echo "  3. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
            elif [[ "$OS" == "macos" ]]; then
                echo "  3. Install Ollama: brew install ollama"
            fi

            echo ""
        else
            echo -e "${RED}${BOLD}============================================================${NC}"
            echo -e "${RED}${BOLD}  Installation failed with exit code: $EXIT_CODE${NC}"
            echo -e "${RED}${BOLD}============================================================${NC}"
            echo ""
            echo "Please check the error messages above."
            echo ""
        fi

        exit $EXIT_CODE
    fi
}

# Run main function
main "$@"
