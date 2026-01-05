#!/bin/bash
# Ollama Auto-Setup Script for Linux/macOS
# DocAssist EMR - Local-First AI-Powered EMR

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "============================================================"
echo "🏥 DocAssist EMR - Ollama Auto-Setup (Linux/macOS)"
echo "============================================================"
echo ""

# Detect OS
OS_TYPE=$(uname -s)
echo "[*] Detected OS: $OS_TYPE"

# Check if Python is installed
echo ""
echo "[*] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    echo ""
    if [ "$OS_TYPE" = "Darwin" ]; then
        echo "Install Python on macOS:"
        echo "  brew install python3"
        echo "  or download from: https://www.python.org/downloads/"
    else
        echo "Install Python on Linux:"
        echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
        echo "  Fedora/RHEL: sudo dnf install python3 python3-pip"
        echo "  Arch: sudo pacman -S python python-pip"
    fi
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}[+] Python found: $PYTHON_VERSION${NC}"

# Check if required packages are installed
echo ""
echo "[*] Checking Python dependencies..."

if ! python3 -c "import requests" 2>/dev/null; then
    echo "[!] Installing requests..."
    pip3 install requests
fi

if ! python3 -c "import psutil" 2>/dev/null; then
    echo "[!] Installing psutil..."
    pip3 install psutil
fi

echo -e "${GREEN}[+] Python dependencies OK${NC}"

# Check if Ollama is installed
echo ""
echo "[*] Checking if Ollama is installed..."
if ! command -v ollama &> /dev/null; then
    echo ""
    echo "============================================================"
    echo -e "${YELLOW}OLLAMA NOT FOUND${NC}"
    echo "============================================================"
    echo ""

    if [ "$OS_TYPE" = "Darwin" ]; then
        echo "📥 Install Ollama on macOS:"
        echo ""
        echo "Option 1: Download from https://ollama.ai/download/mac"
        echo "          Open the .dmg and drag to Applications"
        echo ""
        echo "Option 2: Use Homebrew:"
        echo "          brew install ollama"
        echo ""
    else
        echo "📥 Install Ollama on Linux:"
        echo ""
        echo "Run this command:"
        echo -e "${BLUE}  curl -fsSL https://ollama.ai/install.sh | sh${NC}"
        echo ""
        echo "This will:"
        echo "  • Install Ollama to /usr/local/bin"
        echo "  • Create systemd service (if available)"
        echo "  • Start Ollama automatically"
        echo ""
    fi

    echo "============================================================"
    echo "After installation, run this script again."
    echo "============================================================"
    exit 1
fi

OLLAMA_VERSION=$(ollama --version 2>&1 || echo "unknown")
echo -e "${GREEN}[+] Ollama found: $OLLAMA_VERSION${NC}"

# Check if Ollama is running
echo ""
echo "[*] Checking if Ollama service is running..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}[!] Ollama is not running. Starting Ollama...${NC}"

    # Try to start Ollama
    if [ "$OS_TYPE" = "Darwin" ]; then
        # macOS: Try to open the app
        if [ -d "/Applications/Ollama.app" ]; then
            open -a Ollama
            echo "[*] Waiting for Ollama to start..."
            sleep 5
        else
            # Fallback: start as background process
            ollama serve > /dev/null 2>&1 &
            sleep 5
        fi
    else
        # Linux: Try systemctl first
        if command -v systemctl &> /dev/null; then
            if systemctl start ollama 2>/dev/null; then
                echo "[*] Started Ollama via systemctl"
                sleep 3
            else
                # Fallback: start as background process
                echo "[*] Starting Ollama as background process..."
                nohup ollama serve > /tmp/ollama.log 2>&1 &
                sleep 5
            fi
        else
            # No systemctl, start as background process
            echo "[*] Starting Ollama as background process..."
            nohup ollama serve > /tmp/ollama.log 2>&1 &
            sleep 5
        fi
    fi

    # Verify it started
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo ""
        echo -e "${RED}ERROR: Could not start Ollama automatically${NC}"
        echo ""
        echo "Please start Ollama manually:"
        if [ "$OS_TYPE" = "Darwin" ]; then
            echo "  • Open Ollama from Applications, or"
            echo "  • Run in Terminal: ollama serve"
        else
            echo "  • Run: sudo systemctl start ollama, or"
            echo "  • Run: ollama serve"
        fi
        echo ""
        echo "Then run this script again."
        exit 1
    fi
fi

echo -e "${GREEN}[+] Ollama service is running${NC}"

# Run the Python setup script
echo ""
echo "[*] Running Python setup script..."
echo "============================================================"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the Python script
python3 "$SCRIPT_DIR/setup_ollama.py"

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo -e "${GREEN}✅ SUCCESS! Ollama setup complete${NC}"
    echo "============================================================"
    echo ""
    echo "You can now run DocAssist EMR:"
    echo "  python3 main.py"
    echo ""
else
    echo ""
    echo "============================================================"
    echo -e "${YELLOW}Setup encountered errors. Please check the output above.${NC}"
    echo "============================================================"
    echo ""
    exit 1
fi
